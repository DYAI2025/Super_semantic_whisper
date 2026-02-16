#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcriber.py - MVP Audio-Transkription

Transkribiert Audio-Dateien aus Input/ mit Zeitstempel und Sprecherzuordnung.
Emotionsanalyse ist optional (--emotion).

Ordnerstruktur:
  Input/
    Speaker1/
      WhatsApp Audio 2025-06-29 at 13.20.58.opus
      00000249-AUDIO-2025-02-28-07-05-24.opus
    Speaker2/
      ...

  Output/
    2025-06/
      speaker1.2025-06-29_13-20.md
      speaker1.2025-06-29_13-20.json
    2025-02/
      speaker1.2025-02-28_07-05.md
      speaker1.2025-02-28_07-05.json

Nutzung:
  python3 transcriber.py                          # Standard-Transkription
  python3 transcriber.py --emotion                # Mit Emotionsanalyse
  python3 transcriber.py --input /pfad/input      # Eigener Input-Pfad
  python3 transcriber.py --output /pfad/output    # Eigener Output-Pfad
  python3 transcriber.py --model medium           # Groesseres Whisper-Modell
  python3 transcriber.py --language en            # Andere Sprache
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("transcriber.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unterstuetzte Audio-Formate
# ---------------------------------------------------------------------------
AUDIO_EXTENSIONS = {".opus", ".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"}

# ---------------------------------------------------------------------------
# Optionale Imports fuer Emotionsanalyse
# ---------------------------------------------------------------------------
LIBROSA_AVAILABLE = False
TEXTBLOB_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def _try_import_emotion_deps():
    """Importiere Emotions-Abhaengigkeiten nur wenn benoetigt."""
    global LIBROSA_AVAILABLE, TEXTBLOB_AVAILABLE
    try:
        import librosa  # noqa: F401
        LIBROSA_AVAILABLE = True
    except ImportError:
        logger.warning("librosa nicht installiert - Audio-Emotionsanalyse nicht verfuegbar")
    try:
        from textblob import TextBlob  # noqa: F401
        TEXTBLOB_AVAILABLE = True
    except ImportError:
        logger.warning("textblob nicht installiert - Text-Sentiment nicht verfuegbar")


# ============================================================================
# Zeitstempel-Extraktion
# ============================================================================

def extract_datetime_from_filename(filename: str) -> Optional[datetime]:
    """
    Extrahiere Aufnahme-Datum/Zeit aus Audio-Dateinamen.

    Unterstuetzte Formate:
      - WhatsApp Audio 2025-06-29 at 13.20.58.opus
      - 00000249-AUDIO-2025-02-28-07-05-24.opus
      - 2025-06-29_13-20-58.opus  (generisch)

    Returns:
        datetime oder None wenn nicht erkannt.
    """
    # Pattern 1: WhatsApp Standard
    m = re.search(
        r"WhatsApp (?:Audio|Video|Ptt) (\d{4})-(\d{2})-(\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})",
        filename,
    )
    if m:
        try:
            return datetime(*[int(x) for x in m.groups()])
        except ValueError:
            pass

    # Pattern 2: Nummerierte AUDIO-Dateien (XXXXXXXX-AUDIO-YYYY-MM-DD-HH-MM-SS)
    m = re.search(
        r"\d+-AUDIO-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})",
        filename,
    )
    if m:
        try:
            return datetime(*[int(x) for x in m.groups()])
        except ValueError:
            pass

    # Pattern 3: Generisch YYYY-MM-DD_HH-MM-SS oder YYYY-MM-DD_HH-MM
    m = re.search(
        r"(\d{4})-(\d{2})-(\d{2})[_T](\d{2})-(\d{2})(?:-(\d{2}))?",
        filename,
    )
    if m:
        parts = [int(x) if x else 0 for x in m.groups()]
        try:
            return datetime(*parts)
        except ValueError:
            pass

    return None


def extract_datetime_from_file(filepath: Path) -> Optional[datetime]:
    """
    Extrahiere Datum aus Dateinamen, Fallback auf Datei-Modifikationszeit.
    """
    dt = extract_datetime_from_filename(filepath.name)
    if dt:
        return dt

    # Fallback: Datei-Modifikationszeit
    try:
        mtime = filepath.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        logger.warning(f"Kein Datum im Dateinamen '{filepath.name}' - nutze Dateizeit: {dt}")
        return dt
    except OSError:
        return None


# ============================================================================
# Speaker-Erkennung
# ============================================================================

def detect_speaker(filepath: Path, input_dir: Path) -> str:
    """
    Erkenne Sprecher aus Ordnerstruktur.

    Erwartet: Input/SpeakerName/datei.opus
    -> Speaker = SpeakerName (kleingeschrieben)

    Falls Datei direkt in Input/ liegt -> "unbekannt"
    """
    try:
        relative = filepath.relative_to(input_dir)
        parts = relative.parts
        if len(parts) > 1:
            # Ordnername = Sprechername
            return parts[0].lower().strip()
    except ValueError:
        pass

    return "unbekannt"


# ============================================================================
# Whisper-Transkription
# ============================================================================

def find_whisper_command() -> Optional[str]:
    """Finde verfuegbare Whisper-Installation."""
    candidates = ["whisper", "python3 -m whisper", "python -m whisper"]
    for cmd in candidates:
        try:
            result = subprocess.run(
                cmd.split() + ["--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return cmd
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def transcribe_audio(
    audio_path: Path,
    whisper_cmd: str,
    model: str = "base",
    language: str = "de",
) -> Optional[str]:
    """
    Transkribiere eine Audio-Datei mit Whisper.

    Returns:
        Transkriptions-Text oder None bei Fehler.
    """
    try:
        # Whisper in temporaeres Verzeichnis ausgeben lassen
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd_parts = whisper_cmd.split() + [
                str(audio_path),
                "--language", language,
                "--model", model,
                "--output_format", "txt",
                "--output_dir", tmpdir,
            ]

            logger.debug(f"Whisper-Kommando: {' '.join(cmd_parts)}")

            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=600,  # 10 Minuten max
            )

            if result.returncode != 0:
                logger.error(f"Whisper-Fehler fuer {audio_path.name}: {result.stderr[:500]}")
                return None

            # Finde die generierte .txt Datei
            txt_files = list(Path(tmpdir).glob("*.txt"))
            if txt_files:
                return txt_files[0].read_text(encoding="utf-8").strip()

            logger.error(f"Keine Whisper-Ausgabe fuer {audio_path.name}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"Whisper-Timeout fuer {audio_path.name}")
        return None
    except Exception as e:
        logger.error(f"Transkriptions-Fehler fuer {audio_path.name}: {e}")
        return None


# ============================================================================
# Emotionsanalyse (optional)
# ============================================================================

def analyze_emotion(audio_path: Path, text: str) -> Optional[Dict]:
    """
    Optionale Emotionsanalyse. Nur ausgefuehrt wenn --emotion gesetzt.

    Returns:
        Dict mit Emotionsdaten oder None.
    """
    result = {}

    # Audio-Features via librosa
    if LIBROSA_AVAILABLE and NUMPY_AVAILABLE:
        try:
            import librosa
            y, sr = librosa.load(str(audio_path), sr=22050)

            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            rms = librosa.feature.rms(y=y)[0]
            spectral = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

            result["audio"] = {
                "tempo_bpm": round(float(tempo), 1),
                "energy_mean": round(float(np.mean(rms)), 4),
                "energy_std": round(float(np.std(rms)), 4),
                "spectral_centroid_mean": round(float(np.mean(spectral)), 1),
            }

            # Heuristik-Klassifikation
            energy = float(np.mean(rms))
            t = float(tempo)
            sc = float(np.mean(spectral))

            if energy > 0.1 and t > 130:
                result["audio_emotion"] = "wuetend_rebellisch" if sc > 2000 else "begeistert_enthusiastisch"
            elif energy < 0.05:
                result["audio_emotion"] = "traurig_reflektierend" if t < 100 else "sehnsuchtsvoll_still"
            elif t > 100:
                result["audio_emotion"] = "neugierig_forschend"
            else:
                result["audio_emotion"] = "hoffnungsvoll_antreibend"

        except Exception as e:
            logger.warning(f"Audio-Emotionsanalyse fehlgeschlagen: {e}")

    # Text-Sentiment via TextBlob
    if TEXTBLOB_AVAILABLE and text:
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            result["text"] = {
                "polarity": round(blob.sentiment.polarity, 3),
                "subjectivity": round(blob.sentiment.subjectivity, 3),
            }
        except Exception as e:
            logger.warning(f"Text-Sentiment fehlgeschlagen: {e}")

    return result if result else None


# ============================================================================
# Output-Generierung
# ============================================================================

def build_output_md(
    speaker: str,
    recording_dt: datetime,
    transcription: str,
    audio_filename: str,
    emotion: Optional[Dict] = None,
) -> str:
    """Erzeuge Markdown-Output fuer eine einzelne Nachricht."""
    date_str = recording_dt.strftime("%Y-%m-%d")
    time_str = recording_dt.strftime("%H:%M")
    processed_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Transkription",
        f"",
        f"Nachricht vom: {date_str} time: {time_str}",
        f"Speaker: {speaker}",
        f"Quelldatei: {audio_filename}",
        f"Transkribiert am: {processed_str}",
        f"",
        f"---",
        f"",
        f"## Transkription",
        f"",
        transcription,
    ]

    if emotion:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Emotionsanalyse")
        lines.append("")
        if "audio_emotion" in emotion:
            lines.append(f"Audio-Emotion: {emotion['audio_emotion']}")
        if "audio" in emotion:
            a = emotion["audio"]
            lines.append(f"Tempo: {a.get('tempo_bpm', '?')} BPM")
            lines.append(f"Energie: {a.get('energy_mean', '?')}")
            lines.append(f"Spectral Centroid: {a.get('spectral_centroid_mean', '?')}")
        if "text" in emotion:
            t = emotion["text"]
            lines.append(f"Text-Polarity: {t.get('polarity', '?')} (-1 negativ, +1 positiv)")
            lines.append(f"Text-Subjectivity: {t.get('subjectivity', '?')} (0 objektiv, 1 subjektiv)")

    return "\n".join(lines) + "\n"


def build_output_json(
    speaker: str,
    recording_dt: datetime,
    transcription: str,
    audio_filename: str,
    emotion: Optional[Dict] = None,
) -> Dict:
    """Erzeuge JSON-Output fuer eine einzelne Nachricht."""
    data = {
        "nachricht_vom": recording_dt.strftime("%Y-%m-%d"),
        "time": recording_dt.strftime("%H:%M"),
        "timestamp_iso": recording_dt.isoformat(),
        "speaker": speaker,
        "transcription": transcription,
        "source_file": audio_filename,
        "processed_at": datetime.now().isoformat(),
    }

    if emotion:
        data["emotion"] = emotion

    return data


def output_filename_base(speaker: str, recording_dt: datetime) -> str:
    """
    Erzeuge Basis-Dateiname: speaker.yyyy-mm-dd_hh-mm

    Doppelpunkte im Dateinamen werden durch Bindestriche ersetzt
    (Kompatibilitaet mit allen Betriebssystemen).
    """
    return f"{speaker}.{recording_dt.strftime('%Y-%m-%d_%H-%M')}"


def output_month_dir(recording_dt: datetime) -> str:
    """Erzeuge Monats-Ordnernamen: yyyy-mm"""
    return recording_dt.strftime("%Y-%m")


# ============================================================================
# Audio-Dateien sammeln
# ============================================================================

def collect_audio_files(input_dir: Path) -> List[Path]:
    """Sammle alle Audio-Dateien aus Input-Verzeichnis (rekursiv)."""
    files = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(input_dir.rglob(f"*{ext}"))
    return sorted(files)


# ============================================================================
# Hauptverarbeitung
# ============================================================================

def process_all(
    input_dir: Path,
    output_dir: Path,
    model: str = "base",
    language: str = "de",
    with_emotion: bool = False,
) -> Dict:
    """
    Verarbeite alle Audio-Dateien aus input_dir.

    Returns:
        Statistik-Dict mit processed, skipped, errors.
    """
    # Sicherstellen dass Verzeichnisse existieren
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Whisper finden
    whisper_cmd = find_whisper_command()
    if not whisper_cmd:
        logger.error(
            "Whisper nicht gefunden. Installation: pip install openai-whisper"
        )
        sys.exit(1)
    logger.info(f"Whisper gefunden: {whisper_cmd}")

    # Emotions-Deps nur laden wenn noetig
    if with_emotion:
        _try_import_emotion_deps()
        if not LIBROSA_AVAILABLE and not TEXTBLOB_AVAILABLE:
            logger.warning("Keine Emotions-Bibliotheken verfuegbar - Emotionsanalyse deaktiviert")
            with_emotion = False

    # Audio-Dateien sammeln
    audio_files = collect_audio_files(input_dir)
    total = len(audio_files)
    logger.info(f"Gefunden: {total} Audio-Dateien in {input_dir}")

    if total == 0:
        logger.info(f"Keine Audio-Dateien in {input_dir} gefunden.")
        logger.info(f"Lege Audio-Dateien in Unterordnern ab: {input_dir}/<Speaker>/<audio>.opus")
        return {"processed": 0, "skipped": 0, "errors": 0}

    stats = {"processed": 0, "skipped": 0, "errors": 0}

    for i, audio_file in enumerate(audio_files, 1):
        try:
            # 1. Zeitstempel extrahieren
            recording_dt = extract_datetime_from_file(audio_file)
            if not recording_dt:
                logger.error(f"Kein Zeitstempel fuer {audio_file.name} - uebersprungen")
                stats["errors"] += 1
                continue

            # 2. Speaker erkennen
            speaker = detect_speaker(audio_file, input_dir)

            # 3. Output-Pfade berechnen
            month_dir = output_dir / output_month_dir(recording_dt)
            month_dir.mkdir(parents=True, exist_ok=True)

            base_name = output_filename_base(speaker, recording_dt)
            md_path = month_dir / f"{base_name}.md"
            json_path = month_dir / f"{base_name}.json"

            # 4. Bereits verarbeitet?
            if md_path.exists() and json_path.exists():
                logger.info(f"[{i}/{total}] Bereits vorhanden: {base_name} - uebersprungen")
                stats["skipped"] += 1
                continue

            logger.info(
                f"[{i}/{total}] Verarbeite: {audio_file.name} "
                f"(Speaker: {speaker}, Datum: {recording_dt.strftime('%Y-%m-%d %H:%M')})"
            )

            # 5. Transkribieren
            transcription = transcribe_audio(audio_file, whisper_cmd, model, language)
            if not transcription:
                logger.error(f"Transkription fehlgeschlagen: {audio_file.name}")
                stats["errors"] += 1
                continue

            # 6. Optionale Emotionsanalyse
            emotion = None
            if with_emotion:
                emotion = analyze_emotion(audio_file, transcription)

            # 7. Output schreiben
            md_content = build_output_md(
                speaker, recording_dt, transcription, audio_file.name, emotion
            )
            json_content = build_output_json(
                speaker, recording_dt, transcription, audio_file.name, emotion
            )

            md_path.write_text(md_content, encoding="utf-8")
            json_path.write_text(
                json.dumps(json_content, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            stats["processed"] += 1
            logger.info(
                f"[{i}/{total}] Gespeichert: {month_dir.name}/{base_name}.md/.json"
            )

        except Exception as e:
            logger.error(f"Fehler bei {audio_file.name}: {e}")
            stats["errors"] += 1
            continue

    return stats


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="MVP Audio-Transkription mit Zeitstempel und Sprecherzuordnung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 transcriber.py
  python3 transcriber.py --emotion
  python3 transcriber.py --input ./MeineAudios --output ./MeineTranskripte
  python3 transcriber.py --model medium --language en

Ordnerstruktur:
  Input/Speaker/datei.opus  ->  Output/yyyy-mm/speaker.yyyy-mm-dd_hh-mm.md
                                Output/yyyy-mm/speaker.yyyy-mm-dd_hh-mm.json
        """,
    )
    parser.add_argument(
        "--input", type=str, default="./Input",
        help="Input-Verzeichnis mit Audio-Dateien (Default: ./Input)",
    )
    parser.add_argument(
        "--output", type=str, default="./Output",
        help="Output-Verzeichnis fuer Transkripte (Default: ./Output)",
    )
    parser.add_argument(
        "--model", type=str, default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper-Modell (Default: base)",
    )
    parser.add_argument(
        "--language", type=str, default="de",
        help="Sprache fuer Transkription (Default: de)",
    )
    parser.add_argument(
        "--emotion", action="store_true",
        help="Emotionsanalyse aktivieren (optional, benoetigt librosa/textblob)",
    )

    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    print("=" * 60)
    print("  Audio-Transkription MVP")
    print("=" * 60)
    print(f"  Input:    {input_dir}")
    print(f"  Output:   {output_dir}")
    print(f"  Modell:   {args.model}")
    print(f"  Sprache:  {args.language}")
    print(f"  Emotion:  {'Ja' if args.emotion else 'Nein'}")
    print("=" * 60)
    print()

    # Input-Ordner erstellen falls nicht vorhanden
    input_dir.mkdir(parents=True, exist_ok=True)

    stats = process_all(
        input_dir=input_dir,
        output_dir=output_dir,
        model=args.model,
        language=args.language,
        with_emotion=args.emotion,
    )

    print()
    print("=" * 60)
    print(f"  Ergebnis:")
    print(f"  Verarbeitet: {stats['processed']}")
    print(f"  Uebersprungen: {stats['skipped']}")
    print(f"  Fehler: {stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
