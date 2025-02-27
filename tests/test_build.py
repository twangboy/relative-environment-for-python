import hashlib

import pytest

from mayflower.build.common import Builder, verify_checksum
from mayflower.common import DATADIR, MODULE_DIR, MayflowerException


@pytest.fixture
def fake_download(tmp_path):
    download = tmp_path / "fake_download"
    download.write_text("This is some file contents")
    return download


@pytest.fixture
def fake_download_md5(fake_download):
    return hashlib.md5(fake_download.read_bytes()).hexdigest()


@pytest.mark.skip_unless_on_linux
def test_builder_defaults_linux():
    builder = Builder()
    assert builder.arch == "x86_64"
    assert builder.triplet == "x86_64-linux-gnu"
    assert builder.prefix == DATADIR / "build" / "x86_64-linux-gnu"
    assert builder.sources == DATADIR / "src"
    assert builder.downloads == DATADIR / "download"
    assert builder.toolchains == DATADIR / "toolchain"
    assert builder.toolchain == DATADIR / "toolchain" / "x86_64-linux-gnu"
    assert callable(builder.build_default)
    assert callable(builder.populate_env)
    assert builder.no_download is False
    assert builder.recipies == {}


def test_verify_checksum(fake_download, fake_download_md5):
    assert verify_checksum(fake_download, fake_download_md5) is True


def test_verify_checksum_failed(fake_download):
    pytest.raises(MayflowerException, verify_checksum, fake_download, "no")
