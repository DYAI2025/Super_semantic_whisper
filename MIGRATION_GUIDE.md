# 🔄 Migration Guide: V4 → V5 (Config-Management)

**Version 5.0** führt zentrales Konfigurations-Management ein und eliminiert hardcodierte Pfade.

---

## 🎯 Was hat sich geändert?

### Vorher (V4)
```python
# ❌ Hardcodierter Google Drive Pfad
matcher = WhisperSpeakerMatcherV4()
# → Funktioniert nur für einen Benutzer
```

### Jetzt (V5)
```python
# ✅ Flexible Konfiguration
matcher = WhisperSpeakerMatcherV4()
# → Nutzt config.yaml oder Umgebungsvariablen
```

---

## ✅ Für die meisten Nutzer: KEINE Änderungen nötig!

**Automatischer Fallback:**
- V5 funktioniert **ohne** config.yaml
- Nutzt automatisch `./whisper_speaker_matcher/`
- Bestehende Skripte **funktionieren weiterhin**

---

## 🔄 Migration-Szenarien

### Szenario 1: Du nutzt `--local`

**Vorher:**
```bash
python auto_transcriber_v4_emotion.py --local
```

**Jetzt:**
```bash
# Option 1: Weiterhin nutzen (funktioniert, zeigt Deprecation Warning)
python auto_transcriber_v4_emotion.py --local

# Option 2: Neue Syntax (empfohlen)
python auto_transcriber_v4_emotion.py --base-path .

# Option 3: config.yaml
echo "paths:
  base_path: ." > config.yaml
python auto_transcriber_v4_emotion.py
```

---

### Szenario 2: Du hast den Code mit custom Pfad angepasst

**Vorher:**
```python
# In deinem Skript
from auto_transcriber_v4_emotion import WhisperSpeakerMatcherV4
matcher = WhisperSpeakerMatcherV4(base_path="/mein/pfad")
```

**Jetzt:**
```python
# Funktioniert IDENTISCH (Abwärtskompatibilität)
from auto_transcriber_v4_emotion import WhisperSpeakerMatcherV4
matcher = WhisperSpeakerMatcherV4(base_path="/mein/pfad")

# Oder neu (empfohlen):
matcher = WhisperSpeakerMatcherV4()  # Liest aus config.yaml
```

---

### Szenario 3: Google Drive Nutzer

**Vorher:**
```python
# Hardcoded in Code
self.base_path = Path("/Users/name/GoogleDrive/...")
```

**Jetzt:**

**Option A: config.yaml**
```yaml
paths:
  google_drive:
    enabled: true
    base_path: /Users/name/GoogleDrive/Whisper
```

**Option B: Umgebungsvariable**
```bash
export WHISPER_BASE_PATH="/Users/name/GoogleDrive/Whisper"
```

---

### Szenario 4: Docker/Server-Deployment

**Vorher:**
```dockerfile
# Hacky workaround
RUN sed -i 's|/Users/benjaminpoersch/...|/app/data|g' auto_transcriber_v4.py
```

**Jetzt:**
```dockerfile
# Sauber via ENV var
ENV WHISPER_BASE_PATH=/app/data
```

**Oder mit Config:**
```dockerfile
COPY config/docker_config.yaml /app/config.yaml
```

---

## 📝 Schritt-für-Schritt Migration

### Schritt 1: Erstelle config.yaml

```bash
# Kopiere Template
cp config/default_config.yaml config.yaml

# Editiere
nano config.yaml
```

### Schritt 2: Setze deinen Pfad

```yaml
paths:
  base_path: /dein/whisper/pfad
```

### Schritt 3: Teste

```bash
# Zeige Konfiguration
python auto_transcriber_v4_emotion.py --show-config

# Sollte zeigen:
# Effektive Pfade:
#   base [✓] /dein/whisper/pfad
```

### Schritt 4: Normaler Betrieb

```bash
python auto_transcriber_v4_emotion.py
# → Nutzt jetzt config.yaml
```

---

## 🆕 Neue Features

### 1. `--show-config` Befehl

```bash
python auto_transcriber_v4_emotion.py --show-config
```

Zeigt:
- Welche Config-Datei geladen wurde
- Welche Umgebungsvariablen aktiv sind
- Effektive Pfade
- Ob Pfade existieren

### 2. Mehrere Config-Dateien

```bash
# Development
python auto_transcriber_v4_emotion.py --config config/dev_config.yaml

# Production
python auto_transcriber_v4_emotion.py --config config/prod_config.yaml
```

### 3. Umgebungsvariablen

```bash
export WHISPER_BASE_PATH=/data/whisper
export WHISPER_MODEL=medium
export LOG_LEVEL=DEBUG

python auto_transcriber_v4_emotion.py
```

### 4. Config-Validierung

```bash
python scripts/validate_config.py config.yaml
```

Prüft:
- YAML-Syntax
- Schema-Validierung
- Pfad-Existenz

---

## ⚠️ Breaking Changes

**KEINE!** V5 ist **100% abwärtskompatibel**.

Folgendes funktioniert **weiterhin**:
```python
matcher = WhisperSpeakerMatcherV4()  # Nutzt Fallback
matcher = WhisperSpeakerMatcherV4(base_path="/pfad")  # Expliziter Pfad
```

Nur deprecated:
- `--local` Flag (zeigt Warning, funktioniert aber)

---

## 🐛 Probleme nach Migration?

### Problem 1: FileNotFoundError

```bash
# Prüfe Config
python auto_transcriber_v4_emotion.py --show-config

# Erstelle fehlende Verzeichnisse
mkdir -p /dein/pfad/{Eingang,Memory,Transkripte_LLM}
```

### Problem 2: Falscher Pfad wird genutzt

```bash
# Debug: Zeige Konfiguration
python auto_transcriber_v4_emotion.py --show-config

# Prüfe Priorität:
# 1. CLI-Argument (--base-path)
# 2. ENV var (WHISPER_BASE_PATH)
# 3. config.yaml
# 4. config/default_config.yaml
```

### Problem 3: YAML-Fehler

```bash
# Validiere Syntax
python scripts/validate_config.py config.yaml

# Oder nutze Online-Tool
# → https://www.yamllint.com/
```

---

## 📚 Weitere Dokumentation

- **Vollständige Config-Referenz:** [docs/KONFIGURATION.md](docs/KONFIGURATION.md)
- **Architektur-Übersicht:** [ARCHITEKTUR_ANALYSE.md](ARCHITEKTUR_ANALYSE.md)
- **Schwachstellen-Analyse:** [SCHWACHSTELLE_HARDCODED_PATHS.md](SCHWACHSTELLE_HARDCODED_PATHS.md)

---

## ✅ Zusammenfassung

**TL;DR:**
- ✅ Keine Code-Änderungen nötig
- ✅ Bestehende Skripte funktionieren
- ✅ Optional: Erstelle `config.yaml` für bessere Kontrolle
- ✅ Neue Features: `--show-config`, ENV vars, Multi-Config

**Empfehlung:**
1. Weiter nutzen wie bisher (funktioniert!)
2. Bei Gelegenheit: `config.yaml` erstellen
3. Bei Server-Deployment: Umgebungsvariablen nutzen

---

*Version 5.0 | 2025-12-09*
