from pandoc_runblocks import __version__

import subprocess

from pathlib import Path

BASEDIR = Path(__file__).resolve().parent
SRCDIR = BASEDIR.joinpath("src")
OUTDIR = BASEDIR.joinpath("out")


def get_output_for_path(path):
    return "\n".join(
        subprocess.check_output(
            [
                "pandoc",
                "-t",
                "markdown",
                "--filter",
                "pandoc-runblocks",
                str(path),
            ],
            universal_newlines=True,
        ).splitlines()
    )


def match_file(filename):
    got = get_output_for_path(SRCDIR.joinpath(filename))
    expected = "\n".join(
        OUTDIR.joinpath(Path(filename).stem + ".md").read_text().splitlines()
    )
    assert got == expected


def test_version():
    assert __version__ == "0.1.0.dev"


def test_python_hello_world():
    match_file("python_hello_world.md")
