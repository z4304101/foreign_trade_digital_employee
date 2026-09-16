from pathlib import Path

from desktop.paths import DesktopPaths


def test_desktop_paths_keep_runtime_under_user_data(
    tmp_path: Path,
):
    paths = DesktopPaths.from_root(tmp_path)

    assert paths.settings_file == tmp_path / "settings.json"
    assert paths.pin_file == tmp_path / "admin_pin.json"
    assert paths.history_db == tmp_path / "history_learning.db"
    assert (
        paths.processed_store
        == tmp_path / "processed_message_ids.txt"
    )
    assert paths.result_dir == tmp_path / "result"
    assert paths.log_dir == tmp_path / "logs"
    assert paths.backup_dir == tmp_path / "backups"
