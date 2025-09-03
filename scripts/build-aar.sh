#!/bin/bash
set -euxo pipefail

# Build AAR file from generated .so files
# This script packages all the .so files into an Android AAR

echo "=== Building Vosk Android AAR ==="

GITHUB_WORKSPACE=${GITHUB_WORKSPACE:-/home/runner/work/vosk-api/vosk-api}
cd $GITHUB_WORKSPACE

# Check if we have .so files for all architectures
ARCHITECTURES="arm64-v8a armeabi-v7a x86_64 x86"
MISSING_LIBS=""

echo "Checking for .so files..."
for arch in $ARCHITECTURES; do
    SO_FILE="android/lib/src/main/jniLibs/$arch/libvosk.so"
    if [ -f "$SO_FILE" ]; then
        echo "✅ Found: $SO_FILE"
        ls -lh "$SO_FILE"
    else
        echo "❌ Missing: $SO_FILE"
        MISSING_LIBS="$MISSING_LIBS $arch"
    fi
done

if [ -n "$MISSING_LIBS" ]; then
    echo ""
    echo "⚠️  Warning: Missing .so files for architectures:$MISSING_LIBS"
    echo "The AAR will be built with available architectures only."
    echo ""
fi

# Ensure we have at least one .so file
SO_COUNT=$(find android/lib/src/main/jniLibs -name "libvosk.so" | wc -l)
if [ $SO_COUNT -eq 0 ]; then
    echo "❌ Error: No libvosk.so files found!"
    echo "Please run the build process first to generate .so files."
    exit 1
fi

echo "Found $SO_COUNT .so files. Proceeding with AAR build..."

# Navigate to Android project directory
cd android

# Clean previous builds
echo "Cleaning previous builds..."
./gradlew clean

# Build the AAR
echo "Building AAR..."
./gradlew :lib:assembleRelease

# Check if AAR was generated
AAR_DIR="lib/build/outputs/aar"
AAR_FILE=$(find $AAR_DIR -name "*.aar" | head -1)

if [ -f "$AAR_FILE" ]; then
    echo ""
    echo "🎉 SUCCESS! AAR file generated:"
    ls -lh $AAR_FILE
    
    echo ""
    echo "AAR Contents:"
    unzip -l $AAR_FILE
    
    echo ""
    echo "✅ AAR file location: $AAR_FILE"
    echo ""
    echo "You can now use this AAR file in your Android projects by:"
    echo "1. Copying it to your project's libs/ directory"
    echo "2. Adding it to your build.gradle dependencies:"
    echo "   implementation files('libs/$(basename $AAR_FILE)')"
    echo ""
    echo "Or publish it to a repository for easier distribution."
else
    echo "❌ Error: AAR file was not generated!"
    echo "Check the Gradle build output above for errors."
    exit 1
fi