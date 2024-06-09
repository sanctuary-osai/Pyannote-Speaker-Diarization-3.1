import os
import subprocess

def install_packages():
    package_file = "packages.txt"
    package_manager = ""

    if os.name == "posix":  # Linux
        package_manager = "apt-get install -y"
    elif os.name == "nt":  # Windows
        package_manager = "choco install"

    with open(package_file) as f:
        packages = f.read().splitlines()

    for package in packages:
        subprocess.run(f"{package_manager} {package}", shell=True)

if __name__ == "__main__":
    install_packages()
