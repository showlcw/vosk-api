#!/bin/bash
set -euxo pipefail

# Quick validation script to check if the build environment is properly configured

echo "=== Vosk-API Android Build Validation ==="

# Check Android NDK
if [ -z "${ANDROID_NDK_HOME:-}" ]; then
    echo "❌ ANDROID_NDK_HOME is not set"
    exit 1
fi

if [ ! -d "$ANDROID_NDK_HOME" ]; then
    echo "❌ ANDROID_NDK_HOME directory does not exist: $ANDROID_NDK_HOME"
    exit 1
fi

echo "✅ ANDROID_NDK_HOME: $ANDROID_NDK_HOME"

# Check required tools
REQUIRED_TOOLS="cmake ninja git"
for tool in $REQUIRED_TOOLS; do
    if command -v $tool > /dev/null 2>&1; then
        echo "✅ $tool: $(command -v $tool)"
    else
        echo "❌ $tool is not installed"
        exit 1
    fi
done

# Check Android toolchain
TOOLCHAIN="$ANDROID_NDK_HOME/build/cmake/android.toolchain.cmake"
if [ -f "$TOOLCHAIN" ]; then
    echo "✅ Android CMake toolchain found"
else
    echo "❌ Android CMake toolchain not found: $TOOLCHAIN"
    exit 1
fi

# Check NDK compilers for each architecture
ARCHITECTURES="arm64-v8a armeabi-v7a"
TOOLCHAIN_BIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin"

for arch in $ARCHITECTURES; do
    case $arch in
        arm64-v8a) COMPILER="aarch64-linux-android21-clang++" ;;
        armeabi-v7a) COMPILER="armv7a-linux-androideabi21-clang++" ;;
        x86_64) COMPILER="x86_64-linux-android21-clang++" ;;
        x86) COMPILER="i686-linux-android21-clang++" ;;
    esac
    
    if [ -f "$TOOLCHAIN_BIN/$COMPILER" ]; then
        echo "✅ $arch compiler: $COMPILER"
    else
        echo "❌ $arch compiler not found: $COMPILER"
        exit 1
    fi
done

# Check build script
BUILD_SCRIPT="/home/runner/work/vosk-api/vosk-api/android/lib/build-vosk.sh"
if [ -f "$BUILD_SCRIPT" ] && [ -x "$BUILD_SCRIPT" ]; then
    echo "✅ Build script found and executable"
else
    echo "❌ Build script not found or not executable: $BUILD_SCRIPT"
    exit 1
fi

# Check source files
VOSK_SRC="/home/runner/work/vosk-api/vosk-api/src"
if [ -d "$VOSK_SRC" ] && [ -f "$VOSK_SRC/vosk_api.cc" ]; then
    echo "✅ Vosk source files found"
else
    echo "❌ Vosk source files not found in: $VOSK_SRC"
    exit 1
fi

# Check Android library structure
ANDROID_LIB="/home/runner/work/vosk-api/vosk-api/android/lib"
if [ -f "$ANDROID_LIB/build.gradle" ]; then
    echo "✅ Android library build.gradle found"
else
    echo "❌ Android library build.gradle not found"
    exit 1
fi

# Check jniLibs directories
for arch in $ARCHITECTURES; do
    JNI_DIR="$ANDROID_LIB/src/main/jniLibs/$arch"
    if [ -d "$JNI_DIR" ]; then
        echo "✅ jniLibs directory for $arch exists"
    else
        echo "❌ jniLibs directory for $arch not found: $JNI_DIR"
        exit 1
    fi
done

echo ""
echo "🎉 All validation checks passed!"
echo ""
echo "Build environment is properly configured for Android compilation."
echo "You can now run the full build using:"
echo "  - GitHub Actions workflow (recommended)"
echo "  - Local build: cd android/lib && ./build-vosk.sh"
echo ""

# Show configuration summary
echo "=== Configuration Summary ==="
echo "NDK Version: $(cat $ANDROID_NDK_HOME/source.properties | grep Pkg.Revision | cut -d'=' -f2 | tr -d ' ')"
echo "CMake Version: $(cmake --version | head -1)"
echo "Ninja Version: $(ninja --version)"
echo "Supported Architectures: $ARCHITECTURES"
echo "======================="