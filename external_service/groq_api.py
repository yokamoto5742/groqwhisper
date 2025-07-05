import logging
import os
import traceback
from typing import Optional

from groq import Groq


def setup_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEYの環境変数が未設定です")
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

    checkpoint_logger = logging.getLogger('checkpoint')

    try:
        logging.info("文字起こし開始")
        checkpoint_logger.info("CHECKPOINT_1: 文字起こし処理開始")

        if not os.path.exists(audio_file_path):
            logging.error(f"音声ファイルが存在しません: {audio_file_path}")
            return None

        file_size = os.path.getsize(audio_file_path)
        logging.info(f"音声ファイルサイズ: {file_size} bytes")

        if file_size == 0:
            logging.error("音声ファイルのサイズが0バイトです")
            return None

        checkpoint_logger.info("CHECKPOINT_2: ファイル検証完了")

        logging.info("ファイル読み込み開始")
        with open(audio_file_path, "rb") as file:
            file_content = file.read()
            logging.info(f"ファイル読み込み完了: {len(file_content)} bytes")

            checkpoint_logger.info("CHECKPOINT_3: API呼び出し開始")
            logging.info("Groq API呼び出し開始")

            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file_content),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE']
            )

            checkpoint_logger.info("CHECKPOINT_4: API呼び出し完了")
            logging.info("Groq API呼び出し完了")

        checkpoint_logger.info("CHECKPOINT_5: レスポンス処理開始")

        try:
            logging.info(f"APIレスポンスのタイプ: {type(transcription)}")
            logging.info(f"APIレスポンスの値: {repr(transcription)[:200]}")

            if transcription is None:
                logging.error("APIからのレスポンスがNoneです")
                return None

            text_result = None

            if isinstance(transcription, str):
                text_result = transcription
                logging.info("レスポンスは既に文字列形式です")
            elif hasattr(transcription, 'text') and transcription.text is not None:
                text_result = str(transcription.text)
                logging.info("レスポンスオブジェクトからtextプロパティを取得しました")
            elif hasattr(transcription, '__str__'):
                text_result = str(transcription)
                logging.info("レスポンスを文字列に変換しました")
            else:
                logging.error(f"予期しないレスポンス形式: {type(transcription)}")
                logging.error(f"レスポンス内容: {transcription}")
                return None

            if text_result is None:
                logging.error("文字列変換後の結果がNoneです")
                return None

        except Exception as response_error:
            logging.error(f"レスポンス変換中の予期しないエラー: {str(response_error)}")
            logging.debug(f"レスポンス変換エラー詳細: {traceback.format_exc()}")
            return None

        checkpoint_logger.info("CHECKPOINT_6: レスポンス処理完了")

        char_count = len(text_result) if text_result else 0
        logging.info(f"文字起こし結果の文字数: {char_count}")

        if char_count == 0:
            logging.warning("文字起こし結果が空です")
            return ""

        checkpoint_logger.info("CHECKPOINT_7: 句読点処理開始")
        logging.info("句読点処理開始")
        original_text = text_result

        try:
            if not use_punctuation and isinstance(text_result, str):
                logging.info("句読点（。）を削除します")
                text_result = text_result.replace('。', '')
                logging.info(f"句読点削除後の文字数: {len(text_result)}")

            if not use_comma and isinstance(text_result, str):
                logging.info("読点（、）を削除します")
                text_result = text_result.replace('、', '')
                logging.info(f"読点削除後の文字数: {len(text_result)}")

        except (AttributeError, TypeError) as punctuation_error:
            logging.error(f"句読点処理中にタイプエラー: {str(punctuation_error)}")
            text_result = original_text
        except Exception as punctuation_error:
            logging.error(f"句読点処理中に予期しないエラー: {str(punctuation_error)}")
            text_result = original_text

        checkpoint_logger.info("CHECKPOINT_8: 句読点処理完了")
        logging.info("句読点処理完了")

        final_char_count = len(text_result) if text_result else 0
        logging.info(f"文字起こし完了: {final_char_count}文字")

        # デバッグ用：最初の10文字をログに出力
        if text_result and len(text_result) > 0:
            preview_text = text_result[:10] + "..." if len(text_result) > 10 else text_result
            logging.debug(f"文字起こし結果プレビュー: {preview_text}")

        checkpoint_logger.info("CHECKPOINT_9: 処理完了")
        return text_result

    except FileNotFoundError as e:
        checkpoint_logger.error(f"CHECKPOINT_ERROR: FileNotFoundError - {str(e)}")
        logging.error(f"ファイルが見つかりません: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except PermissionError as e:
        checkpoint_logger.error(f"CHECKPOINT_ERROR: PermissionError - {str(e)}")
        logging.error(f"ファイルアクセス権限エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except OSError as e:
        checkpoint_logger.error(f"CHECKPOINT_ERROR: OSError - {str(e)}")
        logging.error(f"OS関連エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
    except Exception as e:
        checkpoint_logger.error(f"CHECKPOINT_ERROR: Exception - {str(e)}")
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
