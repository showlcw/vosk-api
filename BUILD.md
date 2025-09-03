# Vosk-API Automated Build System

This document describes the automated build system for vosk-api that simplifies compilation and provides a one-command build process.

## Quick Start

### One-Command Build
```bash
# Build everything with optimal settings
./build.sh

# Or use the Python script directly
python3 build.py
```

### Prerequisites
The build script will check for and guide you through installing:

- **CMake** (3.13+) - Build system
- **C++ Compiler** (GCC/Clang) - For C++ compilation  
- **Python 3** - For Python bindings and build script
- **Make** - Build automation
- **Git** - For dependency management
- **Kaldi** - Speech recognition toolkit (see setup below)

## Build Options

### Build Configurations
```bash
./build.sh --config Debug          # Debug build with symbols
./build.sh --config Release        # Optimized release build (default)
./build.sh --config RelWithDebInfo # Optimized with debug info
```

### Language Bindings
```bash
./build.sh --python                # Python bindings (default: enabled)
./build.sh --java                  # Java bindings
./build.sh --csharp                # C# bindings
./build.sh --python --java         # Multiple language bindings
./build.sh --bindings-only         # Skip C++ build, bindings only
```

### Math Libraries
```bash
./build.sh --math-lib openblas     # Use OpenBLAS
./build.sh --math-lib mkl          # Use Intel MKL  
./build.sh --math-lib auto         # Auto-detect (default)
```

### Advanced Options
```bash
./build.sh --cuda                  # Enable CUDA GPU support
./build.sh --use-cmake             # Use CMake instead of Make
./build.sh --install               # Install after building
./build.sh --test                  # Run tests after building
./build.sh --wheel                 # Build Python wheel package
./build.sh --clean                 # Clean build directory first
./build.sh --verbose               # Verbose build output
./build.sh --force                 # Continue despite missing dependencies
```

## Kaldi Setup

Vosk-API requires the Kaldi speech recognition toolkit. The build script will guide you through setup if Kaldi is not found.

### Automatic Detection
The script looks for Kaldi in these locations:
- `$KALDI_ROOT` environment variable
- `../kaldi` (relative to vosk-api)
- `~/kaldi` 
- `~/travis/kaldi`
- `/opt/kaldi`
- `/usr/local/kaldi`

### Manual Kaldi Setup
```bash
# Download and build Kaldi
git clone https://github.com/kaldi-asr/kaldi.git
cd kaldi/tools
make -j$(nproc)
cd ../src  
./configure --shared
make depend -j$(nproc)
make -j$(nproc)

# Set environment variable
export KALDI_ROOT=/path/to/kaldi

# Add to your shell profile (.bashrc, .zshrc, etc.)
echo 'export KALDI_ROOT=/path/to/kaldi' >> ~/.bashrc
```

## Build Examples

### Standard Development Build
```bash
# Full build with Python bindings and tests
./build.sh --config Debug --test
```

### Production Release Build  
```bash
# Optimized build with installation
./build.sh --config Release --install
```

### Python Package Development
```bash
# Build Python wheel for distribution
./build.sh --python --wheel --config Release
```

### Multi-Language Build
```bash
# Build all language bindings
./build.sh --python --java --csharp --test
```

### High-Performance Build
```bash
# Build with CUDA and Intel MKL
./build.sh --config Release --cuda --math-lib mkl --install
```

### CI/CD Build
```bash
# Build suitable for continuous integration
./build.sh --config Release --python --wheel --test --force
```

## Troubleshooting

### Common Issues

#### Kaldi Not Found
```
[ERROR] Kaldi is required for building vosk-api
```
**Solution:** Install Kaldi following the setup instructions above, or use `--force --bindings-only` to build only language bindings.

#### Missing Dependencies
```
[ERROR] Missing required dependencies:
  - cmake - CMake (required for building)
```
**Solution:** Install the missing packages using your system package manager:
```bash
# Ubuntu/Debian
sudo apt-get install cmake build-essential python3-dev

# CentOS/RHEL  
sudo yum install cmake gcc-c++ python3-devel

# macOS
brew install cmake python3
```

#### Python Package Issues
```
[ERROR] Python package cffi not found
```
**Solution:** The script will automatically install required Python packages, or install manually:
```bash
pip3 install cffi setuptools wheel
```

#### CUDA Issues
```
[WARNING] CUDA requested but not found
```
**Solution:** Install CUDA toolkit or remove `--cuda` flag:
```bash
# Check CUDA installation
nvidia-smi
nvcc --version
```

### Build Environment

#### Environment Variables
The build script uses these environment variables:

- `KALDI_ROOT` - Path to Kaldi installation
- `CMAKE_BUILD_TYPE` - Build configuration
- `VOSK_SOURCE` - Path to vosk-api source (auto-detected)
- `CUDA_ROOT` - CUDA installation path (default: /usr/local/cuda)

#### Build Artifacts
Build outputs are placed in:
- `build/` - CMake build directory
- `src/*.so` - Compiled shared libraries (Make builds)  
- `python/dist/` - Python wheel packages
- `python/build/` - Python build artifacts

## Integration

### Makefile Integration
Add to your project Makefile:
```makefile
.PHONY: vosk
vosk:
	cd vosk-api && ./build.sh --config Release --install

clean-vosk:
	cd vosk-api && ./build.sh --clean
```

### CMake Integration
Add to your CMakeLists.txt:
```cmake
# Build vosk-api as external project
include(ExternalProject)
ExternalProject_Add(vosk-api
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/vosk-api
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ./build.sh --config ${CMAKE_BUILD_TYPE} --use-cmake
    INSTALL_COMMAND ""
    BUILD_IN_SOURCE TRUE
)
```

### Docker Integration  
```dockerfile
FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    cmake build-essential python3-dev git

# Build vosk-api
COPY vosk-api /vosk-api
WORKDIR /vosk-api
RUN ./build.sh --config Release --install
```

## Advanced Usage

### Custom Build Options
You can customize the build by setting environment variables:
```bash
# Custom compiler
export CXX=clang++
./build.sh

# Custom optimization flags  
export EXTRA_CFLAGS="-march=native -mtune=native"
./build.sh --config Release

# Custom installation prefix
./build.sh --install --install-prefix /opt/vosk
```

### Parallel Builds
The script automatically uses all available CPU cores, but you can control this:
```bash
# Limit to 4 cores
export MAKEFLAGS="-j4" 
./build.sh
```

### Cross-Compilation
For cross-compilation, set appropriate environment variables:
```bash
export CC=aarch64-linux-gnu-gcc
export CXX=aarch64-linux-gnu-g++
./build.sh --config Release
```

## Contributing

When contributing to the build system:

1. Test changes on multiple platforms (Linux, macOS, Windows)
2. Ensure backward compatibility with existing build methods
3. Update this documentation for any new options
4. Add appropriate error handling and user guidance
5. Test with and without optional dependencies

## Support

For build issues:
1. Check this documentation
2. Run with `--verbose` for detailed output
3. Check the [Vosk documentation](https://alphacephei.com/vosk)
4. Open an issue on the [GitHub repository](https://github.com/alphacep/vosk-api)