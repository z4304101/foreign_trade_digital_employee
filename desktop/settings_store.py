import json
from dataclasses import asdict, fields
from pathlib import Path

from desktop.models import DesktopSettings


class SettingsStore:
    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = Path(path)

    def load(self) -> DesktopSettings:
        if not self.path.exists():
            return DesktopSettings()

        raw = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        allowed_fields = {
            field.name
            for field in fields(DesktopSettings)
        }

        filtered = {
            key: value
            for key, value in raw.items()
            if key in allowed_fields
        }

        return DesktopSettings(
            **filtered
        )

    def save(
        self,
        settings: DesktopSettings,
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = asdict(settings)

        tmp_path = self.path.with_suffix(
            ".tmp"
        )

        tmp_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        tmp_path.replace(
            self.path
        )
