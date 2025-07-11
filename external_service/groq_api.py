import logging
import os
import traceback
from typing import Optional

from groq import Groq

from utils.env_loader import load_env_variables


def setup_groq_client() -> Groq:
    env_vars = load_env_variables()
    api_key = env_vars.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEYが未設定です")
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
        if not os.path.exists(audio_file_path):
            logging.error(f"音声ファイルが存在しません: {audio_file_path}")
            return None

        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            logging.error("音声ファイルのサイズが0バイトです")
            return None

        logging.info("ファイル読み込み開始")
        with open(audio_file_path, "rb") as file:
            file_content = file.read()
            logging.info(f"ファイル読み込み完了: {len(file_content)} bytes")

            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file_content),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE']
            )

        try:
            if transcription is None:
                logging.error("APIからのレスポンスがNoneです")
                return None

            text_result = None

            if isinstance(transcription, str):
                text_result = transcription
            elif hasattr(transcription, 'text') and transcription.text is not None:
                text_result = str(transcription.text)
            elif hasattr(transcription, '__str__'):
                text_result = str(transcription)
            else:
                logging.error(f"予期しないレスポンス形式: {type(transcription)}")
                return None

            if text_result is None:
                logging.error("文字列変換後の結果がNoneです")
                return None

        except Exception as response_error:
            logging.error(f"レスポンス変換中の予期しないエラー: {str(response_error)}")
            logging.debug(f"レスポンス変換エラー詳細: {traceback.format_exc()}")
            return None

        char_count = len(text_result) if text_result else 0

        if char_count == 0:
            logging.warning("文字起こし結果が空です")
            return ""

        original_text = text_result

        try:
            if not use_punctuation and isinstance(text_result, str):
                text_result = text_result.replace('。', '')

            if not use_comma and isinstance(text_result, str):
                text_result = text_result.replace('、', '')

        except (AttributeError, TypeError) as punctuation_error:
            logging.error(f"句読点処理中にタイプエラー: {str(punctuation_error)}")
            text_result = original_text
        except Exception as punctuation_error:
            logging.error(f"句読点処理中に予期しないエラー: {str(punctuation_error)}")
            text_result = original_text

        final_char_count = len(text_result) if text_result else 0
        logging.info(f"文字起こし完了: {final_char_count}文字")

        return text_result

    except FileNotFoundError as e:
        logging.error(f"ファイルが見つかりません: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except PermissionError as e:
        logging.error(f"ファイルアクセス権限エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except OSError as e:
        logging.error(f"OS関連エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None

    except Exception as e:
        logging.error(f"文字起こしエラー: {str(e)}")
        logging.error(f"エラーのタイプ: {type(e).__name__}")
        logging.debug(f"詳細: {traceback.format_exc()}")

        try:
            logging.error(f"音声ファイルパス: {audio_file_path}")
            logging.error(f"use_punctuation: {use_punctuation}")
            logging.error(f"use_comma: {use_comma}")
            logging.error(f"設定ファイル MODEL: {config.get('WHISPER', {}).get('MODEL', 'NOT_SET')}")
            logging.error(f"設定ファイル LANGUAGE: {config.get('WHISPER', {}).get('LANGUAGE', 'NOT_SET')}")
        except Exception as debug_error:
            logging.error(f"デバッグ情報取得エラー: {str(debug_error)}")

        return None
