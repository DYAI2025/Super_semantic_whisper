#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Konfigurationsverwaltung für Super Semantic Whisper

Lädt Konfiguration aus mehreren Quellen (Priorität absteigend):
1. Command-Line-Argumente (explizite Parameter)
2. Umgebungsvariablen
3. config.yaml (User-spezifisch)
4. config/default_config.yaml (System-Default)
5. Hardcoded Fallback
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import warnings

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Verwaltet zentrale Konfiguration mit Multi-Source-Unterstützung

    Beispiel:
        >>> config = ConfigManager()
        >>> base_path = config.get_path('base')
        >>> print(base_path)
        ./whisper_speaker_matcher

        >>> # Mit Umgebungsvariable
        >>> os.environ['WHISPER_BASE_PATH'] = '/data/whisper'
        >>> config = ConfigManager()
        >>> print(config.get_path('base'))
        /data/whisper
    """

    DEFAULT_CONFIG_PATHS = [
        Path("config.yaml"),  # User Config (höchste Priorität)
        Path("config/config.yaml"),
        Path("config/default_config.yaml"),  # System Default
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialisiert ConfigManager

        Args:
            config_path: Expliziter Pfad zur Config-Datei (optional)
        """
        self.config: Dict[str, Any] = {}
        self.config_path = config_path
        self._load_config()
        self._apply_env_overrides()

    def _load_config(self):
        """Lade Konfiguration aus YAML-Datei"""
        config_files = [self.config_path] if self.config_path else self.DEFAULT_CONFIG_PATHS

        for config_file in config_files:
            if config_file and config_file.exists():
                logger.info(f"📄 Lade Konfiguration: {config_file}")
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.config = yaml.safe_load(f) or {}

                    # Validiere Permissions
                    self._validate_permissions(config_file)

                    return
                except yaml.YAMLError as e:
                    logger.error(f"❌ YAML-Fehler in {config_file}: {e}")
                    logger.warning("Versuche nächste Konfigurationsdatei...")
                    continue

        logger.warning("⚠️ Keine Konfigurationsdatei gefunden. Verwende Defaults.")
        self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Hardcoded Fallback-Konfiguration wenn keine Datei verfügbar"""
        return {
            'paths': {
                'base_path': None,
                'local_fallback': {
                    'enabled': True,
                    'base_path': './whisper_speaker_matcher'
                }
            },
            'audio': {
                'whisper_model': 'base',
                'language': 'de',
                'supported_formats': ['.opus', '.wav', '.mp3', '.m4a', '.ogg']
            },
            'emotional_analysis': {
                'enabled': True,
                'use_librosa': True,
                'use_textblob': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'transcription.log',
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            }
        }

    def _apply_env_overrides(self):
        """Überschreibe Config mit Umgebungsvariablen"""
        env_mappings = {
            'WHISPER_BASE_PATH': ('paths', 'base_path'),
            'WHISPER_EINGANG': ('paths', 'eingang'),
            'WHISPER_MEMORY': ('paths', 'memory'),
            'WHISPER_OUTPUT': ('paths', 'output'),
            'WHISPER_MODEL': ('audio', 'whisper_model'),
            'WHISPER_LANGUAGE': ('audio', 'language'),
            'LOG_LEVEL': ('logging', 'level'),
            'LOG_FILE': ('logging', 'file'),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                logger.info(f"🔧 Umgebungsvariable {env_var} überschreibt {section}.{key}")
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value

    def _validate_permissions(self, config_file: Path):
        """
        Prüfe Config-File-Permissions aus Sicherheitsgründen

        Warnt wenn Datei für Gruppe/Andere lesbar ist (könnte Secrets enthalten)
        """
        if not config_file.exists():
            return

        try:
            mode = config_file.stat().st_mode
            # Prüfe ob Gruppe (070) oder Andere (007) Rechte haben
            if mode & 0o077:
                warnings.warn(
                    f"⚠️ SICHERHEITSWARNUNG: {config_file} hat unsichere Permissions ({oct(mode)}). "
                    f"Empfohlen: chmod 600 {config_file}",
                    category=SecurityWarning
                )
        except Exception as e:
            logger.debug(f"Konnte Permissions nicht prüfen: {e}")

    def _validate_path_safety(self, path: Path) -> Path:
        """
        Validiere Pfad gegen Injection-Angriffe

        Args:
            path: Zu validierender Pfad

        Returns:
            Sicherer, aufgelöster Pfad

        Raises:
            ValueError: Bei gefährlichen Zeichen im Pfad
        """
        path_str = str(path)

        # Prüfe auf Shell-Meta-Zeichen (Command Injection)
        dangerous_chars = [';', '|', '&', '$', '`', '\n', '\r', '<', '>']
        for char in dangerous_chars:
            if char in path_str:
                raise ValueError(
                    f"❌ Gefährliche Zeichen in Pfad: {path_str!r} "
                    f"(enthält {char!r})"
                )

        # Resolve symlinks (verhindert Directory Traversal)
        try:
            resolved = path.resolve()
        except Exception as e:
            logger.warning(f"Konnte Pfad nicht auflösen: {path} - {e}")
            resolved = path

        return resolved

    def get(self, *keys, default=None):
        """
        Zugriff auf verschachtelte Config-Werte

        Args:
            *keys: Verschachtelte Keys (z.B. 'paths', 'base_path')
            default: Rückgabewert wenn Key nicht existiert

        Returns:
            Config-Wert oder default

        Beispiel:
            >>> config.get('paths', 'base_path')
            '/data/whisper'
            >>> config.get('paths', 'not_exists', default='/fallback')
            '/fallback'
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    def get_path(self, path_type: str) -> Path:
        """
        Hole Pfad mit Auto-Detection und Fallback

        Priorität:
        1. Expliziter Pfad (paths.<type>)
        2. Base-Path + Unterordner
        3. Google Drive (falls enabled)
        4. Lokaler Fallback
        5. Aktuelles Verzeichnis

        Args:
            path_type: Typ des Pfades ('base', 'eingang', 'memory', 'output')

        Returns:
            Validierter Path-Objekt

        Beispiel:
            >>> config.get_path('eingang')
            PosixPath('/data/whisper/Eingang')
        """
        # 1. Expliziter Pfad
        explicit_path = self.get('paths', path_type)
        if explicit_path:
            path = Path(explicit_path)
            return self._validate_path_safety(path)

        # 2. Base-Path + Unterordner
        base_path = self.get('paths', 'base_path')
        if base_path:
            base = Path(base_path)
            sub_path = self._get_sub_path(base, path_type)
            return self._validate_path_safety(sub_path)

        # 3. Google Drive (falls aktiviert)
        if self.get('paths', 'google_drive', 'enabled'):
            gd_base = self.get('paths', 'google_drive', 'base_path')
            if gd_base:
                gd_path = Path(gd_base)
                if gd_path.exists():
                    logger.info(f"☁️  Nutze Google Drive Pfad: {gd_path}")
                    sub_path = self._get_sub_path(gd_path, path_type)
                    return self._validate_path_safety(sub_path)
                else:
                    logger.warning(f"⚠️ Google Drive Pfad existiert nicht: {gd_path}")

        # 4. Lokaler Fallback
        if self.get('paths', 'local_fallback', 'enabled'):
            fallback_base = Path(self.get(
                'paths', 'local_fallback', 'base_path',
                default='./whisper_speaker_matcher'
            ))
            logger.info(f"💾 Nutze lokalen Fallback: {fallback_base}")
            sub_path = self._get_sub_path(fallback_base, path_type)
            return self._validate_path_safety(sub_path)

        # 5. Letzter Fallback: Aktuelles Verzeichnis
        logger.warning("⚠️ Keine konfigurierten Pfade gefunden, nutze aktuelles Verzeichnis")
        cwd = Path.cwd()
        sub_path = self._get_sub_path(cwd, path_type)
        return self._validate_path_safety(sub_path)

    def _get_sub_path(self, base: Path, path_type: str) -> Path:
        """
        Berechne Unterordner basierend auf path_type

        Args:
            base: Basis-Pfad
            path_type: Typ ('base', 'eingang', 'memory', 'output')

        Returns:
            Vollständiger Pfad
        """
        if path_type == 'base':
            return base
        elif path_type == 'eingang':
            return base / 'Eingang'
        elif path_type == 'memory':
            return base / 'Memory'
        elif path_type == 'output':
            return base / 'Transkripte_LLM'
        else:
            logger.warning(f"Unbekannter path_type: {path_type}, nutze base")
            return base

    def show_effective_config(self):
        """
        Zeige effektive Konfiguration (für Debugging)

        Gibt aktuelle Config mit allen Overrides aus
        """
        print("=" * 60)
        print("📋 EFFEKTIVE KONFIGURATION")
        print("=" * 60)

        if self.config_path and self.config_path.exists():
            print(f"Geladene Datei: {self.config_path}")
        else:
            for path in self.DEFAULT_CONFIG_PATHS:
                if path.exists():
                    print(f"Geladene Datei: {path}")
                    break
            else:
                print("Geladene Datei: <Hardcoded Defaults>")

        print("\nUmgebungsvariablen-Overrides:")
        env_vars = ['WHISPER_BASE_PATH', 'WHISPER_EINGANG', 'WHISPER_MEMORY',
                    'WHISPER_OUTPUT', 'WHISPER_MODEL', 'WHISPER_LANGUAGE']
        any_env = False
        for var in env_vars:
            value = os.getenv(var)
            if value:
                print(f"  {var}={value}")
                any_env = True
        if not any_env:
            print("  <keine>")

        print("\nEffektive Pfade:")
        for path_type in ['base', 'eingang', 'memory', 'output']:
            path = self.get_path(path_type)
            exists = "✓" if path.exists() else "✗"
            print(f"  {path_type:8} [{exists}] {path}")

        print("\nAudio-Konfiguration:")
        print(f"  Modell: {self.get('audio', 'whisper_model', default='base')}")
        print(f"  Sprache: {self.get('audio', 'language', default='de')}")

        print("\nEmotionale Analyse:")
        print(f"  Aktiviert: {self.get('emotional_analysis', 'enabled', default=True)}")
        print(f"  Librosa: {self.get('emotional_analysis', 'use_librosa', default=True)}")
        print(f"  TextBlob: {self.get('emotional_analysis', 'use_textblob', default=True)}")

        print("=" * 60)


# Hilfs-Funktion für CLI
def show_config_cli():
    """CLI-Wrapper für show_effective_config"""
    import sys

    config_file = None
    if len(sys.argv) > 2 and sys.argv[1] == '--config':
        config_file = Path(sys.argv[2])

    config = ConfigManager(config_file)
    config.show_effective_config()


if __name__ == '__main__':
    # Test-Modus
    print("🧪 ConfigManager Test-Modus\n")

    config = ConfigManager()
    config.show_effective_config()

    print("\n🧪 Test: Path-Injection-Schutz")
    try:
        config._validate_path_safety(Path("; rm -rf /"))
        print("❌ FEHLER: Injection nicht erkannt!")
    except ValueError as e:
        print(f"✅ Injection erkannt: {e}")
