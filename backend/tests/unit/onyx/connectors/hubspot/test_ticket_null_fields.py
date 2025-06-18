from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from onyx.connectors.hubspot.connector import HubSpotConnector


def _make_ticket(ticket_id: str = "1", subject: str | None = "Subject", content: str | None = "Content") -> MagicMock:
    ticket = MagicMock()
    ticket.id = ticket_id
    ticket.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    props: dict[str, str] = {}
    if subject is not None:
        props["subject"] = subject
    if content is not None:
        props["content"] = content
    ticket.properties = props
    ticket.associations = None
    return ticket


def _mock_client(tickets: list[MagicMock]) -> MagicMock:
    client = MagicMock()
    client.crm.tickets.get_all.return_value = tickets
    client.crm.contacts.basic_api.get_by_id.return_value = MagicMock(properties={})
    client.crm.objects.notes.basic_api.get_by_id.return_value = MagicMock(properties={})
    return client


@patch("onyx.connectors.hubspot.connector.HubSpot")
def test_missing_subject_uses_default(mock_hubspot: MagicMock) -> None:
    ticket = _make_ticket(subject=None, content="text")
    mock_hubspot.return_value = _mock_client([ticket])

    connector = HubSpotConnector(access_token="token")
    connector.ticket_base_url = "https://example/"

    batches = list(connector.load_from_state())
    assert len(batches) == 1
    docs = batches[0]
    assert len(docs) == 1
    doc = docs[0]
    assert doc.semantic_identifier == "No Subject"
    assert doc.sections[0].text.startswith("text")


@patch("onyx.connectors.hubspot.connector.HubSpot")
def test_missing_content_skips_ticket(mock_hubspot: MagicMock) -> None:
    ticket = _make_ticket(subject="S", content=None)
    mock_hubspot.return_value = _mock_client([ticket])

    connector = HubSpotConnector(access_token="token")
    connector.ticket_base_url = "https://example/"

    batches = list(connector.load_from_state())
    # No documents should be yielded
    assert batches == []
