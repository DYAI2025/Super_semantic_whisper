# Super Semantic Whisper - Dokumentation & Therapeutischer Ausbauplan

## Inhaltsverzeichnis
1. [Aktuelle Systemübersicht](#1-aktuelle-systemübersicht)
2. [Technische Architektur](#2-technische-architektur)
3. [Kernkomponenten](#3-kernkomponenten)
4. [Datenfluss](#4-datenfluss)
5. [Ausbau zum Therapeutischen Transcriber](#5-ausbau-zum-therapeutischen-transcriber)
6. [Qualitäts- und Präzisionsanforderungen](#6-qualitäts--und-präzisionsanforderungen)
7. [Implementierungsroadmap](#7-implementierungsroadmap)

---

## 1. Aktuelle Systemübersicht

### 1.1 Zweck
Das **Super Semantic Whisper**-System ist ein fortschrittliches Audio-Transkriptionssystem mit semantischer Analyse. Es kombiniert:
- OpenAI Whisper für Spracherkennung
- Emotionale Sprachanalyse (Audio + Text)
- Sprecher-Profil-Management
- Semantische Marker-Erkennung
- Beziehungsanalyse zwischen Nachrichten

### 1.2 Aktuelle Fähigkeiten

| Funktion | Status | Beschreibung |
|----------|--------|--------------|
| Audio-Transkription | ✅ Aktiv | Whisper-basiert, mehrere Modellgrößen |
| Emotionserkennung | ✅ Aktiv | Audio-Features + TextBlob Sentiment |
| Sprecher-Profile | ✅ Aktiv | YAML-basierte Memory-Dateien |
| Semantische Marker | ✅ Aktiv | 63+ Marker aus FRAUSAR-System |
| Zeitstempel-Extraktion | ✅ Aktiv | WhatsApp-Dateinamen-Parsing |
| GUI-Interface | ✅ Aktiv | tkinter-basiert |
| Google Drive Sync | ✅ Aktiv | Mit Fallback auf lokal |

### 1.3 Unterstützte Formate
- **Audio**: .opus, .wav, .mp3, .m4a, .ogg
- **Text**: WhatsApp-Export (.txt), Markdown-Transkripte
- **Bilder**: .png, .jpg, .jpeg, .gif (mit OCR)

---

## 2. Technische Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    EINGABE-SCHICHT                               │
├─────────────────────────────────────────────────────────────────┤
│  Eingang/           │  WhatsApp Export    │  Bilder              │
│  [Speaker]/         │  (.txt)             │  (.png, .jpg)        │
│  Audio-Dateien      │                     │                      │
└─────────┬───────────┴─────────┬───────────┴──────────┬──────────┘
          │                     │                      │
          ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 VERARBEITUNGS-SCHICHT                            │
├─────────────────────────────────────────────────────────────────┤
│  auto_transcriber_v4_emotion.py                                  │
│  ├── Whisper Transkription                                       │
│  ├── librosa Audio-Feature-Extraktion                           │
│  ├── TextBlob Sentiment-Analyse                                  │
│  └── Emotionale Marker-Erkennung                                │
├─────────────────────────────────────────────────────────────────┤
│  super_semantic_processor.py                                     │
│  ├── SemanticMessage Erstellung                                  │
│  ├── FRAUSAR Marker-Matching                                    │
│  ├── Beziehungsanalyse (temporal, thematisch, emotional)        │
│  └── Emotionaler Arc Berechnung                                 │
├─────────────────────────────────────────────────────────────────┤
│  build_memory_from_transcripts.py                               │
│  ├── Sprecher-Profil-Erstellung                                 │
│  ├── Sprachmuster-Analyse                                       │
│  └── Themen-Extraktion                                          │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUSGABE-SCHICHT                               │
├─────────────────────────────────────────────────────────────────┤
│  Transkripte_LLM/          │  Memory/           │  Output/       │
│  *_emotion_transkript.md   │  [speaker].yaml    │  .json/.md     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Kernkomponenten

### 3.1 EmotionalAnalyzer (auto_transcriber_v4_emotion.py)

**Funktionen:**
- `analyze_audio_features()`: Extrahiert Tempo, Spektral-Centroid, MFCC, Energy, ZCR
- `analyze_text_emotion()`: Keyword-basierte Emotionserkennung + TextBlob
- `classify_emotion_from_audio()`: Heuristische Klassifikation aus Audio-Features

**Emotionskategorien:**
- hoffnungsvoll_antreibend
- neugierig_forschend
- sehnsuchtsvoll_still
- traurig_reflektierend
- wuetend_rebellisch
- mystisch_symbolisch
- begeistert_enthusiastisch

### 3.2 SuperSemanticProcessor (super_semantic_processor.py)

**Datenklassen:**
```python
@dataclass
class SemanticMessage:
    id: str
    timestamp: datetime
    sender: str
    content: str
    type: str  # text, audio, image
    emotion: Dict[str, float]
    markers: List[str]
    semantic_scores: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class SemanticRelationship:
    from_id: str
    to_id: str
    type: str  # temporal, thematic, emotional, reference
    strength: float
    reason: str

@dataclass
class EmotionalArc:
    timeline: List[Tuple[datetime, float]]
    peaks: List[Dict]
    valleys: List[Dict]
    turning_points: List[Dict]
    overall_trend: str
```

### 3.3 MemoryBuilder (build_memory_from_transcripts.py)

**Profil-Struktur:**
```yaml
name: Speaker Name
last_updated: ISO-Timestamp
total_interactions: int
statistics:
  avg_sentence_length: float
  most_common_words: Dict
  filler_words: Dict
  sentiment:
    positive: int
    negative: int
    ratio: float
topics: Dict[str, int]
characteristics: List[str]
interactions: List[Dict]  # Letzte 50
```

---

## 4. Datenfluss

### 4.1 Audio-Verarbeitung
```
Audio-Datei (.opus)
    │
    ├─► Dateiname-Parsing → Datum/Zeit + Sprecher
    │
    ├─► Whisper Transkription → Text
    │
    ├─► librosa Analyse → Audio-Features
    │       ├── Tempo (BPM)
    │       ├── Spektral-Centroid
    │       ├── MFCC (13 Koeffizienten)
    │       ├── Energy/RMS
    │       └── Zero Crossing Rate
    │
    ├─► TextBlob → Sentiment (Valenz, Subjektivität)
    │
    └─► Emotionale Marker → Dominante Emotion
            │
            ▼
    Markdown-Transkript mit Metadaten
```

### 4.2 Semantische Verarbeitung
```
Transkripte + WhatsApp-Export
    │
    ├─► Parsing → Strukturierte Nachrichten
    │
    ├─► Marker-Erkennung (FRAUSAR + Custom)
    │
    ├─► Semantic Grabber Matching
    │
    ├─► Beziehungsanalyse
    │       ├── Temporal (< 5 Min = direkte Antwort)
    │       ├── Thematisch (gemeinsame Marker)
    │       └── Emotional (Valenz-Änderungen > 0.5)
    │
    └─► Emotionaler Arc
            ├── Peaks (lokale Maxima)
            ├── Valleys (lokale Minima)
            └── Turning Points (große Änderungen)
```

---

## 5. Ausbau zum Therapeutischen Transcriber

### 5.1 Anforderungen für therapeutische Anwendungen

| Anforderung | Priorität | Beschreibung |
|-------------|-----------|--------------|
| **Höchste Transkriptionsgenauigkeit** | KRITISCH | WER < 5% für therapeutische Nutzung |
| **Sprecherdiariisierung** | HOCH | Exakte Trennung Therapeut/Klient |
| **Emotionale Präzision** | HOCH | Validierte Emotionsmodelle |
| **Datenschutz/DSGVO** | KRITISCH | Lokale Verarbeitung, Verschlüsselung |
| **Klinische Marker** | HOCH | DSM-5/ICD-11 relevante Indikatoren |
| **Zeitstempel-Präzision** | MITTEL | Sekundengenau für Sitzungsanalyse |
| **Export für Dokumentation** | MITTEL | Standardformate für Praxissoftware |

### 5.2 Empfohlene Erweiterungen

#### 5.2.1 Transkriptionsqualität verbessern

```python
# Empfohlene Whisper-Konfiguration für Therapie
THERAPY_WHISPER_CONFIG = {
    "model": "large-v3",           # Höchste Genauigkeit
    "language": "de",
    "task": "transcribe",
    "beam_size": 5,                # Mehr Suchpfade
    "best_of": 5,
    "temperature": 0.0,            # Deterministisch
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": True,
    "word_timestamps": True,       # Wort-genaue Zeitstempel
    "vad_filter": True,            # Voice Activity Detection
}
```

#### 5.2.2 Sprecherdiarisierung

**Empfohlene Lösung: pyannote.audio**
```python
# Neue Komponente: speaker_diarization.py
from pyannote.audio import Pipeline

class TherapyDiarizer:
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1"
        )

    def diarize(self, audio_path):
        """Identifiziere Sprecher-Segmente"""
        diarization = self.pipeline(audio_path)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,  # SPEAKER_00, SPEAKER_01
            })
        return segments

    def assign_roles(self, segments, first_speaker_role="therapeut"):
        """Weise Rollen zu (Therapeut spricht meist zuerst)"""
        # Logik zur Rollenzuweisung
        pass
```

#### 5.2.3 Klinische Emotionsmodelle

**Erweiterung des EmotionalAnalyzer:**

```python
CLINICAL_EMOTION_MARKERS = {
    # Affektive Zustände (DSM-5 relevant)
    "depressive_indicators": [
        "hoffnungslos", "sinnlos", "müde", "erschöpft",
        "kann nicht mehr", "wertlos", "schuldig", "leer",
        "interessiert mich nicht", "egal"
    ],
    "anxiety_indicators": [
        "angst", "panik", "sorge", "nervös", "unruhig",
        "herzrasen", "zittern", "atemnot", "gedankenkreisen",
        "was wenn", "schlimmes passiert"
    ],
    "trauma_indicators": [
        "flashback", "alptraum", "erstarrt", "betäubt",
        "ausgelöst", "trigger", "vermeiden", "nicht dran denken",
        "wie damals", "passiert wieder"
    ],
    "dissociative_indicators": [
        "unwirklich", "neben mir", "beobachte mich",
        "abgetrennt", "fremd", "nicht ich", "wie im film",
        "zeit verloren", "lücke"
    ],
    "suicidal_risk": [  # KRITISCH - Sofortige Markierung
        "nicht mehr leben", "aufhören", "beenden",
        "allen besser ohne mich", "keinen sinn",
        "plan", "methode", "abschied"
    ],

    # Positive/Ressourcen-Marker
    "resilience_indicators": [
        "geschafft", "überstanden", "stärker", "gelernt",
        "hoffnung", "unterstützung", "nicht allein",
        "bewältigt", "stolz"
    ],
    "therapeutic_alliance": [
        "verstanden", "vertrauen", "sicher hier",
        "hilft mir", "gut dass", "froh dass"
    ]
}
```

#### 5.2.4 Sitzungsstruktur-Analyse

```python
@dataclass
class TherapySession:
    session_id: str
    date: datetime
    duration_minutes: float

    # Sprecher-Statistik
    therapist_speaking_time: float  # Prozent
    client_speaking_time: float
    silence_time: float

    # Interaktionsmuster
    turn_count: int
    avg_turn_duration: float
    interruptions: int

    # Emotionaler Verlauf
    emotional_arc: EmotionalArc
    clinical_markers_detected: Dict[str, List[str]]

    # Phasen-Erkennung
    phases: List[Dict]  # Eröffnung, Exploration, Intervention, Abschluss

    # Risiko-Assessment
    risk_flags: List[str]
    requires_review: bool
```

#### 5.2.5 Datenschutz-Schicht

```python
class PrivacyManager:
    """DSGVO-konforme Verarbeitung"""

    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def anonymize_transcript(self, text: str) -> str:
        """Entferne/ersetze identifizierende Informationen"""
        # Namen → [NAME_1], [NAME_2]
        # Orte → [ORT]
        # Daten → [DATUM]
        # Telefonnummern → [TELEFON]
        pass

    def encrypt_storage(self, data: bytes) -> bytes:
        """Verschlüssele vor Speicherung"""
        return self.cipher.encrypt(data)

    def secure_delete(self, file_path: Path):
        """Sicheres Löschen (Überschreiben)"""
        pass

    def audit_log(self, action: str, user: str):
        """Protokolliere Zugriffe"""
        pass
```

### 5.3 Therapeutische Ausgabeformate

#### 5.3.1 Sitzungsprotokoll (Markdown)

```markdown
# Therapiesitzung [ID]

**Datum:** DD.MM.YYYY
**Dauer:** XX Minuten
**Sitzungsnummer:** X

## Zusammenfassung
[Automatisch generierte Kurzzusammenfassung]

## Emotionaler Verlauf
[Grafik/ASCII-Art des emotionalen Arcs]

## Klinische Beobachtungen
- **Depressive Marker:** [Liste mit Zeitstempeln]
- **Angst-Marker:** [Liste]
- **Ressourcen:** [Liste]

## Transkript
[Vollständiges, anonymisiertes Transkript mit Sprecherkennzeichnung]

## Notizen für Folgesitzung
[Platzhalter für manuelle Ergänzungen]
```

#### 5.3.2 Strukturierter Export (JSON/XML)

```json
{
  "session_metadata": {
    "id": "UUID",
    "date": "ISO-8601",
    "therapist_id": "anonymized",
    "client_id": "anonymized"
  },
  "transcript": [
    {
      "speaker": "therapist",
      "start_time": 0.0,
      "end_time": 5.2,
      "text": "...",
      "confidence": 0.95
    }
  ],
  "analysis": {
    "clinical_markers": {},
    "emotional_trajectory": [],
    "risk_assessment": {}
  }
}
```

---

## 6. Qualitäts- und Präzisionsanforderungen

### 6.1 Transkriptionsgenauigkeit

| Metrik | Aktuell (geschätzt) | Ziel Therapie |
|--------|---------------------|---------------|
| Word Error Rate (WER) | ~10-15% | < 5% |
| Sprecher-Accuracy | Nicht implementiert | > 95% |
| Zeitstempel-Genauigkeit | ~1s | < 0.5s |

**Maßnahmen zur Verbesserung:**
1. Whisper large-v3 statt base
2. Domänenspezifisches Fine-Tuning (optional)
3. Post-Processing mit Sprachmodell
4. Manuelle Korrektur-Interface

### 6.2 Emotionserkennung

| Aspekt | Aktuell | Ziel |
|--------|---------|------|
| Modell | Keyword-basiert + TextBlob | Validierte klinische Modelle |
| Kategorien | 7 allgemeine | DSM-5/ICD-11 aligned |
| Audio-Analyse | Basic Features | Prosodische Analyse |
| Validierung | Keine | Klinische Studie |

**Empfohlene Modelle:**
- **Text:** German BERT fine-tuned auf therapeutische Gespräche
- **Audio:** wav2vec 2.0 für Emotionserkennung
- **Multimodal:** Fusion von Text + Audio Features

### 6.3 Datenschutz-Compliance

| Anforderung | Status | Maßnahme |
|-------------|--------|----------|
| Lokale Verarbeitung | ✅ Möglich | Whisper lokal ausführen |
| Verschlüsselung at Rest | ❌ Fehlt | AES-256 implementieren |
| Verschlüsselung in Transit | N/A (lokal) | - |
| Anonymisierung | ❌ Fehlt | NER-basierte Entfernung |
| Audit-Trail | ❌ Fehlt | Logging implementieren |
| Löschkonzept | ❌ Fehlt | Secure Delete |

---

## 7. Implementierungsroadmap

### Phase 1: Qualitätsverbesserung (2-4 Wochen)

- [ ] Upgrade auf Whisper large-v3
- [ ] Word-Timestamps aktivieren
- [ ] Konfigurierbare Modellauswahl
- [ ] Batch-Processing optimieren
- [ ] Unit-Tests für Kernfunktionen

### Phase 2: Sprecherdiarisierung (2-3 Wochen)

- [ ] pyannote.audio Integration
- [ ] Rollen-Zuweisung (Therapeut/Klient)
- [ ] Sprecher-Konsistenz über Sitzungen
- [ ] UI für manuelle Korrektur

### Phase 3: Klinische Features (4-6 Wochen)

- [ ] Klinische Marker-Bibliothek
- [ ] Risiko-Flagging System
- [ ] Sitzungsstruktur-Analyse
- [ ] Therapieverlauf-Tracking
- [ ] Validierung mit Fachpersonal

### Phase 4: Datenschutz & Compliance (2-3 Wochen)

- [ ] Verschlüsselungs-Layer
- [ ] Anonymisierungs-Pipeline
- [ ] Audit-Logging
- [ ] Secure Delete
- [ ] DSGVO-Dokumentation

### Phase 5: Integration & Deployment (2-4 Wochen)

- [ ] Export-Schnittstellen (HL7 FHIR optional)
- [ ] Praxissoftware-Integration
- [ ] Benutzerhandbuch
- [ ] Schulungsmaterial
- [ ] Pilottest mit Therapeuten

---

## Anhang

### A. Abhängigkeiten für therapeutische Erweiterung

```txt
# requirements_therapy.txt
openai-whisper>=20231117
torch>=2.0.0
pyannote.audio>=3.1.0
transformers>=4.35.0
librosa>=0.10.0
soundfile>=0.12.0
textblob>=0.17.1
spacy>=3.7.0
cryptography>=41.0.0
pydantic>=2.5.0
```

### B. Konfigurationsbeispiel

```yaml
# config/therapy_config.yaml
transcription:
  model: large-v3
  language: de
  beam_size: 5
  word_timestamps: true

diarization:
  enabled: true
  min_speakers: 2
  max_speakers: 2

analysis:
  clinical_markers: true
  risk_flagging: true
  emotional_arc: true

privacy:
  encryption: true
  anonymization: true
  audit_logging: true
  retention_days: 365

output:
  format: markdown
  include_timestamps: true
  anonymize: true
```

### C. Lizenz-Hinweis

Das aktuelle System steht unter **Creative Commons BY-NC-SA 4.0**.
Für kommerzielle therapeutische Nutzung ist eine separate Lizenzvereinbarung erforderlich.

---

*Dokumentation erstellt am: 2025-11-21*
*Version: 1.0*
*Autor: Claude Code Analysis*
