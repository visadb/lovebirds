import argparse
from unittest.mock import MagicMock

from lovebirds.cli.config import Config
from lovebirds.cli.resolve import resolve_refs
from lovebirds.models.email import EmailAddress
from lovebirds.models.people import (
    Genitalia,
    InformationSource,
    Participation,
    ParticipationPhase,
    ParticipationRole,
    ParticipationStatus,
    People,
    Person,
    PersonRefById,
    PersonRefByName,
    Registration,
)


def _make_config(people: People) -> Config:
    args = argparse.Namespace(dry_run=False)
    config = Config(
        args=args,
        event=None,
        event_id="event1",
        people=people,
    )
    config.save_people = MagicMock()  # type: ignore[method-assign]
    return config


class TestResolveRefs:
    def test_single_match_resolved(self):
        alice = Person(
            email=EmailAddress("alice@example.com"),
            first_name="Alice",
            last_name="Smith",
            languages=["en"],
        )
        bob = Person(
            email=EmailAddress("bob@example.com"),
            first_name="Bob",
            last_name="Jones",
            languages=["en"],
            participation={
                "event1": Participation(
                    registrations=[
                        Registration(
                            genitalia=Genitalia.penis,
                            source=InformationSource.registration_form,
                            operator=EmailAddress("op@example.com"),
                            avecs=[PersonRefByName(name="Alice Smith")],
                        )
                    ],
                    phases=[
                        ParticipationPhase(
                            status=ParticipationStatus.accepted,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                        )
                    ],
                )
            },
        )
        people: People = {alice.email: alice, bob.email: bob}
        config = _make_config(people)
        resolve_refs(config)
        avec = bob.participation["event1"].registrations[0].avecs[0]
        assert isinstance(avec, PersonRefById)
        assert avec.id == EmailAddress("alice@example.com")

    def test_no_match_stays_unresolved(self):
        bob = Person(
            email=EmailAddress("bob@example.com"),
            first_name="Bob",
            last_name="Jones",
            languages=["en"],
            participation={
                "event1": Participation(
                    registrations=[
                        Registration(
                            genitalia=Genitalia.penis,
                            source=InformationSource.registration_form,
                            operator=EmailAddress("op@example.com"),
                            avecs=[PersonRefByName(name="Unknown Person")],
                        )
                    ]
                )
            },
        )
        people: People = {bob.email: bob}
        config = _make_config(people)
        resolve_refs(config)
        avec = bob.participation["event1"].registrations[0].avecs[0]
        assert isinstance(avec, PersonRefByName)

    def test_ambiguous_stays_unresolved(self):
        alice1 = Person(
            email=EmailAddress("alice1@example.com"),
            first_name="Alice",
            last_name="Smith",
            languages=["en"],
        )
        alice2 = Person(
            email=EmailAddress("alice2@example.com"),
            first_name="Alice",
            last_name="Smith",
            languages=["en"],
        )
        bob = Person(
            email=EmailAddress("bob@example.com"),
            first_name="Bob",
            last_name="Jones",
            languages=["en"],
            participation={
                "event1": Participation(
                    registrations=[
                        Registration(
                            genitalia=Genitalia.penis,
                            source=InformationSource.registration_form,
                            operator=EmailAddress("op@example.com"),
                            avecs=[PersonRefByName(name="Alice Smith")],
                        )
                    ]
                )
            },
        )
        people: People = {alice1.email: alice1, alice2.email: alice2, bob.email: bob}
        config = _make_config(people)
        resolve_refs(config)
        avec = bob.participation["event1"].registrations[0].avecs[0]
        assert isinstance(avec, PersonRefByName)

    def test_save_called_with_backup(self):
        people: People = {}
        config = _make_config(people)
        resolve_refs(config)
        config.save_people.assert_called_once_with(backup=True)  # type: ignore[attr-defined]
