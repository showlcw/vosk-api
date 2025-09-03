# TODO: x86/x86_64 Android Architecture Support

## Issue
The current Android build system supports ARM architectures (arm64-v8a, armeabi-v7a) but not x86/x86_64 due to OpenBLAS compilation issues.

## Root Cause
OpenBLAS v0.3.20 has cross-compilation issues for x86 Android targets:
- `DTB_DEFAULT_ENTRIES` undefined errors in kernel/*.c files
- Cross-compilation detection fails with Android NDK compilers
- Unit tests being compiled despite `BUILD_TESTING=OFF`

## Potential Solutions
1. **Use OpenBLAS alternatives for x86**: Switch to a simpler BLAS implementation like Eigen or a precompiled OpenBLAS for x86
2. **Manual kernel patching**: Create patches for the specific OpenBLAS kernel files that fail to compile
3. **Alternative BLAS library**: Use Intel MKL, ATLAS, or another BLAS implementation that has better Android x86 support
4. **Conditional x86 support**: Build x86 versions without BLAS optimization (generic fallback)

## Priority
Low - ARM architectures cover the majority of Android devices. x86 is mainly needed for emulators and some tablets.

## Files to modify when implementing
- `.github/workflows/build-android.yml`
- `android/lib/build-vosk.sh`
- `scripts/validate-build-env.sh`