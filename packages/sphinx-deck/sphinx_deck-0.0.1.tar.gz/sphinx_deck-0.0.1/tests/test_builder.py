import shutil
from pathlib import Path


def test_convert(make_app, sphinx_test_tempdir: Path, rootdir: Path) -> None:
    testroot_path = rootdir / "test-section" / "source"
    srcdir = sphinx_test_tempdir / "section"
    shutil.copytree(testroot_path, srcdir)

    app = make_app("markdown", srcdir=srcdir)
    app.build()

    actual = (app.outdir / "index.md").read_text()
    expected = (rootdir / "test-section" / "expected.md").read_text()
    assert actual == expected
