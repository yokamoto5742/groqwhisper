import logging
import os
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from app_window import VoiceInputManager
from config_manager import load_config
from external_service.groq_api import setup_groq_client
from log_rotation import setup_logging, setup_debug_logging
from service.audio_recorder import AudioRecorder
from service.text_processing import load_replacements
from version import VERSION


def main():
    # 初期化段階での例外キャッチ
    config = None
    recorder = None
    client = None
    replacements = None
    root = None
    app = None

    try:
        # 設定ファイル読み込み
        print("設定ファイルを読み込み中...")
        config = load_config()

        # ログ設定
        print("ログシステムを初期化中...")
        setup_logging(config)

        # デバッグログも設定（一時的）
        debug_logger = setup_debug_logging()
        debug_logger.info("デバッグログシステム初期化完了")

        logging.info("アプリケーションを開始します")
        logging.info(f"バージョン: {VERSION}")

        # チェックポイントログ
        checkpoint_logger = logging.getLogger('checkpoint')
        checkpoint_logger.info("MAIN_CHECKPOINT_1: 設定読み込み完了")

        # 音声レコーダー初期化
        print("音声レコーダーを初期化中...")
        recorder = AudioRecorder(config)
        checkpoint_logger.info("MAIN_CHECKPOINT_2: 音声レコーダー初期化完了")

        # Groqクライアント初期化
        print("Groqクライアントを初期化中...")
        client = setup_groq_client()
        checkpoint_logger.info("MAIN_CHECKPOINT_3: Groqクライアント初期化完了")

        # テキスト置換設定読み込み
        print("テキスト置換設定を読み込み中...")
        replacements = load_replacements()
        checkpoint_logger.info("MAIN_CHECKPOINT_4: テキスト置換設定読み込み完了")

        # Tkinterメインウィンドウ初期化
        print("UIを初期化中...")
        root = tk.Tk()
        checkpoint_logger.info("MAIN_CHECKPOINT_5: Tkinterウィンドウ初期化完了")

        # アプリケーションマネージャー初期化
        app = VoiceInputManager(root, config, recorder, client, replacements, VERSION)
        checkpoint_logger.info("MAIN_CHECKPOINT_6: アプリケーションマネージャー初期化完了")

        # 終了処理の設定
        def safe_close():
            try:
                checkpoint_logger.info("MAIN_CHECKPOINT_7: アプリケーション終了処理開始")
                if app:
                    app.close_application()
                checkpoint_logger.info("MAIN_CHECKPOINT_8: アプリケーション終了処理完了")
            except Exception as close_error:
                logging.error(f"終了処理中にエラー: {str(close_error)}")
                logging.debug(f"終了処理エラー詳細: {traceback.format_exc()}")

        root.protocol("WM_DELETE_WINDOW", safe_close)

        # メインループ開始
        logging.info("メインループを開始します")
        checkpoint_logger.info("MAIN_CHECKPOINT_9: メインループ開始")

        print("アプリケーションが開始されました")
        root.mainloop()

        checkpoint_logger.info("MAIN_CHECKPOINT_10: メインループ終了")
        logging.info("アプリケーションが正常に終了しました")

    except ImportError as e:
        error_msg = f"必要なライブラリのインポートに失敗しました:\n{str(e)}\n\n依存関係を確認してください。"
        logging.error(error_msg)
        logging.debug(f"ImportError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "インポートエラー")

    except FileNotFoundError as e:
        error_msg = f"必要なファイルが見つかりません:\n{str(e)}\n\n設定ファイルやリソースファイルを確認してください。"
        logging.error(error_msg)
        logging.debug(f"FileNotFoundError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "ファイルエラー")

    except PermissionError as e:
        error_msg = f"ファイルアクセス権限エラー:\n{str(e)}\n\n管理者権限で実行するか、ファイル権限を確認してください。"
        logging.error(error_msg)
        logging.debug(f"PermissionError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "権限エラー")

    except ValueError as e:
        error_msg = f"設定値エラー:\n{str(e)}\n\n設定ファイルや環境変数を確認してください。"
        logging.error(error_msg)
        logging.debug(f"ValueError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "設定エラー")

    except tk.TclError as e:
        error_msg = f"UI関連エラー:\n{str(e)}\n\nディスプレイ設定やTkinterの設定を確認してください。"
        logging.error(error_msg)
        logging.debug(f"TclError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "UIエラー")

    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました:\n{str(e)}\n\n詳細は error_log.txt をご確認ください。"
        logging.error(error_msg)
        logging.error(f"予期せぬエラーの詳細: {traceback.format_exc()}")

        # 詳細エラーログファイルの作成
        try:
            detailed_error = f"""
=== GroqWhisper エラーレポート ===
発生日時: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}
バージョン: {VERSION}
エラータイプ: {type(e).__name__}
エラーメッセージ: {str(e)}

=== システム情報 ===
Python バージョン: {sys.version}
プラットフォーム: {sys.platform}
実行ファイル: {sys.executable}

=== 初期化状況 ===
Config: {'初期化済み' if config else '未初期化'}
Recorder: {'初期化済み' if recorder else '未初期化'}
Client: {'初期化済み' if client else '未初期化'}
Replacements: {'初期化済み' if replacements else '未初期化'}
Root: {'初期化済み' if root else '未初期化'}
App: {'初期化済み' if app else '未初期化'}

=== スタックトレース ===
{traceback.format_exc()}

=== 追加情報 ===
作業ディレクトリ: {os.getcwd()}
実行ファイルパス: {__file__}
"""

            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(detailed_error)

            _show_error_dialog(error_msg, "予期せぬエラー")

            # エラーログファイルを開く（可能であれば）
            try:
                os.startfile('error_log.txt')
            except Exception:
                pass  # ファイルを開けなくても続行

        except Exception as log_error:
            # ログファイル作成すら失敗した場合
            final_error = f"エラーログの作成にも失敗しました:\n{str(log_error)}\n\n元のエラー:\n{str(e)}"
            print(final_error, file=sys.stderr)
            _show_error_dialog(final_error, "重大なエラー")

    finally:
        # 最終的なクリーンアップ
        try:
            if app:
                app.cleanup()
        except Exception as cleanup_error:
            logging.error(f"最終クリーンアップ中にエラー: {str(cleanup_error)}")


def _show_error_dialog(message: str, title: str = "エラー"):
    """エラーダイアログを安全に表示"""
    try:
        # 既存のrootがある場合は隠す
        try:
            import tkinter as tk
            root = tk._default_root
            if root:
                root.withdraw()
        except:
            pass

        # 新しいrootを作成してダイアログ表示
        error_root = tk.Tk()
        error_root.withdraw()  # メインウィンドウを隠す
        messagebox.showerror(title, message)
        error_root.destroy()

    except Exception as dialog_error:
        # ダイアログ表示も失敗した場合はコンソール出力
        print(f"{title}: {message}", file=sys.stderr)
        print(f"ダイアログ表示エラー: {str(dialog_error)}", file=sys.stderr)


if __name__ == "__main__":
    main()
