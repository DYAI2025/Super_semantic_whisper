"""Utility to create the file structure for new persons.

The module can be imported or executed as a script. When run directly, one
or more person IDs may be supplied on the command line to create the
respective folders and update the central ``ben.yaml`` configuration.  The
location of the ``network`` directory can be customised via ``BASE_DIR`` or
by passing a ``base_dir`` argument to :func:`initialize_person`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import argparse

import yaml

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Default location for the ``network`` directory.  Tests may patch this
# constant to redirect file operations to a temporary location.
BASE_DIR = Path(__file__).resolve().parent / "network"


def get_person_yaml_template(person_id: str) -> Dict[str, Any]:
    """Return default YAML template for a person.

    Args:
        person_id: Cleaned identifier of the person.

    Returns:
        Dictionary containing the template structure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "person_id": person_id,
        "created_at": timestamp,
        "last_updated": timestamp,
        "perspectives": {
            "self_perspective": {},
            "ben_perspective": {},
        },
        "expression_energy": {
            "current_level": 0.5,
            "energy_type": "unknown",
        },
        "archetype": {
            "current": "unbekannt",
            "confidence": 0.0,
        },
        "evolution_timeline": [],
    }


def initialize_person(person_id: str, base_dir: Path | None = None) -> None:
    """Create folder structure and register a new person in ben.yaml.

    Args:
        person_id: Identifier of the person to initialize.
    """
    cleaned_id = person_id.strip().lower()
    base_path = base_dir or BASE_DIR
    person_path = base_path / cleaned_id
    transcripts_path = person_path / "transcripts"

    if person_path.exists():
        logger.warning(f"⚠️ Person '{cleaned_id}' existiert bereits: {person_path}")
        return

    logger.info(f"📁 Erstelle Ordner: {person_path}")
    transcripts_path.mkdir(parents=True, exist_ok=True)

    person_yaml = person_path / f"{cleaned_id}.yaml"
    logger.info(f"📝 Erstelle {person_yaml}")
    with person_yaml.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            get_person_yaml_template(cleaned_id),
            fh,
            allow_unicode=True,
            sort_keys=False,
        )

    ben_yaml_path = base_path / "ben" / "ben.yaml"
    if not ben_yaml_path.parent.exists():
        logger.info(f"📁 Erstelle zentralen Ordner: {ben_yaml_path.parent}")
        ben_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    if ben_yaml_path.exists():
        with ben_yaml_path.open("r", encoding="utf-8") as fh:
            ben_data = yaml.safe_load(fh) or {}
    else:
        ben_data = {}

    relationship_network = ben_data.get("relationship_network")
    if not isinstance(relationship_network, dict):
        relationship_network = {}
        ben_data["relationship_network"] = relationship_network

    if cleaned_id not in relationship_network:
        relationship_network[cleaned_id] = {
            "archetype_relationship": "unbekannt",
            "linked_since": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"🔗 Füge '{cleaned_id}' zum relationship_network hinzu")
    else:
        logger.info(f"ℹ️ '{cleaned_id}' ist bereits im relationship_network")

    with ben_yaml_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(ben_data, fh, allow_unicode=True, sort_keys=False)
        logger.info(f"💾 Aktualisiere {ben_yaml_path}")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Initialize persons in network")
    parser.add_argument(
        "person_ids",
        nargs="+",
        help="One or more identifiers of persons to create",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None, *, base_dir: Path | None = None) -> None:
    """Entry point used by the command line and tests."""
    args = parse_args(argv)
    for pid in args.person_ids:
        initialize_person(pid, base_dir=base_dir)


if __name__ == "__main__":
    main()
