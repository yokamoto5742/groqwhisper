import os
import logging
from typing import Optional

from groq import Groq


def setup_groq_client() -> Groq:
    """Groqクライアントをセットアップし、返します。"""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return Groq(api_key=api_key)


def transcribe_audio(
    audio_file_path: str,
    use_punctuation: bool,
    use_comma: bool,
    config: dict,
    client: Groq
) -> Optional[str]:
    """音声ファイルをテキストに転写します。"""
    if not audio_file_path:
        logging.warning("No audio file path provided")
        return None

    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE']
            )
    except FileNotFoundError:
        logging.error(f"Audio file not found: {audio_file_path}")
        return None
    except IOError as e:
        logging.error(f"IO error occurred while reading the audio file: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during transcription: {e}")
        return None

    if not use_punctuation:
        transcription = transcription.replace('。', '')
    if not use_comma:
        transcription = transcription.replace('、', '')

    return transcription


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Transcription script started")

    try:
        client = setup_groq_client()
        # ここで必要な設定と音声ファイルのパスを指定してtranscribe_audio関数を呼び出します
    except Exception as e:
        logging.error(f"Failed to setup Groq client: {e}")
