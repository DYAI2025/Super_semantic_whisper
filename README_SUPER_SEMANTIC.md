# 🌟 Super Semantic Processor

> **Verwandle deine Chats in semantische Kunstwerke!**

Der Super Semantic Processor ist ein revolutionäres Tool, das deine WhatsApp-Chats und Audio-Nachrichten in eine tiefe semantische Analyse verwandelt. Es erstellt ein "Super-Semantic-File" - eine vollständige semantische Repräsentation deiner Kommunikationsgeschichte.

## ✨ Features

### 🎯 Kern-Features
- **📱 WhatsApp-Export Analyse**: Verarbeitet komplette Chat-Verläufe
- **🎤 Audio-Integration**: Transkribiert und analysiert Sprachnachrichten mit Emotionen
- **🎭 Emotionale Analyse**: Erkennt emotionale Verläufe und Wendepunkte
- **🏷️ Marker-System**: Nutzt 63+ semantische Marker zur Mustererkennung
- **🧵 Semantische Fäden**: Identifiziert thematische Verbindungen durch die Zeit
- **🔗 Beziehungs-Mapping**: Zeigt Verbindungen zwischen Nachrichten

### 🔧 Integrierte Systeme
- **FRAUSAR**: Marker-Management und Mustererkennung
- **Whisper V4**: Audio-Transkription mit Emotionserkennung
- **CoSD/MARSAP**: Drift-Analyse und semantische Bewegungen
- **Semantic Grabber Library**: Erweiterte Pattern-Matching

## 🚀 Schnellstart

### Option 1: Einfacher Start (Empfohlen)
```bash
cd whisper_speaker_matcher
C
```

Wähle dann:
1. **GUI-Modus** für eine benutzerfreundliche Oberfläche
2. **CLI-Modus** für Kommandozeilen-Nutzung
3. **Demo** um das System zu testen

### Option 2: Direkte GUI
```bash
python3 super_semantic_gui.py
```

### Option 3: Programmatisch
```python
from super_semantic_processor import process_everything

result = process_everything(
    whatsapp_export=Path("chat_export.txt"),
    transcript_dir=Path("Transkripte_LLM"),
    output_path=Path("meine_semantik.json")
)
```

## 📋 Voraussetzungen

### Automatisch installiert:
- `pyyaml` - YAML-Verarbeitung
- `librosa` - Audio-Analyse
- `textblob` - Text-Sentiment
- `scikit-learn` - ML-Algorithmen
- `numpy`, `scipy` - Numerische Berechnungen

### Manuell benötigt:
- **Python 3.8+**
- **tkinter** (für GUI)
  - macOS: `brew install python-tk`
  - Ubuntu: `sudo apt-get install python3-tk`
  - Windows: Bereits enthalten

## 📥 Input-Formate

### WhatsApp-Export
Standard WhatsApp Chat-Export (.txt):
```
[28.06.24, 14:23:15] Max: Hey! Wie geht's?
[28.06.24, 14:24:03] Anna: Super, danke! 😊
```

### Audio-Transkripte
Whisper V4 Emotion Format (`*_emotion_transkript.md`):
```markdown
# Transkript: WhatsApp Audio 2025-06-29 at 13.20.58

**Aufnahme am:** 29.06.2025 um 13:20:58
**Chat mit:** Max
**Dominante Emotion:** Freude 😊
**Emotionale Valenz:** 0.7

## Transkription:
Hey Anna! Ich wollte dir nur sagen...
```

## 📤 Output-Format

### 1. Super-Semantic JSON
Vollständige semantische Struktur mit:
- Allen Nachrichten mit Metadaten
- Emotionalen Verläufen
- Semantischen Beziehungen
- Thematischen Fäden
- Statistiken und Analysen

### 2. Lesbare Zusammenfassung (Markdown)
- Emotionaler Verlauf mit Visualisierung
- Top-Marker und deren Häufigkeit
- Wichtigste semantische Fäden
- Beziehungs-Statistiken

## 🎯 Anwendungsfälle

### Persönliche Reflexion
- **Beziehungsanalyse**: Verstehe emotionale Dynamiken
- **Selbsterkenntnis**: Erkenne eigene Kommunikationsmuster
- **Erinnerungen**: Finde wichtige Momente wieder

### Professionelle Nutzung
- **Therapie**: Analyse von Kommunikationsmustern
- **Forschung**: Studien zu Sprachverhalten
- **Coaching**: Identifikation von Entwicklungsfeldern

### Kreative Projekte
- **Digitale Memoiren**: Erstelle semantische Lebensgeschichten
- **Kunst**: Visualisiere emotionale Landschaften
- **Storytelling**: Finde narrative Strukturen

## 🔮 Die Magie dahinter

### Emotionale Analyse
```python
# Beispiel: Emotionaler Verlauf
timeline = [
    ("2024-06-28 14:23", 0.3),  # Neutral
    ("2024-06-28 14:45", 0.8),  # Sehr positiv
    ("2024-06-28 15:10", -0.2), # Leicht negativ
]
```

### Semantische Fäden
```python
# Beispiel: Thematische Verbindungen
threads = {
    "FREUDE_MARKER": ["msg_001", "msg_045", "msg_089"],
    "PLANUNG_MARKER": ["msg_023", "msg_067", "msg_102"],
}
```

### Beziehungs-Netzwerk
```python
# Beispiel: Nachrichtenbeziehungen
relationships = [
    {
        "from": "msg_001",
        "to": "msg_002",
        "type": "temporal",
        "strength": 0.9,
        "reason": "Direkte Antwort (15s)"
    }
]
```

## 🛠️ Erweiterte Konfiguration

### Marker anpassen
Lege eigene Marker in einer YAML-Datei ab und wähle sie in der GUI aus.
Beispiel `my_markers.yaml`:
```yaml
markers:
  positivity:
    - super
    - toll
  doubt:
    - vielleicht
    - unsicher
```

### Analyse-Fokus wählen
In der GUI kannst du zwischen vordefinierten Marker-Sets wählen, z.B. `All_Markers` oder `Trauma`. Je nach Auswahl wird das entsprechende Marker-Verzeichnis für die Analyse genutzt.

### Semantic Grabbers erweitern
Bearbeite:
```
../Marker_assist_bot/semantic_grabber_library.yaml
```

### Audio-Analyse tunen
Passe Emotionsparameter an in:
```python
# auto_transcriber_v4_emotion.py
EMOTION_THRESHOLDS = {
    'joy': 0.6,
    'sadness': 0.4,
    # ...
}
```

## 🐛 Fehlerbehebung

### "Module not found"
```bash
pip install -r requirements_emotion.txt
```

### "No markers found"
Stelle sicher, dass der Marker-Pfad korrekt ist:
```
../ALL_SEMANTIC_MARKER_TXT/
```

### Audio-Fehler
Prüfe ffmpeg Installation:
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

## 🤝 Beitragen

Wir freuen uns über Beiträge! Besonders in diesen Bereichen:

1. **Neue Marker**: Erweitere die semantische Erkennung
2. **Visualisierungen**: Erstelle schöne Darstellungen
3. **Export-Formate**: Unterstütze mehr Chat-Plattformen
4. **Sprachen**: Übersetze Marker für andere Sprachen

## 📜 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Nutze es frei für persönliche und kommerzielle Zwecke!

## 🙏 Danksagungen

- **OpenAI Whisper**: Für die geniale Transkription
- **Librosa Team**: Für Audio-Analyse-Tools
- **FRAUSAR Community**: Für das Marker-System
- **Alle Beta-Tester**: Für wertvolles Feedback

---

**Made with ❤️ and 🪄 by the Semantic Magic Team**

*"Deine Worte sind mehr als Text - sie sind die Landkarte deiner Seele."* 