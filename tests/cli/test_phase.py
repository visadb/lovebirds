import argparse
from typing import Any
from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest

from lovebirds.cli.config import Config
from lovebirds.cli.phase import add_phase
from lovebirds.models.email import EmailAddress
from lovebirds.models.people import (
    Consent,
    InformationSource,
    Participation,
    ParticipationPhase,
    ParticipationRole,
    ParticipationStatus,
    People,
    Person,
)


def _make_config(people: People, **kwargs: Any) -> Config:
    defaults: dict[str, Any] = dict(
        event_id="event1",
        expr="True",
        new_status="accepted",
        new_role="participant",
        new_comment=None,
        source="organizer",
        operator="op@example.com",
        time=None,
        dry_run=False,
    )
    defaults.update(kwargs)
    args = argparse.Namespace(**defaults)
    config = Config(
        args=args,
        event=None,
        event_id=str(defaults["event_id"]),
        people=people,
    )
    config.save_people = MagicMock()  # type: ignore[method-assign]
    return config


def _simple_person(email: str = "test@example.com", **kwargs: Any) -> Person:
    defaults: dict[str, Any] = dict(
        email=EmailAddress(email),
        languages=["en"],
    )
    defaults.update(kwargs)
    return Person(**defaults)


class TestAddPhase:
    def test_new_participation_created(self):
        person = _simple_person()
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        assert "event1" in person.participation
        assert len(person.participation["event1"].phases) == 1
        assert (
            person.participation["event1"].phases[0].status
            == ParticipationStatus.accepted
        )

    def test_phase_appended_to_existing(self):
        person = _simple_person(
            participation={
                "event1": Participation(
                    phases=[
                        ParticipationPhase(
                            status=ParticipationStatus.invited,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                            time=datetime(2025, 1, 1),
                        )
                    ]
                )
            }
        )
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        assert len(person.participation["event1"].phases) == 2

    def test_same_status_updates_in_place(self):
        person = _simple_person(
            participation={
                "event1": Participation(
                    phases=[
                        ParticipationPhase(
                            status=ParticipationStatus.accepted,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                            time=datetime(2025, 1, 1),
                        )
                    ]
                )
            }
        )
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        # Same status should update in place, not add new phase
        assert len(person.participation["event1"].phases) == 1

    def test_locked_person_skipped(self):
        person = _simple_person(locked=True)
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        assert "event1" not in person.participation

    def test_legacy_person_skipped(self):
        person = _simple_person()
        person.consent = Consent(legacy=True)
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        assert "event1" not in person.participation

    def test_false_expression_no_phase(self):
        person = _simple_person()
        people: People = {person.email: person}
        config = _make_config(people, expr="False")
        add_phase(config)
        assert "event1" not in person.participation

    def test_save_people_called(self):
        person = _simple_person()
        people: People = {person.email: person}
        config = _make_config(people)
        add_phase(config)
        config.save_people.assert_called_once()  # type: ignore[attr-defined]
