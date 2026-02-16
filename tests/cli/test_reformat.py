import argparse
from unittest.mock import MagicMock

from lovebirds.cli.config import Config
from lovebirds.cli.reformat import reformat_people


class TestReformatPeople:
    def test_calls_save_without_backup(self):
        args = argparse.Namespace(dry_run=False)
        config = Config(
            args=args,
            event=None,
            event_id="",
            people={},
        )
        config.save_people = MagicMock()  # type: ignore[method-assign]
        reformat_people(config)
        config.save_people.assert_called_once_with(backup=False)
