import logging
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Dict, Any

from config_manager import get_config_value


class ReplacementsEditor:
    def __init__(self, parent: tk.Tk, config: Dict[str, Any]):
        if 'PATHS' not in config or 'replacements_file' not in config['PATHS']:
            raise ValueError('コンフィグにreplacements_fileのパス設定がありません')

        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title('テキスト置換登録( 置換前 , 置換後 )')
        window_width = get_config_value(self.config, 'EDITOR', 'width', 400)
        window_height = get_config_value(self.config, 'EDITOR', 'height', 700)
        self.window.geometry(f'{window_width}x{window_height}')

        font_name = get_config_value(self.config, 'EDITOR', 'font_name', 'MS Gothic')
        font_size = get_config_value(self.config, 'EDITOR', 'font_size', 12)
        self.text_area = tk.Text(
            self.window,
            wrap=tk.WORD,
            width=50,
            height=20,
            font=(font_name, font_size)
        )
        self.text_area.pack(expand=True, fill='both', padx=10, pady=5)

        # スクロールバーの追加
        scrollbar = ttk.Scrollbar(self.window, command=self.text_area.yview)
        scrollbar.pack(side='right', fill='y')
        self.text_area['yscrollcommand'] = scrollbar.set

        # ボタンフレーム
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=5)

        # 保存ボタン
        save_button = ttk.Button(
            button_frame,
            text='保存',
            command=self.save_file
        )
        save_button.pack(side='left', padx=5)

        # キャンセルボタン
        cancel_button = ttk.Button(
            button_frame,
            text='キャンセル',
            command=self.window.destroy
        )
        cancel_button.pack(side='left', padx=5)

        # ファイル読み込み
        self.load_file()

        # ウィンドウを最前面に
        self.window.transient(parent)
        self.window.grab_set()

    def load_file(self) -> None:
        """ファイルの内容を読み込んでテキストエリアに表示"""
        replacements_path = self.config['PATHS']['replacements_file']

        try:
            if os.path.exists(replacements_path):
                with open(replacements_path, encoding='utf-8') as f:
                    content = f.read()
                self.text_area.insert('1.0', content)
            else:
                logging.warning(f'置換設定ファイルが見つかりません: {replacements_path}')
                messagebox.showwarning(
                    '警告',
                    f'ファイルが見つかりません。新規作成します：\n{replacements_path}'
                )
        except Exception as e:
            logging.error(f'ファイルの読み込みに失敗しました: {str(e)}')
            messagebox.showerror(
                'エラー',
                f'ファイルの読み込みに失敗しました：\n{str(e)}'
            )

    def save_file(self) -> None:
        """テキストエリアの内容をファイルに保存"""
        replacements_path = self.config['PATHS']['replacements_file']

        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(replacements_path), exist_ok=True)

            content = self.text_area.get('1.0', 'end-1c')
            with open(replacements_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo(
                '保存完了',
                'ファイルを保存しました'
            )
            self.window.destroy()

        except Exception as e:
            logging.error(f'ファイルの保存に失敗しました: {str(e)}')
            messagebox.showerror(
                'エラー',
                f'ファイルの保存に失敗しました：\n{str(e)}'
            )
