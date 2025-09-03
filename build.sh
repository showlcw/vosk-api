#!/bin/bash
#
# Vosk-API Build Script
# Simple wrapper around the Python build script for easier command-line usage
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SCRIPT="$SCRIPT_DIR/build.py"

# Check if Python build script exists
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "Error: Build script not found at $BUILD_SCRIPT"
    exit 1
fi

# Show help for common cases
show_help() {
    cat << EOF
Vosk-API Automated Build Script

USAGE:
    $0 [OPTIONS]

QUICK START:
    $0                    # Build everything with optimal settings
    $0 --help             # Show detailed help

COMMON OPTIONS:
    --config CONF         Build configuration: Debug, Release, RelWithDebInfo
    --python             Build Python bindings (default: enabled)
    --java               Build Java bindings  
    --csharp             Build C# bindings
    --cuda               Enable CUDA support
    --install            Install after building
    --test               Run tests after building
    --clean              Clean build directory first
    --verbose            Verbose output
    --force              Continue even if dependencies are missing

EXAMPLES:
    $0 --config Release --install           # Optimized build and install
    $0 --python --wheel                     # Build Python wheel package
    $0 --java --csharp --test              # Build multiple language bindings
    $0 --bindings-only                     # Skip C++ build, bindings only
    $0 --cuda --math-lib mkl               # High-performance build

For complete help: $0 --help
EOF
}

# Handle special cases
case "$1" in
    -h|--help|-help|help)
        if [ "$1" = "--help" ] || [ "$1" = "-help" ]; then
            # Pass through to Python script for detailed help
            python3 "$BUILD_SCRIPT" --help
        else
            # Show quick help
            show_help
        fi
        exit 0
        ;;
    "")
        # Default build - optimal settings for most users
        echo "🚀 Starting Vosk-API build with optimal settings..."
        python3 "$BUILD_SCRIPT" --config Release --python
        ;;
    *)
        # Pass all arguments to Python script
        python3 "$BUILD_SCRIPT" "$@"
        ;;
esac