# Super Semantic Whisper - Iterativer Fertigstellungsplan

**Stand:** 2026-02-16
**Gesamtstatus:** Funktionsfaehiger Monolith mit kritischen Portabilitaetsproblemen und unvollstaendigen Modulen

---

## Legende

- `[ ]` Offen
- `[~]` In Arbeit
- `[x]` Erledigt
- `P0` = Kritisch/Blocker, `P1` = Hoch, `P2` = Mittel, `P3` = Niedrig

---

## Phase 1: Stabilisierung und Portabilitaet (P0)

Ziel: Code laeuft auf jedem Rechner ohne Anpassungen.

### 1.1 Hardcodierte Pfade vollstaendig eliminieren

- [ ] `auto_transcriber_v2.py`: Hardcodierten Pfad durch `ConfigManager` ersetzen
- [ ] `auto_transcriber_v3.py`: Hardcodierten Pfad durch `ConfigManager` ersetzen
- [ ] `build_memory_from_transcripts.py`: Hardcodierten Pfad durch `ConfigManager` ersetzen
- [ ] `auto_transcriber_v4_emotion.py` pruefen: Sicherstellen, dass kein Fallback auf hardcodierten Pfad mehr existiert
- [ ] Alle Referenzen auf `/Users/benjaminpoersch/...` im gesamten Projekt finden und entfernen

### 1.2 Leere und tote Dateien aufraeumen

- [ ] `auto_transcriber.py` (0 Bytes) loeschen oder mit Verweis auf V4 fuellen
- [ ] `whisper_transcriber.py` (0 Bytes) loeschen
- [ ] `whisper_auto_runner.py` (0 Bytes) loeschen
- [ ] Doppelte Memory-Verzeichnisse konsolidieren (`Memory/` vs. `whisper_speaker_matcher/Memory/`)

### 1.3 Konfiguration abschliessen

- [ ] `config/default_config.yaml` vervollstaendigen: Alle Module referenzieren
- [ ] config.yaml.example erstellen als Vorlage fuer neue Benutzer
- [ ] `.gitignore` erweitern: `config.yaml` (User-spezifisch), Log-Dateien, `__pycache__`

---

## Phase 2: Externe Abhaengigkeiten klaeren (P1)

Ziel: System funktioniert eigenstaendig ohne Geschwisterprojekte oder degradiert transparent.

### 2.1 FRAUSAR Marker-System integrieren

- [ ] Klaeren: Koennen die Marker-Definitionen (63+ Marker TXT-Dateien) ins Repository aufgenommen werden?
- [ ] Falls ja: `ALL_SEMANTIC_MARKER_TXT/` als Unterverzeichnis einbinden
- [ ] Falls nein: Git Submodule oder pip-installierbares Paket erstellen
- [ ] `super_semantic_processor.py`: `sys.path.insert` durch sauberen Import ersetzen
- [ ] Fallback-Marker einbauen: Basis-Set an Markern direkt im Projekt mitliefern

### 2.2 MARSAP/CoSD optional machen

- [ ] `super_semantic_processor.py`: CoSD/MARSAP-Import korrekt als optional markieren
- [ ] Feature-Flag in `config.yaml` fuer CoSD/MARSAP (`enabled: false` als Default)
- [ ] Klare Fehlermeldung wenn aktiviert aber nicht installiert

### 2.3 Semantic Grabber Library

- [ ] Pruefen ob `semantic_grabber_library.yaml` ins Projekt uebernommen werden kann
- [ ] Falls ja: Integrieren und Pfad-Referenz anpassen
- [ ] Falls nein: Dokumentieren wo/wie es installiert wird

---

## Phase 3: Tests und Qualitaetssicherung (P1)

Ziel: Automatisierte Tests fuer alle Kernfunktionen.

### 3.1 Test-Infrastruktur aufbauen

- [ ] `pytest` und `pytest-cov` zu requirements_dev.txt hinzufuegen
- [ ] `tests/` Verzeichnis erstellen
- [ ] `tests/conftest.py` mit Fixtures (Beispiel-Audio, Beispiel-Chat-Export, Temp-Verzeichnisse)
- [ ] `pytest.ini` oder `pyproject.toml` mit Test-Konfiguration

### 3.2 Unit Tests schreiben

- [ ] `tests/test_config_manager.py`: Default-Config, Env-Override, Explizite Config, Prioritaet
- [ ] `tests/test_emotional_analyzer.py`: classify_emotion_from_audio mit verschiedenen Feature-Kombinationen
- [ ] `tests/test_whatsapp_parser.py`: Regex-Parsing von WhatsApp-Export-Zeilen
- [ ] `tests/test_memory_builder.py`: Profil-Erstellung, inkrementelles Update, YAML-Round-Trip
- [ ] `tests/test_semantic_processor.py`: Beziehungsanalyse, Thread-Identifikation, Emotional Arc
- [ ] `tests/test_merge_transcripts.py`: Zeitstempel-Parsing, Sortierung, Sprecher-Inferenz

### 3.3 Integration Tests

- [ ] `tests/test_transcription_pipeline.py`: Audio -> Transkript -> Memory (mit Mock-Whisper)
- [ ] `tests/test_semantic_pipeline.py`: Chat-Export -> Semantische Analyse -> JSON Output
- [ ] `tests/test_gui_integration.py`: GUI laesst sich starten (ohne Display: headless check)

### 3.4 CI/CD einrichten

- [ ] `.github/workflows/test.yml` fuer pytest
- [ ] `.github/workflows/lint.yml` fuer flake8/ruff
- [ ] Badge in README einbinden

---

## Phase 4: whatsapp_auto_transcriber-Modul implementieren (P2)

Ziel: Modularer Neuansatz ist funktionsfaehig und ersetzt monolithische Skripte.

### 4.1 FileWatcher implementieren

- [ ] `whatsapp_auto_transcriber/src/file_watcher.py`: watchdog-basiertes Directory Watching
- [ ] Neue Audio-Dateien erkennen (.opus, .wav, .mp3, .m4a, .ogg)
- [ ] Debouncing implementieren (Dateien erst verarbeiten wenn vollstaendig geschrieben)
- [ ] Event-Callback fuer neue Dateien

### 4.2 AudioProcessor implementieren

- [ ] `whatsapp_auto_transcriber/src/audio_processor.py`: Whisper-Integration
- [ ] Code aus `auto_transcriber_v4_emotion.py` refactoren und uebernehmen
- [ ] EmotionalAnalyzer integrieren
- [ ] Ergebnis-Speicherung als Markdown

### 4.3 SpeakerDetector implementieren

- [ ] `whatsapp_auto_transcriber/src/speaker_detector.py`: Sprechererkennung
- [ ] Ordner-basierte Erkennung (aus V4 uebernehmen)
- [ ] Keyword-basierte Erkennung
- [ ] Memory-basierte Vorhersage (aus Profilen)

### 4.4 Monitoring implementieren

- [ ] `whatsapp_auto_transcriber/src/monitoring.py`: Verarbeitungsstatistiken
- [ ] Erfolg/Fehler-Zaehler
- [ ] Verarbeitungszeit-Tracking
- [ ] Log-Aggregation

### 4.5 Integration

- [ ] `whatsapp_auto_transcriber/main.py`: Alle Komponenten verbinden
- [ ] CLI-Argumente (start, stop, status)
- [ ] Graceful Shutdown
- [ ] Tests fuer das Modul

---

## Phase 5: WordThread UI anbinden (P2)

Ziel: React/Electron-UI kommuniziert mit Python-Backend.

### 5.1 Python REST API erstellen

- [ ] FastAPI oder Flask Backend aufsetzen
- [ ] `api/` Verzeichnis erstellen
- [ ] Endpoint: `POST /api/transcribe` - Audio-Datei transkribieren
- [ ] Endpoint: `POST /api/analyze` - Text semantisch analysieren
- [ ] Endpoint: `GET /api/markers` - Marker-Liste abrufen
- [ ] Endpoint: `GET /api/profiles` - Sprecher-Profile abrufen
- [ ] Endpoint: `POST /api/process` - Vollstaendige Pipeline ausfuehren
- [ ] OpenAPI/Swagger-Dokumentation

### 5.2 WordThread UI anbinden

- [ ] `wordthread-ui/src/api.ts`: Mock-Stubs durch echte API-Calls ersetzen
- [ ] API-URL konfigurierbar machen (env variable)
- [ ] Error-Handling fuer Backend-Fehler
- [ ] Loading-States in UI-Komponenten

### 5.3 Electron-Python-Bridge

- [ ] Python-Backend als Child-Process starten
- [ ] IPC oder HTTP-Kommunikation einrichten
- [ ] Auto-Start/Stop des Backends mit Electron

---

## Phase 6: Containerisierung und Deployment (P3)

Ziel: Ein-Klick-Deployment moeglich.

### 6.1 Docker

- [ ] `Dockerfile` fuer Python-Backend (inkl. FFmpeg, Whisper)
- [ ] `docker-compose.yml` fuer Gesamtsystem
- [ ] Volume-Mounts fuer Eingang/, Memory/, Transkripte_LLM/
- [ ] Umgebungsvariablen-Dokumentation fuer Docker

### 6.2 Deployment-Dokumentation

- [ ] `docs/DEPLOYMENT.md` schreiben
- [ ] Lokale Installation (Schritt-fuer-Schritt)
- [ ] Docker-Installation
- [ ] Server-Deployment (Linux)

---

## Phase 7: Verbesserungen und Erweiterungen (P3)

Ziel: Qualitaet und Features verbessern.

### 7.1 Emotionsanalyse verbessern

- [ ] Heuristik-basierte Klassifikation durch trainierbares ML-Modell ersetzen
- [ ] Validierung der Emotionserkennung mit gelabelten Daten
- [ ] Mehr Emotionskategorien oder dimensionales Modell (Valence-Arousal-Dominance)

### 7.2 Datenbank-Option

- [ ] SQLite als Alternative zum Dateisystem evaluieren
- [ ] Schema fuer Nachrichten, Profile, Beziehungen entwerfen
- [ ] Migration-Skript: Dateisystem -> Datenbank
- [ ] Query-API fuer komplexe Abfragen ("Alle Nachrichten mit Marker X im Zeitraum Y")

### 7.3 Multi-Plattform-Support

- [ ] Windows-Kompatibilitaet testen und sicherstellen
- [ ] Pfad-Handling plattformuebergreifend pruefen (Path vs. String)
- [ ] Installation-Anleitung fuer Windows ergaenzen

### 7.4 Performance

- [ ] Whisper-Modell-Cache implementieren (Modell nur einmal laden)
- [ ] Batch-Verarbeitung fuer mehrere Audio-Dateien
- [ ] Parallele Transkription (multiprocessing)
- [ ] Caching fuer bereits verarbeitete Dateien (Hash-basiert)

### 7.5 Mehrsprachigkeit

- [ ] Marker-System fuer weitere Sprachen (Englisch, Franzoesisch)
- [ ] Spracherkennung pro Audio-Datei (auto-detect statt fix "de")
- [ ] UI-Uebersetzungen

---

## Zusammenfassung der Phasen

| Phase | Ziel | Prioritaet | Abhaengigkeiten |
|-------|------|-----------|----------------|
| 1 | Stabilisierung & Portabilitaet | P0 | Keine |
| 2 | Externe Abhaengigkeiten klaeren | P1 | Phase 1 |
| 3 | Tests & Qualitaetssicherung | P1 | Phase 1 |
| 4 | whatsapp_auto_transcriber implementieren | P2 | Phase 1, 3 |
| 5 | WordThread UI anbinden | P2 | Phase 3, teilweise 4 |
| 6 | Containerisierung & Deployment | P3 | Phase 1, 2, 3 |
| 7 | Verbesserungen & Erweiterungen | P3 | Phase 1-3 |

**Empfohlene Reihenfolge:** Phase 1 -> Phase 2 + 3 (parallel) -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 7

Phase 1 ist der kritische Pfad. Ohne abgeschlossene Phase 1 sind alle weiteren Phasen instabil.
