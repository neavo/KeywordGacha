# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KeywordGacha is an AI-powered translation terminology/glossary extraction tool. It analyzes text (novels, games, subtitles) using LLMs to generate consistent glossaries for translators. Built with Python 3.12, PyQt5 + PyQt-Fluent-Widgets GUI, supports 16+ languages.

## Development Commands

```bash
# Install dependencies
pip install -U -r requirements.txt

# Run the application (GUI mode)
python app.py

# Build Windows executable
python resource/pyinstaller.py
```

There is no automated test suite (no pytest/unittest). Testing is done manually via the UI and `APITester` module.

## Architecture

### Entry Point
- `app.py` — Initializes Qt app, loads config, creates main window. Also supports CLI mode via `CLIManager`.

### Core Patterns
- **Event-driven**: `base/EventManager.py` provides pub-sub for decoupled communication between UI and backend (events: `PROJECT_CHECK_RUN`, `NER_ANALYZER_RUN`, `NER_ANALYZER_EXPORT`, `TOAST`, etc.)
- **Singletons**: `Engine`, `Config`, `LogManager`, `CacheManager`, `Localizer` all use `get()` classmethod pattern
- **Thread-safe data**: `model/Item.py` and `model/Project.py` use `threading.Lock` for getters/setters
- **Config persistence**: JSON-based config at `resource/config.json`, thread-safe load/save

### Processing Pipeline
1. **File Discovery** (`module/File/FileManager.py`) — Scans input folder, routes to format-specific handlers
2. **File Parsing** (`module/File/*.py`) — Extracts text into `Item` objects. Supports: TXT, MD, SRT, ASS, EPUB, XLSX, RenPy, KVJSON (MTool), MESSAGEJSON (SExtractor), TRANS (Translator++)
3. **NER Analysis** (`module/Engine/NERAnalyzer/`) — Batches items, builds prompts, sends to LLM, parses JSON responses with `src`/`dst`/`type` fields
4. **Caching** (`module/CacheManager.py`) — Auto-saves every 15s to `output_folder/cache/items.json`, enables task resumption

### AI Integration
- `module/Engine/TaskRequester.py` — Unified client for OpenAI, Anthropic, Google GenAI APIs
- `module/Engine/TaskLimiter.py` — Rate limiting and concurrency control
- Supports API key rotation, configurable timeouts, multiple model types
- Token counting via `tiktoken`

### UI Layer
- `frontend/` — PyQt5 pages using Fluent Design widgets
- `widget/` — Reusable UI card components (ComboBoxCard, SliderCard, SwitchButtonCard, etc.)
- `frontend/AppFluentWindow.py` — Main window with navigation

### Text Processing
- `module/Normalizer.py` — Unicode normalization
- `module/RubyCleaner.py` — Removes Japanese ruby annotations
- `module/FakeNameHelper.py` — Replaces names with placeholders for privacy during API calls
- `module/PromptBuilder.py` — Generates LLM prompts from templates in `resource/prompt/{zh,en}/`

### Localization
- `module/Localizer/` — Runtime language switching (ZH/EN)
- UI strings as class attributes in `LocalizerZH.py` / `LocalizerEN.py`

## Key Conventions

- All UI text must support both Chinese and English via the Localizer system
- LLM responses are expected as JSON arrays with `src`, `dst`, `type` fields; parsed with `json-repair` for robustness
- File format handlers inherit common patterns but are standalone modules under `module/File/`
- Pre-configured AI platform definitions live in `resource/platforms/{zh,en}/`

## 参考代码
实现新功能时，参考 `../LinguaGacha/` 目录下的代码写法，

