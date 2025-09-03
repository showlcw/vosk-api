# Building Vosk-API for Android

This document explains how to build Vosk-API for Android to generate .so files for different architectures and package them into an AAR file.

## Prerequisites

- Android NDK (r25b or later)
- CMake
- Ninja build system
- Git

## Architecture Support

The build system supports the following Android architectures:
- `arm64-v8a` (64-bit ARM) ✅
- `armeabi-v7a` (32-bit ARM) ✅

*Note: x86 and x86_64 support is temporarily disabled due to OpenBLAS compilation issues. ARM architectures cover the majority of Android devices.*

## Build Process

### GitHub Actions (Recommended)

The easiest way to build is using the GitHub Actions workflow:

1. Push changes to trigger the workflow
2. The workflow will build all architectures in parallel
3. Download the generated AAR file from the artifacts

### Manual Local Build

For local development:

```bash
# Set environment variable
export ANDROID_NDK_HOME=/path/to/your/android-ndk

# Navigate to Android library directory
cd android/lib

# Run the build script (builds all architectures)
./build-vosk.sh

# Build the AAR using Gradle
cd ..
./gradlew :lib:assembleRelease
```

## Build Components

The build process compiles these components in order:

1. **OpenBLAS** - Linear algebra library
2. **CLAPACK** - Linear algebra routines
3. **OpenFST** - Finite state transducers
4. **Kaldi** - Speech recognition toolkit
5. **Vosk** - Main speech recognition library

## Generated Artifacts

### .so Files
Located in `android/lib/src/main/jniLibs/<architecture>/libvosk.so`

### AAR File
Located in `android/lib/build/outputs/aar/vosk-android-<version>-release.aar`

## Troubleshooting

### NDK Issues
- Ensure ANDROID_NDK_HOME is set correctly
- Use NDK r25b or later
- Make sure CMake and Ninja are installed

### Build Failures
- Check that all Git submodules are cloned
- Verify sufficient disk space (build requires ~5GB per architecture)
- Review error logs for specific component failures

## Using the Generated Libraries

The AAR file can be used in Android projects:

```gradle
dependencies {
    implementation 'com.alphacephei:vosk-android:0.3.50'
}
```

The .so files can be used directly:
- Copy to `src/main/jniLibs/<architecture>/` in your Android project
- Use JNA or JNI to load the library

## Configuration

Build configuration can be modified in:
- `.github/workflows/build-android.yml` - CI/CD settings
- `android/lib/build-vosk.sh` - Build script parameters
- `android/lib/build.gradle` - Gradle build settings