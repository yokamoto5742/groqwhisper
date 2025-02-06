import subprocess
from version_manager import update_version, update_version_py


def build_executable():
    new_version = update_version()
    update_version_py(new_version)

    subprocess.run([
        "pyinstaller",
        "--name=GroqWhisper",
        "--windowed",
        "--icon=assets/GroqWhisper.ico",
        "--add-data", "config.ini:.",
        "--add-data", "replacements.txt:.",
        "main.py"
    ])

    print(f"Executable built successfully. Version: {new_version}")


if __name__ == "__main__":
    build_executable()
