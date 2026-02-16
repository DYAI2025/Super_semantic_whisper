# Super Semantic Whisper (SSW)

**Intelligentes System zur automatischen Transkription von WhatsApp-Audionachrichten mit Sprechererkennung, emotionaler Analyse und semantischer Mustererkennung.**

**Status:** Funktionsfaehiger Monolith mit kritischen Portabilitaetsproblemen
**Sprache:** Python 3.8+
**Lizenz:** Creative Commons BY-NC-SA 4.0

---

## Inhaltsverzeichnis

1. [Uebersicht](#uebersicht)
2. [Architektur und Komponenten](#architektur-und-komponenten)
3. [Verarbeitungs-Pipeline](#verarbeitungs-pipeline)
4. [Voraussetzungen und Installation](#voraussetzungen-und-installation)
5. [Konfiguration](#konfiguration)
6. [Nutzung](#nutzung)
7. [Verzeichnisstruktur](#verzeichnisstruktur)
8. [Detaillierte Komponentenbeschreibung](#detaillierte-komponentenbeschreibung)
9. [Datenformate](#datenformate)
10. [Was funktioniert](#was-funktioniert)
11. [Was nicht funktioniert oder unvollstaendig ist](#was-nicht-funktioniert-oder-unvollstaendig-ist)
12. [Externe Abhaengigkeiten](#externe-abhaengigkeiten)
13. [Fehlerbehebung](#fehlerbehebung)

---

## Uebersicht

Super Semantic Whisper transformiert rohe Chat-Verlaeufe (Text + Audio) in strukturiertes semantisches Wissen. Das System:

- Transkribiert WhatsApp-Audio (.opus, .wav, .mp3, .m4a, .ogg) mittels OpenAI Whisper
- Erkennt Sprecher durch Dateinamen-Analyse, Keyword-Matching und Kontextanalyse
- Analysiert emotionale Toene aus Audio-Features (librosa) und Text (TextBlob)
- Identifiziert semantische Muster mittels 63+ Marker-Systemen (FRAUSAR)
- Baut lernende Sprecher-Profile auf (YAML-basiert)
- Generiert "Super-Semantic-Files" (JSON) fuer LLM-Verarbeitung
- Erstellt lesbare Markdown-Zusammenfassungen

---

## Architektur und Komponenten

Das System besteht aus fuenf Hauptschichten:

```
INPUT (WhatsApp-Export, Audio, Bilder)
  |
  v
TRANSKRIPTION (auto_transcriber_v4_emotion.py)
  |  Whisper: Audio -> Text
  |  Librosa: Audio-Feature-Extraktion
  |  TextBlob: Sentiment-Analyse
  |
  v
MEMORY (build_memory_from_transcripts.py)
  |  Sprecher-Profile aufbauen/aktualisieren
  |  YAML-Serialisierung
  |
  v
SEMANTISCHE ANALYSE (super_semantic_processor.py)
  |  FRAUSAR Marker-Erkennung
  |  Beziehungs-Analyse (temporal, thematisch, emotional)
  |  Thread-Identifikation
  |  Emotionaler Verlauf
  |
  v
OUTPUT (JSON + Markdown)
  |  super_semantic_output.json
  |  super_semantic_output.summary.md
```

### Datei-Uebersicht

| Datei | Funktion | Status |
|-------|----------|--------|
| `start_super_semantic.py` | Haupteinstiegspunkt mit Menue | Funktioniert |
| `super_semantic_processor.py` | Kern-Engine fuer semantische Analyse (736 Zeilen) | Funktioniert |
| `super_semantic_gui.py` | TKinter-GUI | Funktioniert |
| `auto_transcriber_v4_emotion.py` | Audio-Transkription mit Emotionsanalyse (692 Zeilen) | Funktioniert |
| `auto_transcriber_v3.py` | Audio-Transkription mit Datumsextraktion | Veraltet (deprecated) |
| `auto_transcriber_v2.py` | Basis-Transkription | Veraltet (deprecated) |
| `build_memory_from_transcripts.py` | Sprecher-Profil-Aufbau | Funktioniert |
| `semantic_chat_weaver.py` | Semantische Knoten- und Thread-Erstellung | Funktioniert |
| `integrated_semantic_weaver.py` | Integrationsschicht fuer externe Systeme | Funktioniert |
| `speaker_diarizer.py` | Sprechertrennung (pyannote.audio) | Bedingt (HuggingFace-Token noetig) |
| `merge_transcripts.py` | Transkript-Zusammenfuehrung nach Zeitstempel | Funktioniert |
| `google_drive_sync.py` | Google Drive Integration | Optional |
| `initialize_person.py` | Neue Sprecher-Profile anlegen | Funktioniert |
| `run_local.py` | Lokaler Modus ohne Google Drive | Funktioniert |
| `setup_environment.py` | Umgebungseinrichtung | Funktioniert |
| `src/config_manager.py` | Zentrale Konfigurationsverwaltung | Funktioniert |
| `whatsapp_auto_transcriber/` | Modularer Neuansatz | Nur Skelett (nicht implementiert) |

---

## Verarbeitungs-Pipeline

### 1. Parsing und Extraktion

**WhatsApp-Export** wird via Regex geparst:
```
Format: [DD.MM.YY, HH:MM:SS] Sender: Nachricht
```

**Audio-Dateien** werden verarbeitet durch:
1. Datums-Extraktion aus Dateinamen (Regex)
2. Sprecher-Erkennung aus Ordnername (`Eingang/Zoe/` -> Sprecher = Zoe)
3. Whisper-Transkription (CLI-Wrapper)
4. Audio-Feature-Extraktion via Librosa

### 2. Emotionale Analyse

**Audio-Features** (via Librosa):
- Tempo (BPM) via Beat-Tracking
- MFCC (Mel-Frequency Cepstral Coefficients) - Klangfarbe
- Spectral Centroid - Helligkeit
- Zero Crossing Rate - Rauschen
- RMS Energy - Lautstaerke
- Tempogramm - Rhythmusstabilitaet

**Emotionsklassifikation** (heuristisch):

| Emotion | Bedingungen |
|---------|------------|
| `begeistert_enthusiastisch` | Hohe Energie + hohes Tempo + niedrige Frequenzen |
| `wuetend_rebellisch` | Hohe Energie + hohes Tempo + hohe Frequenzen |
| `traurig_reflektierend` | Niedrige Energie + langsames Tempo |
| `sehnsuchtsvoll_still` | Niedrige Energie + normales Tempo |
| `neugierig_forschend` | Mittlere Werte + schnelleres Tempo |
| `hoffnungsvoll_antreibend` | Mittlere Werte + langsameres Tempo |
| `mystisch_symbolisch` | Marker-basiert aus Text |

**Text-Sentiment** (via TextBlob):
- Polarity: -1.0 (negativ) bis +1.0 (positiv)
- Zusaetzlich Marker-Wort-Matching gegen Emotionskategorien

### 3. Beziehungsanalyse

Der `SuperSemanticProcessor` erstellt drei Typen von Beziehungen:

- **Temporal:** Nachrichten innerhalb 5 Minuten -> `Staerke = 1.0 - (Zeitdifferenz / 300)`
- **Thematisch:** Gemeinsame Marker in den letzten 10 Nachrichten -> `Staerke = gemeinsame / gesamt`
- **Emotional:** Valenz-Shift > 0.5 -> `Staerke = abs(Valenz-Delta)`

### 4. Thread-Identifikation

Nachrichten werden nach Markern gruppiert. Nur Threads mit mindestens 3 Nachrichten werden behalten.

### 5. Emotionaler Verlauf

- Sammlung aller Valenz-Werte mit Zeitstempeln
- Identifikation von Peaks (lokale Maxima), Valleys (lokale Minima)
- Wendepunkte (Veraenderung > 0.5)
- Gesamttrend: `rising_positive`, `falling_negative`, `stable`

### 6. Output-Generierung

- **JSON:** Komplettes semantisches Datenmodell mit Nachrichten, Beziehungen, Threads, emotionalem Verlauf
- **Markdown:** Lesbare Zusammenfassung mit Statistiken

---

## Voraussetzungen und Installation

### Systemanforderungen

- **Python 3.8+**
- **FFmpeg** (fuer Audio-Konvertierung)
- **Mindestens 4GB RAM** (fuer Whisper-Modelle)

### FFmpeg Installation

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download von https://ffmpeg.org/ und zum PATH hinzufuegen
```

### Python-Abhaengigkeiten installieren

```bash
# Basis
pip3 install -r requirements.txt

# Mit emotionaler Analyse (empfohlen)
pip3 install -r requirements_emotion.txt
```

### Abhaengigkeiten

**Kern:**
- `openai-whisper` - Audio-Transkription
- `PyYAML` - YAML-Verarbeitung
- `numpy` - Numerische Berechnungen
- `torch` - PyTorch (fuer Whisper)

**Emotionale Analyse:**
- `librosa` - Audio-Feature-Extraktion
- `textblob` - Text-Sentiment
- `scikit-learn` - ML-Algorithmen
- `soundfile`, `audioread` - Audio-I/O

**Optional:**
- `scipy`, `matplotlib`, `seaborn` - Visualisierung
- `nltk`, `spacy` - Erweiterte NLP
- `pillow`, `pytesseract` - Bildverarbeitung/OCR
- `pyannote.audio` - Sprecherdiarisierung (HuggingFace-Token noetig)

---

## Konfiguration

Die Konfiguration erfolgt ueber den `ConfigManager` (`src/config_manager.py`) mit folgender Prioritaet:

1. **Command-Line-Argumente** (hoechste Prioritaet)
2. **Umgebungsvariablen**
3. **config.yaml** (User-spezifisch)
4. **config/default_config.yaml** (System-Default)
5. **Hardcoded Fallback** (niedrigste Prioritaet)

### Schnellstart: Config-Datei

```bash
cp config/default_config.yaml config.yaml
# Dann config.yaml anpassen
```

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `WHISPER_BASE_PATH` | Basis-Verzeichnis | `./whisper_speaker_matcher` |
| `WHISPER_EINGANG` | Input-Verzeichnis | `{base}/Eingang` |
| `WHISPER_MEMORY` | Sprecher-Profile | `{base}/Memory` |
| `WHISPER_OUTPUT` | Transkripte-Output | `{base}/Transkripte_LLM` |
| `WHISPER_MODEL` | Whisper-Modell | `base` |
| `WHISPER_LANGUAGE` | Sprache | `de` |
| `LOG_LEVEL` | Logging-Level | `INFO` |
| `LOG_FILE` | Log-Datei | `transcription.log` |

### config/default_config.yaml

```yaml
paths:
  base_path: null      # null = Auto-Detection
  eingang: null
  memory: null
  output: null
  google_drive:
    enabled: false
    base_path: null
    timeout_seconds: 5
  local_fallback:
    enabled: true
    base_path: "./whisper_speaker_matcher"

audio:
  whisper_model: "base"   # tiny, base, small, medium, large
  language: "de"
  supported_formats: [.opus, .wav, .mp3, .m4a, .ogg]

emotional_analysis:
  enabled: true
  use_librosa: true
  use_textblob: true

logging:
  level: INFO
  file: "transcription.log"
```

---

## Nutzung

### Option 1: Interaktives Menue (empfohlen)

```bash
python3 start_super_semantic.py
```

Menue:
1. GUI-Modus (TKinter-Oberflaeche)
2. Kommandozeilen-Modus
3. Demo mit Beispieldaten
4. Hilfe
5. Beenden

### Option 2: Direkte GUI

```bash
python3 super_semantic_gui.py
```

Die GUI bietet:
- Dateiauswahl fuer WhatsApp-Exports und Transkript-Verzeichnisse
- Marker-Set-Auswahl (All_Markers, Meta_Message, Relationship_Patterns, etc.)
- Optionen fuer Marker, Emotion, CoSD/MARSAP
- Echtzeit-Verarbeitungsstatus

### Option 3: Programmatisch

```python
from super_semantic_processor import process_everything

result = process_everything(
    whatsapp_export=Path("chat_export.txt"),
    transcript_dir=Path("Transkripte_LLM"),
    output_path=Path("output.json")
)
```

### Option 4: Nur Audio-Transkription

```bash
# Mit ConfigManager (empfohlen)
python3 auto_transcriber_v4_emotion.py

# Mit explizitem Pfad
python3 auto_transcriber_v4_emotion.py --base-path /pfad/zu/daten

# Lokal (deprecated)
python3 auto_transcriber_v4_emotion.py --local
```

### Option 5: Memory aufbauen

```bash
python3 build_memory_from_transcripts.py
```

### Option 6: Transkripte zusammenfuehren

```bash
python3 merge_transcripts.py
```

---

## Verzeichnisstruktur

```
Super_semantic_whisper/
|
|-- Eingang/                       # Input: Audio-Dateien pro Sprecher
|   |-- Zoe/                      # Ordnername = Sprechername
|   |-- Ben/
|   +-- Schroeti/
|
|-- Memory/                        # Sprecher-Profile (YAML)
|   |-- zoe.yaml
|   |-- ben.yaml
|   +-- schroeti.yaml
|
|-- Transkripte_LLM/               # Output: Generierte Transkripte
|   +-- YYYY-MM-DD_HH-MM-SS_Sprecher_..._emotion_transkript.md
|
|-- config/                        # Konfigurationsdateien
|   +-- default_config.yaml
|
|-- src/                           # Kernmodule
|   +-- config_manager.py
|
|-- whatsapp_auto_transcriber/     # Modularer Neuansatz (Skelett)
|   |-- main.py
|   +-- src/
|       |-- config_manager.py
|       |-- file_watcher.py        # STUB
|       |-- audio_processor.py     # STUB
|       +-- speaker_detector.py    # STUB
|
|-- wordthread-ui/                 # React/Electron UI (Prototyp)
|   +-- src/components/
|
|-- whisper_speaker_matcher/       # Lokale Fallback-Struktur
|   |-- Eingang/
|   +-- Memory/
|
+-- docs/                          # Zusaetzliche Dokumentation
```

---

## Detaillierte Komponentenbeschreibung

### auto_transcriber_v4_emotion.py (Aktive Version)

**Zweck:** Audio-Transkription mit emotionaler Analyse

**Klassen:**

`EmotionalAnalyzer`
- `analyze_audio_features(audio_path)` - Extrahiert Tempo, MFCC, Spectral Centroid, ZCR, RMS Energy via Librosa
- `analyze_text_emotion(text)` - TextBlob-Sentiment + Marker-Wort-Matching
- `classify_emotion_from_audio(features)` - Heuristik-basierte Klassifikation in 7 Kategorien

`WhisperSpeakerMatcherV4`
- `__init__(base_path, config_path, use_faster_whisper)` - Initialisierung mit ConfigManager
- `extract_whatsapp_datetime(filename)` - Regex-basierte Datumsextraktion aus Dateinamen
- `get_chatpartner_from_path(audio_path)` - Ordner-basierte Sprechererkennung
- `transcribe_audio_standard(audio_path)` - Whisper-CLI-Wrapper
- `identify_speaker_in_conversation(text)` - Regelbasierte Sprecheridentifikation
- `format_for_llm_with_emotion(text, speaker, emotion_data)` - Markdown-Generierung
- `process_audio_files()` - Hauptpipeline

**Verarbeitungsablauf:**
```
Audio-Datei -> Datumsextraktion -> Sprechererkennung -> Whisper-Transkription
  -> Audio-Feature-Extraktion (Librosa) -> Text-Sentiment (TextBlob)
  -> Emotionsklassifikation -> Markdown-Generierung -> Datei speichern
```

### super_semantic_processor.py (Kern-Engine)

**Zweck:** Vollstaendige semantische Analyse von Chat-Verlaeufen

**Datenklassen:**

```python
SemanticMessage:
  id, timestamp, sender, content, type,
  emotion (Dict), markers (List), semantic_scores (Dict), metadata (Dict)

SemanticRelationship:
  from_id, to_id, type, strength, reason

EmotionalArc:
  timeline, peaks, valleys, turning_points, overall_trend
```

**SuperSemanticProcessor-Methoden:**
- `_initialize_components()` - Laedt externe Systeme (FRAUSAR, MARSAP, Semantic Grabbers)
- `process_whatsapp_export(file_path)` - Parst WhatsApp-Text-Export
- `process_audio_transcripts(directory)` - Parst Emotions-Transkripte
- `process_image_files(directory)` - OCR + Helligkeitsanalyse
- `process_export_folder(folder)` - Bulk-Verarbeitung eines Ordners
- `analyze_relationships()` - Erstellt temporale/thematische/emotionale Verbindungen
- `identify_semantic_threads()` - Gruppiert Nachrichten nach Markern (min. 3)
- `calculate_emotional_arc()` - Berechnet Peaks, Valleys, Wendepunkte, Trend
- `generate_super_semantic_file(output_path)` - Generiert JSON + Markdown

### build_memory_from_transcripts.py (Memory-System)

**Zweck:** Baut lernende Sprecher-Profile aus Transkripten auf

**MemoryBuilder:**
- `extract_speaker_from_filename(filename)` - Pattern-Matching fuer Sprechername
- `analyze_text_patterns(text)` - Wortfrequenz, Fuellwoerter, Satzlaenge
- `extract_topics(text)` - Topic-Klassifikation via Keywords
- `build_speaker_profile(speaker)` - Erstellt YAML-Profil
- `update_speaker_profile(speaker, new_data)` - Inkrementelles Update

**Profil-Struktur:**
```yaml
name: Zoe
created_at: 2025-01-12T15:30:00
last_updated: 2025-02-16T10:35
total_interactions: 42
statistics:
  avg_sentence_length: 12.5
  most_common_words: {wow: 15, krass: 12}
  sentiment: {positive: 25, negative: 3, ratio: 0.89}
topics: {creativity: 15, art: 12}
voice_characteristics: [hell, energisch, expressiv]
characteristics: [expressiv, kreativ, emotional]
recent_interactions: [...]  # Letzte 50
```

### semantic_chat_weaver.py

**Zweck:** Erstellt semantische Knoten und Thread-Strukturen

- `SemanticNode` - Einzelnachricht mit Metadaten, Verbindungen
- `SemanticThread` - Thematischer Thread mit emotionalem Verlauf
- `SemanticChatWeaver` - Orchestriert Knoten-Erstellung, Thread-Erkennung, Spannungsanalyse

### src/config_manager.py

**Zweck:** Zentrale Konfigurationsverwaltung mit Multi-Source-Unterstuetzung

- Laedt aus YAML-Dateien, Umgebungsvariablen, Hardcoded-Defaults
- Pfad-Aufloesungskette: Explizit -> Config -> Google Drive -> Lokal -> CWD
- Validierung und Sicherheitspruefungen
- Debug-Ausgabe der effektiven Konfiguration

### speaker_diarizer.py

**Zweck:** Sprechertrennung mittels pyannote.audio

- `SpeakerDiarizer.diarize(audio_path)` - Trennt Sprecher aus Audio
- `assign_roles()` - Klassifiziert Rollen (z.B. "Therapeut", "Klient")
- Benoetigt HuggingFace-Token und pyannote.audio-Modelle

---

## Datenformate

### Input: WhatsApp-Export (.txt)
```
[28.06.24, 14:23:15] Max: Hey! Wie geht's?
[28.06.24, 14:24:03] Anna: Super, danke!
```

### Input: Audio-Dateien
```
Eingang/Zoe/WhatsApp Audio 2025-06-29 at 13.20.58.opus
```

### Output: Emotions-Transkript (.md)
```markdown
# WhatsApp Audio Transkription mit emotionaler Analyse

**Chat mit:** Zoe
**Aufnahme am:** 29.06.2025 um 13:20:58
**Verarbeitet am:** 16.02.2026 um 10:15:23

## Emotionale Analyse:
**Dominante Emotion:** Hoffnungsvoll & Antreibend
**Emotionale Valenz:** 0.35 (Positivitaet: -1 bis +1)
**Emotionale Intensitaet:** 0.42

## Transkription:
**[Zoe - 13:20:58] +:** Hey ich wollte dir nur sagen...
```

### Output: Super-Semantic-File (.json)
```json
{
  "metadata": {
    "created_at": "2026-02-16T10:35:00",
    "version": "1.0",
    "time_span": {"start": "...", "end": "..."}
  },
  "messages": {"msg_id": {"id": "...", "timestamp": "...", "sender": "...", ...}},
  "relationships": [{"from_id": "...", "to_id": "...", "type": "temporal", ...}],
  "semantic_threads": {"MARKER_NAME": ["msg_001", "msg_045", ...]},
  "emotional_arc": {"timeline": [...], "peaks": [...], "valleys": [...], "overall_trend": "..."},
  "analysis_summary": {"total_messages": 0, "marker_frequencies": {}, ...}
}
```

### Sprecher-Profil (.yaml)
Siehe Memory-System-Abschnitt oben.

---

## Was funktioniert

### Voll funktionsfaehig

1. **Audio-Transkription** (`auto_transcriber_v4_emotion.py`)
   - Whisper-Integration transkribiert zuverlaessig
   - Emotionale Analyse (Audio-Features + Text-Sentiment) liefert plausible Ergebnisse
   - Sprechererkennung ueber Ordnernamen funktioniert zuverlaessig
   - Datumsextraktion aus Dateinamen funktioniert
   - Output-Formatierung als Markdown ist sauber

2. **Memory-System** (`build_memory_from_transcripts.py`)
   - Profile werden korrekt erstellt und inkrementell aktualisiert
   - YAML-Serialisierung funktioniert
   - Themen-Erkennung und Sentiment-Ratio werden berechnet

3. **Semantische Verarbeitung** (`super_semantic_processor.py`)
   - WhatsApp-Export-Parsing funktioniert
   - Beziehungsanalyse (temporal, thematisch, emotional) funktioniert
   - Thread-Identifikation funktioniert
   - Emotionaler Verlauf mit Peaks/Valleys wird korrekt berechnet
   - JSON + Markdown Output wird generiert

4. **GUI** (`super_semantic_gui.py`)
   - Dateiauswahl, Optionen, Verarbeitung funktionieren
   - Threading fuer nicht-blockierende Operationen

5. **Konfigurationsmanagement** (`src/config_manager.py`)
   - Multi-Source-Laden, Pfad-Auflosung, Env-Override funktionieren korrekt

6. **Transkript-Zusammenfuehrung** (`merge_transcripts.py`)
   - Chronologische Sortierung und Sprecher-Inferenz funktionieren

7. **Einstiegspunkt** (`start_super_semantic.py`)
   - Dependency-Check, Menue, Modi funktionieren

### Bedingt funktionsfaehig

1. **Sprecherdiarisierung** (`speaker_diarizer.py`)
   - Funktioniert nur mit installiertem pyannote.audio und HuggingFace-Token
   - Ohne Token: Warning im Log, Weiterlauf ohne Diarisierung

2. **Google Drive Sync** (`google_drive_sync.py`)
   - Funktioniert mit konfiguriertem Google Drive
   - Fallback auf lokales Dateisystem bei Nicht-Verfuegbarkeit

3. **Bildverarbeitung** (in `super_semantic_processor.py`)
   - Funktioniert nur mit installiertem Tesseract OCR
   - Ohne Tesseract: Bilder werden uebersprungen

4. **Externe Marker-Systeme** (FRAUSAR, CoSD/MARSAP)
   - Erfordern Geschwisterprojekte in `../Marker_assist_bot/`, `../MARSAP/`, etc.
   - Graceful Degradation: System laeuft ohne sie, aber Marker-Erkennung ist stark eingeschraenkt
   - `try/except` um alle externen Imports

---

## Was nicht funktioniert oder unvollstaendig ist

### Kritische Probleme

#### 1. Hardcodierte Benutzerpfade (P0 - KRITISCH)

**Betrifft:** `auto_transcriber_v2.py`, `auto_transcriber_v3.py`, `auto_transcriber_v4_emotion.py`, `build_memory_from_transcripts.py`

In den Transcriber-Dateien existiert weiterhin ein Referenz-Pfad auf einen spezifischen Google-Drive-Pfad eines einzelnen Benutzers. Obwohl der `ConfigManager` bereits implementiert ist und `auto_transcriber_v4_emotion.py` ihn inzwischen nutzt, verwenden die aelteren Versionen (V2, V3) und teilweise `build_memory_from_transcripts.py` noch hartcodierte Pfade.

**Auswirkung:** Code schlaegt auf anderen Rechnern fehl. CI/CD, Docker, Kollaboration sind blockiert fuer Komponenten, die den ConfigManager noch nicht nutzen.

#### 2. Fehlende externe Systeme (P1)

`super_semantic_processor.py` erwartet Geschwisterprojekte:
```python
sys.path.insert(0, "../Marker_assist_bot")   # FRAUSAR
sys.path.insert(0, "../MARSAP")              # CoSD
sys.path.insert(0, "../MARSAPv2")
sys.path.insert(0, "../ALL_SEMANTIC_MARKER_TXT")
```
Diese existieren nicht im Repository. Ohne sie fehlen wesentliche Features (63+ semantische Marker, Drift-Analyse). Das System laeuft zwar (try/except), aber die Kern-Analysefunktionalitaet ist stark eingeschraenkt.

### Nicht implementiert

#### 3. whatsapp_auto_transcriber-Modul (P2)

Der gesamte modulare Neuansatz unter `whatsapp_auto_transcriber/` ist nur ein Skelett:
- `FileWatcher.start()` ist `pass`
- `AudioProcessor` hat keine Implementierung
- `SpeakerDetector` hat keine Implementierung
- `Monitoring` ist minimal

Nur die Config-Klasse und die Verzeichnisstruktur existieren. Keine funktionsfaehige Logik.

#### 4. WordThread UI (P2)

Der React/Electron-Prototyp unter `wordthread-ui/` hat:
- Schoene UI-Komponenten (MarkerLibrary, AudioTranscriber, TextAnalyzer, Timeline)
- Aber: Alle API-Calls sind Stubs mit Mock-Daten
- Keine REST-API definiert
- Keine Verbindung zum Python-Backend

#### 5. Leere Dateien

Folgende Dateien existieren, sind aber leer (0 Bytes):
- `auto_transcriber.py`
- `whisper_transcriber.py`
- `whisper_auto_runner.py`

### Schwaechen

#### 6. Keine Tests

Ausser `test_initialize_person.py` existieren keine automatisierten Tests. Kein pytest, kein CI/CD.

#### 7. Keine Containerisierung

Kein Dockerfile, kein docker-compose.yml. Installation ist manuell und fehleranfaellig.

#### 8. Keine Datenbank

Alles basiert auf Dateisystem (YAML, JSON, Markdown). Fuer kleine Datenmengen ausreichend, aber nicht skalierbar. Keine Queries moeglich ausser File-Scan.

#### 9. Emotionsklassifikation ist rein heuristisch

Die Emotionserkennung aus Audio basiert auf einfachen Schwellwert-Regeln (Tempo > 130 + Energie > 0.1 = "wuetend/begeistert"). Kein trainiertes ML-Modell. Ergebnisse sind plausibel, aber nicht validiert.

#### 10. Plattformabhaengigkeit

Dokumentation und Installation gehen primaer von macOS aus. Linux-Kompatibilitaet ist gegeben, Windows-Unterstuetzung ist nicht getestet.

---

## Externe Abhaengigkeiten

| Dienst/Tool | Zweck | Erforderlich | Fallback |
|-------------|-------|--------------|----------|
| OpenAI Whisper | Audio-Transkription | Ja | Keiner (Kernfeature) |
| FFmpeg | Audio-Format-Konvertierung | Ja | Systemabhaengigkeit |
| Google Drive API | Cloud-Speicher | Nein | Lokales Dateisystem |
| HuggingFace Models | Sprecherdiarisierung | Nein | Ohne Diarisierung |
| Tesseract OCR | Bild-Textextraktion | Nein | Bilder uebersprungen |
| Librosa | Audio-Feature-Extraktion | Ja (fuer Emotion) | Reduzierte Features |
| TextBlob | Text-Sentiment | Ja (fuer Emotion) | Einfaches Keyword-Matching |
| FRAUSAR (extern) | 63+ semantische Marker | Nein | Stark reduzierte Analyse |
| MARSAP/CoSD (extern) | Semantische Drift-Analyse | Nein | Feature fehlt |

---

## Fehlerbehebung

### "Module not found"
```bash
pip install -r requirements_emotion.txt
```

### "FileNotFoundError" bei Start
Config-Datei anlegen oder Umgebungsvariable setzen:
```bash
export WHISPER_BASE_PATH=/pfad/zu/daten
```
Oder:
```bash
cp config/default_config.yaml config.yaml
# config.yaml anpassen
```

### FFmpeg nicht gefunden
```bash
# Installation pruefen
ffmpeg -version

# macOS: Homebrew-Pfad pruefen
export PATH="/opt/homebrew/bin:$PATH"
```

### "No markers found"
Externe Marker-Systeme sind nicht vorhanden. Das ist kein Fehler, sondern eine Einschraenkung. Das System funktioniert mit reduzierter Marker-Erkennung weiter.

### Whisper-Probleme
```bash
pip3 uninstall openai-whisper
pip3 install openai-whisper
```

### Logging
Log-Dateien befinden sich im Projektverzeichnis:
- `transcription.log`
- `transcription_v4_emotion.log` (detailliert)
