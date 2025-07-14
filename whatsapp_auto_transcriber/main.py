"""Entry point for the WhatsApp audio transcriber."""

from pathlib import Path
from src.config_manager import ConfigManager
from src.file_watcher import FileWatcher


def main():
    config_path = Path('config/config.yaml')
    manager = ConfigManager(config_path)
    config = manager.load()

    watcher = FileWatcher(config)
    watcher.start()


if __name__ == '__main__':
    main()
