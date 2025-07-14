import logging
import yaml
import initialize_person as ip

def test_successful_initialization(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    base_dir = tmp_path / "network"
    ip.initialize_person("clara", base_dir=base_dir)
    person_dir = base_dir / "clara"
    assert person_dir.exists()
    assert (person_dir / "transcripts").exists()
    assert (person_dir / "clara.yaml").exists()
    ben_file = base_dir / "ben" / "ben.yaml"
    assert ben_file.exists()
    with ben_file.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert "clara" in data.get("relationship_network", {})


def test_duplicate_person_warning(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    base_dir = tmp_path / "network"
    ip.initialize_person("bob", base_dir=base_dir)
    ip.initialize_person("bob", base_dir=base_dir)
    assert any("existiert bereits" in m for m in caplog.text.splitlines())


def test_input_sanitization(tmp_path):
    base_dir = tmp_path / "network"
    ip.initialize_person("  EVA  ", base_dir=base_dir)
    assert (base_dir / "eva").exists()


def test_multiple_person_creation(tmp_path):
    base_dir = tmp_path / "network"
    ip.main(["markus", "eva", "chloe"], base_dir=base_dir)
    for pid in ["markus", "eva", "chloe"]:
        assert (base_dir / pid).exists()
