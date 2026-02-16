from datetime import datetime

import pytest

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
    Registration,
    sorted_people,
)


class TestPersonExperience:
    def test_no_participation(self, make_person):
        person = make_person()
        assert person.experience == 0

    def test_counts_participated_status(self, make_person, make_phase):
        person = make_person(
            participation={
                "event1": Participation(
                    phases=[make_phase(status=ParticipationStatus.participated)]
                ),
                "event2": Participation(
                    phases=[make_phase(status=ParticipationStatus.participated)]
                ),
            }
        )
        assert person.experience == 2

    def test_does_not_count_accepted(self, make_person, make_phase):
        person = make_person(
            participation={
                "event1": Participation(
                    phases=[make_phase(status=ParticipationStatus.accepted)]
                ),
            }
        )
        assert person.experience == 0


class TestPersonFullName:
    def test_both_names(self, make_person):
        person = make_person(first_name="Alice", last_name="Smith")
        assert person.full_name == "Alice Smith"

    def test_first_only(self, make_person):
        person = make_person(first_name="Alice", last_name=None)
        assert person.full_name == "Alice"

    def test_last_only(self, make_person):
        person = make_person(first_name=None, last_name="Smith")
        assert person.full_name == "Smith"

    def test_neither(self, make_person):
        person = make_person(first_name=None, last_name=None)
        assert person.full_name is None


class TestPersonAliasName:
    def test_with_aliases(self, make_person):
        person = make_person(
            first_name="Alice", last_name="Smith", aliases=["Ali", "Ally"]
        )
        assert person.alias_name == "Alice (Ali/Ally) Smith"

    def test_without_aliases(self, make_person):
        person = make_person(first_name="Alice", last_name="Smith", aliases=[])
        assert person.alias_name == "Alice Smith"

    def test_no_names_falls_back_to_email(self, make_person):
        person = make_person(
            email=EmailAddress("anon@example.com"),
            first_name=None,
            last_name=None,
            aliases=[],
        )
        assert person.alias_name == "anon@example.com"


class TestPersonNamedEmail:
    def test_with_name(self, make_person):
        person = make_person(
            email=EmailAddress("alice@example.com"),
            first_name="Alice",
            last_name="Smith",
        )
        assert person.named_email == "Alice Smith <alice@example.com>"

    def test_without_name(self, make_person):
        person = make_person(
            email=EmailAddress("anon@example.com"),
            first_name=None,
            last_name=None,
        )
        assert person.named_email == "anon@example.com"


class TestRegistrationEqualInfo:
    def test_same_content_different_time_hash(self, make_registration):
        reg1 = make_registration(time=datetime(2025, 1, 1), hash="abc")
        reg2 = make_registration(time=datetime(2025, 6, 1), hash="def")
        assert reg1.equal_info(reg2) is True

    def test_different_content(self, make_registration):
        reg1 = make_registration(genitalia=Genitalia.vulva)
        reg2 = make_registration(genitalia=Genitalia.penis)
        assert reg1.equal_info(reg2) is False


class TestSortedPeople:
    def test_alphabetical_sort(self, make_person):
        zoe = make_person(
            email=EmailAddress("zoe@example.com"), first_name="Zoe", last_name="Adams"
        )
        alice = make_person(
            email=EmailAddress("alice@example.com"),
            first_name="Alice",
            last_name="Baker",
        )
        people: People = {zoe.email: zoe, alice.email: alice}
        result = sorted_people(people)
        keys = list(result.keys())
        assert keys[0] == EmailAddress("alice@example.com")
        assert keys[1] == EmailAddress("zoe@example.com")

    def test_returns_deep_copy(self, make_person):
        person = make_person()
        people: People = {person.email: person}
        result = sorted_people(people)
        result_person = list(result.values())[0]
        assert result_person is not person
        assert result_person.email == person.email
