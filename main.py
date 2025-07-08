import logging
import os
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from app_window import VoiceInputManager
from external_service.groq_api import setup_groq_client
from utils.config_manager import load_config
from utils.log_rotation import setup_logging, setup_debug_logging
from service.audio_recorder import AudioRecorder
from service.text_processing import load_replacements
from version import VERSION


def main():
    config = None
    recorder = None
    client = None
    replacements = None
    root = None
    app = None

    try:
        config = load_config()
        setup_logging(config)

        debug_logger = setup_debug_logging()
        debug_logger.info("デバッグログシステム初期化完了")

        logging.info("アプリケーションを開始します")
        logging.info(f"バージョン: {VERSION}")

        checkpoint_logger = logging.getLogger('checkpoint')
        checkpoint_logger.info("MAIN_CHECKPOINT_1: 設定読み込み完了")

        recorder = AudioRecorder(config)
        checkpoint_logger.info("MAIN_CHECKPOINT_2: 音声レコーダー初期化完了")

        client = setup_groq_client()
        checkpoint_logger.info("MAIN_CHECKPOINT_3: Groqクライアント初期化完了")

        replacements = load_replacements()
        checkpoint_logger.info("MAIN_CHECKPOINT_4: テキスト置換設定読み込み完了")

        root = tk.Tk()
        checkpoint_logger.info("MAIN_CHECKPOINT_5: Tkinterウィンドウ初期化完了")

        app = VoiceInputManager(root, config, recorder, client, replacements, VERSION)
        checkpoint_logger.info("MAIN_CHECKPOINT_6: アプリケーションマネージャー初期化完了")

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

        logging.info("メインループを開始します")
        checkpoint_logger.info("MAIN_CHECKPOINT_9: メインループ開始")

        root.mainloop()

        checkpoint_logger.info("MAIN_CHECKPOINT_10: メインループ終了")
        logging.info("アプリケーションが正常に終了しました")

    except FileNotFoundError as e:
        error_msg = f"必要なファイルが見つかりません:\n{str(e)}\n\n設定ファイルやリソースファイルを確認してください。"
        logging.error(error_msg)
        logging.debug(f"FileNotFoundError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "ファイルエラー")

    except ValueError as e:
        error_msg = f"設定値エラー:\n{str(e)}\n\n設定ファイルや環境変数を確認してください。"
        logging.error(error_msg)
        logging.debug(f"ValueError詳細: {traceback.format_exc()}")
        _show_error_dialog(error_msg, "設定エラー")

    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました:\n{str(e)}\n\n詳細は error_log.txt をご確認ください。"
        logging.error(error_msg)
        logging.error(f"予期せぬエラーの詳細: {traceback.format_exc()}")

        try:
            detailed_error = f"""
=== GroqWhisper エラーレポート ===
発生日時: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}
バージョン: {VERSION}
エラータイプ: {type(e).__name__}
エラーメッセージ: {str(e)}

=== 初期化状況 ===
Config: {'初期化済み' if config else '未初期化'}
Recorder: {'初期化済み' if recorder else '未初期化'}
Client: {'初期化済み' if client else '未初期化'}
Replacements: {'初期化済み' if replacements else '未初期化'}
Root: {'初期化済み' if root else '未初期化'}
App: {'初期化済み' if app else '未初期化'}

=== スタックトレース ===
{traceback.format_exc()}

"""

            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(detailed_error)

            _show_error_dialog(error_msg, "予期せぬエラー")

            try:
                os.startfile('error_log.txt')
            except Exception:
                pass

        except Exception as log_error:
            final_error = f"エラーログの作成にも失敗しました:\n{str(log_error)}\n\n元のエラー:\n{str(e)}"
            print(final_error, file=sys.stderr)
            _show_error_dialog(final_error, "重大なエラー")

    finally:
        try:
            # VoiceInputManagerの適切なクリーンアップ呼び出し
            if app and hasattr(app, 'close_application'):
                logging.info("最終クリーンアップを実行します")
                app.close_application()
            elif app:
                logging.warning("close_applicationメソッドが見つかりません。代替クリーンアップを実行します")
                # 代替クリーンアップ
                _emergency_cleanup(app)
        except Exception as cleanup_error:
            logging.error(f"最終クリーンアップ中にエラー: {str(cleanup_error)}")
            logging.debug(f"クリーンアップエラー詳細: {traceback.format_exc()}")


def _emergency_cleanup(app):
    """緊急時のクリーンアップ処理"""
    try:
        logging.info("緊急クリーンアップを開始します")

        # 各コンポーネントを個別にクリーンアップ
        cleanup_items = [
            ('recording_controller', getattr(app, 'recording_controller', None)),
            ('keyboard_handler', getattr(app, 'keyboard_handler', None)),
            ('notification_manager', getattr(app, 'notification_manager', None))
        ]

        for name, component in cleanup_items:
            if component and hasattr(component, 'cleanup'):
                try:
                    component.cleanup()
                    logging.info(f"緊急クリーンアップ完了: {name}")
                except Exception as e:
                    logging.error(f"緊急クリーンアップ失敗 ({name}): {str(e)}")

        # UIの終了処理
        if hasattr(app, 'master') and app.master:
            try:
                app.master.quit()
                app.master.destroy()
                logging.info("UI緊急終了完了")
            except Exception as e:
                logging.error(f"UI緊急終了中にエラー: {str(e)}")

    except Exception as e:
        logging.critical(f"緊急クリーンアップ中に重大なエラー: {str(e)}")


def _show_error_dialog(message: str, title: str = "エラー"):
    try:
        try:
            root = tk._default_root
            if root:
                root.withdraw()
        except:
            pass

        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror(title, message)
        error_root.destroy()

    except Exception as dialog_error:
        print(f"{title}: {message}", file=sys.stderr)
        print(f"ダイアログ表示エラー: {str(dialog_error)}", file=sys.stderr)


if __name__ == "__main__":
    main()
