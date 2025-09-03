#!/bin/bash
set -euxo pipefail

# Test build script for a single architecture to validate the complete pipeline
# This script tests building arm64-v8a to ensure all dependencies work correctly

ABI=arm64-v8a
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin
GITHUB_WORKSPACE=${GITHUB_WORKSPACE:-/home/runner/work/vosk-api/vosk-api}
WORK=$GITHUB_WORKSPACE/android/lib/build/$ABI

# Add NDK tools to PATH
export PATH=$ANDROID_TOOLCHAIN_PATH:$PATH

echo "=== Testing complete build for $ABI ==="
echo "ANDROID_NDK_HOME: $ANDROID_NDK_HOME"
echo "WORK: $WORK"

# Create work directory
mkdir -p $WORK
cd $WORK

echo "=== Building OpenBLAS ==="
# Build OpenBLAS (already done, so skip if exists)
if [ ! -f local/lib/libopenblas.a ]; then
    echo "OpenBLAS not found, please run the OpenBLAS build first"
    exit 1
fi

echo "=== Building CLAPACK ==="
# CLAPACK
if [ ! -d clapack ]; then
    git clone -b v3.2.1 --single-branch https://github.com/alphacep/clapack
fi

# Set compiler variables for arm64-v8a
HOST=aarch64-linux-android
CC=$ANDROID_TOOLCHAIN_PATH/aarch64-linux-android21-clang
ARCHFLAGS=""

mkdir -p clapack/BUILD && cd clapack/BUILD
cmake -DCMAKE_C_FLAGS="$ARCHFLAGS" -DCMAKE_C_COMPILER_TARGET=$HOST \
  -DCMAKE_C_COMPILER=$CC -DCMAKE_SYSTEM_NAME=Generic \
  -DCMAKE_AR=$ANDROID_TOOLCHAIN_PATH/llvm-ar \
  -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
  -DCMAKE_CROSSCOMPILING=True ..
make -j 4 -C F2CLIBS/libf2c
make -j 4 -C BLAS/SRC  
make -j 4 -C SRC
find . -name "*.a" | xargs cp -t $WORK/local/lib

echo "=== Building OpenFST ==="
cd $WORK
# OpenFST
if [ ! -d openfst ]; then
    git clone https://github.com/alphacep/openfst
fi
cd openfst

CXX=$ANDROID_TOOLCHAIN_PATH/aarch64-linux-android21-clang++

autoreconf -i
CXX=$CXX CXXFLAGS="$ARCHFLAGS -O3 -DFST_NO_DYNAMIC_LINKING" ./configure --prefix=${WORK}/local \
  --enable-shared --enable-static --with-pic --disable-bin \
  --enable-lookahead-fsts --enable-ngram-fsts --host=$HOST --build=x86-linux-gnu
make -j 4
make install

echo "=== Building Kaldi ==="
cd $WORK
# Kaldi
if [ ! -d kaldi ]; then
    git clone -b vosk-android --single-branch https://github.com/alphacep/kaldi
fi

cd $WORK/kaldi/src
CXX=$CXX AR=$ANDROID_TOOLCHAIN_PATH/llvm-ar RANLIB=$ANDROID_TOOLCHAIN_PATH/llvm-ranlib CXXFLAGS="$ARCHFLAGS -O3 -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
  --mathlib=OPENBLAS_CLAPACK --shared \
  --android-incdir=${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include \
  --host=$HOST --openblas-root=${WORK}/local \
  --fst-root=${WORK}/local --fst-version=1.8.0
make -j 4 depend
make -j 4 online2 rnnlm

echo "=== Building Vosk ==="
cd $WORK

CXX=$ANDROID_TOOLCHAIN_PATH/aarch64-linux-android21-clang++
PAGESIZE_LDFLAGS="-Wl,-z,common-page-size=4096 -Wl,-z,max-page-size=16384"

mkdir -p $WORK/vosk
make -j 4 -C $GITHUB_WORKSPACE/src \
  OUTDIR=$WORK/vosk \
  KALDI_ROOT=${WORK}/kaldi \
  OPENFST_ROOT=${WORK}/local \
  OPENBLAS_ROOT=${WORK}/local \
  CXX=$CXX \
  EXTRA_LDFLAGS="-llog -static-libstdc++ -Wl,-soname,libvosk.so ${PAGESIZE_LDFLAGS}"

# Copy to JNI directory
mkdir -p $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI
cp $WORK/vosk/libvosk.so $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so

echo "=== Verify Build Output ==="
echo "Generated libvosk.so for $ABI:"
ls -lh $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/
file $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so

echo "=== Build completed successfully! ==="