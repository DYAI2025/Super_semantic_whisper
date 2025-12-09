# 🔴 KRITISCHE SCHWACHSTELLE: Hardcodierte Benutzerpfade

**Identifiziert am:** 2025-12-09
**Severity:** KRITISCH (P0)
**Impact:** Blocker für Deployment, Testing, Kollaboration
**Estimated Fix Effort:** 2-4 Stunden

---

## 📋 Problem-Beschreibung

### Betroffene Dateien

1. **`auto_transcriber_v2.py:255`**
2. **`auto_transcriber_v3.py:255`**
3. **`auto_transcriber_v4_emotion.py:255`** ⚠️ (Aktuell genutzter Code)

### Code-Analyse

**Problematischer Code:**
```python
class WhisperSpeakerMatcherV4:
    def __init__(self, base_path=None, use_faster_whisper=True):
        if base_path is None:
            self.base_path = Path("/Users/benjaminpoersch/Library/CloudStorage/GoogleDrive-benjamin.poersch@diyrigent.de/Meine Ablage/MyMind/WhisperSprecherMatcher")
        else:
            self.base_path = Path(base_path)

        self.eingang_path = self.base_path / "Eingang"
        self.memory_path = self.base_path / "Memory"
        self.output_path = self.base_path / "Transkripte_LLM"

        # Fallback für lokale Entwicklung
        if not self.base_path.exists():
            logger.warning(f"Google Drive Pfad nicht verfügbar: {self.base_path}")
            self.base_path = Path("./whisper_speaker_matcher")
            # ... Fallback-Logik
```

### Warum ist das kritisch?

#### 1. **Entwickler-Spezifisch**
```
/Users/benjaminpoersch/...
      ^^^^^^^^^^^^^^^^^
      Nur für EINEN Benutzer
```

- ❌ Andere Entwickler: Instant Crash
- ❌ CI/CD Pipeline: Nicht lauffähig
- ❌ Production Server: Unmöglich zu deployen
- ❌ Docker Container: Pfad existiert nicht

#### 2. **Plattform-Spezifisch**
```
/Users/...
^^^^^^
macOS-spezifisch
```

- ❌ Linux: `/home/user/...` erwartet
- ❌ Windows: `C:\Users\...` erwartet
- ❌ Cloud: Unterschiedliche Filesysteme

#### 3. **Google-Drive-Spezifisch**
```
.../GoogleDrive-benjamin.poersch@diyrigent.de/...
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Cloud-Storage-abhängig
```

- ❌ Netzwerk-Latenz
- ❌ Offline-Modus unmöglich
- ❌ Rate Limiting möglich
- ❌ Sync-Konflikte

#### 4. **Fallback ist unzureichend**
```python
if not self.base_path.exists():
    self.base_path = Path("./whisper_speaker_matcher")
```

**Problem:**
- Fallback wird erst NACH fehlgeschlagenem Google Drive Zugriff aktiv
- Google Drive kann existieren, aber langsam sein (timeout)
- Keine explizite Wahl zwischen Modi

---

## 💥 Impact-Analyse

### Szenarien mit Fehler

#### Szenario 1: Neuer Entwickler
```bash
$ git clone https://github.com/user/Super_semantic_whisper.git
$ cd Super_semantic_whisper
$ python auto_transcriber_v4_emotion.py

Traceback (most recent call last):
  File "auto_transcriber_v4_emotion.py", line 681, in <module>
    matcher = WhisperSpeakerMatcherV4()
  File "auto_transcriber_v4_emotion.py", line 266, in __init__
    logger.warning(f"Google Drive Pfad nicht verfügbar: {self.base_path}")
  ...
FileNotFoundError: [Errno 2] No such file or directory: './whisper_speaker_matcher/Eingang'
```

**Result:** ❌ Sofortiger Abbruch

#### Szenario 2: CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: python -m pytest tests/
```

**Result:**
```
E   FileNotFoundError: /Users/benjaminpoersch/Library/...
FAILED tests/test_transcriber.py::test_basic_transcription
```

❌ Pipeline schlägt fehl

#### Szenario 3: Docker Container
```dockerfile
FROM python:3.10
COPY . /app
RUN python auto_transcriber_v4_emotion.py
```

**Result:**
```
Step 3/5 : RUN python auto_transcriber_v4_emotion.py
 ---> Running in abc123
FileNotFoundError: /Users/benjaminpoersch/...
ERROR: The command '/bin/sh -c python auto_transcriber_v4_emotion.py' returned a non-zero code: 1
```

❌ Build schlägt fehl

#### Szenario 4: Production Server (Linux)
```bash
$ python auto_transcriber_v4_emotion.py
⚠️ Google Drive Pfad nicht verfügbar: /Users/benjaminpoersch/...
INFO: Lokale Struktur erstellt: ./whisper_speaker_matcher
```

⚠️ Läuft, aber:
- Erstellt Verzeichnisse an falschen Stellen
- Keine Daten verfügbar (Memory-Profile fehlen)
- Unerwartetes Verhalten

---

## 🎯 Ziel: Konfigurierbare Pfad-Verwaltung

### Anforderungen

**Functional Requirements:**
1. ✅ Pfade müssen konfigurierbar sein
2. ✅ Mehrere Konfigurations-Quellen (Priorität)
3. ✅ Sinnvolle Defaults
4. ✅ Explizite Wahl zwischen Google Drive / Lokal
5. ✅ Validierung der Pfade

**Non-Functional Requirements:**
1. ✅ Abwärtskompatibilität (bestehende Skripte)
2. ✅ Keine Breaking Changes für User
3. ✅ Einfache Migration
4. ✅ Gut dokumentiert

---

## 🔧 ITERATIVER BEHEBUNGSPLAN

### Iteration 1: Zentrale Konfiguration (30 Min)

**Ziel:** Config-File Support

**Tasks:**
1. Erstelle `config/default_config.yaml`
2. Erstelle `ConfigManager` Klasse
3. Definiere Config-Schema

**Code:**

**`config/default_config.yaml`:**
```yaml
# Super Semantic Whisper - Zentrale Konfiguration

paths:
  # Basis-Pfad (wird erweitert um Unterordner)
  base_path: null  # null = auto-detect

  # Explizite Pfade (überschreiben base_path)
  eingang: null
  memory: null
  output: null

  # Google Drive Konfiguration
  google_drive:
    enabled: false
    base_path: null  # z.B. /Users/name/GoogleDrive/WhisperSprecherMatcher
    timeout_seconds: 5

  # Lokale Fallback-Pfade
  local_fallback:
    enabled: true
    base_path: "./whisper_speaker_matcher"

audio:
  # Whisper Modell
  whisper_model: "base"  # tiny, base, small, medium, large
  language: "de"

  # Audio-Verarbeitung
  supported_formats:
    - .opus
    - .wav
    - .mp3
    - .m4a
    - .ogg

emotional_analysis:
  enabled: true
  use_librosa: true
  use_textblob: true

  # Externe Marker-Systeme
  external_markers:
    frausar_path: null  # Optional
    marsap_path: null   # Optional
    all_markers_path: null  # Optional

logging:
  level: INFO
  file: "transcription.log"
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

**`src/config_manager.py`:**
```python
#!/usr/bin/env python3
"""Zentrale Konfigurationsverwaltung"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Lädt und verwaltet Konfiguration aus mehreren Quellen (Priorität):
    1. Command-Line-Argumente
    2. Umgebungsvariablen
    3. config.yaml (User)
    4. config/default_config.yaml (System)
    """

    DEFAULT_CONFIG_PATHS = [
        Path("config.yaml"),  # User Config
        Path("config/config.yaml"),
        Path("config/default_config.yaml"),  # System Default
    ]

    def __init__(self, config_path: Optional[Path] = None):
        self.config: Dict[str, Any] = {}
        self.config_path = config_path
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self):
        """Lade Konfiguration aus YAML-Datei"""
        config_files = [self.config_path] if self.config_path else self.DEFAULT_CONFIG_PATHS

        for config_file in config_files:
            if config_file and config_file.exists():
                logger.info(f"Lade Konfiguration: {config_file}")
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                return

        logger.warning("Keine Konfigurationsdatei gefunden. Verwende Defaults.")
        self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Hardcoded Fallback-Konfiguration"""
        return {
            'paths': {
                'base_path': None,
                'local_fallback': {
                    'enabled': True,
                    'base_path': './whisper_speaker_matcher'
                }
            },
            'audio': {
                'whisper_model': 'base',
                'language': 'de'
            },
            'emotional_analysis': {
                'enabled': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'transcription.log'
            }
        }

    def _apply_env_overrides(self):
        """Überschreibe Config mit Umgebungsvariablen"""
        env_mappings = {
            'WHISPER_BASE_PATH': ('paths', 'base_path'),
            'WHISPER_EINGANG': ('paths', 'eingang'),
            'WHISPER_MEMORY': ('paths', 'memory'),
            'WHISPER_OUTPUT': ('paths', 'output'),
            'WHISPER_MODEL': ('audio', 'whisper_model'),
            'WHISPER_LANGUAGE': ('audio', 'language'),
            'LOG_LEVEL': ('logging', 'level'),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                logger.info(f"Umgebungsvariable {env_var} überschreibt {section}.{key}")
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value

    def get(self, *keys, default=None):
        """Zugriff auf verschachtelte Config-Werte"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    def get_path(self, path_type: str) -> Path:
        """
        Hole Pfad mit Auto-Detection und Fallback

        path_type: 'base', 'eingang', 'memory', 'output'
        """
        # 1. Expliziter Pfad
        explicit_path = self.get('paths', path_type)
        if explicit_path:
            return Path(explicit_path)

        # 2. Base-Path + Unterordner
        base_path = self.get('paths', 'base_path')
        if base_path:
            base = Path(base_path)
            if path_type == 'base':
                return base
            elif path_type == 'eingang':
                return base / 'Eingang'
            elif path_type == 'memory':
                return base / 'Memory'
            elif path_type == 'output':
                return base / 'Transkripte_LLM'

        # 3. Google Drive (falls aktiviert)
        if self.get('paths', 'google_drive', 'enabled'):
            gd_base = self.get('paths', 'google_drive', 'base_path')
            if gd_base and Path(gd_base).exists():
                logger.info("Nutze Google Drive Pfad")
                base = Path(gd_base)
                if path_type == 'base':
                    return base
                elif path_type == 'eingang':
                    return base / 'Eingang'
                elif path_type == 'memory':
                    return base / 'Memory'
                elif path_type == 'output':
                    return base / 'Transkripte_LLM'

        # 4. Lokaler Fallback
        if self.get('paths', 'local_fallback', 'enabled'):
            fallback_base = Path(self.get('paths', 'local_fallback', 'base_path', default='./whisper_speaker_matcher'))
            logger.info(f"Nutze lokalen Fallback: {fallback_base}")
            if path_type == 'base':
                return fallback_base
            elif path_type == 'eingang':
                return fallback_base / 'Eingang'
            elif path_type == 'memory':
                return fallback_base / 'Memory'
            elif path_type == 'output':
                return fallback_base / 'Transkripte_LLM'

        # 5. Letzter Fallback: Aktuelles Verzeichnis
        logger.warning("Keine konfigurierten Pfade gefunden, nutze aktuelles Verzeichnis")
        cwd = Path.cwd()
        if path_type == 'base':
            return cwd
        elif path_type == 'eingang':
            return cwd / 'Eingang'
        elif path_type == 'memory':
            return cwd / 'Memory'
        elif path_type == 'output':
            return cwd / 'Transkripte_LLM'

        return cwd
```

**Validation:**
```python
# Test
config = ConfigManager()
print(config.get_path('eingang'))  # ./whisper_speaker_matcher/Eingang (Fallback)

# Mit Umgebungsvariable
os.environ['WHISPER_BASE_PATH'] = '/data/whisper'
config = ConfigManager()
print(config.get_path('eingang'))  # /data/whisper/Eingang
```

**Deliverables:**
- ✅ `config/default_config.yaml`
- ✅ `src/config_manager.py`
- ✅ Tests für ConfigManager

---

### Iteration 2: Transcriber Migration (45 Min)

**Ziel:** `auto_transcriber_v4_emotion.py` nutzt ConfigManager

**Änderungen:**

**`auto_transcriber_v4_emotion.py`:**
```python
# Alte Version (Zeile 252-271)
class WhisperSpeakerMatcherV4:
    def __init__(self, base_path=None, use_faster_whisper=True):
        if base_path is None:
            self.base_path = Path("/Users/benjaminpoersch/Library/CloudStorage/...")  # ❌ HARDCODED
        else:
            self.base_path = Path(base_path)

        self.eingang_path = self.base_path / "Eingang"
        self.memory_path = self.base_path / "Memory"
        self.output_path = self.base_path / "Transkripte_LLM"

        # Fallback für lokale Entwicklung
        if not self.base_path.exists():
            logger.warning(f"Google Drive Pfad nicht verfügbar: {self.base_path}")
            self.base_path = Path("./whisper_speaker_matcher")
            # ...
```

**Neue Version:**
```python
from src.config_manager import ConfigManager

class WhisperSpeakerMatcherV4:
    def __init__(self, base_path=None, config_path=None, use_faster_whisper=True):
        """
        Initialisiert den WhisperSpeakerMatcher mit konfigurierbaren Pfaden

        Args:
            base_path: Expliziter Basis-Pfad (überschreibt Config)
            config_path: Pfad zur config.yaml (optional)
            use_faster_whisper: Nutze faster-whisper statt standard whisper
        """
        # Lade Konfiguration
        self.config = ConfigManager(config_path)

        # Pfade aus Config oder Argument
        if base_path:
            # Expliziter Pfad hat Priorität
            self.base_path = Path(base_path)
            self.eingang_path = self.base_path / "Eingang"
            self.memory_path = self.base_path / "Memory"
            self.output_path = self.base_path / "Transkripte_LLM"
        else:
            # Nutze ConfigManager
            self.base_path = self.config.get_path('base')
            self.eingang_path = self.config.get_path('eingang')
            self.memory_path = self.config.get_path('memory')
            self.output_path = self.config.get_path('output')

        # Erstelle Verzeichnisse falls nicht vorhanden
        self._ensure_directories()

        # Logging
        logger.info(f"Basis-Pfad: {self.base_path}")
        logger.info(f"Eingang: {self.eingang_path}")
        logger.info(f"Memory: {self.memory_path}")
        logger.info(f"Output: {self.output_path}")

        self.use_faster_whisper = use_faster_whisper
        self.speakers = self._load_speaker_profiles()
        self.emotion_analyzer = EmotionalAnalyzer()

    def _ensure_directories(self):
        """Erstelle notwendige Verzeichnisse"""
        for path in [self.eingang_path, self.memory_path, self.output_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Verzeichnis erstellt/geprüft: {path}")
```

**Main-Funktion Update:**
```python
def main():
    """Hauptfunktion"""
    print("🎤🎭 WhisperSprecherMatcher V4 mit emotionaler Analyse gestartet...")

    import argparse
    parser = argparse.ArgumentParser(description="WhisperSprecherMatcher V4 (Emotion)")
    parser.add_argument("--local", action="store_true", help="Verwende lokalen Pfad (deprecated, nutze --base-path)")
    parser.add_argument("--base-path", type=str, help="Expliziter Basis-Pfad")
    parser.add_argument("--config", type=str, help="Pfad zur config.yaml")

    args = parser.parse_args()

    try:
        # Abwärtskompatibilität
        if args.local:
            logger.warning("--local ist deprecated, nutze --base-path oder config.yaml")
            matcher = WhisperSpeakerMatcherV4(base_path=".")
        elif args.base_path:
            matcher = WhisperSpeakerMatcherV4(base_path=args.base_path, config_path=args.config)
        else:
            # Standard: Nutze ConfigManager
            matcher = WhisperSpeakerMatcherV4(config_path=args.config)

        matcher.process_audio_files()
        print("✅ Verarbeitung erfolgreich abgeschlossen!")
        print(f"📁 Transkripte gespeichert in: {matcher.output_path}")

    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        print(f"❌ Fehler: {e}")
        sys.exit(1)
```

**Deliverables:**
- ✅ Migrierter `auto_transcriber_v4_emotion.py`
- ✅ Abwärtskompatibilität erhalten
- ✅ CLI mit neuen Optionen

---

### Iteration 3: Alle Transcriber migrieren (30 Min)

**Ziel:** V2, V3 ebenfalls migrieren

**Tasks:**
1. `auto_transcriber_v2.py` → ConfigManager
2. `auto_transcriber_v3.py` → ConfigManager
3. Konsistente CLI-Argumente

**Vorteil:**
- Alle Versionen nutzen gleiche Config
- Einfache Umschaltung zwischen Versionen
- Konsistente Pfade

---

### Iteration 4: Testing & Validation (30 Min)

**Ziel:** Sicherstellen, dass alles funktioniert

**Tests:**

**`tests/test_config_manager.py`:**
```python
import os
import pytest
from pathlib import Path
from src.config_manager import ConfigManager

def test_default_config():
    """Test Default-Konfiguration"""
    config = ConfigManager()
    base = config.get_path('base')
    assert base.name == 'whisper_speaker_matcher'

def test_env_override():
    """Test Umgebungsvariablen"""
    os.environ['WHISPER_BASE_PATH'] = '/tmp/test_whisper'
    config = ConfigManager()
    base = config.get_path('base')
    assert str(base) == '/tmp/test_whisper'
    del os.environ['WHISPER_BASE_PATH']

def test_explicit_config_file():
    """Test explizite Config-Datei"""
    config_content = """
    paths:
      base_path: /custom/path
    """
    config_file = Path('/tmp/test_config.yaml')
    config_file.write_text(config_content)

    config = ConfigManager(config_file)
    base = config.get_path('base')
    assert str(base) == '/custom/path'

    config_file.unlink()

def test_priority():
    """Test Konfigurations-Priorität"""
    # ENV > YAML
    config_content = """
    paths:
      base_path: /yaml/path
    """
    config_file = Path('/tmp/test_config.yaml')
    config_file.write_text(config_content)

    os.environ['WHISPER_BASE_PATH'] = '/env/path'
    config = ConfigManager(config_file)
    base = config.get_path('base')
    assert str(base) == '/env/path'  # ENV wins

    del os.environ['WHISPER_BASE_PATH']
    config_file.unlink()
```

**Integration Test:**
```python
def test_transcriber_with_config():
    """Test Transcriber mit ConfigManager"""
    from auto_transcriber_v4_emotion import WhisperSpeakerMatcherV4

    # Setup Test-Umgebung
    test_base = Path('/tmp/test_whisper')
    test_base.mkdir(exist_ok=True)
    (test_base / 'Eingang').mkdir(exist_ok=True)
    (test_base / 'Memory').mkdir(exist_ok=True)

    # Test mit explizitem Pfad
    matcher = WhisperSpeakerMatcherV4(base_path=str(test_base))
    assert matcher.eingang_path == test_base / 'Eingang'

    # Cleanup
    import shutil
    shutil.rmtree(test_base)
```

**Manual Tests:**
```bash
# Test 1: Default (Fallback)
python auto_transcriber_v4_emotion.py
# Erwartet: ./whisper_speaker_matcher/

# Test 2: Umgebungsvariable
export WHISPER_BASE_PATH=/tmp/whisper_test
python auto_transcriber_v4_emotion.py
# Erwartet: /tmp/whisper_test/

# Test 3: Config-Datei
cat > config.yaml <<EOF
paths:
  base_path: /data/whisper
EOF
python auto_transcriber_v4_emotion.py
# Erwartet: /data/whisper/

# Test 4: CLI-Argument (höchste Priorität)
python auto_transcriber_v4_emotion.py --base-path /custom/path
# Erwartet: /custom/path/

# Test 5: Abwärtskompatibilität
python auto_transcriber_v4_emotion.py --local
# Erwartet: ./Eingang/, ./Memory/, etc.
```

**Deliverables:**
- ✅ Unit Tests (pytest)
- ✅ Integration Tests
- ✅ Manuelle Testszenarien dokumentiert
- ✅ CI/CD Integration

---

### Iteration 5: Dokumentation (20 Min)

**Ziel:** User + Developer Docs

**`docs/KONFIGURATION.md`:**
```markdown
# Konfigurationsanleitung

## Übersicht

Super Semantic Whisper unterstützt mehrere Konfigurationsmöglichkeiten (Priorität absteigend):

1. **Command-Line-Argumente** (höchste Priorität)
2. **Umgebungsvariablen**
3. **config.yaml** (User)
4. **config/default_config.yaml** (System)
5. **Hardcoded Fallback** (niedrigste Priorität)

## Quick Start

### Option 1: Config-Datei (empfohlen)

```bash
# Kopiere Template
cp config/default_config.yaml config.yaml

# Editiere config.yaml
nano config.yaml
```

```yaml
paths:
  base_path: /data/whisper_projects
```

```bash
python auto_transcriber_v4_emotion.py
```

### Option 2: Umgebungsvariablen

```bash
export WHISPER_BASE_PATH=/data/whisper
python auto_transcriber_v4_emotion.py
```

### Option 3: CLI-Argument

```bash
python auto_transcriber_v4_emotion.py --base-path /data/whisper
```

## Alle Umgebungsvariablen

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `WHISPER_BASE_PATH` | Basis-Verzeichnis | `/data/whisper` |
| `WHISPER_EINGANG` | Input-Verzeichnis | `/data/input` |
| `WHISPER_MEMORY` | Sprecher-Profile | `/data/memory` |
| `WHISPER_OUTPUT` | Transkripte-Output | `/data/output` |
| `WHISPER_MODEL` | Whisper-Modell | `base`, `medium`, `large` |
| `WHISPER_LANGUAGE` | Sprache | `de`, `en` |
| `LOG_LEVEL` | Logging-Level | `INFO`, `DEBUG` |

## Google Drive Integration

```yaml
paths:
  google_drive:
    enabled: true
    base_path: /Users/name/GoogleDrive/Whisper
    timeout_seconds: 5
```

Bei Timeout → Fallback auf lokal.

## Docker

```yaml
# config/docker_config.yaml
paths:
  base_path: /app/data
```

```dockerfile
FROM python:3.10
ENV WHISPER_BASE_PATH=/app/data
COPY config/docker_config.yaml /app/config.yaml
```

## Troubleshooting

**Fehler:** `FileNotFoundError: /Users/benjaminpoersch/...`

**Lösung:** Config-Datei anlegen oder `WHISPER_BASE_PATH` setzen.
```

**Update `README.md`:**
```markdown
# Installation

## Konfiguration

Erstelle `config.yaml`:

\`\`\`bash
cp config/default_config.yaml config.yaml
nano config.yaml
\`\`\`

Oder nutze Umgebungsvariablen:

\`\`\`bash
export WHISPER_BASE_PATH=/deine/daten
\`\`\`

Siehe [Konfigurationsanleitung](docs/KONFIGURATION.md) für Details.
```

**Deliverables:**
- ✅ `docs/KONFIGURATION.md`
- ✅ Aktualisierte `README.md`
- ✅ Migration Guide für Bestandsnutzer

---

## 📊 Zusammenfassung Iterativer Plan

| Iteration | Ziel | Dauer | Deliverables |
|-----------|------|-------|--------------|
| **1** | Zentrale Config | 30 Min | `ConfigManager`, `default_config.yaml` |
| **2** | Transcriber V4 Migration | 45 Min | Migrierter `auto_transcriber_v4_emotion.py` |
| **3** | Transcriber V2/V3 Migration | 30 Min | Alle Transcriber einheitlich |
| **4** | Testing & Validation | 30 Min | pytest Tests, Integration Tests |
| **5** | Dokumentation | 20 Min | `KONFIGURATION.md`, Updated `README.md` |
| **GESAMT** | **Vollständige Lösung** | **~2.5h** | Produktionsreife Konfiguration |

---

## ✅ Erfolgskriterien

**Nach Implementierung muss gelten:**

### 1. Entwickler-Experience
- [ ] `git clone` → `python auto_transcriber_v4_emotion.py` funktioniert (mit Fallback)
- [ ] Config-Datei überschreibt Defaults
- [ ] Umgebungsvariablen überschreiben Config
- [ ] CLI-Argumente überschreiben alles
- [ ] Klare Fehlermeldungen wenn Pfade fehlen

### 2. Testing
- [ ] Unit Tests für ConfigManager
- [ ] Integration Tests für Transcriber
- [ ] CI/CD Pipeline läuft durch
- [ ] Docker Build erfolgreich

### 3. Deployment
- [ ] Server-Deployment ohne hardcoded paths
- [ ] Docker Container lauffähig
- [ ] Kubernetes ConfigMaps nutzbar

### 4. Abwärtskompatibilität
- [ ] Bestehende Skripte funktionieren
- [ ] `--local` flag weiterhin unterstützt (deprecated warning)
- [ ] User-Daten bleiben zugänglich

### 5. Dokumentation
- [ ] Klar dokumentierte Konfigurationsoptionen
- [ ] Migration Guide für Bestandsnutzer
- [ ] Troubleshooting-Sektion

---

## 🎯 Nächste Schritte

1. **Iteration 1 starten** - ConfigManager implementieren
2. **Review & Test** - Validierung mit Sample-Daten
3. **Iteration 2-5** - Systematische Abarbeitung
4. **Release** - v5.0 mit Config-Management

**Geschätzte Completion:** 2-4 Stunden
**Breaking Changes:** Keine (Abwärtskompatibilität)
**User Impact:** Positiv (mehr Flexibilität)

---

*Plan erstellt: 2025-12-09*
*Start Implementierung: Sofort nach Review*
