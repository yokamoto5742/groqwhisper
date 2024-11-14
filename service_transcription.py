import os
import logging
from typing import Optional
from groq import Groq


def setup_groq_client() -> Groq:
    """Groqクライアントをセットアップし返します。"""
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
    if not audio_file_path:
        logging.warning("音声ファイルパスが未指定")
        return None

    try:
        logging.info("文字起こし開始")
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE']
            )

        if transcription:
            logging.info(f"文字起こし完了: {len(transcription)}文字")

            if not use_punctuation:
                transcription = transcription.replace('。', '')
            if not use_comma:
                transcription = transcription.replace('、', '')

        return transcription

    except Exception as e:
        logging.error(f"文字起こしエラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None

