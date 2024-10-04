import subprocess

from version_manager import update_version, update_main_py


def build_executable():
    """実行可能ファイルをビルドし、必要なファイルをコピーする"""
    new_version = update_version()
    update_main_py(new_version)

    # PyInstallerを実行
    subprocess.run([
        "pyinstaller",
        "--name=GroqWhisper",
        "--windowed",
        "--icon=assets/GroqWhisper.ico",
        "main.py"
    ])

    print(f"Executable built successfully. Version: {new_version}")


if __name__ == "__main__":
    build_executable()
