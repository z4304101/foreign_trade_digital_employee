import plistlib


def test_macos_autostart_writes_user_launch_agent(
    tmp_path,
):
    from desktop.autostart import (
        MacOSAutostartAdapter,
    )

    plist_path = (
        tmp_path
        / "Library"
        / "LaunchAgents"
        / "com.foreigntrade.digitalemployee.plist"
    )

    adapter = MacOSAutostartAdapter(
        plist_path=plist_path
    )

    command = (
        '"/Applications/'
        'Foreign Trade Digital Employee.app/'
        'Contents/MacOS/'
        'ForeignTradeDigitalEmployee"'
    )

    assert (
        adapter.is_enabled()
        is False
    )

    adapter.enable(
        command
    )

    assert (
        adapter.is_enabled()
        is True
    )

    payload = plistlib.loads(
        plist_path.read_bytes()
    )

    assert (
        payload["Label"]
        == "com.foreigntrade.digitalemployee"
    )

    assert payload[
        "ProgramArguments"
    ] == [
        (
            "/Applications/"
            "Foreign Trade Digital Employee.app/"
            "Contents/MacOS/"
            "ForeignTradeDigitalEmployee"
        )
    ]

    assert (
        payload["RunAtLoad"]
        is True
    )

    adapter.disable()

    assert (
        adapter.is_enabled()
        is False
    )


def test_windows_autostart_uses_current_user_run_key():
    from desktop.autostart import (
        WindowsAutostartAdapter,
    )

    class FakeRegistry:
        HKEY_CURRENT_USER = "HKCU"
        KEY_SET_VALUE = 1
        KEY_READ = 2
        REG_SZ = 1

        def __init__(self):
            self.values = {}

        def CreateKey(
            self,
            root,
            path,
        ):
            return (
                root,
                path,
            )

        def OpenKey(
            self,
            root,
            path,
            reserved=0,
            access=0,
        ):
            return (
                root,
                path,
            )

        def CloseKey(
            self,
            key,
        ):
            pass

        def SetValueEx(
            self,
            key,
            name,
            reserved,
            value_type,
            value,
        ):
            self.values[
                (
                    key,
                    name,
                )
            ] = value

        def QueryValueEx(
            self,
            key,
            name,
        ):
            lookup = (
                key,
                name,
            )

            if lookup not in self.values:
                raise FileNotFoundError

            return (
                self.values[
                    lookup
                ],
                self.REG_SZ,
            )

        def DeleteValue(
            self,
            key,
            name,
        ):
            lookup = (
                key,
                name,
            )

            if lookup not in self.values:
                raise FileNotFoundError

            del self.values[
                lookup
            ]

    registry = FakeRegistry()

    adapter = WindowsAutostartAdapter(
        registry_module=registry
    )

    command = (
        '"C:\\Program Files\\'
        'ForeignTradeDigitalEmployee\\'
        'ForeignTradeDigitalEmployee.exe"'
    )

    assert (
        adapter.is_enabled()
        is False
    )

    adapter.enable(
        command
    )

    assert (
        adapter.is_enabled()
        is True
    )

    adapter.disable()

    assert (
        adapter.is_enabled()
        is False
    )


def test_platform_factory_selects_supported_adapter(
    tmp_path,
):
    from desktop.autostart import (
        MacOSAutostartAdapter,
        create_autostart_adapter,
    )

    adapter = create_autostart_adapter(
        platform_name="darwin",
        home=tmp_path,
    )

    assert isinstance(
        adapter,
        MacOSAutostartAdapter,
    )
