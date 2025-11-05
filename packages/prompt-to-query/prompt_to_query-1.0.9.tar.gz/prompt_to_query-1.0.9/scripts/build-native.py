#!/usr/bin/env python3
"""
Script to build native libraries for all supported platforms.
This script should be run before publishing to PyPI.

Usage:
    python scripts/build-native.py              # Build for current platform
    python scripts/build-native.py --all        # Build for all platforms (uses Docker)
    python scripts/build-native.py --docker     # Same as --all
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import argparse


class NativeBuilder:
    """Handles building native libraries for different platforms"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.sdk_dir = self.script_dir.parent
        self.project_root = self.sdk_dir.parent.parent
        self.lib_dir = self.sdk_dir / "prompt_to_query" / "lib"
        self.core_build_dir = self.project_root / "core" / "build"
        self.core_src_dir = self.project_root / "core" / "src"

        print("🔨 Building native libraries...")
        print()
        print(f"Project root: {self.project_root}")
        print(f"SDK directory: {self.sdk_dir}")
        print(f"Library output: {self.lib_dir}")
        print()

    def clean_previous_builds(self):
        """Clean previous builds"""
        print("🧹 Cleaning previous builds...")

        # Create directories if they don't exist
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        self.core_build_dir.mkdir(parents=True, exist_ok=True)

        # Remove old libraries
        if self.lib_dir.exists():
            for f in self.lib_dir.glob("*"):
                if f.is_file():
                    f.unlink()

        if self.core_build_dir.exists():
            for f in self.core_build_dir.glob("*"):
                if f.is_file():
                    f.unlink()

    def build_current_platform(self):
        """Build for the current platform"""
        print()
        print("📦 Building for current platform...")

        # Run make build
        result = subprocess.run(
            ["make", "build"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False

        # Copy the current platform library
        copied = False
        for pattern in ["*.so", "*.dylib", "*.dll"]:
            for lib_file in self.core_build_dir.glob(pattern):
                shutil.copy2(lib_file, self.lib_dir)
                print(f"✅ Built and copied {lib_file.name}")
                copied = True

        return copied

    def check_docker(self):
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def build_with_docker(self):
        """Build using Docker for all platforms"""
        print()
        print("🐳 Building with Docker for all platforms...")

        if not self.check_docker():
            print("❌ Docker not found. Install Docker to build for all platforms.")
            return False

        builds = [
            {
                "name": "Linux AMD64",
                "platform": "linux/amd64",
                "image": "golang:1.21-bullseye",
                "env": {"CGO_ENABLED": "1", "GOOS": "linux", "GOARCH": "amd64"},
                "output": "libprompttoquery_linux_amd64.so"
            },
            {
                "name": "Linux ARM64",
                "platform": "linux/arm64",
                "image": "golang:1.21-bullseye",
                "env": {"CGO_ENABLED": "1", "GOOS": "linux", "GOARCH": "arm64"},
                "output": "libprompttoquery_linux_arm64.so"
            },
            {
                "name": "Linux AMD64 (Alpine/musl)",
                "platform": "linux/amd64",
                "image": "golang:1.21-alpine",
                "env": {"CGO_ENABLED": "1", "GOOS": "linux", "GOARCH": "amd64"},
                "output": "libprompttoquery_linux_amd64_musl.so",
                "pre_cmd": "apk add --no-cache gcc musl-dev > /dev/null 2>&1"
            },
            {
                "name": "Linux ARM64 (Alpine/musl)",
                "platform": "linux/arm64",
                "image": "golang:1.21-alpine",
                "env": {"CGO_ENABLED": "1", "GOOS": "linux", "GOARCH": "arm64"},
                "output": "libprompttoquery_linux_arm64_musl.so",
                "pre_cmd": "apk add --no-cache gcc musl-dev > /dev/null 2>&1"
            },
            {
                "name": "Windows AMD64",
                "platform": None,
                "image": "golang:1.21-bullseye",
                "env": {
                    "CGO_ENABLED": "1",
                    "GOOS": "windows",
                    "GOARCH": "amd64",
                    "CC": "x86_64-w64-mingw32-gcc"
                },
                "output": "prompttoquery_windows_amd64.dll",
                "pre_cmd": "apt-get update -qq && apt-get install -qq -y mingw-w64 > /dev/null 2>&1"
            }
        ]

        success_count = 0
        for build in builds:
            print()
            print(f"Building for {build['name']}...")

            # Build Docker command
            docker_cmd = ["docker", "run", "--rm"]

            if build["platform"]:
                docker_cmd.extend(["--platform", build["platform"]])

            docker_cmd.extend([
                "-v", f"{self.project_root}:/workspace",
                "-w", "/workspace/core/src",
                build["image"]
            ])

            # Build the command to run inside Docker
            env_vars = " ".join([f"{k}={v}" for k, v in build["env"].items()])
            build_cmd = f"go build -buildmode=c-shared -o ../build/{build['output']} ."

            if "pre_cmd" in build:
                full_cmd = f"{build['pre_cmd']} && {env_vars} {build_cmd}"
            else:
                full_cmd = f"{env_vars} {build_cmd}"

            docker_cmd.extend(["bash" if "bullseye" in build["image"] else "sh", "-c", full_cmd])

            # Run the build
            result = subprocess.run(docker_cmd, capture_output=True, text=True)

            output_file = self.core_build_dir / build["output"]
            if result.returncode == 0 and output_file.exists():
                shutil.copy2(output_file, self.lib_dir)
                print(f"✅ Built {build['name']}")
                success_count += 1
            else:
                print(f"⚠️  {build['name']} build failed")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")

        return success_count > 0

    def build_macos(self):
        """Build for macOS (both architectures)"""
        if platform.system() != "Darwin":
            print("⚠️  Skipping macOS build (not running on macOS)")
            return False

        print()
        print("🍎 Building for macOS (all architectures)...")

        builds = [
            {"name": "macOS AMD64", "goarch": "amd64", "output": "libprompttoquery_darwin_amd64.dylib"},
            {"name": "macOS ARM64", "goarch": "arm64", "output": "libprompttoquery_darwin_arm64.dylib"}
        ]

        success_count = 0
        for build in builds:
            print(f"Building for {build['name']}...")

            env = os.environ.copy()
            env.update({
                "CGO_ENABLED": "1",
                "GOOS": "darwin",
                "GOARCH": build["goarch"]
            })

            result = subprocess.run(
                ["go", "build", "-buildmode=c-shared", "-o", f"../build/{build['output']}", "."],
                cwd=self.core_src_dir,
                env=env,
                capture_output=True,
                text=True
            )

            output_file = self.core_build_dir / build["output"]
            if result.returncode == 0 and output_file.exists():
                shutil.copy2(output_file, self.lib_dir)
                print(f"✅ Built {build['name']}")
                success_count += 1
            else:
                print(f"❌ {build['name']} build failed")
                if result.stderr:
                    print(f"   Error: {result.stderr}")

        return success_count > 0

    def print_summary(self):
        """Print build summary"""
        print()
        print("📊 Build summary:")
        print("━" * 60)

        if self.lib_dir.exists():
            lib_files = sorted(self.lib_dir.glob("*"))
            if lib_files:
                for lib_file in lib_files:
                    size = lib_file.stat().st_size / (1024 * 1024)  # Convert to MB
                    print(f"  {lib_file.name:<50} {size:>6.1f} MB")
            else:
                print("  No libraries built")
        else:
            print("  No libraries built")

        print("━" * 60)

    def run(self, build_all=False):
        """Run the build process"""
        self.clean_previous_builds()

        if build_all:
            # Build macOS natively (if on macOS)
            self.build_macos()

            # Build Linux and Windows with Docker
            self.build_with_docker()
        else:
            # Build for current platform only
            self.build_current_platform()

            # If on macOS, also build both macOS architectures
            if platform.system() == "Darwin":
                self.build_macos()

        self.print_summary()

        # Count built libraries
        lib_count = len(list(self.lib_dir.glob("*")))

        if lib_count == 0:
            print()
            print("❌ No libraries were built!")
            print("Please ensure Go and build tools are installed.")
            return False

        print()
        print(f"✅ Build complete! {lib_count} native librar{'y' if lib_count == 1 else 'ies'} ready.")
        print()

        if not build_all:
            print("💡 To build for all platforms, run:")
            print("   python scripts/build-native.py --all")
            print()

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Build native libraries for prompt-to-query SDK"
    )
    parser.add_argument(
        "--all", "--docker",
        action="store_true",
        dest="build_all",
        help="Build for all platforms using Docker"
    )

    args = parser.parse_args()

    builder = NativeBuilder()
    success = builder.run(build_all=args.build_all)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
