# Phase 1 - Task 1.1 Analysis

The original project contains a large script `auto_transcriber_v4_emotion.py`.
Important components that can be reused are:

- **`EmotionalAnalyzer`** – loads emotional marker files and extracts audio/text
  based emotion scores.
- **`WhisperSpeakerMatcherV4`** – orchestrates transcription, speaker detection
  and formatting of results.
  - utilities like `extract_whatsapp_datetime`, `get_chatpartner_from_path` and
    `transcribe_audio_standard` will be refactored into separate modules.

## Dependencies
The current code relies on:
- `openai-whisper`
- `librosa`
- `textblob`
- `numpy`

Additional packages required for the new watcher system:
- `watchdog>=3.0.0` for monitoring directories
- `pyyaml>=6.0` for configuration
- `psutil>=5.9.0` for resource monitoring

## Planned Project Structure
```
whatsapp_auto_transcriber/
├── config/
│   ├── config.yaml
│   └── config_template.yaml
├── src/
│   ├── __init__.py
│   ├── file_watcher.py
│   ├── audio_processor.py
│   ├── speaker_detector.py
│   ├── config_manager.py
│   └── monitoring.py
├── tests/
├── logs/
├── output/
├── docs/
│   └── phase1_task1_1_analysis.md
├── main.py
├── requirements.txt
└── README.md
```
This structure separates concerns and prepares for further tasks such as
implementing a file watcher, configuration management and tests.
