#!/bin/bash
set -euxo pipefail

# Quick build script to generate a working .so file for arm64-v8a
# This demonstrates that the build system is now functional

echo "=== Quick Build Demo for arm64-v8a ==="
echo "This script will build a libvosk.so file to demonstrate the fixes"

ABI=arm64-v8a
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin
GITHUB_WORKSPACE=${GITHUB_WORKSPACE:-/home/runner/work/vosk-api/vosk-api}
WORK=$GITHUB_WORKSPACE/android/lib/build/$ABI

# Skip if already exists
if [ -f "$GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so" ]; then
    echo "libvosk.so already exists for $ABI"
    ls -lh "$GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so"
    file "$GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so"
    echo "=== Build demo completed - .so file exists! ==="
    exit 0
fi

echo "Starting build process..."

# The OpenBLAS and dependencies are already built from our previous test
# Let's try to build just Vosk directly

if [ ! -f "$WORK/local/lib/libopenblas.a" ]; then
    echo "ERROR: OpenBLAS not found. Please run the full build first."
    exit 1
fi

# Check if we have the other dependencies
if [ ! -d "$WORK/clapack" ] || [ ! -d "$WORK/openfst" ] || [ ! -d "$WORK/kaldi" ]; then
    echo "Missing dependencies. Please run the full test script first."
    echo "Required dependencies:"
    echo "  - $WORK/clapack"
    echo "  - $WORK/openfst" 
    echo "  - $WORK/kaldi"
    exit 1
fi

echo "Dependencies found. Building Vosk..."

cd $WORK

# Set compiler for arm64-v8a
CXX=$ANDROID_TOOLCHAIN_PATH/aarch64-linux-android21-clang++
PAGESIZE_LDFLAGS="-Wl,-z,common-page-size=4096 -Wl,-z,max-page-size=16384"

# Create Vosk output directory
mkdir -p $WORK/vosk

# Build Vosk
echo "Building libvosk.so..."
make -j 4 -C $GITHUB_WORKSPACE/src \
  OUTDIR=$WORK/vosk \
  KALDI_ROOT=${WORK}/kaldi \
  OPENFST_ROOT=${WORK}/local \
  OPENBLAS_ROOT=${WORK}/local \
  CXX=$CXX \
  EXTRA_LDFLAGS="-llog -static-libstdc++ -Wl,-soname,libvosk.so ${PAGESIZE_LDFLAGS}"

# Copy to JNI directory
echo "Installing libvosk.so..."
mkdir -p $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI
cp $WORK/vosk/libvosk.so $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so

echo "=== Build Results ==="
echo "Generated libvosk.so for $ABI:"
ls -lh $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/
file $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so

echo ""
echo "🎉 SUCCESS! libvosk.so has been generated successfully!"
echo ""
echo "Location: $GITHUB_WORKSPACE/android/lib/src/main/jniLibs/$ABI/libvosk.so"
echo "This demonstrates that the build system is now working correctly."
echo ""
echo "To build all architectures, run the GitHub Actions workflow or use:"
echo "  ./scripts/test-build-single-arch.sh  # for local testing"
echo "  # or trigger the GitHub Actions workflow for all architectures"