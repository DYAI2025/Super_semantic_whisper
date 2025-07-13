#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Semantic Processor - Die Magie beginnt hier! ✨
Vollständige Integration aller Komponenten
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import yaml
import re
from typing import List, Dict, Any, Optional, Tuple
import hashlib
from dataclasses import dataclass, asdict
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Füge alle notwendigen Pfade hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "Marker_assist_bot"))
sys.path.insert(0, str(Path(__file__).parent.parent / "MARSAP"))
sys.path.insert(0, str(Path(__file__).parent.parent / "MARSAPv2"))
sys.path.insert(0, str(Path(__file__).parent.parent / "ALL_SEMANTIC_MARKER_TXT"))

@dataclass
class SemanticMessage:
    """Repräsentiert eine Nachricht mit allen semantischen Informationen"""
    id: str
    timestamp: datetime
    sender: str
    content: str
    type: str  # text, audio, image, document
    emotion: Dict[str, float]
    markers: List[str]
    semantic_scores: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class SemanticRelationship:
    """Repräsentiert eine Beziehung zwischen Nachrichten"""
    from_id: str
    to_id: str
    type: str  # temporal, thematic, emotional, reference
    strength: float
    reason: str

@dataclass 
class EmotionalArc:
    """Repräsentiert den emotionalen Verlauf"""
    timeline: List[Tuple[datetime, float]]  # (Zeit, Valenz)
    peaks: List[Dict[str, Any]]
    valleys: List[Dict[str, Any]]
    turning_points: List[Dict[str, Any]]
    overall_trend: str

class SuperSemanticProcessor:
    """Der Hauptprozessor für die semantische Integration"""

    def __init__(self, marker_yaml_path: Optional[str] = None, marker_set: Optional[str] = None):
        self.messages: Dict[str, SemanticMessage] = {}
        self.relationships: List[SemanticRelationship] = []
        self.emotional_arc: Optional[EmotionalArc] = None
        self.semantic_threads: Dict[str, List[str]] = {}
        self.marker_system = None
        self.cosd_analyzer = None
        self.semantic_grabbers = {}
        self.custom_markers: Dict[str, List[str]] = {}
        self.marker_yaml_path = marker_yaml_path
        self.marker_set = marker_set
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialisiere alle Komponenten"""
        logger.info("🚀 Initialisiere Super Semantic Processor...")
        
        # 1. Lade Marker-System
        try:
            from frausar_gui import FRAUSARAssistant
            marker_path = Path("../ALL_SEMANTIC_MARKER_TXT")
            if self.marker_set:
                marker_path = marker_path / self.marker_set
            self.marker_system = FRAUSARAssistant(str(marker_path))
            logger.info("✅ FRAUSAR Marker-System geladen")
        except Exception as e:
            logger.warning(f"⚠️ FRAUSAR nicht verfügbar: {e}")
            
        # 2. Lade CoSD/MARSAP
        try:
            from cosd import CoSDAnalyzer
            self.cosd_analyzer = CoSDAnalyzer()
            logger.info("✅ CoSD/MARSAP Analyzer geladen")
        except Exception as e:
            logger.warning(f"⚠️ CoSD nicht verfügbar: {e}")
            
        # 3. Lade Semantic Grabbers
        self._load_semantic_grabbers()

        # 4. Lade benutzerdefinierte Marker aus YAML, falls vorhanden
        self._load_custom_markers(self.marker_yaml_path)
        
    def _load_semantic_grabbers(self):
        """Lade Semantic Grabber Library"""
        grabber_path = Path("../Marker_assist_bot/semantic_grabber_library.yaml")
        if grabber_path.exists():
            with open(grabber_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.semantic_grabbers = data.get('semantic_grabbers', {})
                logger.info(f"✅ {len(self.semantic_grabbers)} Semantic Grabbers geladen")
        else:
            logger.warning("⚠️ Semantic Grabber Library nicht gefunden")

    def _load_custom_markers(self, yaml_path: Optional[str]):
        """Lade benutzerdefinierte Marker aus einer YAML-Datei"""
        if not yaml_path:
            return
        path = Path(yaml_path)
        if not path.exists():
            logger.warning(f"⚠️ Marker YAML nicht gefunden: {yaml_path}")
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                self.custom_markers = data.get('markers', {})
                logger.info(f"✅ {len(self.custom_markers)} benutzerdefinierte Marker geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden benutzerdefinierter Marker: {e}")
    
    def process_whatsapp_export(self, export_file: Path) -> Dict[str, Any]:
        """Verarbeite einen WhatsApp-Export"""
        logger.info(f"📱 Verarbeite WhatsApp-Export: {export_file}")
        
        messages = self._parse_whatsapp_export(export_file)
        
        for msg in messages:
            semantic_msg = self._create_semantic_message(msg)
            self.messages[semantic_msg.id] = semantic_msg
            
        return {"processed": len(messages)}
    
    def process_audio_transcripts(self, transcript_dir: Path) -> Dict[str, Any]:
        """Verarbeite Audio-Transkripte mit Emotionen"""
        logger.info(f"🎤 Verarbeite Audio-Transkripte aus: {transcript_dir}")
        
        processed = 0
        for transcript_file in transcript_dir.glob("*_emotion_transkript.md"):
            msg = self._parse_emotion_transcript(transcript_file)
            if msg:
                semantic_msg = self._create_semantic_message(msg)
                self.messages[semantic_msg.id] = semantic_msg
                processed += 1
                
        return {"processed": processed}
    
    def _parse_whatsapp_export(self, export_file: Path) -> List[Dict[str, Any]]:
        """Parse WhatsApp Export Format"""
        messages = []
        
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # WhatsApp Format: [DD.MM.YY, HH:MM:SS] Sender: Message
        pattern = r'\[(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2}:\d{2})\] ([^:]+): (.+?)(?=\[\d{2}\.\d{2}\.\d{2}|$)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            date_str, time_str, sender, message = match.groups()
            
            # Parse Timestamp
            timestamp = datetime.strptime(f"20{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            
            messages.append({
                'timestamp': timestamp,
                'sender': sender.strip(),
                'content': message.strip(),
                'type': 'text',
                'source': 'whatsapp'
            })
            
        logger.info(f"📝 {len(messages)} WhatsApp-Nachrichten geparst")
        return messages
    
    def _parse_emotion_transcript(self, transcript_file: Path) -> Optional[Dict[str, Any]]:
        """Parse Emotion-Transkript Format"""
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extrahiere Metadaten
            msg = {
                'type': 'audio',
                'source': 'whisper_v4',
                'file': transcript_file.name
            }
            
            # Timestamp
            timestamp_match = re.search(r'\*\*Aufnahme am:\*\* (.+)', content)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                # Parse verschiedene Formate
                for fmt in ['%d.%m.%Y um %H:%M:%S', '%d.%m.%Y um %H:%M']:
                    try:
                        msg['timestamp'] = datetime.strptime(timestamp_str, fmt)
                        break
                    except:
                        continue
                        
            # Sender
            sender_match = re.search(r'\*\*Chat mit:\*\* (.+)', content)
            if sender_match:
                msg['sender'] = sender_match.group(1)
                
            # Content
            content_match = re.search(r'## Transkription:\n\n(.+?)##', content, re.DOTALL)
            if content_match:
                msg['content'] = content_match.group(1).strip()
                
            # Emotion
            emotion_match = re.search(r'\*\*Dominante Emotion:\*\* (.+)', content)
            valence_match = re.search(r'\*\*Emotionale Valenz:\*\* ([\d.-]+)', content)
            
            msg['emotion'] = {
                'dominant': emotion_match.group(1) if emotion_match else 'neutral',
                'valence': float(valence_match.group(1)) if valence_match else 0.0
            }
            
            return msg
            
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {transcript_file}: {e}")
            return None
    
    def _create_semantic_message(self, msg_data: Dict[str, Any]) -> SemanticMessage:
        """Erstelle eine semantische Nachricht mit allen Analysen"""
        
        # Generiere ID
        content_preview = msg_data.get('content', '')[:50]
        timestamp = msg_data.get('timestamp', datetime.now())
        msg_id = hashlib.md5(
            f"{timestamp}{content_preview}".encode()
        ).hexdigest()[:12]
        
        # Basis-Message
        semantic_msg = SemanticMessage(
            id=msg_id,
            timestamp=timestamp,
            sender=msg_data.get('sender', 'unknown'),
            content=msg_data.get('content', ''),
            type=msg_data.get('type', 'text'),
            emotion=msg_data.get('emotion', {}),
            markers=[],
            semantic_scores={},
            metadata=msg_data.get('metadata', {})
        )
        
        # Führe Analysen durch
        if semantic_msg.content:
            # 1. Marker-Erkennung
            if self.marker_system or self.custom_markers:
                self._detect_markers(semantic_msg)
                
            # 2. Semantic Grabber Matching
            self._match_semantic_grabbers(semantic_msg)
            
            # 3. Emotionale Analyse (falls noch nicht vorhanden)
            if not semantic_msg.emotion:
                self._analyze_emotion(semantic_msg)
                
        return semantic_msg
    
    def _detect_markers(self, msg: SemanticMessage):
        """Erkenne Marker in der Nachricht"""
        try:
            # Nutze FRAUSAR zur Marker-Erkennung
            detected = []
            if self.marker_system:
                detected = self.marker_system.analyze_text_for_markers(msg.content)
                msg.markers.extend([m.get('name', '') for m in detected if m.get('name')])

            # Benutzerdefinierte Marker
            if self.custom_markers:
                text_lower = msg.content.lower()
                for name, patterns in self.custom_markers.items():
                    for pattern in patterns:
                        if pattern.lower() in text_lower:
                            msg.markers.append(name)
                            break

            logger.debug(f"🏷️ Erkannte Marker: {msg.markers}")
        except Exception as e:
            logger.error(f"Fehler bei Marker-Erkennung: {e}")
    
    def _match_semantic_grabbers(self, msg: SemanticMessage):
        """Matche gegen Semantic Grabbers"""
        for grabber_id, grabber_data in self.semantic_grabbers.items():
            patterns = grabber_data.get('patterns', [])
            matches = 0
            
            for pattern in patterns:
                if pattern.lower() in msg.content.lower():
                    matches += 1
                    
            if matches > 0:
                score = matches / len(patterns) if patterns else 0
                msg.semantic_scores[grabber_id] = score
    
    def _analyze_emotion(self, msg: SemanticMessage):
        """Analysiere Emotion (Fallback)"""
        # Einfache Sentiment-Analyse
        positive_words = ['freude', 'glücklich', 'toll', 'super', 'liebe']
        negative_words = ['traurig', 'schlecht', 'angst', 'wütend', 'einsam']
        
        text_lower = msg.content.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        valence = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        msg.emotion = {'valence': valence, 'method': 'fallback'}

    # ------------------------------------------------------------------
    # Neue Funktionen zur Verarbeitung von Bildern und kompletten Export-
    # Ordnern. Dadurch werden Text-, Audio- und Bilddateien gemeinsam
    # erkannt und verarbeitet.
    # ------------------------------------------------------------------

    def process_image_files(self, image_dir: Path) -> Dict[str, Any]:
        """Verarbeite alle Bilder in einem Ordner"""
        logger.info(f"🖼️  Verarbeite Bilder aus: {image_dir}")

        processed = 0
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.gif"):
            for image_file in image_dir.rglob(ext):
                msg = self._parse_image_file(image_file)
                if msg:
                    semantic_msg = self._create_semantic_message(msg)
                    self.messages[semantic_msg.id] = semantic_msg
                    processed += 1

        return {"processed": processed}

    def _parse_image_file(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Extrahiere Basisinformationen aus einem Bild"""
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(image_path)
            width, height = img.size
            brightness = sum(img.convert("L").getdata()) / (width * height * 255)

            ocr_text = ""
            try:
                ocr_text = pytesseract.image_to_string(img)
            except Exception as e:
                logger.warning(f"OCR fehlgeschlagen für {image_path.name}: {e}")

            return {
                'timestamp': datetime.fromtimestamp(image_path.stat().st_mtime),
                'sender': self._infer_sender_from_name(image_path.name),
                'content': ocr_text.strip() or '[Bild]',
                'type': 'image',
                'emotion': {'brightness': brightness},
                'metadata': {'file': image_path.name}
            }
        except Exception as e:
            logger.error(f"Fehler beim Analysieren von {image_path}: {e}")
            return None

    def _infer_sender_from_name(self, name: str) -> str:
        """Versuche, den Sender aus dem Dateinamen zu ermitteln"""
        match = re.search(r'(Ben|Zoe|Max|Anna|[A-Z][a-z]+)', name)
        return match.group(1) if match else 'unknown'

    def process_export_folder(self, export_path: Path) -> Dict[str, Any]:
        """Verarbeite einen kompletten Chat-Export-Ordner"""
        logger.info(f"📦 Verarbeite Export-Ordner: {export_path}")

        counts = {"text": 0, "audio": 0, "images": 0}

        for txt in export_path.rglob("*.txt"):
            res = self.process_whatsapp_export(txt)
            counts["text"] += res.get("processed", 0)

        for transcript_file in export_path.rglob("*_emotion_transkript.md"):
            msg = self._parse_emotion_transcript(transcript_file)
            if msg:
                semantic_msg = self._create_semantic_message(msg)
                self.messages[semantic_msg.id] = semantic_msg
                counts["audio"] += 1

        img_res = self.process_image_files(export_path)
        counts["images"] += img_res.get("processed", 0)

        logger.info(
            f"📊 Export verarbeitet: {counts['text']} Text, {counts['audio']} Audio, {counts['images']} Bilder"
        )
        return counts
    
    def analyze_relationships(self):
        """Analysiere Beziehungen zwischen Nachrichten"""
        logger.info("🔗 Analysiere semantische Beziehungen...")
        
        msg_list = sorted(self.messages.values(), key=lambda m: m.timestamp)
        
        for i in range(len(msg_list)):
            current = msg_list[i]
            
            # 1. Temporale Beziehungen
            if i > 0:
                prev = msg_list[i-1]
                time_diff = (current.timestamp - prev.timestamp).total_seconds()
                
                # Direkte Antwort (< 5 Minuten)
                if time_diff < 300:
                    self.relationships.append(SemanticRelationship(
                        from_id=prev.id,
                        to_id=current.id,
                        type='temporal',
                        strength=1.0 - (time_diff / 300),
                        reason=f"Direkte zeitliche Nähe ({time_diff:.0f}s)"
                    ))
            
            # 2. Thematische Beziehungen (gleiche Marker)
            for j in range(max(0, i-10), i):  # Schaue bis zu 10 Nachrichten zurück
                other = msg_list[j]
                common_markers = set(current.markers) & set(other.markers)
                
                if common_markers:
                    self.relationships.append(SemanticRelationship(
                        from_id=other.id,
                        to_id=current.id,
                        type='thematic',
                        strength=len(common_markers) / max(len(current.markers), 1),
                        reason=f"Gemeinsame Marker: {', '.join(common_markers)}"
                    ))
            
            # 3. Emotionale Beziehungen
            if i > 0 and current.emotion and prev.emotion:
                curr_val = current.emotion.get('valence', 0)
                prev_val = prev.emotion.get('valence', 0)
                
                # Starker emotionaler Wechsel
                emotion_diff = abs(curr_val - prev_val)
                if emotion_diff > 0.5:
                    self.relationships.append(SemanticRelationship(
                        from_id=prev.id,
                        to_id=current.id,
                        type='emotional',
                        strength=emotion_diff,
                        reason=f"Emotionaler Wechsel von {prev_val:.2f} zu {curr_val:.2f}"
                    ))
    
    def identify_semantic_threads(self):
        """Identifiziere semantische Fäden durch die Konversation"""
        logger.info("🧵 Identifiziere semantische Fäden...")
        
        # Gruppiere nach Markern
        for msg in self.messages.values():
            for marker in msg.markers:
                if marker not in self.semantic_threads:
                    self.semantic_threads[marker] = []
                self.semantic_threads[marker].append(msg.id)
        
        # Filtere kleine Threads
        self.semantic_threads = {
            k: v for k, v in self.semantic_threads.items() 
            if len(v) >= 3  # Mindestens 3 Nachrichten
        }
        
        logger.info(f"📊 {len(self.semantic_threads)} semantische Fäden identifiziert")
    
    def calculate_emotional_arc(self):
        """Berechne den emotionalen Verlauf"""
        logger.info("📈 Berechne emotionalen Verlauf...")
        
        # Sammle emotionale Datenpunkte
        timeline = []
        for msg in sorted(self.messages.values(), key=lambda m: m.timestamp):
            if msg.emotion and 'valence' in msg.emotion:
                timeline.append((msg.timestamp, msg.emotion['valence']))
        
        if not timeline:
            logger.warning("Keine emotionalen Daten gefunden")
            return
        
        # Finde Höhen und Tiefen
        valences = [v for _, v in timeline]
        peaks = []
        valleys = []
        turning_points = []
        
        for i in range(1, len(valences) - 1):
            # Lokales Maximum
            if valences[i] > valences[i-1] and valences[i] > valences[i+1]:
                peaks.append({
                    'index': i,
                    'timestamp': timeline[i][0],
                    'valence': valences[i],
                    'message_id': sorted(self.messages.values(), key=lambda m: m.timestamp)[i].id
                })
            
            # Lokales Minimum
            elif valences[i] < valences[i-1] and valences[i] < valences[i+1]:
                valleys.append({
                    'index': i,
                    'timestamp': timeline[i][0],
                    'valence': valences[i],
                    'message_id': sorted(self.messages.values(), key=lambda m: m.timestamp)[i].id
                })
            
            # Wendepunkt (große Änderung)
            if i > 0 and abs(valences[i] - valences[i-1]) > 0.5:
                turning_points.append({
                    'index': i,
                    'timestamp': timeline[i][0],
                    'change': valences[i] - valences[i-1],
                    'message_id': sorted(self.messages.values(), key=lambda m: m.timestamp)[i].id
                })
        
        # Bestimme Gesamt-Trend
        if len(valences) > 1:
            start_val = sum(valences[:3]) / 3  # Durchschnitt erste 3
            end_val = sum(valences[-3:]) / 3   # Durchschnitt letzte 3
            
            if end_val > start_val + 0.2:
                overall_trend = "rising_positive"
            elif end_val < start_val - 0.2:
                overall_trend = "falling_negative"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "insufficient_data"
        
        self.emotional_arc = EmotionalArc(
            timeline=timeline,
            peaks=peaks,
            valleys=valleys,
            turning_points=turning_points,
            overall_trend=overall_trend
        )
    
    def generate_super_semantic_file(self, output_path: Path) -> Dict[str, Any]:
        """Generiere die finale Super-Semantic-File"""
        logger.info("✨ Generiere Super-Semantic-File...")
        
        # Führe alle Analysen durch
        self.analyze_relationships()
        self.identify_semantic_threads()
        self.calculate_emotional_arc()
        
        # Erstelle Struktur
        super_semantic = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "3.0",
                "total_messages": len(self.messages),
                "time_span": {
                    "start": min(m.timestamp for m in self.messages.values()).isoformat() if self.messages else None,
                    "end": max(m.timestamp for m in self.messages.values()).isoformat() if self.messages else None
                },
                "components_used": {
                    "whisper_v4_emotion": True,
                    "frausar_markers": bool(self.marker_system),
                    "semantic_grabbers": len(self.semantic_grabbers) > 0,
                    "cosd_marsap": bool(self.cosd_analyzer)
                }
            },
            "messages": {
                msg_id: asdict(msg) for msg_id, msg in self.messages.items()
            },
            "relationships": [
                asdict(rel) for rel in self.relationships
            ],
            "semantic_threads": self.semantic_threads,
            "emotional_arc": asdict(self.emotional_arc) if self.emotional_arc else None,
            "analysis_summary": self._generate_summary()
        }
        
        # Speichere JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(super_semantic, f, indent=2, ensure_ascii=False, default=str)
        
        # Erstelle auch lesbare Zusammenfassung
        summary_path = output_path.with_suffix('.summary.md')
        self._create_readable_summary(super_semantic, summary_path)
        
        logger.info(f"✅ Super-Semantic-File erstellt: {output_path}")
        return super_semantic
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generiere Analyse-Zusammenfassung"""
        # Marker-Statistiken
        all_markers = []
        for msg in self.messages.values():
            all_markers.extend(msg.markers)
        
        marker_freq = {}
        for marker in all_markers:
            marker_freq[marker] = marker_freq.get(marker, 0) + 1
        
        # Emotionale Statistiken
        valences = [
            msg.emotion.get('valence', 0) 
            for msg in self.messages.values() 
            if msg.emotion
        ]
        
        return {
            "marker_statistics": {
                "total_markers_found": len(all_markers),
                "unique_markers": len(set(all_markers)),
                "top_markers": sorted(marker_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            "emotional_statistics": {
                "average_valence": sum(valences) / len(valences) if valences else 0,
                "emotional_range": {
                    "min": min(valences) if valences else 0,
                    "max": max(valences) if valences else 0
                },
                "emotional_volatility": sum(abs(valences[i] - valences[i-1]) for i in range(1, len(valences))) / len(valences) if len(valences) > 1 else 0
            },
            "relationship_statistics": {
                "total_relationships": len(self.relationships),
                "by_type": {
                    rel_type: len([r for r in self.relationships if r.type == rel_type])
                    for rel_type in set(r.type for r in self.relationships)
                }
            },
            "thread_statistics": {
                "total_threads": len(self.semantic_threads),
                "longest_thread": max((len(msgs), thread) for thread, msgs in self.semantic_threads.items())[1] if self.semantic_threads else None,
                "average_thread_length": sum(len(msgs) for msgs in self.semantic_threads.values()) / len(self.semantic_threads) if self.semantic_threads else 0
            }
        }
    
    def _create_readable_summary(self, data: Dict[str, Any], output_path: Path):
        """Erstelle lesbare Markdown-Zusammenfassung"""
        summary = f"""# 🌟 Super-Semantic Chat-Analyse

**Erstellt am:** {data['metadata']['created_at']}
**Nachrichten analysiert:** {data['metadata']['total_messages']}
**Zeitraum:** {data['metadata']['time_span']['start']} bis {data['metadata']['time_span']['end']}

## 🎭 Emotionaler Verlauf

**Gesamt-Trend:** {data['emotional_arc']['overall_trend'] if data['emotional_arc'] else 'Keine Daten'}
**Durchschnittliche Valenz:** {data['analysis_summary']['emotional_statistics']['average_valence']:.2f}
**Emotionale Volatilität:** {data['analysis_summary']['emotional_statistics']['emotional_volatility']:.2f}

### Emotionale Höhepunkte:
"""
        
        if data['emotional_arc'] and data['emotional_arc']['peaks']:
            for peak in data['emotional_arc']['peaks'][:3]:
                msg = data['messages'].get(peak['message_id'], {})
                summary += f"- **{peak['timestamp']}**: {msg.get('content', '')[:100]}... (Valenz: {peak['valence']:.2f})\n"
        
        summary += f"""

## 🏷️ Semantische Marker

**Gefundene Marker:** {data['analysis_summary']['marker_statistics']['total_markers_found']}
**Einzigartige Marker:** {data['analysis_summary']['marker_statistics']['unique_markers']}

### Top Marker:
"""
        
        for marker, count in data['analysis_summary']['marker_statistics']['top_markers'][:5]:
            summary += f"- **{marker}**: {count} mal\n"
        
        summary += f"""

## 🧵 Semantische Fäden

**Identifizierte Fäden:** {data['analysis_summary']['thread_statistics']['total_threads']}
**Längster Faden:** {data['analysis_summary']['thread_statistics']['longest_thread']}

## 🔗 Beziehungen

**Gesamt:** {data['analysis_summary']['relationship_statistics']['total_relationships']}
"""
        
        for rel_type, count in data['analysis_summary']['relationship_statistics']['by_type'].items():
            summary += f"- **{rel_type}**: {count} Verbindungen\n"
        
        summary += """

---
*Diese Analyse wurde mit dem Super Semantic Processor erstellt und zeigt die tiefe semantische Struktur der Konversation.*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)


# Hauptfunktion für einfache Verwendung
def process_everything(
    whatsapp_export: Optional[Path] = None,
    transcript_dir: Optional[Path] = None,
    export_folder: Optional[Path] = None,
    output_path: Path = Path("super_semantic_output.json")
) -> Dict[str, Any]:
    """Verarbeite alles und erstelle Super-Semantic-File"""
    
    processor = SuperSemanticProcessor()
    
    # Verarbeite Export-Ordner, falls angegeben
    if export_folder and export_folder.exists():
        processor.process_export_folder(export_folder)

    # Verarbeite WhatsApp-Export wenn vorhanden
    if whatsapp_export and whatsapp_export.exists():
        processor.process_whatsapp_export(whatsapp_export)

    # Verarbeite Transkripte wenn vorhanden
    if transcript_dir and transcript_dir.exists():
        processor.process_audio_transcripts(transcript_dir)
    
    # Generiere Output
    return processor.generate_super_semantic_file(output_path)


if __name__ == "__main__":
    # Demo-Verwendung
    logger.info("🚀 Starte Super Semantic Processor Demo...")
    
    result = process_everything(
        transcript_dir=Path("Transkripte_LLM"),
        output_path=Path("demo_super_semantic_complete.json")
    )
    
    logger.info("✨ Fertig! Magie vollbracht!") 
