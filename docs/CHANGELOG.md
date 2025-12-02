# 変更履歴

すべての変更がこのファイルに記録されます。

このプロジェクトは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に従い、
[セマンティック バージョニング](https://semver.org/lang/ja/)を採用しています。

## [Unreleased]

## [1.0.2] - 2025-12-02

### 追加
- RecordingController: UIコールバックをキューイングする処理を追加

### 変更
- デバッグモードを有効に設定

## [1.0.1] - 2025-12-02

### 変更
- バージョンと日付を更新
- RecordingControllerの古い一時ファイル削除ログを音声ファイル削除へ修正
- 通知表示時間を短縮
- 句読点処理関数のdocstringを削除
- クリップボード操作のdocstringを簡潔化
- 置換エディタウィンドウタイトルを修正
- プロジェクト構造スクリプトの出力フォーマットを整理

### 追加
- UI: テキストラベルを「置換テキスト登録」から「置換単語登録」に変更

### 修正
- Groq API: 音声ファイル検証エラーメッセージを修正
- ログローテーション: ログディレクトリのパス解決を修正

## [1.0.0] - 2025-11-28

### 追加
- Groq Whisper APIを使用した音声認識機能
- リアルタイム音声入力とテキスト変換
- テキスト置換機能（replacements.txt）
- キーボードショートカット対応
  - Pause: 録音の開始/停止
  - F8: 最新の音声ファイルを再度文字起こし
  - F9: 句読点の有無を切り替え
  - Esc: アプリケーション終了
- Windows SendInput APIを使用した安全なテキスト貼り付け
- マルチスレッド録音処理
- トースト通知によるユーザーフィードバック
- ログローテーション機能
- 置換ルール編集用GUI
- 句読点処理機能
- Tkinter ベースのUI
- 設定ファイル（config.ini）による動作カスタマイズ

### 技術的詳細
- Python 3.8以上対応
- マルチスレッドで安全な録音・文字起こし処理
- PyAudio を使用したマイク入力キャプチャ
- global keyboard hooks による低遅延なショートカット検出
- pyperclip による クロスプラットフォーム対応のクリップボード操作
- 設定駆動型アーキテクチャ

[Unreleased]: https://github.com/yourusername/groqwhisper/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/yourusername/groqwhisper/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/yourusername/groqwhisper/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/yourusername/groqwhisper/releases/tag/v1.0.0
