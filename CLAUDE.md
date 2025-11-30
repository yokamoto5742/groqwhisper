# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Project Overview

GroqWhisper is a Windows desktop application that provides real-time voice-to-text transcription using Groq's Whisper API. The application records audio from a microphone, transcribes it to text, and automatically pastes it into the active application.

## Development Commands

### Running the Application
```bash
python main.py
```

### Running Tests
```bash
# Run all tests with verbose output and short traceback
python -m pytest tests/ -v --tb=short

# Run tests without warnings
python -m pytest tests/ -v --tb=short --disable-warnings

# Run specific test file
python -m pytest tests/test_recording_controller.py -v

# Run with coverage
python -m pytest tests/ -v --cov
```

### Building Executable
```bash
# Build Windows executable with PyInstaller (auto-increments version)
python build.py
```

### Type Checking
```bash
# Run pyright type checker (config in pyrightconfig.json)
pyright app service utils widgets
```

## Architecture

### Application Structure

The codebase follows a modular MVC-like pattern with clear separation of concerns:

- **app/**: Application layer and UI components
  - `app_window.py`: Main application controller (`VoiceInputManager`)
  - `app_ui_components.py`: UI widgets and layout

- **service/**: Business logic and core services
  - `recording_controller.py`: Orchestrates recording, transcription, and text processing
  - `audio_recorder.py`: Handles audio capture with PyAudio
  - `keyboard_handler.py`: Global keyboard hooks for shortcuts
  - `text_processing.py`: Text replacement and clipboard operations
  - `safe_paste_sendinput.py`: Safe text pasting using Windows SendInput API
  - `notification.py`: Toast notifications for user feedback
  - `replacements_editor.py`: GUI for editing text replacement rules

- **external_service/**: External API integrations
  - `groq_api.py`: Groq Whisper API client for transcription

- **utils/**: Configuration and utilities
  - `config_manager.py`: Config file loading and management
  - `env_loader.py`: Environment variable handling (.env)
  - `log_rotation.py`: Logging setup with rotation

- **widgets/**: Reusable UI components (currently empty)

### Key Design Patterns

1. **Threading Model**: Audio recording and processing run in separate threads to keep UI responsive. The `RecordingController` manages thread safety with locks and scheduled tasks.

2. **Callback Architecture**: The `VoiceInputManager` passes callbacks to `RecordingController` for UI updates, enabling loose coupling between business logic and UI.

3. **Configuration-Driven**: Nearly all behavior is configurable via `utils/config.ini` (audio parameters, keyboard shortcuts, UI settings, etc.)

4. **Version Management**: Version is stored in `app/__init__.py` as `__version__` and auto-incremented by `scripts/version_manager.py` during builds.

### Critical Dependencies

- **Groq API**: Requires `GROQ_API_KEY` in `.env` file
- **PyAudio**: Native audio recording (Windows-specific)
- **keyboard**: Global keyboard hooks (requires admin privileges on Windows)
- **pyperclip**: Cross-platform clipboard access
- **tkinter**: GUI framework (Python standard library)

## Important Implementation Details

### Audio Recording Flow

1. User presses `Pause` key or clicks UI button
2. `KeyboardHandler` triggers `toggle_recording()` callback
3. `RecordingController.start_recording()` initiates audio capture
4. `AudioRecorder.record()` streams audio in chunks until stopped or timeout (60s default)
5. Audio saved to temp directory as WAV file
6. `RecordingController` calls `transcribe_audio()` in background thread
7. Groq API transcribes audio to text
8. Text replacement applied from `replacements.txt`
9. Result copied to clipboard and pasted via SendInput

### Text Replacement System

- Replacement rules stored in `service/replacements.txt` format: `before,after`
- Rules loaded at startup and applied post-transcription
- GUI editor accessible via "置換テキスト登録" button
- Example: `少子体,硝子体` (medical term correction)

### Keyboard Shortcuts (configurable in config.ini)

- `Pause`: Toggle recording on/off
- `F9`: Toggle punctuation in transcription
- `F8`: Reload and re-transcribe latest audio file
- `Esc`: Exit application

### Threading Safety

The `RecordingController` uses:
- `_ui_lock`: Threading lock for UI updates
- `_scheduled_tasks`: Set to track pending tkinter `after()` calls
- Always schedule UI updates via `master.after()` to run on main thread

## Testing

Tests are written with pytest and use pytest-mock for mocking. Test files mirror the source structure:

- `test_audio_recorder.py`: Audio recording functionality
- `test_groq_api.py`: API integration tests
- `test_recording_controller.py`: Recording orchestration
- `test_text_processing.py`: Text replacement and clipboard operations

When writing tests:
- Mock external dependencies (Groq API, PyAudio, keyboard hooks)
- Test threading behavior with proper synchronization
- Use fixtures for common setup (config, mocks)

## Environment Setup

1. Create `.env` file with:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify config paths in `utils/config.ini` (especially `PATHS` section for temp directory)

## Configuration Notes

- `utils/config.ini` is the single source of truth for configuration
- Whisper model: `whisper-large-v3-turbo` (configurable)
- Language: Japanese (`ja`)
- Custom prompt includes medical and programming terminology context
- Audio: 16kHz mono, optimized for speech

## Build Process

The `build.py` script:
1. Calls `scripts/version_manager.py` to increment version
2. Updates `app/__init__.py` and `docs/README.md`
3. Runs PyInstaller with Windows-specific settings
4. Bundles `.env`, `config.ini`, and `replacements.txt` into executable
