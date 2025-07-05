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

    try:
        logging.info("文字起こし開始")

        # ファイル存在確認
        if not os.path.exists(audio_file_path):
            logging.error(f"音声ファイルが存在しません: {audio_file_path}")
            return None

        # ファイルサイズ確認
        file_size = os.path.getsize(audio_file_path)
        logging.info(f"音声ファイルサイズ: {file_size} bytes")

        if file_size == 0:
            logging.error("音声ファイルのサイズが0バイトです")
            return None

        logging.info("ファイル読み込み開始")
        with open(audio_file_path, "rb") as file:
            file_content = file.read()
            logging.info(f"ファイル読み込み完了: {len(file_content)} bytes")

            logging.info("Groq API呼び出し開始")
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file_content),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE']
            )
            logging.info("Groq API呼び出し完了")

        # レスポンス内容の詳細チェック
        logging.info(f"APIレスポンスのタイプ: {type(transcription)}")

        if transcription is None:
            logging.error("APIからのレスポンスがNoneです")
            return None

        # transcriptionが文字列でない場合の処理
        if not isinstance(transcription, str):
            logging.warning(f"レスポンスが文字列ではありません。型: {type(transcription)}, 値: {transcription}")
            # オブジェクトから文字列を取得する試み
            try:
                if hasattr(transcription, 'text'):
                    transcription = transcription.text
                    logging.info("レスポンスオブジェクトからtextプロパティを取得しました")
                else:
                    transcription = str(transcription)
                    logging.info("レスポンスを文字列に変換しました")
            except Exception as convert_error:
                logging.error(f"レスポンス変換エラー: {str(convert_error)}")
                return None

        # 文字数チェック
        char_count = len(transcription) if transcription else 0
        logging.info(f"文字起こし結果の文字数: {char_count}")

        if char_count == 0:
            logging.warning("文字起こし結果が空です")
            return ""

        # 句読点処理開始
        logging.info("句読点処理開始")
        original_text = transcription

        try:
            if not use_punctuation:
                logging.info("句読点（。）を削除します")
                transcription = transcription.replace('。', '')
                logging.info(f"句読点削除後の文字数: {len(transcription)}")

            if not use_comma:
                logging.info("読点（、）を削除します")
                transcription = transcription.replace('、', '')
                logging.info(f"読点削除後の文字数: {len(transcription)}")

        except Exception as punctuation_error:
            logging.error(f"句読点処理中にエラー: {str(punctuation_error)}")
            # エラーが発生した場合は元のテキストを返す
            transcription = original_text

        logging.info("句読点処理完了")

        # 最終結果のログ
        final_char_count = len(transcription) if transcription else 0
        logging.info(f"文字起こし完了: {final_char_count}文字")

        # デバッグ用：最初の100文字をログに出力
        if transcription and len(transcription) > 0:
            preview_text = transcription[:100] + "..." if len(transcription) > 100 else transcription
            logging.debug(f"文字起こし結果プレビュー: {preview_text}")

        return transcription

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

        # 追加のデバッグ情報
        try:
            logging.error(f"音声ファイルパス: {audio_file_path}")
            logging.error(f"use_punctuation: {use_punctuation}")
            logging.error(f"use_comma: {use_comma}")
            logging.error(f"設定ファイル MODEL: {config.get('WHISPER', {}).get('MODEL', 'NOT_SET')}")
            logging.error(f"設定ファイル LANGUAGE: {config.get('WHISPER', {}).get('LANGUAGE', 'NOT_SET')}")
        except Exception as debug_error:
            logging.error(f"デバッグ情報取得エラー: {str(debug_error)}")

        return None
