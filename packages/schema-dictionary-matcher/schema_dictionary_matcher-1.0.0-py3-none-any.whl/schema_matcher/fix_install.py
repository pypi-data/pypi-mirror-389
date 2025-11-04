"""
Quick fix script to install missing dependencies
"""
import subprocess
import sys


def main():
    print("Installing missing dependencies...")

    packages = [
        "openpyxl",
        "onnxruntime"
    ]

    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                package, "--user"
            ])
            print(f"✓ {package} installed successfully")
        except Exception as e:
            print(f"✗ Failed to install {package}: {e}")

    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)
    print("\nNow run: python run_demo.py")


if __name__ == "__main__":
    main()