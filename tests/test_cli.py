# -*- coding: utf-8 -*-
from click.testing import CliRunner

from osmcha.scripts.cli import cli


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ['31984168'])
    assert result.exit_code == 0
    assert "Created: 0. Modified: 5. Deleted: 0" in result.output
    assert "The changeset 31984168 is not suspect!" in result.output

    result = runner.invoke(cli, ['45632780'])
    assert result.exit_code == 0
    assert "Created: 47. Modified: 0. Deleted: 0" in result.output
    assert "The changeset 45632780 is suspect!" in result.output
    assert "Reasons: suspect_word" in result.output
