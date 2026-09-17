import plistlib
import shlex
import sys
from pathlib import Path
from typing import Protocol


MAC_LABEL = (
    "com.foreigntrade.digitalemployee"
)

WINDOWS_VALUE_NAME = (
    "ForeignTradeDigitalEmployee"
)

WINDOWS_RUN_KEY = (
    r"Software\Microsoft\Windows"
    r"\CurrentVersion\Run"
)


class AutostartAdapter(Protocol):
    def enable(
        self,
        command: str,
    ) -> None:
        ...

    def disable(
        self,
    ) -> None:
        ...

    def is_enabled(
        self,
    ) -> bool:
        ...


class MacOSAutostartAdapter:
    def __init__(
        self,
        *,
        plist_path: Path
        | None = None,
    ) -> None:
        self.plist_path = (
            Path(plist_path)
            if plist_path is not None
            else (
                Path.home()
                / "Library"
                / "LaunchAgents"
                / (
                    MAC_LABEL
                    + ".plist"
                )
            )
        )

    def enable(
        self,
        command: str,
    ) -> None:
        arguments = shlex.split(
            command
        )

        if not arguments:
            raise ValueError(
                "autostart command is empty"
            )

        payload = {
            "Label": MAC_LABEL,
            "ProgramArguments": (
                arguments
            ),
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        self.plist_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.plist_path.write_bytes(
            plistlib.dumps(
                payload
            )
        )

    def disable(
        self,
    ) -> None:
        try:
            self.plist_path.unlink()

        except FileNotFoundError:
            pass

    def is_enabled(
        self,
    ) -> bool:
        return (
            self.plist_path.exists()
        )


class WindowsAutostartAdapter:
    def __init__(
        self,
        *,
        registry_module=None,
    ) -> None:
        self._registry_module = (
            registry_module
        )

    def _registry(
        self,
    ):
        if (
            self._registry_module
            is not None
        ):
            return self._registry_module

        import winreg

        return winreg

    def enable(
        self,
        command: str,
    ) -> None:
        if not command.strip():
            raise ValueError(
                "autostart command is empty"
            )

        registry = (
            self._registry()
        )

        key = registry.CreateKey(
            registry.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
        )

        try:
            registry.SetValueEx(
                key,
                WINDOWS_VALUE_NAME,
                0,
                registry.REG_SZ,
                command,
            )

        finally:
            registry.CloseKey(
                key
            )

    def disable(
        self,
    ) -> None:
        registry = (
            self._registry()
        )

        try:
            key = registry.OpenKey(
                registry.HKEY_CURRENT_USER,
                WINDOWS_RUN_KEY,
                0,
                registry.KEY_SET_VALUE,
            )

        except FileNotFoundError:
            return

        try:
            try:
                registry.DeleteValue(
                    key,
                    WINDOWS_VALUE_NAME,
                )

            except FileNotFoundError:
                pass

        finally:
            registry.CloseKey(
                key
            )

    def is_enabled(
        self,
    ) -> bool:
        registry = (
            self._registry()
        )

        try:
            key = registry.OpenKey(
                registry.HKEY_CURRENT_USER,
                WINDOWS_RUN_KEY,
                0,
                registry.KEY_READ,
            )

        except FileNotFoundError:
            return False

        try:
            try:
                registry.QueryValueEx(
                    key,
                    WINDOWS_VALUE_NAME,
                )

                return True

            except FileNotFoundError:
                return False

        finally:
            registry.CloseKey(
                key
            )


def create_autostart_adapter(
    *,
    platform_name: str
    | None = None,
    home: Path
    | None = None,
    registry_module=None,
):
    platform_name = (
        platform_name
        or sys.platform
    )

    if platform_name == "darwin":
        base_home = (
            Path(home)
            if home is not None
            else Path.home()
        )

        return MacOSAutostartAdapter(
            plist_path=(
                base_home
                / "Library"
                / "LaunchAgents"
                / (
                    MAC_LABEL
                    + ".plist"
                )
            )
        )

    if platform_name.startswith(
        "win"
    ):
        return WindowsAutostartAdapter(
            registry_module=(
                registry_module
            )
        )

    raise RuntimeError(
        "unsupported autostart platform: "
        + platform_name
    )
