# 🔧 Konfigurationsanleitung

**Super Semantic Whisper** unterstützt flexible Konfiguration über mehrere Quellen.

---

## 📋 Übersicht: Konfigurationsquellen

Die Konfiguration wird in folgender Priorität geladen (höchste zuerst):

1. **Command-Line-Argumente** (`--base-path /data/whisper`)
2. **Umgebungsvariablen** (`WHISPER_BASE_PATH=/data/whisper`)
3. **config.yaml** (User-spezifische Config)
4. **config/default_config.yaml** (System-Defaults)
5. **Hardcoded Fallback** (`./whisper_speaker_matcher/`)

---

## 🚀 Quick Start

### Option 1: Config-Datei (Empfohlen)

**Schritt 1:** Kopiere das Template
```bash
cp config/default_config.yaml config.yaml
```

**Schritt 2:** Editiere `config.yaml`
```yaml
paths:
  base_path: /data/whisper_projects
```

**Schritt 3:** Starte Transcriber
```bash
python auto_transcriber_v4_emotion.py
```

---

### Option 2: Umgebungsvariablen

Perfekt für **Docker** und **CI/CD**:

```bash
export WHISPER_BASE_PATH=/data/whisper
python auto_transcriber_v4_emotion.py
```

---

### Option 3: CLI-Argument

Für **einmalige Ausführungen**:

```bash
python auto_transcriber_v4_emotion.py --base-path /data/whisper
```

---

## 📝 Vollständige Config-Referenz

### Beispiel: `config.yaml`

```yaml
# Super Semantic Whisper - Konfiguration

paths:
  # Basis-Pfad (wird erweitert um Unterordner)
  base_path: /data/whisper

  # Optional: Explizite Pfade (überschreiben base_path)
  eingang: null
  memory: null
  output: null

  # Google Drive Integration (optional)
  google_drive:
    enabled: false
    base_path: /Users/name/GoogleDrive/Whisper
    timeout_seconds: 5

  # Lokaler Fallback (wird genutzt wenn base_path null)
  local_fallback:
    enabled: true
    base_path: "./whisper_speaker_matcher"

audio:
  whisper_model: "base"  # tiny, base, small, medium, large
  language: "de"
  supported_formats:
    - .opus
    - .wav
    - .mp3

emotional_analysis:
  enabled: true
  use_librosa: true
  use_textblob: true

logging:
  level: INFO
  file: "transcription.log"
```

---

## 🌍 Alle Umgebungsvariablen

| Variable | Beschreibung | Beispiel | Überschreibt |
|----------|--------------|----------|--------------|
| `WHISPER_BASE_PATH` | Basis-Verzeichnis | `/data/whisper` | `paths.base_path` |
| `WHISPER_EINGANG` | Input-Verzeichnis | `/data/input` | `paths.eingang` |
| `WHISPER_MEMORY` | Sprecher-Profile | `/data/memory` | `paths.memory` |
| `WHISPER_OUTPUT` | Transkripte-Output | `/data/output` | `paths.output` |
| `WHISPER_MODEL` | Whisper-Modell | `medium`, `large` | `audio.whisper_model` |
| `WHISPER_LANGUAGE` | Sprache | `de`, `en` | `audio.language` |
| `LOG_LEVEL` | Logging-Level | `DEBUG`, `INFO` | `logging.level` |
| `LOG_FILE` | Log-Datei | `debug.log` | `logging.file` |

---

## 💻 CLI-Argumente

### Alle Optionen

```bash
python auto_transcriber_v4_emotion.py --help
```

**Ausgabe:**
```
usage: auto_transcriber_v4_emotion.py [-h] [--local] [--base-path BASE_PATH]
                                      [--config CONFIG] [--show-config]

WhisperSprecherMatcher V4 (Emotion)

optional arguments:
  -h, --help            show this help message and exit
  --local               Verwende lokalen Pfad (DEPRECATED)
  --base-path BASE_PATH
                        Expliziter Basis-Pfad (überschreibt config.yaml)
  --config CONFIG       Pfad zur config.yaml
  --show-config         Zeige effektive Konfiguration und beende
```

### Beispiele

**Zeige aktuelle Konfiguration:**
```bash
python auto_transcriber_v4_emotion.py --show-config
```

**Nutze custom config:**
```bash
python auto_transcriber_v4_emotion.py --config /etc/whisper/config.yaml
```

**Expliziter Pfad (überschreibt alles):**
```bash
python auto_transcriber_v4_emotion.py --base-path /tmp/whisper_test
```

---

## 🐳 Docker-Integration

### Dockerfile mit Umgebungsvariablen

```dockerfile
FROM python:3.10

# Installiere FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Setze Basis-Pfad
ENV WHISPER_BASE_PATH=/app/data
ENV WHISPER_MODEL=base
ENV LOG_LEVEL=INFO

# Kopiere Code
COPY . /app
WORKDIR /app

# Installiere Dependencies
RUN pip install -r requirements_emotion.txt

# Erstelle Datenverzeichnisse
RUN mkdir -p /app/data/Eingang /app/data/Memory /app/data/Transkripte_LLM

# Starte Transcriber
CMD ["python", "auto_transcriber_v4_emotion.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  whisper-transcriber:
    build: .
    volumes:
      - ./data:/app/data
      - ./Memory:/app/data/Memory:ro
    environment:
      - WHISPER_BASE_PATH=/app/data
      - WHISPER_MODEL=medium
      - LOG_LEVEL=DEBUG
```

**Starten:**
```bash
docker-compose up
```

---

## ☁️ Google Drive Integration

### Konfiguration

```yaml
paths:
  google_drive:
    enabled: true
    base_path: /Users/name/GoogleDrive/Whisper
    timeout_seconds: 5

  local_fallback:
    enabled: true
    base_path: ./local_backup
```

### Verhalten

1. **Google Drive verfügbar** → Nutzt Google Drive Pfad
2. **Google Drive nicht erreichbar** (Timeout) → Fallback auf `./local_backup`
3. **Logs zeigen aktiven Modus:**
   ```
   INFO: ☁️ Nutze Google Drive Pfad: /Users/name/GoogleDrive/Whisper
   ```
   oder
   ```
   INFO: 💾 Nutze lokalen Fallback: ./local_backup
   ```

---

## 🔒 Sicherheits-Best-Practices

### 1. Config-File-Permissions

```bash
# Setze restriktive Permissions (nur Owner lesen/schreiben)
chmod 600 config.yaml
```

**Warnung:**
```
⚠️ SICHERHEITSWARNUNG: config.yaml hat unsichere Permissions (0o644).
Empfohlen: chmod 600 config.yaml
```

### 2. Secrets NICHT in config.yaml

❌ **Falsch:**
```yaml
paths:
  google_drive:
    api_token: "secret_xyz"  # ❌ NIEMALS!
```

✅ **Richtig:**
```yaml
# config.yaml (im Git)
paths:
  google_drive:
    enabled: true
```

```bash
# .env (NICHT im Git)
export GOOGLE_DRIVE_TOKEN=secret_xyz
```

### 3. .gitignore

Stelle sicher, dass `config.yaml` **nicht** ins Git committed wird:

```gitignore
# .gitignore
config.yaml
*.log
```

**Im Git sollte nur sein:**
```
config/default_config.yaml  # ✓ Template
```

---

## 🧪 Entwicklung & Testing

### Test-Konfiguration

Erstelle `config/test_config.yaml`:

```yaml
paths:
  base_path: /tmp/whisper_test

logging:
  level: DEBUG
  file: test.log
```

**Nutze in Tests:**
```bash
python auto_transcriber_v4_emotion.py --config config/test_config.yaml
```

### Multiple Environments

```
config/
├── default_config.yaml      # System Default
├── dev_config.yaml          # Development
├── staging_config.yaml      # Staging
└── prod_config.yaml         # Production
```

**Umschalten:**
```bash
# Development
python auto_transcriber_v4_emotion.py --config config/dev_config.yaml

# Production
python auto_transcriber_v4_emotion.py --config config/prod_config.yaml
```

---

## 🚨 Troubleshooting

### Problem: `FileNotFoundError: /Users/benjaminpoersch/...`

**Ursache:** Du nutzt alte Version ohne Config-Management.

**Lösung:**
```bash
# Option 1: Erstelle config.yaml
cp config/default_config.yaml config.yaml
nano config.yaml  # Setze paths.base_path

# Option 2: Nutze ENV var
export WHISPER_BASE_PATH=/deine/daten
python auto_transcriber_v4_emotion.py

# Option 3: CLI-Argument
python auto_transcriber_v4_emotion.py --base-path /deine/daten
```

---

### Problem: "Keine Konfigurationsdatei gefunden"

**Meldung:**
```
⚠️ Keine Konfigurationsdatei gefunden. Verwende Defaults.
INFO: 💾 Nutze lokalen Fallback: ./whisper_speaker_matcher
```

**Lösung:** Das ist OK! Der Fallback funktioniert automatisch.

**Optional:**
```bash
cp config/default_config.yaml config.yaml
```

---

### Problem: Pfad existiert nicht

**Warnung:**
```
⚠️ Warnung: Basis-Pfad existiert nicht: /data/whisper
```

**Lösung:**
```bash
# Erstelle Verzeichnis
mkdir -p /data/whisper

# Oder ändere config.yaml
paths:
  base_path: /existierender/pfad
```

---

### Problem: YAML-Syntax-Fehler

**Fehler:**
```
❌ YAML-Fehler in config.yaml: mapping values are not allowed here
```

**Lösung:**
```bash
# Validiere Config
python scripts/validate_config.py config.yaml

# Prüfe Syntax (Online)
# → https://www.yamllint.com/
```

---

## 📊 Debugging: Zeige effektive Konfiguration

Wenn unsicher, welche Konfiguration geladen wird:

```bash
python auto_transcriber_v4_emotion.py --show-config
```

**Ausgabe:**
```
============================================================
📋 EFFEKTIVE KONFIGURATION
============================================================
Geladene Datei: config.yaml

Umgebungsvariablen-Overrides:
  WHISPER_BASE_PATH=/data/whisper

Effektive Pfade:
  base     [✓] /data/whisper
  eingang  [✓] /data/whisper/Eingang
  memory   [✓] /data/whisper/Memory
  output   [✗] /data/whisper/Transkripte_LLM

Audio-Konfiguration:
  Modell: base
  Sprache: de

Emotionale Analyse:
  Aktiviert: True
  Librosa: True
  TextBlob: True
============================================================
```

---

## 🆘 Weitere Hilfe

- **Hauptdokumentation:** [README.md](../README.md)
- **Ordner-Struktur:** [ORDNER_ANLEITUNG.md](../ORDNER_ANLEITUNG.md)
- **Architektur:** [ARCHITEKTUR_ANALYSE.md](../ARCHITEKTUR_ANALYSE.md)
- **Issues:** [GitHub Issues](https://github.com/username/repo/issues)

---

*Aktualisiert: 2025-12-09 | Version 5.0*
