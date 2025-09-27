#!/usr/bin/env python3
"""Textual-based TUI for managing GovInfo ingestion pipelines.

This interface allows users to select ingestion targets, configure filters, and
submit jobs to the ingestion queue. It currently emits JSON payloads to stdout
and can be wired into the queue table described in the runbook.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Switch,
)


INGESTION_TYPES = {
    "govinfo_bills": "GovInfo Bills",
    "govinfo_agendas": "GovInfo Agendas",
    "govinfo_calendars": "GovInfo Calendars",
    "member_data": "Member Data",
    "bill_votes": "Bill Vote Records",
    "bill_status": "Bill Status / Milestones",
}

COLLECTION_OPTIONS = [
    ("Bills", "BILLS"),
    ("BillStatus", "BILLSTATUS"),
    ("Calendars", "CCAL"),
    ("Agendas", "AGENDA"),
    ("Votes", "VOTES"),
]

PARTY_CHOICES = [("Any", ""), ("Democrat", "DEM"), ("Republican", "REP"), ("Other", "OTH")]


@dataclass
class IngestionParameters:
    ingestion_type: str
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    member_name: Optional[str] = None
    bill_number: Optional[str] = None
    party: Optional[str] = None
    collection: Optional[str] = None
    text_search: Optional[str] = None
    limit: Optional[int] = None
    recursive: bool = False
    enqueue_only: bool = False


class FilterPanel(Static):
    def compose(self) -> ComposeResult:
        yield Label("Year Range")
        with Horizontal():
            yield Input(placeholder="From", id="year_from", classes="small-input")
            yield Input(placeholder="To", id="year_to", classes="small-input")
        yield Label("Member / Sponsor")
        yield Input(placeholder="Member name", id="member_name")
        yield Label("Bill Number")
        yield Input(placeholder="e.g. S123", id="bill_number")
        yield Label("Party")
        yield Select(PARTY_CHOICES, id="party_select")
        yield Label("Collection")
        yield Select(COLLECTION_OPTIONS, id="collection_select")
        yield Label("Full-text Search")
        yield Input(placeholder="Search terms", id="text_search")
        yield Label("Record Limit")
        yield Input(placeholder="100", id="limit")
        with Horizontal():
            yield Checkbox(label="Recursive discovery", id="recursive")
            yield Checkbox(label="Queue only (do not run)", id="enqueue_only")


class IngestionTUI(App):
    CSS_PATH = ""
    TITLE = "GovInfo Ingestion Dashboard"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Horizontal(id="top-row"):
                yield Static(Label("Ingestion Type"), id="type_label")
                yield Select([(label, key) for key, label in INGESTION_TYPES.items()], id="ingestion_type")
            yield FilterPanel(id="filters")
            with Horizontal(id="buttons"):
                yield Button("Queue Job", id="queue")
                yield Button("Exit", id="exit")
            yield Static(id="output")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "queue":
            params = self.collect_parameters()
            output = self.query_one("#output", Static)
            output.update(json.dumps(asdict(params), indent=2))
            # Placeholder: in production, insert into ingestion_queue or call API.
            print(json.dumps(asdict(params)))
        elif event.button.id == "exit":
            self.exit()

    def collect_parameters(self) -> IngestionParameters:
        ingestion_type = self.query_one("#ingestion_type", Select).value
        year_from = self._parse_int(self.query_one("#year_from", Input).value)
        year_to = self._parse_int(self.query_one("#year_to", Input).value)
        member_name = self.query_one("#member_name", Input).value or None
        bill_number = self.query_one("#bill_number", Input).value or None
        party = self.query_one("#party_select", Select).value or None
        collection = self.query_one("#collection_select", Select).value or None
        text_search = self.query_one("#text_search", Input).value or None
        limit = self._parse_int(self.query_one("#limit", Input).value)
        recursive = self.query_one("#recursive", Checkbox).value
        enqueue_only = self.query_one("#enqueue_only", Checkbox).value

        return IngestionParameters(
            ingestion_type=ingestion_type,
            year_from=year_from,
            year_to=year_to,
            member_name=member_name,
            bill_number=bill_number,
            party=party,
            collection=collection,
            text_search=text_search,
            limit=limit,
            recursive=bool(recursive),
            enqueue_only=bool(enqueue_only),
        )

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None or value.strip() == "":
            return None
        try:
            return int(value)
        except ValueError:
            return None


if __name__ == "__main__":
    app = IngestionTUI()
    app.run()
