from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SequenceTest:
    id: int
    parent_id: int | None
    name: str
    enabled: bool
    units: str
    min_limit: float | int | None
    max_limit: float | int | None
    steps: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SequenceGroup:
    id: int
    parent_id: int | None
    name: str
    enabled: bool


SequenceEntry = SequenceGroup | SequenceTest


@dataclass(frozen=True)
class SequenceDefinition:
    file_path: Path
    sequence_name: str
    version: str
    station_name: str
    station_id: str
    board_pn: str
    groups: list[SequenceGroup]
    tests: list[SequenceTest]
    entries: list[SequenceEntry]


class SequenceLoader:
    @staticmethod
    def load(file_path: Path) -> SequenceDefinition:
        payload = json.loads(file_path.read_text(encoding='utf-8'))
        station = payload.get('station', {})

        groups: list[SequenceGroup] = []
        tests: list[SequenceTest] = []
        entries: list[SequenceEntry] = []

        for entry in payload.get('tests', []):
            entry_type = entry.get('type')
            if entry_type == 'group':
                group = SequenceGroup(
                    id=int(entry['id']),
                    parent_id=entry.get('parent_id'),
                    name=str(entry.get('name', 'Unnamed Group')),
                    enabled=bool(entry.get('enabled', True)),
                )
                groups.append(group)
                entries.append(group)
                continue

            if entry_type == 'test':
                limits = entry.get('limits', {})
                test = SequenceTest(
                    id=int(entry['id']),
                    parent_id=entry.get('parent_id'),
                    name=str(entry.get('name', 'Unnamed Test')),
                    enabled=bool(entry.get('enabled', True)),
                    units=str(entry.get('units', '')),
                    min_limit=limits.get('min'),
                    max_limit=limits.get('max'),
                    steps=list(entry.get('steps', [])),
                )
                tests.append(test)
                entries.append(test)

        return SequenceDefinition(
            file_path=file_path,
            sequence_name=str(payload.get('sequence_name', file_path.stem)),
            version=str(payload.get('version', '')),
            station_name=str(station.get('name', '')),
            station_id=str(station.get('station_id', '')),
            board_pn=str(station.get('board_pn', '')),
            groups=groups,
            tests=tests,
            entries=entries,
        )
