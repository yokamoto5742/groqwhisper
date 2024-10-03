import os
import shutil
import subprocess

from version.version_manager import update_version, update_main_py

# プロジェクトのルートディレクトリのパスを取得
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


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
        "--add-data=src/audio_recorder.py:.",
        "--add-data=src/gui.py:.",
        "--add-data=src/text_processing.py:.",
        "--add-data=src/transcription.py:.",
        "--add-data=src/log_rotation.py:.",
        "--hidden-import=audio_recorder",
        "--hidden-import=gui",
        "--hidden-import=text_processing",
        "--hidden-import=transcription",
        "--hidden-import=log_rotation",
        "--hidden-import=pyaudio",
        "--hidden-import=wave",
        os.path.join(PROJECT_ROOT, "src", "main.py")
    ])

    # 必要なファイルをdistフォルダにコピー
    dist_dir = os.path.join(PROJECT_ROOT, "dist", "GroqWhisper")
    shutil.copy(
        os.path.join(PROJECT_ROOT, "config", "config.ini"),
        dist_dir
    )
    shutil.copy(
        os.path.join(PROJECT_ROOT, "config", "replacements.txt"),
        dist_dir
    )

    print(f"Executable built successfully. Version: {new_version}")


if __name__ == "__main__":
    build_executable()
