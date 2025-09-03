# Quick Start Guide

## Building Vosk-API for Android

This repository now includes a complete build system for generating Android .so files and AAR packages for multiple architectures.

### Prerequisites

- Android NDK r25b or later
- CMake 3.10+
- Ninja build system

### Quick Build (GitHub Actions)

1. **Push to trigger build**: Any push will trigger the Android build workflow
2. **Download artifacts**: Check the Actions tab for generated .so files and AAR packages
3. **Use in your project**: Download and integrate the AAR file

### Local Build

1. **Validate environment**:
   ```bash
   ./scripts/validate-build-env.sh
   ```

2. **Build all architectures**:
   ```bash
   cd android/lib
   ./build-vosk.sh
   ```

3. **Package AAR** (requires Android SDK):
   ```bash
   cd android
   ./gradlew :lib:assembleRelease
   ```

### Generated Files

- **Native libraries**: `android/lib/src/main/jniLibs/<arch>/libvosk.so`
- **AAR package**: `android/lib/build/outputs/aar/vosk-android-*.aar`

### Supported Architectures

- `arm64-v8a` - 64-bit ARM (modern Android devices) ✅
- `armeabi-v7a` - 32-bit ARM (older Android devices) ✅

*Note: x86 and x86_64 support is currently disabled due to OpenBLAS compilation issues. See [TODO-x86-support.md](TODO-x86-support.md) for details.*

### Documentation

See [BUILD-ANDROID.md](BUILD-ANDROID.md) for detailed build instructions and troubleshooting.

### Usage in Android Projects

Add the AAR to your project:

```gradle
dependencies {
    implementation 'com.alphacephei:vosk-android:0.3.50'
}
```

Or copy the .so files to your `src/main/jniLibs/` directory.