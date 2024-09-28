from groq import Groq
import os


def setup_groq_client():
    return Groq(api_key=os.environ.get("GROQ_API_KEY"))


def transcribe_audio(audio_file_path, use_punctuation, use_comma, config, client):
    if not audio_file_path:
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

        if not use_punctuation:
            transcription = transcription.replace('。', '')
        if not use_comma:
            transcription = transcription.replace('、', '')

        return transcription

    except Exception as e:
        print(f"テキスト出力中にエラーが発生しました: {str(e)}")
        return None
