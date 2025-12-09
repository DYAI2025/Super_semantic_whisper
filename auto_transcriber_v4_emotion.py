#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhisperSprecherMatcher V4 - Mit emotionaler Sprachanalyse
- Extrahiert Datum/Zeit aus Audio-Dateinamen  
- Erkennt emotionale Sprachfärbung während der Transkription
- Zeigt Original-Aufnahmezeit und Emotionen im Transkript
- Nutzt vorhandene Marker-Systeme für emotionale Klassifikation
"""

import os
import sys
import subprocess
import json
import yaml
import re
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Tuple, Optional

# Import ConfigManager
sys.path.insert(0, str(Path(__file__).parent))
from src.config_manager import ConfigManager

# Versuche zusätzliche Audio-Bibliotheken zu importieren
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ Librosa nicht installiert. Audio-Feature-Extraktion limitiert.")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob nicht installiert. Sentiment-Analyse limitiert.")

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcription_v4_emotion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmotionalAnalyzer:
    """Analysiert emotionale Sprachfärbung aus Audio und Text"""
    
    def __init__(self):
        self.emotional_markers = self._load_emotional_markers()
        
    def _load_emotional_markers(self):
        """Lade emotionale Marker aus deinem bestehenden System"""
        try:
            # Lade deine emotionalen Marker aus dem bestehenden System
            marker_paths = [
                Path("../ALL_SEMANTIC_MARKER_TXT/Former_NEW_MARKER_FOLDERS/emotions"),
                Path("../Assist_TXT_marker_py: 2/resonance"),
                Path("../ALL_SEMANTIC_MARKER_TXT/ALL_NEWMARKER01")
            ]
            
            markers = {}
            
            for marker_path in marker_paths:
                if marker_path.exists():
                    for marker_file in marker_path.glob("*.txt"):
                        emotion_name = marker_file.stem.lower()
                        try:
                            with open(marker_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Extrahiere Keywords aus den Marker-Dateien
                                keywords = re.findall(r'\b\w+\b', content.lower())
                                if keywords:  # Nur wenn Keywords gefunden wurden
                                    markers[emotion_name] = keywords[:20]  # Top 20 Keywords
                        except Exception as e:
                            logger.debug(f"Fehler beim Lesen von {marker_file}: {e}")
                            
            if markers:
                logger.info(f"Emotionale Marker geladen: {list(markers.keys())[:5]}...")
                return markers
            else:
                return self._create_default_emotional_markers()
                
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Marker: {e}")
            return self._create_default_emotional_markers()
    
    def _create_default_emotional_markers(self):
        """Erstelle Standard-Emotionsmarker basierend auf deinen resonance-Dateien"""
        return {
            'hoffnungsvoll_antreibend': [
                'aufbruch', 'chancen', 'möglichkeiten', 'weiter', 'loslegen', 
                'positiv', 'motivierend', 'antreibend', 'energie', 'kraft'
            ],
            'neugierig_forschend': [
                'was wäre wenn', 'mal angenommen', 'zeig mir', 'experimentiere',
                'neugierig', 'interessant', 'spannend', 'frage', 'erkunden'
            ],
            'sehnsuchtsvoll_still': [
                'vermisse', 'fehlt mir', 'leere', 'sehnsucht', 'heimweh',
                'melancholisch', 'ruhig', 'zart', 'sanft', 'still'
            ],
            'traurig_reflektierend': [
                'verloren', 'schade', 'einsamkeit', 'traurig', 'leer',
                'reflektierend', 'nachdenklich', 'schwermütig', 'betrübt'
            ],
            'wuetend_rebellisch': [
                'ungerecht', 'nicht mit mir', 'kämpfen', 'widerstand', 'bullshit',
                'wütend', 'rebellisch', 'dagegen', 'aufgeladen', 'konfrontation'
            ],
            'mystisch_symbolisch': [
                'geheimnis', 'symbol', 'tor', 'schwelle', 'schlüssel',
                'verborgen', 'unsichtbar', 'schatten', 'vision', 'mystisch'
            ],
            'begeistert_enthusiastisch': [
                'fantastisch', 'wunderbar', 'begeistert', 'großartig', 'toll',
                'super', 'genial', 'wow', 'krass', 'mega', 'cool'
            ]
        }
    
    def analyze_audio_features(self, audio_path: Path) -> Dict[str, float]:
        """Analysiere Audio-Features für emotionale Erkennung"""
        if not LIBROSA_AVAILABLE:
            logger.warning("Librosa nicht verfügbar - Audio-Feature-Extraktion übersprungen")
            return {}
            
        try:
            # Lade Audio-Datei
            y, sr = librosa.load(str(audio_path), sr=22050)
            
            # Extrahiere emotionale Audio-Features
            features = {}
            
            # 1. Tempo
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            
            # 2. Spektrale Features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_std'] = float(np.std(spectral_centroids))
            
            # 3. MFCC Features (wichtig für Emotion)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(3):  # Nur die ersten 3 MFCCs für Emotion
                features[f'mfcc_{i}_mean'] = float(np.mean(mfccs[i]))
                features[f'mfcc_{i}_std'] = float(np.std(mfccs[i]))
            
            # 4. Energy und Intensität
            rms = librosa.feature.rms(y=y)[0]
            features['energy_mean'] = float(np.mean(rms))
            features['energy_std'] = float(np.std(rms))
            
            # 5. Zero Crossing Rate (Sprachfluss)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zcr_mean'] = float(np.mean(zcr))
            
            return features
            
        except Exception as e:
            logger.error(f"Fehler bei Audio-Analyse: {e}")
            return {}
    
    def analyze_text_emotion(self, text: str) -> Dict[str, any]:
        """Analysiere emotionale Färbung des Textes"""
        if not text:
            return {'dominant_emotion': 'neutral', 'emotion_scores': {}, 'valence': 0.0}
        
        text_lower = text.lower()
        emotion_scores = {}
        
        # Analysiere mit emotionalen Markern
        for emotion, keywords in self.emotional_markers.items():
            score = 0
            for keyword in keywords:
                # Exakte und partielle Matches
                if keyword in text_lower:
                    score += text_lower.count(keyword)
                # Fuzzy matching für ähnliche Wörter
                for word in text_lower.split():
                    if len(word) > 3 and keyword in word:
                        score += 0.5
            
            emotion_scores[emotion] = score
        
        # Normalisiere Scores
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v/total_score for k, v in emotion_scores.items()}
        
        # Finde dominante Emotion
        dominant_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else 'neutral'
        
        # Sentiment-Analyse mit TextBlob
        valence = 0.0
        arousal = 0.0
        subjectivity = 0.0
        
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                valence = blob.sentiment.polarity  # -1 (negativ) bis +1 (positiv)
                arousal = abs(blob.sentiment.polarity)  # Intensität
                subjectivity = blob.sentiment.subjectivity
            except:
                valence = 0.0
                arousal = 0.0
                subjectivity = 0.0
        
        return {
            'dominant_emotion': dominant_emotion,
            'emotion_scores': emotion_scores,
            'valence': valence,
            'arousal': arousal,
            'subjectivity': subjectivity
        }
    
    def classify_emotion_from_audio(self, audio_features: Dict[str, float]) -> str:
        """Klassifiziere Emotion basierend auf Audio-Features (vereinfacht)"""
        if not audio_features:
            return 'neutral'
        
        # Vereinfachte Heuristik basierend auf Audio-Features
        energy_mean = audio_features.get('energy_mean', 0)
        tempo = audio_features.get('tempo', 120)
        spectral_centroid = audio_features.get('spectral_centroid_mean', 0)
        
        # Hohe Energie + hohes Tempo = Begeistert/Wütend
        if energy_mean > 0.1 and tempo > 130:
            if spectral_centroid > 2000:  # Höhere Frequenzen
                return 'wuetend_rebellisch'
            else:
                return 'begeistert_enthusiastisch'
        
        # Niedrige Energie = Traurig/Sehnsuchtsvoll
        elif energy_mean < 0.05:
            if tempo < 100:
                return 'traurig_reflektierend'
            else:
                return 'sehnsuchtsvoll_still'
        
        # Mittlere Werte = Neugierig/Hoffnungsvoll
        elif tempo > 100:
            return 'neugierig_forschend'
        else:
            return 'hoffnungsvoll_antreibend'

class WhisperSpeakerMatcherV4:
    def __init__(self, base_path=None, config_path=None, use_faster_whisper=True):
        """
        Initialisiert den WhisperSpeakerMatcher mit konfigurierbaren Pfaden

        Args:
            base_path: Expliziter Basis-Pfad (überschreibt Config) - für Abwärtskompatibilität
            config_path: Pfad zur config.yaml (optional)
            use_faster_whisper: Nutze faster-whisper statt standard whisper
        """
        # Lade Konfiguration
        self.config = ConfigManager(config_path)

        # Pfade aus Config oder Argument (Argument hat Priorität für Abwärtskompatibilität)
        if base_path:
            # Expliziter Pfad wurde übergeben (Legacy-Mode)
            logger.info(f"💡 Nutze expliziten Basis-Pfad: {base_path}")
            self.base_path = Path(base_path)
            self.eingang_path = self.base_path / "Eingang"
            self.memory_path = self.base_path / "Memory"
            self.output_path = self.base_path / "Transkripte_LLM"
        else:
            # Nutze ConfigManager (empfohlener Weg)
            logger.info("⚙️  Nutze ConfigManager für Pfadverwaltung")
            self.base_path = self.config.get_path('base')
            self.eingang_path = self.config.get_path('eingang')
            self.memory_path = self.config.get_path('memory')
            self.output_path = self.config.get_path('output')

        # Erstelle Verzeichnisse falls nicht vorhanden
        self._ensure_directories()

        # Logging der finalen Pfade
        logger.info(f"📁 Basis-Pfad: {self.base_path}")
        logger.info(f"📂 Eingang: {self.eingang_path}")
        logger.info(f"🧠 Memory: {self.memory_path}")
        logger.info(f"📝 Output: {self.output_path}")

        self.use_faster_whisper = use_faster_whisper
        self.speakers = self._load_speaker_profiles()
        self.emotion_analyzer = EmotionalAnalyzer()

    def _ensure_directories(self):
        """Erstelle notwendige Verzeichnisse"""
        for path in [self.eingang_path, self.memory_path, self.output_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"✓ Verzeichnis erstellt/geprüft: {path}")
        
    
    def _load_speaker_profiles(self):
        """Lade bekannte Sprecher-Profile aus Memory-Ordner"""
        speakers = {}
        
        if not self.memory_path.exists():
            logger.warning(f"Memory-Pfad existiert nicht: {self.memory_path}")
            return self._create_default_speakers()
            
        for yaml_file in self.memory_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    profile = yaml.safe_load(f)
                    speaker_name = yaml_file.stem
                    speakers[speaker_name] = profile
                    logger.info(f"Sprecher-Profil geladen: {speaker_name}")
            except Exception as e:
                logger.error(f"Fehler beim Laden von {yaml_file}: {e}")
                
        return speakers if speakers else self._create_default_speakers()
    
    def _create_default_speakers(self):
        """Erstelle Standard-Sprecher wenn keine Profile gefunden werden"""
        return {
            'ben': {
                'name': 'Benjamin Poersch',
                'keywords': ['also', 'genau', 'interessant', 'technisch', 'system']
            },
            'zoe': {
                'name': 'Zoe',
                'keywords': ['wow', 'krass', 'mega', 'cool', 'schön']
            },
            'ich': {
                'name': 'Ich',
                'keywords': []
            }
        }
    
    def extract_whatsapp_datetime(self, filename: str) -> Tuple[Optional[datetime], str]:
        """
        Extrahiere Datum und Zeit aus Audio-Dateinamen
        Beispiele:
        - WhatsApp Audio 2025-06-29 at 13.20.58.opus
        - 00000249-AUDIO-2025-02-28-07-05-24.opus
        """
        # Pattern für WhatsApp Dateien (Standard-Format)
        whatsapp_pattern = r'WhatsApp (?:Audio|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})'
        
        match = re.search(whatsapp_pattern, filename)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                formatted_date = dt.strftime('%Y-%m-%d_%H-%M-%S')
                return dt, formatted_date
            except ValueError as e:
                logger.warning(f"Ungültiges Datum in {filename}: {e}")
        
        # Pattern für nummerierte AUDIO-Dateien (Format: XXXXXXXX-AUDIO-YYYY-MM-DD-HH-MM-SS.opus)
        audio_pattern = r'\d+-AUDIO-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})'
        
        match = re.search(audio_pattern, filename)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                formatted_date = dt.strftime('%Y-%m-%d_%H-%M-%S')
                logger.info(f"Erkanntes Aufnahmedatum: {dt.strftime('%d.%m.%Y um %H:%M:%S')} aus Datei {filename}")
                return dt, formatted_date
            except ValueError as e:
                logger.warning(f"Ungültiges Datum in {filename}: {e}")
        
        # Fallback: Verwende Datei-Erstellungszeit
        logger.warning(f"Kein Datum im Dateinamen erkannt: {filename}")
        return None, "unbekannt"

    def get_chatpartner_from_path(self, file_path: Path) -> str:
        """Extrahiere Chatpartner aus Ordnerstruktur"""
        relative_path = file_path.relative_to(self.eingang_path)
        parts = relative_path.parts
        
        if len(parts) > 1:
            chatpartner = parts[0]
            return chatpartner.replace('_', ' ')
        
        filename = file_path.name.lower()
        for known_person in ['zoe', 'schroeti', 'freddy', 'marike', 'vincent', 'elke']:
            if known_person in filename:
                return known_person.title()
        
        return "Unbekannt"

    def transcribe_audio_standard(self, audio_path: Path) -> Optional[str]:
        """Standard Whisper Transkription"""
        try:
            whisper_cmd = self._find_whisper_command()
            
            if not whisper_cmd:
                raise Exception("Whisper nicht gefunden. Bitte installieren: pip install openai-whisper")
            
            cmd = [whisper_cmd, str(audio_path), "--language", "de", "--model", "base", "--output_format", "txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Whisper Fehler: {result.stderr}")
                return None
                
            # Whisper erstellt TXT im aktuellen Verzeichnis
            txt_filename = audio_path.name.replace('.opus', '.txt')
            txt_path = Path(txt_filename)
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as f:
                    transcription = f.read().strip()
                txt_path.unlink()  # Lösche temporäre Datei
                return transcription
            
            return None
                
        except Exception as e:
            logger.error(f"Transkriptions-Fehler für {audio_path}: {e}")
            return None

    def _find_whisper_command(self):
        """Finde verfügbare Whisper-Installation"""
        possible_commands = ['whisper', 'python -m whisper', 'python3 -m whisper']
        
        for cmd in possible_commands:
            try:
                result = subprocess.run(cmd.split() + ['--help'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd.split()[0] if len(cmd.split()) == 1 else cmd
            except:
                continue
        return None

    def identify_speaker_in_conversation(self, transcription: str, chatpartner: str) -> List[Tuple[str, str]]:
        """Identifiziere Sprecher in der Konversation"""
        transcription_lower = transcription.lower()
        
        my_indicators = ['ich schicke', 'ich sende', 'hier ist', 'ich wollte', 'von mir', 'meine']
        is_my_message = any(indicator in transcription_lower for indicator in my_indicators)
        
        if is_my_message:
            speaker = "Ich"
        else:
            speaker = chatpartner
        
        return [(speaker, transcription)]

    def format_for_llm_with_emotion(self, chatpartner: str, conversation_parts: List[Tuple[str, str]], 
                                  audio_file: Path, recording_datetime: Optional[datetime], 
                                  processing_time: datetime, emotion_analysis: Dict) -> str:
        """Formatiere Transkription für optimale LLM-Verarbeitung mit emotionaler Analyse"""
        
        if recording_datetime:
            recording_str = recording_datetime.strftime('%d.%m.%Y um %H:%M:%S')
            recording_date = recording_datetime.strftime('%Y-%m-%d')
            recording_time = recording_datetime.strftime('%H:%M:%S')
        else:
            recording_str = "Unbekannt"
            recording_date = "Unbekannt"
            recording_time = "Unbekannt"
        
        # Emotionale Zusammenfassung
        emotion_summary = self._format_emotion_summary(emotion_analysis)
        
        output = f"""# WhatsApp Audio Transkription mit emotionaler Analyse

**Chat mit:** {chatpartner}
**Aufnahme am:** {recording_str}
**Verarbeitet am:** {processing_time.strftime('%d.%m.%Y um %H:%M:%S')}
**Original-Datei:** {audio_file.name}

## Zeitstempel:
- **Aufnahme-Datum:** {recording_date}
- **Aufnahme-Uhrzeit:** {recording_time}
- **Verarbeitungszeit:** {processing_time.strftime('%Y-%m-%d %H:%M:%S')}

## 🎭 Emotionale Analyse:
{emotion_summary}

## Transkription:

"""
        
        for speaker, text in conversation_parts:
            # Füge emotionale Marker zur Transkription hinzu
            emotion_marker = self._get_emotion_marker_for_text(text, emotion_analysis)
            
            if speaker == "Ich":
                output += f"**[Ich - {recording_time}]{emotion_marker}:** {text}\n\n"
            else:
                output += f"**[{speaker} - {recording_time}]{emotion_marker}:** {text}\n\n"
        
        output += f"""## Kontext für LLM:
Diese Nachricht wurde am {recording_str} in einem WhatsApp-Chat zwischen mir und {chatpartner} aufgenommen.

### Emotionale Einordnung:
Die Sprachanalyse zeigt {emotion_analysis.get('dominant_emotion', 'neutrale')} emotionale Färbung mit einer Valenz von {emotion_analysis.get('valence', 0):.2f} (Positivität/Negativität) und einer Intensität von {emotion_analysis.get('arousal', 0):.2f}.

---
*Transkribiert mit WhisperSprecherMatcher V4 (Emotion) am {processing_time.strftime('%d.%m.%Y um %H:%M:%S')}*
"""
        
        return output
    
    def _format_emotion_summary(self, emotion_analysis: Dict) -> str:
        """Formatiere emotionale Analyse für das Transkript"""
        dominant = emotion_analysis.get('dominant_emotion', 'neutral')
        valence = emotion_analysis.get('valence', 0)
        arousal = emotion_analysis.get('arousal', 0)
        scores = emotion_analysis.get('emotion_scores', {})
        
        # Deutsche Übersetzungen
        emotion_translations = {
            'hoffnungsvoll_antreibend': 'Hoffnungsvoll & Antreibend',
            'neugierig_forschend': 'Neugierig & Forschend', 
            'sehnsuchtsvoll_still': 'Sehnsuchtsvoll & Still',
            'traurig_reflektierend': 'Traurig & Reflektierend',
            'wuetend_rebellisch': 'Wütend & Rebellisch',
            'mystisch_symbolisch': 'Mystisch & Symbolisch',
            'begeistert_enthusiastisch': 'Begeistert & Enthusiastisch',
            'neutral': 'Neutral'
        }
        
        summary = f"""
**Dominante Emotion:** {emotion_translations.get(dominant, dominant)}
**Emotionale Valenz:** {valence:.2f} (Positivität: -1 bis +1)
**Emotionale Intensität:** {arousal:.2f} (Aufregung/Energie)

**Top Emotionen erkannt:**"""

        # Zeige Top 3 Emotionen
        top_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for emotion, score in top_emotions:
            if score > 0:
                emotion_name = emotion_translations.get(emotion, emotion)
                percentage = score * 100
                summary += f"\n- {emotion_name}: {percentage:.1f}%"
        
        return summary
    
    def _get_emotion_marker_for_text(self, text: str, emotion_analysis: Dict) -> str:
        """Generiere emotionalen Marker für die Transkription"""
        dominant = emotion_analysis.get('dominant_emotion', 'neutral')
        valence = emotion_analysis.get('valence', 0)
        
        # Emoji-Mapping für emotionale Marker
        emotion_emojis = {
            'hoffnungsvoll_antreibend': ' 🚀',
            'neugierig_forschend': ' 🔍',
            'sehnsuchtsvoll_still': ' 🌙',
            'traurig_reflektierend': ' 😔',
            'wuetend_rebellisch': ' ⚡',
            'mystisch_symbolisch': ' ✨',
            'begeistert_enthusiastisch': ' 🎉',
            'neutral': ''
        }
        
        emoji = emotion_emojis.get(dominant, '')
        
        # Zusätzliche Valenz-Indikatoren
        if valence > 0.3:
            emoji += ' +'
        elif valence < -0.3:
            emoji += ' -'
            
        return emoji

    def get_sorted_audio_files(self) -> List[Path]:
        """Hole alle OPUS-Dateien, priorisiere Zoe-Ordner"""
        if not self.eingang_path.exists():
            logger.error(f"Eingang-Ordner nicht gefunden: {self.eingang_path}")
            return []

        all_opus_files = list(self.eingang_path.rglob("*.opus"))
        
        zoe_files = []
        other_files = []
        
        for file in all_opus_files:
            if 'zoe' in str(file).lower():
                zoe_files.append(file)
            else:
                other_files.append(file)
        
        def sort_by_whatsapp_date(file_path):
            dt, _ = self.extract_whatsapp_datetime(file_path.name)
            return dt if dt else datetime.fromtimestamp(file_path.stat().st_mtime)
        
        zoe_files.sort(key=sort_by_whatsapp_date, reverse=True)
        other_files.sort(key=sort_by_whatsapp_date, reverse=True)
        
        return zoe_files + other_files

    def process_audio_files(self):
        """Verarbeite alle OPUS Audio-Dateien mit emotionaler Analyse"""
        
        audio_files = self.get_sorted_audio_files()
        logger.info(f"Gefunden: {len(audio_files)} OPUS-Dateien")
        
        if audio_files:
            zoe_count = sum(1 for f in audio_files if 'zoe' in str(f).lower())
            logger.info(f"Davon {zoe_count} Dateien im Zoe-Ordner (werden zuerst verarbeitet)")
        
        processed_count = 0
        for audio_file in audio_files:
            try:
                recording_datetime, formatted_date = self.extract_whatsapp_datetime(audio_file.name)
                chatpartner = self.get_chatpartner_from_path(audio_file)
                
                if recording_datetime:
                    output_filename = f"{formatted_date}_{chatpartner.replace(' ', '_')}_{audio_file.stem}_emotion_transkript.md"
                else:
                    output_filename = f"{chatpartner.replace(' ', '_')}_{audio_file.stem}_emotion_transkript.md"
                
                output_path = self.output_path / output_filename
                
                if output_path.exists():
                    logger.info(f"Bereits verarbeitet: {audio_file.name}")
                    continue
                
                if recording_datetime:
                    logger.info(f"Verarbeite: {audio_file.name} (Chat mit {chatpartner}, aufgenommen am {recording_datetime.strftime('%d.%m.%Y um %H:%M')})")
                else:
                    logger.info(f"Verarbeite: {audio_file.name} (Chat mit {chatpartner})")
                
                # 1. Audio transkribieren
                transcription = self.transcribe_audio_standard(audio_file)
                
                if not transcription:
                    logger.warning(f"Keine Transkription erhalten für {audio_file.name}")
                    continue
                
                # 2. Emotionale Analyse
                logger.info(f"🎭 Analysiere emotionale Sprachfärbung...")
                
                # Audio-Features analysieren
                audio_features = self.emotion_analyzer.analyze_audio_features(audio_file)
                
                # Text-Emotion analysieren
                text_emotion = self.emotion_analyzer.analyze_text_emotion(transcription)
                
                # Audio-Emotion klassifizieren
                audio_emotion = self.emotion_analyzer.classify_emotion_from_audio(audio_features)
                
                # Kombiniere beide Analysen
                emotion_analysis = {
                    'dominant_emotion': text_emotion['dominant_emotion'],  # Priorität auf Text
                    'audio_emotion': audio_emotion,
                    'emotion_scores': text_emotion['emotion_scores'],
                    'valence': text_emotion['valence'],
                    'arousal': text_emotion['arousal'],
                    'audio_features': audio_features
                }
                
                logger.info(f"🎭 Emotionale Färbung: {emotion_analysis['dominant_emotion']} (Valenz: {emotion_analysis['valence']:.2f})")
                
                # 3. Sprecher identifizieren
                conversation_parts = self.identify_speaker_in_conversation(transcription, chatpartner)
                
                # 4. Formatiere für LLM mit emotionaler Analyse
                processing_time = datetime.now()
                llm_formatted = self.format_for_llm_with_emotion(chatpartner, conversation_parts, 
                                                               audio_file, recording_datetime, 
                                                               processing_time, emotion_analysis)
                
                # 5. Speichere Transkript
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(llm_formatted)
                
                processed_count += 1
                logger.info(f"✅ Verarbeitet: {audio_file.name} -> {output_filename}")
                
                progress = (audio_files.index(audio_file) + 1) / len(audio_files) * 100
                logger.info(f"Fortschritt: {progress:.1f}% ({audio_files.index(audio_file) + 1}/{len(audio_files)})")
                
            except Exception as e:
                logger.error(f"Fehler bei {audio_file.name}: {e}")
                continue
        
        logger.info(f"Verarbeitung abgeschlossen. {processed_count} neue Dateien verarbeitet.")

def main():
    """Hauptfunktion"""
    print("🎤🎭 WhisperSprecherMatcher V4 mit emotionaler Analyse gestartet...")
    print("Mit Datum/Zeit-Extraktion und emotionaler Sprachfärbung")
    print()

    import argparse
    import warnings

    parser = argparse.ArgumentParser(
        description="WhisperSprecherMatcher V4 (Emotion)",
        epilog="Siehe docs/KONFIGURATION.md für Details zur Pfad-Konfiguration"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Verwende lokalen Pfad (DEPRECATED: Nutze --base-path oder config.yaml)"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        help="Expliziter Basis-Pfad (überschreibt config.yaml)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Pfad zur config.yaml (default: config.yaml → config/default_config.yaml)"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Zeige effektive Konfiguration und beende"
    )

    args = parser.parse_args()

    try:
        # Zeige Konfiguration und beende
        if args.show_config:
            config = ConfigManager(Path(args.config) if args.config else None)
            config.show_effective_config()
            return

        # Abwärtskompatibilität: --local
        if args.local:
            warnings.warn(
                "--local ist deprecated. Nutze stattdessen:\n"
                "  --base-path .  ODER\n"
                "  config.yaml mit paths.base_path: .",
                DeprecationWarning,
                stacklevel=2
            )
            matcher = WhisperSpeakerMatcherV4(
                base_path=".",
                config_path=Path(args.config) if args.config else None
            )
        # Expliziter Basis-Pfad
        elif args.base_path:
            matcher = WhisperSpeakerMatcherV4(
                base_path=args.base_path,
                config_path=Path(args.config) if args.config else None
            )
        # Standard: Nutze ConfigManager
        else:
            matcher = WhisperSpeakerMatcherV4(
                config_path=Path(args.config) if args.config else None
            )

        print()
        matcher.process_audio_files()
        print()
        print("✅ Verarbeitung erfolgreich abgeschlossen!")
        print(f"📁 Transkripte mit emotionaler Analyse gespeichert in: {matcher.output_path}")

    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 