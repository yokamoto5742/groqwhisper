## 2. クリティカルな改善点 (Priority High)

### 2.1. `service/safe_paste_sendinput.py` の複雑性と車輪の再発明
**現状:**
`ctypes` を使用して Windows API (`keybd_event`, `SendMessage`, `GetForegroundWindow`) を直接呼び出しています。実装が非常に低レイヤーで、可読性が低く、メンテナンスコストが高い状態です。また、すでに `keyboard` ライブラリが依存関係に含まれています。

**KISSに基づく改善案:**
Windows API の直接操作を廃止し、既存のライブラリまたはシンプルな `pyperclip` + ショートカット送信に置き換えます。

* **推奨:** `keyboard` ライブラリの `send` 関数を活用する。
* **理由:** `keyboard.send('ctrl+v')` は内部でOSごとの差異を吸収しており、自前で `keybd_event` を実装する必要がありません。

**リファクタリング例:**
```python
import time
import logging
import keyboard
import pyperclip

logger = logging.getLogger(__name__)

def safe_paste_text(text: str) -> bool:
    if not text:
        return False
    
    try:
        # クリップボードへのコピー
        pyperclip.copy(text)
        time.sleep(0.1) # クリップボード反映待ち
        
        # Ctrl+V 送信 (keyboardライブラリを使用)
        keyboard.send('ctrl+v')
        return True
    except Exception as e:
        logger.error(f"貼り付け操作に失敗: {e}")
        return False
````

これだけで `ClipboardPaster` クラスとその複雑なメソッド群（約130行）を10数行に短縮できます。クリップボードのバックアップ/リストア機能が必要であれば、デコレータとして実装することで関心を分離できます。

### 2.2. `service/recording_controller.py` の責務過多 (God Object)

**現状:**
`RecordingController` クラスが以下の責務をすべて負っており、巨大化しています。

1.  録音の開始/停止ロジック
2.  音声ファイルの一時保存管理
3.  API呼び出しのトリガー
4.  スレッド管理と排他制御
5.  **複雑なUIタスクスケジューリング** (`_schedule_ui_task`)
6.  一時ファイルのクリーンアップ

**改善案:**
責務を分割し、`RecordingController` は「処理の流れ（オーケストレーション）」のみに集中させるべきです。

1.  **スレッド/UI管理の簡素化:**
    Tkinterの `after` メソッドはスレッドセーフ（メインループへのイベント登録）として機能するため、複雑な `_ui_lock` や `_scheduled_tasks` の管理機構は過剰設計である可能性が高いです。Python 3と近年のTkinterでは、別スレッドから `master.after(0, callback)` を呼ぶだけで十分安全な場合が多いです。もしくは `queue.Queue` パターンを使用してください。

2.  **ファイル管理の分離:**
    `_cleanup_temp_files` やファイルパス生成ロジックは `AudioManager` または `FileService` クラスとして切り出すべきです。

-----

## 3\. メンテナンス性の向上 (Priority Medium)

### 3.1. `external_service/groq_api.py` の関心の分離

**現状:**
`transcribe_audio` 関数が、「ファイルの読み込み・検証」「API呼び出し」「レスポンスのパース」「句読点処理」「エラーハンドリング」をすべて行っています。

**改善案:**
`transcribe_audio` は「音声データを受け取り、テキストを返す」ことだけに集中すべきです。

  * ファイルの読み込み検証は呼び出し元（Controller）で行う。
  * 句読点処理は `service/text_processing.py` に移動する。

### 3.2. クリップボードロジックの分散

**現状:**

  * `service/text_processing.py`: `copy_and_paste_transcription` 内でクリップボード操作とスレッド起動を行っている。
  * `service/safe_paste_sendinput.py`: 低レベルな貼り付け処理を行っている。

**改善案:**
クリップボードに関する操作（コピー、ペースト、バックアップ）は一つのサービス（例: `ClipboardService`）に集約し、`text_processing.py` は純粋なテキスト変換（置換処理など）のみを行うように変更してください。

### 3.3. ログ設定の分散

`main.py`, `service/audio_recorder.py` などで個別に `logging.basicConfig` や `getLogger` の設定が見られます。`utils/log_rotation.py` に設定が集約されていますが、各ファイルでの呼び出し方を統一（`logger = logging.getLogger(__name__)` のみ記述）し、設定はエントリーポイントで一度だけ行うスタイルを徹底してください。


## 5\. 推奨されるリファクタリング手順

1.  **Step 1 (Cleanup):** `service/safe_paste_sendinput.py` を削除し、`keyboard` ライブラリを使用したシンプルな関数に置き換える。
2.  **Step 2 (Refactor):** `RecordingController` から「UIスケジューリングの独自実装」を削除し、標準的なTkinterの方法に置き換える。
3.  **Step 3 (Separation):** `transcribe_audio` からテキスト加工ロジックを分離する。
