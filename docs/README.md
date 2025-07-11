# GroqWhisper 音声入力メモ

## 概要

GroqWhisper 音声入力メモは、Groq社のWhisper APIを利用してリアルタイムで音声をテキストに変換し、自動的にクリップボードに貼り付けるWindowsアプリケーションです。

## 主な機能

### 🎤 音声入力機能
- **リアルタイム音声認識**: マイクからの音声をリアルタイムでテキストに変換
- **キーボードショートカット**: `Pause`キーで音声入力の開始/停止
- **自動停止**: 一定時間で自動的に録音を停止
- **音声ファイル読み込み**: WAVファイルを直接読み込んで文字起こし

### ⚙️ カスタマイズ機能
- **句読点切り替え**: `F9`キーで句読点の有無を切り替え
- **テキスト置換**: 誤認識しやすい専門用語を自動置換
- **設定可能なパラメータ**: 音声品質、貼り付け遅延時間など

### 🖥️ ユーザーインターフェース
- **最小化起動**: 起動時にタスクトレイに最小化
- **直感的なUI**: シンプルで使いやすいボタン配置
- **リアルタイム通知**: 処理状況をポップアップで表示

## 必要な環境

### システム要件
- **OS**: Windows 10/11
- **Python**: 3.11以上（実行ファイル版では不要）
- **マイク**: 音声入力デバイス

### 依存関係
主要なライブラリ（requirements.txtに記載）：
- `groq`: Groq API クライアント
- `pyaudio`: 音声録音機能
- `keyboard`: グローバルキーボードフック
- `pyperclip`: クリップボード操作
- `tkinter`: GUI（Pythonに標準含有）

## セットアップ

### 1. 環境変数の設定
プロジェクトルートに`.env`ファイルを作成し、GroqのAPIキーを設定してください：

```bash
GROQ_API_KEY=your_groq_api_key_here
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. 設定ファイルの確認
`utils/config.ini`で各種設定を確認・変更できます：

```ini
[KEYS]
toggle_recording = pause    # 録音開始/停止キー
exit_app = esc             # アプリ終了キー
reload_audio = f8          # 最新音声再読込キー
toggle_punctuation = f9    # 句読点切り替えキー

[PATHS]
replacements_file = C:\Shinseikai\GroqWhisper\_internal\replacements.txt
temp_dir = C:\Shinseikai\GroqWhisper\temp
```

## 使用方法

### 基本的な使い方

1. **アプリケーションを起動**
   ```bash
   python main.py
   ```

2. **音声入力を開始**
   - `Pause`キーを押すか、「音声入力開始」ボタンをクリック
   - マイクに向かって話す

3. **音声入力を停止**
   - 再度`Pause`キーを押すか、「音声入力停止」ボタンをクリック
   - テキストが自動的にクリップボードにコピーされ、アクティブなアプリケーションに貼り付けられます

### テキスト置換機能

アプリケーション内の「置換テキスト登録」ボタンから、誤認識されやすい単語の置換ルールを編集できます。

**置換ルールの例**：
```
少子体,硝子体
医療秘書科,医療秘書課
C-Sharp,C#
クロード,Claude
```

形式：`置換前,置換後`（1行に1つの置換ルール）

## ファイル構成

```
GroqWhisper/
├── main.py                          # メインエントリーポイント
├── app_window.py                    # アプリケーションメインウィンドウ
├── app_ui_components.py             # UIコンポーネント
├── version.py                       # バージョン情報
├── requirements.txt                 # 依存関係
├── external_service/
│   └── groq_api.py                 # Groq API クライアント
├── service/
│   ├── audio_recorder.py           # 音声録音機能
│   ├── keyboard_handler.py         # キーボードハンドリング
│   ├── notification.py             # 通知機能
│   ├── recording_controller.py     # 録音制御
│   ├── replacements_editor.py      # 置換テキスト編集
│   ├── safe_paste_sendinput.py     # 安全な貼り付け機能
│   ├── text_processing.py          # テキスト処理
│   └── replacements.txt            # 置換ルール
└── utils/
    ├── config.ini                  # 設定ファイル
    ├── config_manager.py           # 設定管理
    ├── env_loader.py               # 環境変数読み込み
    └── log_rotation.py             # ログローテーション
```

## トラブルシューティング

### よくある問題

**Q: マイクが認識されない**
- Windowsの音声設定でマイクが有効になっているか確認
- 他のアプリケーションがマイクを使用していないか確認

**Q: テキストが貼り付けられない**
- 貼り付け先のアプリケーションがアクティブになっているか確認
- クリップボードの権限設定を確認

**Q: APIエラーが発生する**
- `.env`ファイルのGroq APIキーが正しく設定されているか確認
- インターネット接続を確認

### ログの確認

ログファイルは`logs/`ディレクトリに保存されます：
- `groqwhisper.log`: 通常のログ
- `debug.log`: デバッグモード時の詳細ログ

## 開発者向け情報

### アーキテクチャ

- **MVC パターン**: UIとビジネスロジックを分離
- **マルチスレッド**: 音声処理とUI操作を非同期実行
- **モジュラー設計**: 機能ごとにモジュールを分割

### 主要なクラス

- `VoiceInputManager`: アプリケーションの中心制御
- `RecordingController`: 録音制御とテキスト変換
- `AudioRecorder`: 音声録音機能
- `UIComponents`: ユーザーインターフェース
- `KeyboardHandler`: グローバルキーボードフック

### カスタマイズ

設定ファイル（`utils/config.ini`）で以下をカスタマイズできます：

- 音声録音パラメータ
- キーボードショートカット
- ファイルパス
- ログ設定
- UI設定

## ライセンス
このプロジェクトのライセンス情報については、LICENSEファイルを参照してください。
