import pytest
from unittest.mock import patch

from lovebirds.models.email import EmailAddress
from lovebirds.models.people import (
    Participation,
    ParticipationPhase,
    ParticipationRole,
    ParticipationStatus,
    InformationSource,
    People,
    Person,
)
from lovebirds.statistics import (
    EventParticipantsStatistics,
    get_event_participants_statistics,
)


def _make_person(
    email: str,
    birth_year: int | None = 1990,
    status: ParticipationStatus = ParticipationStatus.accepted,
) -> Person:
    return Person(
        email=EmailAddress(email),
        first_name="Test",
        languages=["en"],
        birth_year=birth_year,
        participation={
            "event1": Participation(
                phases=[
                    ParticipationPhase(
                        status=status,
                        role=ParticipationRole.participant,
                        source=InformationSource.organizer,
                        operator=EmailAddress("op@example.com"),
                    )
                ]
            )
        },
    )


class TestGetEventParticipantsStatistics:
    @patch("lovebirds.statistics.calculate_age")
    def test_basic_statistics(self, mock_age):
        mock_age.side_effect = [25, 30, 35]
        people: People = {
            EmailAddress("a@e.com"): _make_person("a@e.com", 1999),
            EmailAddress("b@e.com"): _make_person("b@e.com", 1994),
            EmailAddress("c@e.com"): _make_person("c@e.com", 1989),
        }
        result = get_event_participants_statistics("event1", people)
        assert result is not None
        assert result.count == 3
        assert result.min_age == 25
        assert result.max_age == 35
        assert result.age_average == 30
        assert "\u2013" in result.age_range  # en-dash

    def test_no_participants_returns_none(self):
        people: People = {}
        result = get_event_participants_statistics("event1", people)
        assert result is None

    @patch("lovebirds.statistics.calculate_age")
    def test_filters_by_last_phase(self, mock_age):
        """A person who was accepted then withdrew should be excluded."""
        mock_age.return_value = 30
        person = Person(
            email=EmailAddress("x@e.com"),
            languages=["en"],
            birth_year=1994,
            participation={
                "event1": Participation(
                    phases=[
                        ParticipationPhase(
                            status=ParticipationStatus.accepted,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                        ),
                        ParticipationPhase(
                            status=ParticipationStatus.withdrew,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                        ),
                    ]
                )
            },
        )
        people: People = {person.email: person}
        result = get_event_participants_statistics("event1", people)
        assert result is None

    @patch("lovebirds.statistics.calculate_age")
    def test_both_accepted_and_participated_included(self, mock_age):
        mock_age.side_effect = [25, 30]
        people: People = {
            EmailAddress("a@e.com"): _make_person(
                "a@e.com", status=ParticipationStatus.accepted
            ),
            EmailAddress("b@e.com"): _make_person(
                "b@e.com", status=ParticipationStatus.participated
            ),
        }
        result = get_event_participants_statistics("event1", people)
        assert result is not None
        assert result.count == 2

    @patch("lovebirds.statistics.calculate_age")
    def test_age_clamped_to_18(self, mock_age):
        mock_age.return_value = 16
        people: People = {
            EmailAddress("a@e.com"): _make_person("a@e.com", 2008),
        }
        result = get_event_participants_statistics("event1", people)
        assert result is not None
        assert result.min_age == 18

    @patch("lovebirds.statistics.calculate_age")
    def test_age_range_uses_en_dash(self, mock_age):
        mock_age.side_effect = [25, 35]
        people: People = {
            EmailAddress("a@e.com"): _make_person("a@e.com"),
            EmailAddress("b@e.com"): _make_person("b@e.com"),
        }
        result = get_event_participants_statistics("event1", people)
        assert result is not None
        assert result.age_range == "25\u201335"

    def test_all_birth_years_none_crashes(self):
        """Documents the latent bug: min([]) raises ValueError when all birth_years are None."""
        person = Person(
            email=EmailAddress("x@e.com"),
            languages=["en"],
            birth_year=None,
            participation={
                "event1": Participation(
                    phases=[
                        ParticipationPhase(
                            status=ParticipationStatus.accepted,
                            role=ParticipationRole.participant,
                            source=InformationSource.organizer,
                            operator=EmailAddress("op@example.com"),
                        )
                    ]
                )
            },
        )
        people: People = {person.email: person}
        with pytest.raises(ValueError):
            get_event_participants_statistics("event1", people)
