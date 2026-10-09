from pathlib import Path

from vlog_capture.portability import (
    PathFlavor,
    classify_path,
    foreign_absolute_reason,
    runtime_directories,
    shared_checkout_reason,
)


def test_classifies_path_flavors_without_host_filesystem_access() -> None:
    assert classify_path(r"C:\\src\\vlog") == PathFlavor.WINDOWS_ABSOLUTE
    assert classify_path(r"C:vlog") == PathFlavor.WINDOWS_DRIVE_RELATIVE
    assert classify_path(r"\\\\server\\share\\vlog") == PathFlavor.WINDOWS_UNC
    assert classify_path("/home/user/vlog") == PathFlavor.POSIX_ABSOLUTE
    assert classify_path("data/recordings") == PathFlavor.RELATIVE


def test_foreign_absolute_path_detection_is_symmetric() -> None:
    assert foreign_absolute_reason(r"C:\\src\\vlog", system="Linux")
    assert foreign_absolute_reason("/home/user/vlog", system="Windows")
    assert foreign_absolute_reason("/home/user/vlog", system="Linux") is None
    assert foreign_absolute_reason(r"C:\\src\\vlog", system="Windows") is None


def test_shared_checkout_policy_marks_cross_filesystem_topologies() -> None:
    assert shared_checkout_reason("/mnt/c/src/vlog", system="Linux")
    assert shared_checkout_reason(
        r"\\\\wsl.localhost\\Ubuntu\\home\\user\\vlog", system="Windows"
    )
    assert shared_checkout_reason("/home/user/vlog", system="Linux") is None
    assert shared_checkout_reason(r"C:\\src\\vlog", system="Windows") is None


def test_runtime_directories_follow_xdg_and_windows_appdata() -> None:
    linux = runtime_directories(
        env={
            "XDG_CONFIG_HOME": "/cfg",
            "XDG_STATE_HOME": "/state",
            "XDG_CACHE_HOME": "/cache",
        },
        system="Linux",
        home=Path("/home/test"),
    )
    assert linux.config == Path("/cfg/vlog")
    assert linux.state == Path("/state/vlog")
    assert linux.cache == Path("/cache/vlog")

    windows = runtime_directories(
        env={"APPDATA": r"C:\\Roaming", "LOCALAPPDATA": r"C:\\Local"},
        system="Windows",
        home=Path("C:/Users/test"),
    )
    assert str(windows.config).endswith("VLog")
    assert str(windows.state).replace("\\\\", "/").endswith("VLog/State")
    assert str(windows.cache).replace("\\\\", "/").endswith("VLog/Cache")
