# This file is part of pymarc. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# https://opensource.org/licenses/BSD-2-Clause. pymarc may be copied, modified,
# propagated, or distributed according to the terms contained in the LICENSE
# file.

"""Pymarc Writer."""

import csv
from collections.abc import Iterable
from typing import TextIO
from warnings import warn

from pymarc import Record, Writer


class CSVWriter(Writer):
    """A class for writing records as an array of MARC-in-CSV objects.

    IMPORTANT: You must close a CSVWriter,
    otherwise you will not get valid CSV.
    CSVWriter uses a "field_order" column to recreate the original order of records.

    Simple usage::

    .. code-block:: python

        from pymarc import CSVWriter

        # writing individual records to a file (not recommended)
        writer = CSVWriter(open('file.csv','wt'))
        writer.add_tags(['001', '003', '264', '300']
        writer.write_one(record1)
        writer.write_one(record2)
        writer.close()  # Important!

        #writing multiple records (as list) to a file (recommended)
        writer = CSVWriter(open('file.csv','wt'))
        writer.write(records)
        writer.close()  # Important!

        # writing to a string
        string = StringIO()
        writer = CSVWriter(string)
        writer.write(records)
        writer.close(close_fh=False)  # Im6portant!
        print(string)
    """

    # Note if file_handle is a BinaryIO, csv writing won't work
    def __init__(self, file_handle: TextIO) -> None:
        super().__init__(file_handle)
        self.write_count = 0
        self.marc_tags: list[str] = ["LDR"]
        self.csv_dict_writer = None

    def write(self, records: Record | list[Record]) -> None:  # type: ignore[override]
        """Writes records.
        Infers the columns for CSV from tags in records,
        so there's no need to call `CSVWriter.add_tags`."""
        if not isinstance(records, list):
            records = [records]
        csv_records = []
        for record in records:
            Writer.write(self, record)
            csv_record = {}
            if record:
                leader = record.leader.leader
                csv_record["LDR"] = leader
                tag_counts = {}
                csv_fields = []
                for marc_field in record.get_fields():
                    cur_tag = marc_field.tag
                    tag_counts[cur_tag] = tag_counts.get(cur_tag, 0) + 1
                    if tag_counts[cur_tag] > 1:
                        cur_tag = f"{cur_tag}_{tag_counts[cur_tag]}"
                    if cur_tag not in self.marc_tags:
                        self.marc_tags.append(cur_tag)
                    csv_fields.append(cur_tag)
                    # deal with indicators
                    indicator1 = (
                        marc_field.indicator1 if marc_field.indicator1 != " " else "\\"
                    )
                    indicator2 = (
                        marc_field.indicator2 if marc_field.indicator2 != " " else "\\"
                    )
                    if not indicator1:
                        indicator1 = "\\"
                    if not indicator2:
                        indicator2 = "\\"
                    # note that some fields may have no subfields (as with control fields).
                    # in this case, marc_field.subfields returns and empty list.
                    if marc_field.subfields:
                        csv_record[cur_tag] = (
                            f"{indicator1}{indicator2}{''.join([f'${s.code}{s.value}' for s in marc_field.subfields])}"
                        )
                    # handle field without subfields. These should be control fields.
                    else:
                        csv_record[cur_tag] = marc_field.data
                csv_record["field_order"] = " ".join(csv_fields)

                csv_records.append(csv_record)
        if not self.csv_dict_writer:
            self.marc_tags = sorted(self.marc_tags)
            csv_headings = self.marc_tags + ["field_order"]
            self.csv_dict_writer = csv.DictWriter(
                self.file_handle,  # type: ignore
                csv_headings,
            )
            self.csv_dict_writer.writeheader()

        self.csv_dict_writer.writerows(csv_records)

    def write_one(self, record: Record):
        """Writes a single record.
        Note that for writing single records to a CSV file, if record contains
        a tag that hasn't been defined (explicitly with `CSVWriter.add_tags`
        or implicitly with `write`), the corresponding field will simply be skipped.
        This applies to duplicate tags as well: to process multiple fields with the
        same tag, e.g. two fields with tag 630, `self.marc_tags` must contain
        '630' and '630_2', if three fields, '630_3', etc.
        So `CSVWriter.add_tags` or `CSVWriter.write` should always be called beforehand.
        For simple tasks it's best always to use `CSVWriter.write`.
        For processing large numbers of records, it might be best to loop through and identify
        what tags are needed (with duplicates in format ###_2, ###_3 etc.), call add_tags
        and then process records individually with write_one to avoid having to create a massive list."""
        Writer.write(self, record)
        leader = record.leader.leader
        csv_record = {}
        csv_record["LDR"] = leader
        tag_counts = {}
        field_order = []
        for marc_field in record.get_fields():
            tag_counts[marc_field.tag] = tag_counts.get(marc_field.tag, 0) + 1
            cur_tag = marc_field.tag
            if tag_counts[marc_field.tag] > 1:
                cur_tag = f"{marc_field.tag}_{tag_counts[marc_field.tag]}"
            if cur_tag not in self.marc_tags:
                print(f"skipping marc tag: {marc_field.tag}")
                continue
            field_order.append(cur_tag)
            indicator1 = marc_field.indicator1 if marc_field.indicator1 != " " else "\\"
            indicator2 = marc_field.indicator2 if marc_field.indicator2 != " " else "\\"
            if not indicator1:
                indicator1 = "\\"
            if not indicator2:
                indicator2 = "\\"
            if marc_field.subfields:
                csv_record[cur_tag] = (
                    f"{indicator1}{indicator2}{''.join([f'${s.code}{s.value}' for s in marc_field.subfields])}"
                )
            else:
                csv_record[marc_field.tag] = marc_field.data
        csv_record["field_order"] = " ".join(field_order)

        if not self.csv_dict_writer:
            self.marc_tags = sorted(self.marc_tags)
            csv_headings = self.marc_tags + ["field_order"]
            self.csv_dict_writer = csv.DictWriter(
                self.file_handle,  # type: ignore
                csv_headings,
            )
            self.csv_dict_writer.writeheader()

        if len(self.marc_tags) <= 1:
            msg = "No marc tags have been added, so CSV will be missing fields. Call add_tags or write before write."
            warn(msg, UserWarning, stacklevel=1)

        self.csv_dict_writer.writerow(csv_record)

    def add_tags(self, tags: Iterable) -> list[str]:
        """Add CSV columns for fields in marc records.
        Only necessary if calling `CSVWriter.write`
        without previously calling `CSVWriter.write`."""
        tag_counts = {}

        def process_duplicate_tags(tag):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            cur_tag = tag
            if tag_counts[tag] > 1:
                cur_tag = f"{tag}_{tag_counts[tag]}"
            return cur_tag

        self.marc_tags.extend([process_duplicate_tags(tag) for tag in tags])
        return self.marc_tags

    def close(self, close_fh: bool = True) -> None:
        """Closes the writer.

        If close_fh is False close will also close the underlying file
        handle that was passed in to the constructor. The default is True.
        """
        Writer.close(self, close_fh)
