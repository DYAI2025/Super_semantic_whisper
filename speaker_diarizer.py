#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speaker Diarizer - Sprechertrennung für therapeutische Transkription
Nutzt pyannote.audio für präzise Sprecher-Identifikation
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Versuche pyannote zu importieren
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logger.warning("pyannote.audio nicht installiert. Sprechertrennung deaktiviert.")


@dataclass
class SpeakerSegment:
    """Ein Segment mit Sprecher-Zuordnung"""
    start: float
    end: float
    speaker: str  # SPEAKER_00, SPEAKER_01, etc.
    role: Optional[str] = None  # "therapeut" oder "klient"
    text: Optional[str] = None


class SpeakerDiarizer:
    """Sprechertrennung mit pyannote.audio"""

    def __init__(self, hf_token: Optional[str] = None, device: str = "cpu"):
        """
        Initialisiere den Diarizer.

        Args:
            hf_token: HuggingFace Token für pyannote Modelle
            device: "cpu" oder "cuda"
        """
        self.pipeline = None
        self.device = device

        if not PYANNOTE_AVAILABLE:
            logger.error("pyannote.audio nicht verfügbar!")
            return

        try:
            # Lade pyannote Pipeline
            # Hinweis: Erfordert HuggingFace Account und Token-Akzeptanz
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )

            if device == "cuda":
                import torch
                if torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
                    logger.info("Pyannote läuft auf GPU")
                else:
                    logger.warning("CUDA nicht verfügbar, nutze CPU")

            logger.info("Pyannote Speaker Diarization Pipeline geladen")

        except Exception as e:
            logger.error(f"Fehler beim Laden der Pyannote Pipeline: {e}")
            logger.info("Tipp: HuggingFace Token benötigt. Setze HF_TOKEN Umgebungsvariable.")
            self.pipeline = None

    def diarize(self, audio_path: Path) -> List[SpeakerSegment]:
        """
        Führe Sprecherdiarisierung durch.

        Args:
            audio_path: Pfad zur Audio-Datei

        Returns:
            Liste von SpeakerSegment mit Start, Ende, Sprecher
        """
        if not self.pipeline:
            logger.warning("Pipeline nicht geladen - überspringe Diarisierung")
            return []

        try:
            logger.info(f"Diarisiere: {audio_path.name}")

            # Führe Diarisierung durch
            diarization = self.pipeline(str(audio_path))

            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker
                )
                segments.append(segment)

            logger.info(f"Gefunden: {len(segments)} Segmente, "
                       f"{len(set(s.speaker for s in segments))} Sprecher")

            return segments

        except Exception as e:
            logger.error(f"Diarisierung fehlgeschlagen: {e}")
            return []

    def assign_roles(
        self,
        segments: List[SpeakerSegment],
        first_speaker_is_therapist: bool = True
    ) -> List[SpeakerSegment]:
        """
        Weise Rollen zu (Therapeut/Klient).

        Args:
            segments: Liste von Segmenten
            first_speaker_is_therapist: Wenn True, ist der erste Sprecher der Therapeut

        Returns:
            Segmente mit zugewiesenen Rollen
        """
        if not segments:
            return segments

        # Finde alle einzigartigen Sprecher
        speakers = list(dict.fromkeys(s.speaker for s in segments))

        if len(speakers) == 0:
            return segments

        # Rolle zuweisen
        if first_speaker_is_therapist:
            role_map = {speakers[0]: "therapeut"}
            if len(speakers) > 1:
                role_map[speakers[1]] = "klient"
        else:
            # Alternativ: Sprecher mit mehr Redezeit = Klient
            speaking_time = {}
            for s in segments:
                speaking_time[s.speaker] = speaking_time.get(s.speaker, 0) + (s.end - s.start)

            sorted_speakers = sorted(speaking_time.items(), key=lambda x: x[1], reverse=True)
            role_map = {}
            if len(sorted_speakers) >= 1:
                role_map[sorted_speakers[0][0]] = "klient"  # Mehr Redezeit
            if len(sorted_speakers) >= 2:
                role_map[sorted_speakers[1][0]] = "therapeut"

        # Rollen auf Segmente anwenden
        for segment in segments:
            segment.role = role_map.get(segment.speaker, "unbekannt")

        return segments

    def merge_with_whisper_result(
        self,
        segments: List[SpeakerSegment],
        whisper_words: List[Dict],
    ) -> List[SpeakerSegment]:
        """
        Kombiniere Diarisierung mit Whisper Word-Timestamps.

        Args:
            segments: Diarisierungs-Segmente
            whisper_words: Whisper-Ergebnis mit word_timestamps
                          [{"word": "Hallo", "start": 0.0, "end": 0.5}, ...]

        Returns:
            Segmente mit zugeordnetem Text
        """
        if not segments or not whisper_words:
            return segments

        # Für jedes Diarisierungs-Segment: Finde passende Wörter
        for segment in segments:
            words_in_segment = []

            for word_info in whisper_words:
                word_start = word_info.get("start", 0)
                word_end = word_info.get("end", 0)
                word_mid = (word_start + word_end) / 2

                # Wort gehört zum Segment wenn Mittelpunkt darin liegt
                if segment.start <= word_mid <= segment.end:
                    words_in_segment.append(word_info.get("word", ""))

            segment.text = " ".join(words_in_segment).strip()

        return segments

    def get_speaker_statistics(self, segments: List[SpeakerSegment]) -> Dict:
        """
        Berechne Sprecher-Statistiken.

        Returns:
            Dict mit Redezeit, Anzahl Turns, etc. pro Sprecher
        """
        stats = {}

        for segment in segments:
            role = segment.role or segment.speaker

            if role not in stats:
                stats[role] = {
                    "speaking_time": 0.0,
                    "turn_count": 0,
                    "word_count": 0
                }

            stats[role]["speaking_time"] += segment.end - segment.start
            stats[role]["turn_count"] += 1
            if segment.text:
                stats[role]["word_count"] += len(segment.text.split())

        # Berechne Prozentanteile
        total_time = sum(s["speaking_time"] for s in stats.values())
        if total_time > 0:
            for role in stats:
                stats[role]["speaking_percentage"] = round(
                    stats[role]["speaking_time"] / total_time * 100, 1
                )

        return stats


def create_diarizer(hf_token: Optional[str] = None) -> Optional[SpeakerDiarizer]:
    """
    Factory-Funktion zum Erstellen eines Diarizers.

    Versucht Token aus Umgebungsvariable zu laden falls nicht angegeben.
    """
    import os

    token = hf_token or os.environ.get("HF_TOKEN")

    if not token:
        logger.warning(
            "Kein HuggingFace Token gefunden. "
            "Setze HF_TOKEN Umgebungsvariable oder übergebe hf_token Parameter."
        )

    diarizer = SpeakerDiarizer(hf_token=token)

    if diarizer.pipeline is None:
        return None

    return diarizer


# Standalone Test
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python speaker_diarizer.py <audio_file>")
        print("Setze HF_TOKEN Umgebungsvariable für pyannote Zugriff")
        sys.exit(1)

    audio_file = Path(sys.argv[1])

    if not audio_file.exists():
        print(f"Datei nicht gefunden: {audio_file}")
        sys.exit(1)

    diarizer = create_diarizer()

    if diarizer:
        segments = diarizer.diarize(audio_file)
        segments = diarizer.assign_roles(segments)

        print("\n=== Sprechersegmente ===")
        for seg in segments:
            print(f"[{seg.start:.1f}s - {seg.end:.1f}s] {seg.role}: {seg.text or '(kein Text)'}")

        print("\n=== Statistiken ===")
        stats = diarizer.get_speaker_statistics(segments)
        for role, data in stats.items():
            print(f"{role}: {data['speaking_time']:.1f}s ({data['speaking_percentage']}%), "
                  f"{data['turn_count']} Turns")
    else:
        print("Diarizer konnte nicht initialisiert werden")
