#!/usr/bin/env python3
"""
Automated build script for vosk-api
Simplifies the compilation process by checking dependencies, setting up environment,
and building the C++ library and language bindings.
"""

import os
import sys
import subprocess
import argparse
import platform
import shutil
import urllib.request
import tarfile
import tempfile
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class BuildError(Exception):
    """Custom exception for build errors"""
    pass

class VoskBuilder:
    def __init__(self, args):
        self.args = args
        self.repo_root = Path(__file__).parent.absolute()
        self.build_dir = self.repo_root / "build"
        self.src_dir = self.repo_root / "src"
        self.dependencies_checked = False
        
    def log(self, message, color=Colors.BLUE):
        """Print colored log message"""
        print(f"{color}[VOSK-BUILD]{Colors.ENDC} {message}")
        
    def error(self, message):
        """Print error message and exit"""
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")
        sys.exit(1)
        
    def warning(self, message):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {message}")
        
    def success(self, message):
        """Print success message"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")
        
    def run_command(self, cmd, cwd=None, env=None, check=True):
        """Run shell command with error handling"""
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        self.log(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd or self.repo_root,
                env=env,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print(result.stderr)
                
            return result
        except subprocess.CalledProcessError as e:
            self.error(f"Command failed: {' '.join(cmd)}\n{e.stderr}")
        except FileNotFoundError:
            self.error(f"Command not found: {cmd[0]}")
            
    def check_command(self, cmd):
        """Check if command exists"""
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
            
    def check_dependencies(self):
        """Check for required dependencies"""
        self.log("Checking dependencies...")
        
        # Required tools
        required_tools = {
            'cmake': 'CMake (required for building)',
            'make': 'Make (required for building)', 
            'g++': 'G++ compiler (required for C++ compilation)',
            'python3': 'Python 3 (required for Python bindings)',
            'git': 'Git (required for downloading dependencies)'
        }
        
        missing_tools = []
        for tool, description in required_tools.items():
            if self.check_command(tool):
                self.success(f"✓ {tool} found")
            else:
                missing_tools.append(f"{tool} - {description}")
        
        if missing_tools:
            self.error("Missing required dependencies:\n" + 
                      "\n".join(f"  - {tool}" for tool in missing_tools) +
                      "\n\nPlease install the missing dependencies and try again.")
        
        # Python packages for Python bindings
        if self.args.python:
            python_packages = ['cffi', 'setuptools', 'wheel']
            for package in python_packages:
                try:
                    __import__(package)
                    self.success(f"✓ Python package {package} found")
                except ImportError:
                    self.log(f"Installing Python package {package}...")
                    self.run_command([sys.executable, "-m", "pip", "install", package])
        
        self.success("All dependencies are available")
        self.dependencies_checked = True
        
    def setup_kaldi_environment(self):
        """Set up Kaldi environment or provide guidance"""
        self.log("Setting up Kaldi environment...")
        
        # Check if KALDI_ROOT is set
        kaldi_root = os.environ.get('KALDI_ROOT')
        if kaldi_root and Path(kaldi_root).exists():
            self.success(f"Using existing Kaldi installation at {kaldi_root}")
            return kaldi_root
            
        # Look for Kaldi in common locations
        common_kaldi_paths = [
            self.repo_root.parent / "kaldi",
            Path.home() / "kaldi",
            Path.home() / "travis" / "kaldi",
            Path("/opt/kaldi"),
            Path("/usr/local/kaldi")
        ]
        
        for path in common_kaldi_paths:
            if path.exists() and (path / "src").exists():
                self.success(f"Found Kaldi installation at {path}")
                os.environ['KALDI_ROOT'] = str(path)
                return str(path)
        
        # Kaldi not found - provide setup guidance
        self.warning("Kaldi not found. Please set up Kaldi:")
        print(f"""
{Colors.YELLOW}Kaldi Setup Instructions:{Colors.ENDC}

1. Download and build Kaldi:
   git clone https://github.com/kaldi-asr/kaldi.git
   cd kaldi/tools
   make -j$(nproc)
   cd ../src
   ./configure --shared
   make depend -j$(nproc)
   make -j$(nproc)

2. Set KALDI_ROOT environment variable:
   export KALDI_ROOT=/path/to/kaldi

3. Re-run this build script

For more details, see: https://kaldi-asr.org/doc/build_setup.html
""")
        
        if not self.args.force:
            self.error("Kaldi is required for building vosk-api. Use --force to continue without Kaldi (for binding-only builds).")
        else:
            self.warning("Continuing without Kaldi (--force enabled)")
            return None
            
    def setup_build_environment(self):
        """Set up build environment variables"""
        self.log("Setting up build environment...")
        
        # Ensure build directory exists
        self.build_dir.mkdir(exist_ok=True)
        
        # Set environment variables
        env = os.environ.copy()
        
        # Build configuration
        if self.args.config == 'Release':
            env['CMAKE_BUILD_TYPE'] = 'Release'
            env['EXTRA_CFLAGS'] = '-O3 -DNDEBUG'
        elif self.args.config == 'Debug':
            env['CMAKE_BUILD_TYPE'] = 'Debug'
            env['EXTRA_CFLAGS'] = '-g -O0'
        else:
            env['CMAKE_BUILD_TYPE'] = 'RelWithDebInfo'
            env['EXTRA_CFLAGS'] = '-O2 -g'
            
        # Math library configuration
        if self.args.math_lib == 'openblas':
            env['HAVE_OPENBLAS_CLAPACK'] = '1'
            env['HAVE_MKL'] = '0'
        elif self.args.math_lib == 'mkl':
            env['HAVE_MKL'] = '1' 
            env['HAVE_OPENBLAS_CLAPACK'] = '0'
        
        # CUDA support
        if self.args.cuda:
            env['HAVE_CUDA'] = '1'
        else:
            env['HAVE_CUDA'] = '0'
            
        return env
        
    def build_cpp_library(self, env):
        """Build the C++ library"""
        self.log("Building C++ library...")
        
        if self.args.use_cmake:
            self.build_with_cmake(env)
        else:
            self.build_with_make(env)
            
    def build_with_cmake(self, env):
        """Build using CMake"""
        self.log("Building with CMake...")
        
        cmake_args = [
            'cmake',
            '-B', str(self.build_dir),
            '-S', str(self.repo_root),
            f'-DCMAKE_BUILD_TYPE={env.get("CMAKE_BUILD_TYPE", "Release")}'
        ]
        
        if self.args.install_prefix:
            cmake_args.extend(['-DCMAKE_INSTALL_PREFIX', self.args.install_prefix])
            
        self.run_command(cmake_args, env=env)
        self.run_command(['cmake', '--build', str(self.build_dir), '--parallel'], env=env)
        
    def build_with_make(self, env):
        """Build using Makefile"""
        self.log("Building with Make...")
        
        make_args = ['make', '-j', str(os.cpu_count() or 4)]
        if self.args.verbose:
            make_args.append('V=1')
            
        self.run_command(make_args, cwd=self.src_dir, env=env)
        
    def build_python_bindings(self):
        """Build Python bindings"""
        if not self.args.python:
            return
            
        self.log("Building Python bindings...")
        
        python_dir = self.repo_root / "python"
        
        # Set VOSK_SOURCE environment variable
        env = os.environ.copy()
        env['VOSK_SOURCE'] = str(self.repo_root)
        
        # Build CFFI module
        self.log("Building CFFI module...")
        self.run_command([sys.executable, "vosk_builder.py"], cwd=python_dir, env=env)
        
        # Build wheel
        if self.args.wheel:
            self.log("Building Python wheel...")
            self.run_command([sys.executable, "setup.py", "bdist_wheel"], cwd=python_dir, env=env)
        else:
            # Install in development mode
            self.log("Installing Python package in development mode...")
            self.run_command([sys.executable, "-m", "pip", "install", "-e", "."], cwd=python_dir, env=env)
            
    def build_java_bindings(self):
        """Build Java bindings"""
        if not self.args.java:
            return
            
        self.log("Building Java bindings...")
        java_dir = self.repo_root / "java"
        
        # Check for Java tools
        if not self.check_command('javac') or not self.check_command('jar'):
            self.warning("Java compiler not found. Skipping Java bindings.")
            return
            
        self.run_command(['make'], cwd=java_dir)
        
    def build_csharp_bindings(self):
        """Build C# bindings"""
        if not self.args.csharp:
            return
            
        self.log("Building C# bindings...")
        csharp_dir = self.repo_root / "csharp"
        
        # Check for .NET
        if not self.check_command('dotnet'):
            self.warning(".NET SDK not found. Skipping C# bindings.")
            return
            
        self.run_command(['dotnet', 'build'], cwd=csharp_dir)
        
    def run_tests(self):
        """Run tests if available"""
        if not self.args.test:
            return
            
        self.log("Running tests...")
        
        # Test C library
        c_dir = self.repo_root / "c"
        if c_dir.exists():
            try:
                self.run_command(['make'], cwd=c_dir)
                self.success("C tests completed")
            except:
                self.warning("C tests failed")
        
        # Test Python bindings
        if self.args.python:
            python_test_dir = self.repo_root / "python" / "test"
            if python_test_dir.exists():
                try:
                    # Run a simple import test
                    self.run_command([sys.executable, "-c", "import vosk; print('Python bindings work!')"])
                    self.success("Python tests completed")
                except:
                    self.warning("Python tests failed")
                    
    def install(self):
        """Install the built libraries"""
        if not self.args.install:
            return
            
        self.log("Installing...")
        
        if self.args.use_cmake:
            self.run_command(['cmake', '--install', str(self.build_dir)])
        else:
            # Copy files manually for Make-based build
            install_prefix = self.args.install_prefix or "/usr/local"
            lib_dir = Path(install_prefix) / "lib"
            include_dir = Path(install_prefix) / "include"
            
            lib_dir.mkdir(parents=True, exist_ok=True)
            include_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy library files
            for lib_file in self.src_dir.glob("*.so"):
                shutil.copy2(lib_file, lib_dir)
                
            # Copy header files
            shutil.copy2(self.src_dir / "vosk_api.h", include_dir)
            
        self.success("Installation completed")
        
    def print_summary(self):
        """Print build summary"""
        print(f"\n{Colors.GREEN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}VOSK-API BUILD COMPLETED SUCCESSFULLY{Colors.ENDC}")
        print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}")
        
        print(f"\n{Colors.BLUE}Build Configuration:{Colors.ENDC}")
        print(f"  Configuration: {self.args.config}")
        print(f"  Math Library: {self.args.math_lib}")
        print(f"  CUDA Support: {'Yes' if self.args.cuda else 'No'}")
        print(f"  Build System: {'CMake' if self.args.use_cmake else 'Make'}")
        
        print(f"\n{Colors.BLUE}Language Bindings:{Colors.ENDC}")
        print(f"  Python: {'Yes' if self.args.python else 'No'}")
        print(f"  Java: {'Yes' if self.args.java else 'No'}")
        print(f"  C#: {'Yes' if self.args.csharp else 'No'}")
        
        if self.args.python:
            print(f"\n{Colors.BLUE}Python Usage:{Colors.ENDC}")
            print("  import vosk")
            print("  model = vosk.Model('path/to/model')")
            print("  rec = vosk.KaldiRecognizer(model, 16000)")
            
        print(f"\n{Colors.BLUE}Next Steps:{Colors.ENDC}")
        print("  1. Download a language model from https://alphacephei.com/vosk/models")
        print("  2. Try the examples in the respective language directories")
        print("  3. Read the documentation at https://alphacephei.com/vosk")
        
    def build(self):
        """Main build process"""
        try:
            self.log("Starting vosk-api automated build...")
            
            # Check dependencies
            self.check_dependencies()
            
            # Set up Kaldi (if needed for C++ build)
            if not self.args.bindings_only:
                self.setup_kaldi_environment()
            
            # Set up build environment
            env = self.setup_build_environment()
            
            # Build C++ library (unless bindings-only)
            if not self.args.bindings_only:
                self.build_cpp_library(env)
            
            # Build language bindings
            self.build_python_bindings()
            self.build_java_bindings()
            self.build_csharp_bindings()
            
            # Run tests
            self.run_tests()
            
            # Install
            self.install()
            
            # Print summary
            self.print_summary()
            
        except BuildError as e:
            self.error(str(e))
        except KeyboardInterrupt:
            self.error("Build interrupted by user")
        except Exception as e:
            self.error(f"Unexpected error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Automated build script for vosk-api",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Build everything with default settings
  %(prog)s --config Release         # Build optimized release version
  %(prog)s --python --wheel         # Build Python bindings as wheel
  %(prog)s --java --csharp          # Build Java and C# bindings
  %(prog)s --bindings-only          # Build only language bindings (skip C++)
  %(prog)s --cuda --math-lib mkl    # Build with CUDA and Intel MKL support
        """
    )
    
    # Build configuration
    parser.add_argument('--config', choices=['Debug', 'Release', 'RelWithDebInfo'], 
                       default='Release', help='Build configuration (default: Release)')
    parser.add_argument('--math-lib', choices=['openblas', 'mkl', 'auto'], 
                       default='auto', help='Math library to use (default: auto)')
    parser.add_argument('--cuda', action='store_true', help='Enable CUDA support')
    parser.add_argument('--use-cmake', action='store_true', help='Use CMake instead of Make')
    
    # Language bindings
    parser.add_argument('--python', action='store_true', default=True, 
                       help='Build Python bindings (default: True)')
    parser.add_argument('--java', action='store_true', help='Build Java bindings')
    parser.add_argument('--csharp', action='store_true', help='Build C# bindings')
    parser.add_argument('--bindings-only', action='store_true', 
                       help='Build only language bindings (skip C++ library)')
    
    # Python specific options
    parser.add_argument('--wheel', action='store_true', 
                       help='Build Python wheel instead of installing')
    parser.add_argument('--no-python', dest='python', action='store_false',
                       help='Skip Python bindings')
    
    # Installation and testing
    parser.add_argument('--install', action='store_true', help='Install after building')
    parser.add_argument('--install-prefix', default='/usr/local',
                       help='Installation prefix (default: /usr/local)')
    parser.add_argument('--test', action='store_true', help='Run tests after building')
    
    # Other options
    parser.add_argument('--force', action='store_true', 
                       help='Continue build even if some dependencies are missing')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--clean', action='store_true', help='Clean build directory first')
    
    args = parser.parse_args()
    
    # Clean build directory if requested
    if args.clean:
        build_dir = Path(__file__).parent / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            print(f"Cleaned build directory: {build_dir}")
    
    # Create and run builder
    builder = VoskBuilder(args)
    builder.build()

if __name__ == '__main__':
    main()