# This file is part of pymarc_csv. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# https://opensource.org/licenses/BSD-2-Clause. pymarc_csv may be copied, modified,
# propagated, or distributed according to the terms contained in the LICENSE
# file.

"""Pymarc Reader."""

import csv
import io
import os
import sys
from io import StringIO, TextIOBase
from pathlib import Path
from typing import TextIO

from pymarc import Field, Indicators, Leader, Reader, Record, Subfield


class CSVReader(Reader):
    """CSV Reader."""

    file_handle: TextIOBase

    def __init__(
        self,
        marc_target: bytes | str | Path | TextIO,
        encoding: str = "utf-8",
        stream: bool = False,
    ) -> None:
        """Basically the argument you pass in should be raw csv in transmission format.
        A csv.DictReader object is used to handle the records."""
        # streaming is not implemented.
        self.encoding = encoding
        if isinstance(marc_target, io.TextIOBase):
            if hasattr(marc_target, "mode") and "b" in getattr(marc_target, "mode", ""):
                raise ValueError(
                    "CSVReader requires a text-mode file handle, not binary."
                )  # because csv.DictReader requires this
            self.file_handle = marc_target
        elif isinstance(marc_target, (str, Path)):
            if (isinstance(marc_target, str) and os.path.exists(marc_target)) or (
                isinstance(marc_target, Path) and marc_target.exists()
            ):
                self.file_handle = open(marc_target, encoding=encoding)  # noqa: SIM115
            else:
                self.file_handle = StringIO(marc_target)  # type: ignore
        elif isinstance(marc_target, bytes):
            # try to coerce bytes into text
            self.file_handle = StringIO(marc_target.decode(encoding))

        if stream:
            sys.stderr.write(
                "Streaming not yet implemented, your data will be loaded into memory\n"
            )
        self.records = list(csv.DictReader(self.file_handle))

    def __iter__(self) -> "CSVReader":
        self.iter = iter(self.records)
        return self

    def __next__(self) -> Record:
        line: dict = next(self.iter)
        return self._make_record(line)

    def _make_record(self, line) -> Record:
        rec = Record()
        leader = line.get("LDR")
        if not leader:
            leader = line["leader"]
        rec.leader = Leader(leader)
        fields = line["field_order"].split()
        for field in fields:
            if not line.get(field):
                continue
            line[field] = line[field].replace(chr(31), "$")
            if "$" in line[field][:3]:
                indicators, field_text = line[field].split("$", maxsplit=1)
                indicators = indicators.replace("\\", " ")
                indicators = list(indicators)[:2]
            else:
                indicators, field_text = (None, line[field])
            # deal with duplicate tags that have been written to CSV
            # by appending '_<#>'
            tag = field
            if "_" in tag:
                tag = tag[: tag.index("_")]
            if indicators:
                subfields = (
                    [Subfield(code=s[0], value=s[1:]) for s in field_text.split("$")]
                    if field_text
                    else []
                )
                field = Field(
                    tag=tag,
                    indicators=Indicators(*indicators),
                    subfields=subfields,
                )
            else:
                field = Field(
                    tag=tag,
                    data=field_text,
                )
            rec.add_field(field)
        return rec
