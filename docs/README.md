# 音声入力メモアプリ GroqWhisper

## 概要
このアプリケーションは、音声入力を利用してテキストメモを作成するための便利なツールです。音声をリアルタイムで文字起こしし、テキストエリアに表示します。また、クリップボードへのコピーや自動貼り付け機能も備えています。

## 主な機能
- 音声入力によるテキスト生成
- テキストの自動クリップボードコピーと貼り付け
- 句読点の有無を切り替え可能
- キーボードショートカットによる操作
- 自動停止タイマー

## 必要条件
- Python 3.x
- 必要なライブラリ：pyaudio, pyperclip, tkinter, keyboard, pyautogui, groq

## インストール方法
1. リポジトリをクローンまたはダウンロードします。
2. 必要なライブラリをインストールします：
   ```
   pip install pyaudio pyperclip keyboard pyautogui groq
   ```
3. Groq APIキーを環境変数にセットします：
   ```
   export GROQ_API_KEY=your_api_key_here
   ```

## 使用方法
1. アプリケーションを起動します：
   ```
   python main.py
   ```
2. 「音声入力開始」ボタンをクリックするか、設定されたショートカットキーを押して録音を開始します。
3. 話し終わったら、再度ボタンをクリックするかショートカットキーを押して録音を停止します。
4. 文字起こしされたテキストがテキストエリアに表示され、自動的にクリップボードにコピーされます。

## 設定
`config.ini`ファイルで以下の設定を変更できます：

- `start_minimized`: 起動時に最小化するかどうか
- `TOGGLE_RECORDING_KEY`: 録音開始/停止のショートカットキー
- `EXIT_APP_KEY`: アプリ終了のショートカットキー
- `TOGGLE_PUNCTUATION_KEY`: 句点切り替えのショートカットキー
- `TOGGLE_COMMA_KEY`: 読点切り替えのショートカットキー
- `AUTO_STOP_TIMER`: 自動停止までの時間（秒）
- `USE_PUNCTUATION`: デフォルトの句点使用設定
- `USE_COMMA`: デフォルトの読点使用設定

その他、オーディオ設定やUIサイズなども調整可能です。

### AUTO_STOP_TIMER について
AUTO_STOP_TIMER は、音声入力の自動停止を制御する機能です。：

1. 自動停止のタイミング設定：
   - このタイマーは、音声入力が開始されてから自動的に停止するまでの時間を秒単位で指定します。
   - 例：AUTO_STOP_TIMER = 60 と設定すると、音声入力は60秒後に自動的に停止します。

2. 長時間の誤録音防止：
   - ユーザーが録音停止を忘れた場合や、誤って長時間録音してしまうのを防ぎます。
   - 不要な音声データの処理を避け、システムリソースを節約します。

3. ユーザーへの通知：
   - 自動停止の5秒前にユーザーに通知を表示します。
   - ユーザーは録音が間もなく終了することを事前に知ることができます。

4. 柔軟な設定：
   - config.ini ファイル内でこの値を変更することで、ユーザーのニーズに合わせて自動停止のタイミングを調整できます。

5. 録音プロセスの制御：
   - アプリケーション内部で、このタイマーを使用して自動停止のスケジュールを設定しています。

この機能により、ユーザーは長時間の録音を気にせずにアプリケーションを使用でき、同時にシステムも効率的に動作することができます。

## 注意事項
- 音声認識にはインターネット接続が必要です。
- Groq APIの利用には有効なAPIキーが必要です。

## ライセンス
このプロジェクトのライセンス情報については、LICENSEファイルを参照してください。