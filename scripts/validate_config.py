#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config-Validierungs-Tool für Super Semantic Whisper

Validiert config.yaml gegen Schema und prüft Pfad-Existenz

Usage:
    python scripts/validate_config.py config.yaml
    python scripts/validate_config.py  # Nutzt default paths
"""

import sys
import yaml
from pathlib import Path

# Schema-Definition (JSON Schema compatible)
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "paths": {
            "type": "object",
            "properties": {
                "base_path": {"type": ["string", "null"]},
                "eingang": {"type": ["string", "null"]},
                "memory": {"type": ["string", "null"]},
                "output": {"type": ["string", "null"]},
                "google_drive": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "base_path": {"type": ["string", "null"]},
                        "timeout_seconds": {"type": "integer", "minimum": 1}
                    }
                },
                "local_fallback": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "base_path": {"type": "string"}
                    },
                    "required": ["enabled", "base_path"]
                }
            },
            "required": ["local_fallback"]
        },
        "audio": {
            "type": "object",
            "properties": {
                "whisper_model": {
                    "type": "string",
                    "enum": ["tiny", "base", "small", "medium", "large"]
                },
                "language": {
                    "type": "string",
                    "pattern": "^[a-z]{2}$"
                },
                "supported_formats": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "emotional_analysis": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "use_librosa": {"type": "boolean"},
                "use_textblob": {"type": "boolean"}
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                },
                "file": {"type": "string"},
                "format": {"type": "string"}
            }
        }
    },
    "required": ["paths"]
}


def validate_yaml_syntax(config_file: Path) -> tuple:
    """
    Validiert YAML-Syntax

    Returns:
        (bool, config_dict or error_message)
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return True, config
    except yaml.YAMLError as e:
        return False, f"YAML-Syntax-Fehler: {e}"
    except FileNotFoundError:
        return False, f"Datei nicht gefunden: {config_file}"
    except Exception as e:
        return False, f"Fehler beim Lesen: {e}"


def validate_schema(config: dict) -> tuple:
    """
    Validiert Config gegen Schema (simplifizierte Version ohne jsonschema)

    Returns:
        (bool, error_message or None)
    """
    errors = []

    # Prüfe required top-level keys
    if 'paths' not in config:
        errors.append("Fehlendes required field: 'paths'")

    # Prüfe paths.local_fallback
    if 'paths' in config:
        paths = config['paths']
        if 'local_fallback' not in paths:
            errors.append("Fehlendes required field: 'paths.local_fallback'")
        elif not isinstance(paths['local_fallback'], dict):
            errors.append("'paths.local_fallback' muss ein Objekt sein")
        else:
            lb = paths['local_fallback']
            if 'enabled' not in lb:
                errors.append("Fehlendes field: 'paths.local_fallback.enabled'")
            if 'base_path' not in lb:
                errors.append("Fehlendes field: 'paths.local_fallback.base_path'")

    # Prüfe audio.whisper_model
    if 'audio' in config and 'whisper_model' in config['audio']:
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        model = config['audio']['whisper_model']
        if model not in valid_models:
            errors.append(
                f"Ungültiges whisper_model: '{model}'. "
                f"Erlaubt: {', '.join(valid_models)}"
            )

    # Prüfe logging.level
    if 'logging' in config and 'level' in config['logging']:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level = config['logging']['level']
        if level not in valid_levels:
            errors.append(
                f"Ungültiges logging.level: '{level}'. "
                f"Erlaubt: {', '.join(valid_levels)}"
            )

    if errors:
        return False, "\n".join(f"  - {err}" for err in errors)
    return True, None


def check_paths(config: dict) -> list:
    """
    Prüfe ob konfigurierte Pfade existieren (Warnings, keine Errors)

    Returns:
        Liste von Warnungen
    """
    warnings = []

    if 'paths' not in config:
        return warnings

    paths = config['paths']

    # Prüfe base_path
    if paths.get('base_path'):
        base_path = Path(paths['base_path'])
        if not base_path.exists():
            warnings.append(f"Basis-Pfad existiert nicht: {base_path}")

    # Prüfe Google Drive
    if paths.get('google_drive', {}).get('enabled'):
        gd_path = paths['google_drive'].get('base_path')
        if gd_path:
            gd = Path(gd_path)
            if not gd.exists():
                warnings.append(f"Google Drive Pfad existiert nicht: {gd}")

    # Prüfe lokalen Fallback
    if paths.get('local_fallback', {}).get('enabled'):
        lb_path = Path(paths['local_fallback']['base_path'])
        if not lb_path.exists():
            warnings.append(
                f"Lokaler Fallback-Pfad existiert nicht: {lb_path} "
                f"(wird automatisch erstellt)"
            )

    return warnings


def validate_config(config_file: Path, verbose: bool = True) -> bool:
    """
    Vollständige Config-Validierung

    Args:
        config_file: Pfad zur config.yaml
        verbose: Ausgabe auf Console

    Returns:
        True wenn valid, False sonst
    """
    if verbose:
        print(f"🔍 Validiere: {config_file}")
        print()

    # 1. YAML-Syntax
    success, result = validate_yaml_syntax(config_file)
    if not success:
        if verbose:
            print(f"❌ YAML-SYNTAX-FEHLER:")
            print(f"   {result}")
        return False

    if verbose:
        print("✅ YAML-Syntax OK")

    config = result

    # 2. Schema-Validierung
    success, error = validate_schema(config)
    if not success:
        if verbose:
            print(f"❌ SCHEMA-VALIDIERUNG FEHLGESCHLAGEN:")
            print(error)
        return False

    if verbose:
        print("✅ Schema-Validierung OK")

    # 3. Pfad-Existenz (Warnings only)
    warnings = check_paths(config)
    if warnings:
        if verbose:
            print("⚠️  WARNUNGEN:")
            for warning in warnings:
                print(f"   - {warning}")
    else:
        if verbose:
            print("✅ Pfad-Prüfung OK (alle Pfade existieren)")

    if verbose:
        print()
        print("=" * 60)
        print("✅ KONFIGURATION VALIDE")
        print("=" * 60)

    return True


def main():
    """CLI Entry Point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validiert Super Semantic Whisper Konfigurationsdateien"
    )
    parser.add_argument(
        'config_file',
        nargs='?',
        default='config.yaml',
        help='Pfad zur config.yaml (default: config.yaml)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Keine Ausgabe (Exit-Code only)'
    )

    args = parser.parse_args()

    config_file = Path(args.config_file)

    if not config_file.exists():
        if not args.quiet:
            print(f"❌ Config-Datei nicht gefunden: {config_file}")
            print()
            print("Verfügbare Optionen:")
            print("  1. Erstelle config.yaml:")
            print("     cp config/default_config.yaml config.yaml")
            print()
            print("  2. Validiere System-Default:")
            print(f"     {sys.argv[0]} config/default_config.yaml")
        sys.exit(1)

    success = validate_config(config_file, verbose=not args.quiet)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
