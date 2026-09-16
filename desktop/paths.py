from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path


APP_NAME = "ForeignTradeDigitalEmployee"
APP_AUTHOR = "ForeignTradeDigitalEmployee"


@dataclass(frozen=True)
class DesktopPaths:
    root: Path
    settings_file: Path
    pin_file: Path
    history_db: Path
    processed_store: Path
    result_dir: Path
    log_dir: Path
    backup_dir: Path

    @classmethod
    def from_root(
        cls,
        root: Path,
    ) -> "DesktopPaths":
        return cls(
            root=root,
            settings_file=root / "settings.json",
            pin_file=root / "admin_pin.json",
            history_db=root / "history_learning.db",
            processed_store=(
                root / "processed_message_ids.txt"
            ),
            result_dir=root / "result",
            log_dir=root / "logs",
            backup_dir=root / "backups",
        )

    @classmethod
    def for_current_user(
        cls,
    ) -> "DesktopPaths":
        root = Path(
            user_data_path(
                APP_NAME,
                APP_AUTHOR,
            )
        )

        return cls.from_root(root)

    def ensure(self) -> None:
        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.result_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.backup_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
