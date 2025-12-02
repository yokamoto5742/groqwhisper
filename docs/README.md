# GroqWhisper

リアルタイム音声認識でテキストを自動入力するWindows向けデスクトップアプリケーション

- **バージョン**: 1.0.1
- **最終更新**: 2025年12月2日

## 概要

GroqWhisperは、Groq社のWhisper APIを利用してマイクからの音声をリアルタイムでテキストに変換し、自動的にアクティブなアプリケーションに貼り付けるWindowsアプリケーションです。医学分野やソフトウェア開発など、専門用語を含む音声入力に対応しています。

## 主な機能

- **リアルタイム音声認識**: マイクから音声をキャプチャし、Groq Whisper APIで高精度のテキスト変換
- **キーボードショートカット**: Pauseキー1つで音声入力のオン/オフを切り替え
- **自動テキスト置換**: 誤認識しやすい専門用語を設定ファイルで自動修正
- **句読点制御**: F9キーで句読点の有無を切り替え可能
- **WAVファイル対応**: 音声ファイルを直接読み込んで文字起こし
- **タスクトレイ常駐**: 起動時にタスクトレイに最小化して利便性向上
- **カスタマイズ性**: 音声品質、キーボードショートカット、貼り付け遅延など細かく設定可能

## 必要な環境

### システム要件

- Windows 10/11
- Python 3.11以上（実行ファイル版では不要）
- マイク（音声入力デバイス）

### 依存ライブラリ

```bash
groq                 # Groq API クライアント
pyaudio             # 音声録音
keyboard            # グローバルキーボードフック
pyperclip           # クリップボード操作
python-dotenv       # .env ファイル読み込み
```

完全なリストは `requirements.txt` を参照してください。

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-repo/groqwhisper.git
cd groqwhisper
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成します:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

[Groq コンソール](https://console.groq.com)からAPIキーを取得してください。

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 設定ファイルの確認

`utils/config.ini` でパス設定を環境に合わせて調整してください:

```ini
[PATHS]
replacements_file = C:\path\to\replacements.txt
temp_dir = C:\path\to\temp
```

### 5. アプリケーションの起動

```bash
python main.py
```

## 使用方法

### 基本的な音声入力

1. アプリケーションを起動
2. **Pauseキー** を押して音声入力開始
3. マイクに向かって話す
4. **Pauseキー** を再度押して入力終了
5. テキストが自動的にアクティブなアプリケーションに貼り付けられます

### キーボードショートカット

| キー | 機能 |
|------|------|
| `Pause` | 音声入力の開始/停止 |
| `F9` | 句読点の有無を切り替え |
| `F8` | 最新の音声ファイルを再読込 |
| `Esc` | アプリケーション終了 |

設定ファイルで各ショートカットはカスタマイズ可能です。

### テキスト置換機能

誤認識しやすい専門用語を自動修正するには、UIの「置換単語登録」ボタンから置換ルールを編集します。

**ファイル形式**: `service/replacements.txt`

```
少子体,硝子体
医療秘書科,医療秘書課
C-Sharp,C#
クロード,Claude
```

形式は `置換前,置換後` で、1行に1つのルール。置換は大文字小文字を区別します。

## 設定

### config.ini の主要セクション

**[AUDIO]** - 音声キャプチャ設定
```ini
sample_rate = 16000    # サンプリングレート（Hz）
channels = 1           # モノラル
chunk = 1024           # フレームサイズ
```

**[WHISPER]** - Whisper API設定
```ini
model = whisper-large-v3-turbo
language = ja
prompt = 眼科医師とプログラマーの会話です...
```

**[FORMATTING]** - テキスト形式
```ini
use_punctuation = True    # 句読点を使用
use_comma = True         # カンマを使用
```

**[CLIPBOARD]** - 貼り付け設定
```ini
paste_delay = 0.2        # 貼り付け前の遅延（秒）
use_sendinput = True     # SendInput API を使用
sendinput_delay = 0.05   # SendInputの送信間隔
```

**[KEYS]** - キーボードショートカット
```ini
toggle_recording = pause
exit_app = esc
reload_audio = f8
toggle_punctuation = f9
```

**[RECORDING]** - 録音制御
```ini
auto_stop_timer = 60     # 無音で自動停止（秒）
```

**[LOGGING]** - ログ設定
```ini
log_level = INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL
debug_mode = False
log_directory = logs
log_retention_days = 7   # ログファイル保持期間
```

**[PATHS]** - ファイルパス
```ini
replacements_file = ...  # 置換ルールファイル
temp_dir = ...          # 一時ファイルディレクトリ
cleanup_minutes = 240   # 古い一時ファイルを削除（分）
```

## ファイル構成

```
GroqWhisper/
├── main.py                           # メインエントリーポイント
├── build.py                          # PyInstaller ビルドスクリプト
├── requirements.txt                  # Python 依存関係
├── .env                              # API キー設定（Git除外）
│
├── app/
│   ├── __init__.py                   # バージョン情報
│   ├── main_window.py                # VoiceInputManager（メイン制御）
│   └── ui_components.py              # UIコンポーネント（ボタン等）
│
├── service/
│   ├── recording_controller.py       # 録音・文字起こし制御
│   ├── audio_recorder.py             # PyAudio を使用した音声キャプチャ
│   ├── keyboard_handler.py           # グローバルキーボードフック
│   ├── text_processing.py            # テキスト置換とクリップボード処理
│   ├── safe_paste_sendinput.py       # SendInput API を使用した安全な貼り付け
│   ├── notification.py               # トースト通知表示
│   ├── replacements_editor.py        # 置換ルール編集GUI
│   └── replacements.txt              # 置換ルール（CSV形式）
│
├── external_service/
│   └── groq_api.py                   # Groq Whisper API クライアント
│
├── utils/
│   ├── config_manager.py             # config.ini 読み込み・保存
│   ├── env_loader.py                 # .env 環境変数読み込み
│   ├── log_rotation.py               # ログローテーション設定
│   └── config.ini                    # 設定ファイル
│
├── tests/
│   ├── test_audio_recorder.py
│   ├── test_groq_api.py
│   ├── test_recording_controller.py
│   ├── test_text_processing.py
│   └── conftest.py                   # pytest フィクスチャ
│
├── scripts/
│   ├── version_manager.py            # バージョン自動更新
│   └── project_structure.py          # プロジェクト構造表示
│
├── docs/
│   └── README.md                     # このファイル
│
└── assets/
    └── GroqWhisper.ico               # アプリケーションアイコン
```

## アーキテクチャ

### 設計パターン

**MVC パターン**
- **Model**: `RecordingController`, `AudioRecorder`, API クライアント
- **View**: `UIComponents`, `NotificationManager`
- **Controller**: `VoiceInputManager`

**マルチスレッド設計**
- UI スレッド: tkinter メインループ
- 録音スレッド: 音声キャプチャ
- 処理スレッド: API呼び出し、テキスト処理、貼り付け

**モジュール分離**
- 各機能を独立した責任を持つモジュールに分割
- 疎結合設計でテスト容易性を確保

### 主要なクラス

**VoiceInputManager** (`app/main_window.py`)
- アプリケーションのメイン制御クラス
- UI コンポーネント、キーボードハンドラ、録音制御を統合
- ウィンドウイベント処理

**RecordingController** (`service/recording_controller.py`)
- 音声録音からテキスト貼り付けまでの全フロー制御
- 複数の非同期処理を スレッドセーフに管理
- UI更新をメインスレッドで実行（thread-safe）

**AudioRecorder** (`service/audio_recorder.py`)
- PyAudio を使用したマイク音声キャプチャ
- WAV形式での音声ファイル保存

**KeyboardHandler** (`service/keyboard_handler.py`)
- グローバルキーボードフック
- Pauseキーなどのショートカット検出

**TextProcessing** (`service/text_processing.py`)
- テキスト置換ロジック
- クリップボード操作
- 句読点処理

### 処理フロー

```
[ユーザー] --Pauseキー--> [KeyboardHandler]
                            |
                            v
                    [RecordingController]
                            |
                 +----------+----------+
                 |                    |
                 v                    v
          [AudioRecorder]      [Thread: transcribe]
                 |                    |
          [WAV ファイル] ------>  [Groq API]
                                      |
                                      v
                                 [TextProcessing]
                                      |
                    +--------+--------+
                    |                 |
                    v                 v
              [Replacement]    [Punctuation]
                    |                 |
                    +--------+--------+
                             |
                             v
                    [クリップボード]
                             |
                             v
                    [アクティブウィンドウ]
```

## テスト実行

### 全テストの実行

```bash
python -m pytest tests/ -v --tb=short
```

### 警告を非表示にする

```bash
python -m pytest tests/ -v --tb=short --disable-warnings
```

### 特定のテストファイルのみ実行

```bash
python -m pytest tests/test_recording_controller.py -v
```

### カバレッジレポート付き

```bash
python -m pytest tests/ -v --cov --cov-report=html
```

## ビルド

実行ファイル（EXE）を作成します。PyInstaller を使用し、バージョンを自動インクリメントします。

```bash
python build.py
```

このコマンドは以下を実行します:
1. `scripts/version_manager.py` でバージョンを自動更新
2. `app/__init__.py` のバージョンを更新
3. `docs/README.md` の最終更新日を更新
4. PyInstaller でスタンドアロンEXEを生成
5. 設定ファイル（`.env`, `config.ini`, `replacements.txt`）を EXE に同梱

生成されたEXEは `dist/GroqWhisper/` に配置されます。

## トラブルシューティング

### マイクが認識されない

**症状**: 「マイクデバイスが見つかりません」エラー

**解決方法**:
- Windows 音声設定でマイクが有効か確認
- 他のアプリケーションがマイクを独占していないか確認
- `ログ/groqwhisper.log` でエラーメッセージを確認
- マイクを接続し直す

### テキストが貼り付けられない

**症状**: クリップボードにはコピーされるが、テキストが入力されない

**解決方法**:
- 貼り付け先アプリケーションが最前面にあるか確認
- `config.ini` の `[CLIPBOARD]` セクションを確認
  - `use_sendinput = True` （SendInput API を使用）
  - `paste_delay` を増加（例: 0.5）
- アプリケーションの管理者権限を確認

### API エラー「GROQ_API_KEY未設定」

**症状**: Groq API に接続できない

**解決方法**:
- `.env` ファイルが存在するか確認
- `GROQ_API_KEY=...` が正しく設定されているか確認
- APIキーに余分なスペースが無いか確認
- [Groq コンソール](https://console.groq.com)でキーが有効か確認
- インターネット接続を確認

### ログファイルの確認

```
logs/
├── groqwhisper.log    # 通常のログ
└── debug.log          # デバッグ時の詳細ログ（debug_mode=True時）
```

ログファイルは自動的にローテーション（デフォルト7日保持）されます。

## 開発者向け情報

### 環境構築

```bash
# Python 3.11+ の仮想環境を作成
python -m venv .venv

# 仮想環境を有効化（Windows）
.venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

### コーディング規約

- **言語**: Python 3.11+
- **コード規約**: [PEP 8](https://pep8.org/) に準拠
- **関数の長さ**: 最大50行（目安）
- **命名**: 説明的で分かりやすい名前（`tmp`, `data` は避ける）
- **DRY原則**: コード重複を避ける
- **型ヒント**: 関数のシグネチャに型を記述
- **コメント**: 分かりにくいロジックのみ、日本語で記述（文末の句点/ピリオド不要）
- **import 順序**:
  1. 標準ライブラリ
  2. サードパーティライブラリ
  3. カスタムモジュール
  - 各グループ内はアルファベット順（`import` が `from` より先）

### 型チェック

```bash
pyright app service utils
```

### 変更履歴

すべての重要な変更は `docs/CHANGELOG.md` に記録します。
フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠。

## ライセンス

このプロジェクトのライセンス情報は `docs/LICENSE` を参照してください。
