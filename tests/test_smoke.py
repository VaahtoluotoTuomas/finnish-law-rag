import pytest

import lakirag
from lakirag.cli import main


def test_package_has_version():
    assert lakirag.__version__


def test_cli_without_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: lakirag" in capsys.readouterr().out


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert lakirag.__version__ in capsys.readouterr().out
