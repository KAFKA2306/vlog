from pathlib import Path

import pytest
from vlog_capture import gpu_libraries
from vlog_capture.gpu_libraries import (
    GpuLibraryError,
    discover,
    ld_library_path,
    require,
    wsl_native_cuda,
)

ROOT = Path(__file__).resolve().parents[1]


def make_site(tmp_path: Path, version: str, system: str = "Linux") -> Path:
    site = tmp_path / "venv" / "lib" / f"python{version}" / "site-packages"
    sub = "lib" if system == "Linux" else "bin"
    for package, lib in (("cublas", "libcublas.so.12"), ("cudnn", "libcudnn.so.9")):
        directory = site / "nvidia" / package / sub
        directory.mkdir(parents=True)
        (directory / lib).write_bytes(b"")
    return site


@pytest.mark.parametrize("version", ["3.11", "3.12", "3.13", "3.14"])
def test_discovers_libraries_for_any_python_version(tmp_path: Path, version: str):
    site = make_site(tmp_path, version)
    found = discover(search_path=[str(site)], system="Linux")
    assert [item.package for item in found] == ["nvidia.cublas", "nvidia.cudnn"]
    assert found[0].directory == site / "nvidia" / "cublas" / "lib"
    assert found[1].libraries == ("libcudnn.so.9",)


def test_windows_layout_uses_bin(tmp_path: Path):
    site = make_site(tmp_path, "3.12", system="Windows")
    found = discover(search_path=[str(site)], system="Windows")
    assert found[0].directory == site / "nvidia" / "cublas" / "bin"


def test_missing_packages_fail_loud(tmp_path: Path):
    found = discover(search_path=[str(tmp_path)], system="Linux")
    assert all(item.directory is None for item in found)
    with pytest.raises(GpuLibraryError) as error:
        require(found)
    assert "nvidia.cublas" in str(error.value)
    assert "nvidia.cudnn" in str(error.value)


def test_package_without_library_dir_is_missing(tmp_path: Path):
    (tmp_path / "nvidia" / "cublas").mkdir(parents=True)
    found = discover(search_path=[str(tmp_path)], system="Linux")
    assert found[0].directory is None


def test_ld_library_path_is_minimal_and_prepends(tmp_path: Path):
    site = make_site(tmp_path, "3.12")
    found = discover(search_path=[str(site)], system="Linux")
    value = ld_library_path(found, existing="/usr/lib/wsl/lib", system="Linux")
    parts = value.split(":")
    assert parts[:2] == [str(item.directory) for item in found]
    assert parts[2] == "/usr/lib/wsl/lib"
    again = ld_library_path(found, existing=value, system="Linux")
    assert again == value


def test_ld_library_path_unchanged_when_nothing_found(tmp_path: Path):
    found = discover(search_path=[str(tmp_path)], system="Linux")
    assert ld_library_path(found, existing="/x", system="Linux") == "/x"


def test_wsl_native_cuda_distinguished_from_pip_libs(tmp_path: Path):
    assert wsl_native_cuda(tmp_path) is None
    (tmp_path / "libcuda.so.1").write_bytes(b"")
    assert wsl_native_cuda(tmp_path) == tmp_path / "libcuda.so.1"


def test_report_shows_resolution_and_native_status(tmp_path: Path):
    site = make_site(tmp_path, "3.12")
    found = discover(search_path=[str(site)], system="Linux")
    text = gpu_libraries.report(found, native=None)
    assert str(site / "nvidia" / "cublas" / "lib") in text
    assert "wsl-native-cuda: UNAVAILABLE" in text


def test_repository_has_no_version_pinned_nvidia_path():
    needle = "python3." + "12"
    skipped = {".git", ".venv", "node_modules", ".claude"}
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or skipped & set(path.parts):
            continue
        if path.suffix not in {".py", ".bat", ".ps1", ".yaml", ".yml", ".sh", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if needle in text and "site-packages" in text and "nvidia" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
