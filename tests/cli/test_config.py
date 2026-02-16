import argparse
from unittest.mock import patch, MagicMock

import pytest

from lovebirds.cli.config import Config
from lovebirds.models.email import EmailAddress
from lovebirds.models.people import People, Person


def _make_config(dry_run: bool = False, people: People | None = None) -> Config:
    if people is None:
        people = {}
    args = argparse.Namespace(
        dry_run=dry_run,
        people_file="/tmp/test_people.yaml",
    )
    return Config(
        args=args,
        event=None,
        event_id="",
        people=people,
    )


class TestConfigSavePeople:
    @patch("lovebirds.cli.config.save_people")
    @patch("lovebirds.cli.config.backup_file")
    @patch("lovebirds.cli.config.check_type")
    def test_dry_run_skips_save(self, mock_check, mock_backup, mock_save):
        config = _make_config(dry_run=True)
        config.save_people()
        mock_save.assert_not_called()
        mock_backup.assert_not_called()

    @patch("lovebirds.cli.config.save_people")
    @patch("lovebirds.cli.config.backup_file")
    @patch("lovebirds.cli.config.check_type")
    def test_backup_true_calls_backup(self, mock_check, mock_backup, mock_save):
        config = _make_config(dry_run=False)
        config.save_people(backup=True)
        mock_backup.assert_called_once_with("/tmp/test_people.yaml")
        mock_save.assert_called_once()

    @patch("lovebirds.cli.config.save_people")
    @patch("lovebirds.cli.config.backup_file")
    @patch("lovebirds.cli.config.check_type")
    def test_backup_false_skips_backup(self, mock_check, mock_backup, mock_save):
        config = _make_config(dry_run=False)
        config.save_people(backup=False)
        mock_backup.assert_not_called()
        mock_save.assert_called_once()
