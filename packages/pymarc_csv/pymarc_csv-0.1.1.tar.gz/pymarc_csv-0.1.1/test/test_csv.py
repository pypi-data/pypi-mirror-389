# This file is part of pymarc. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# https://opensource.org/licenses/BSD-2-Clause. pymarc may be copied, modified,
# propagated, or distributed according to the terms contained in the LICENSE
# file.

import copy
import csv
import io
import unittest
from typing import Any, cast

import pymarc
from pymarc import Field, Indicators, Record, Subfield

import pymarc_csv


class CSVReaderTest(unittest.TestCase):
    def setUp(self):
        with open("test/test.csv") as fh:
            self.in_csv = list(csv.DictReader(fh, strict=False))

        self._csv_fh = open("test/test.csv")  # noqa: SIM115
        self.reader = pymarc_csv.CSVReader(self._csv_fh)  # type: ignore

    def tearDown(self) -> None:
        self._csv_fh.close()

    def testRoundtrip(self):
        """Test from and to csv.

        Tests that result of loading records from the test file
        produces objects deeply equal to the result of loading
        marc-in-csv files directly
        """
        recs = list(self.reader)
        self.assertEqual(
            len(self.in_csv), len(recs), "Incorrect number of records found"
        )
        for i, rec in enumerate(recs):
            deserialized = pymarc_csv.parse_csv_to_dict(pymarc_csv.as_csv(rec))
            comp = copy.deepcopy(self.in_csv[i])
            # remove empty fields from csv dict
            to_delete = []
            for key in comp:
                if not comp[key]:
                    to_delete.append(key)
            for key in to_delete:
                del comp[key]
            self.assertEqual(comp, deserialized)

    def testOneRecord(self):
        """Tests case when in source csv there is only 1 record not wrapped in list."""
        output = io.StringIO(newline="")
        fieldnames = list(self.in_csv[0])
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(self.in_csv[0])
        data = output.getvalue()
        # remove empty fields from csv dict
        to_delete = []
        comp = copy.deepcopy(self.in_csv[0])
        for key in comp:
            if not comp[key]:
                to_delete.append(key)
        for key in to_delete:
            del comp[key]
        reader = pymarc_csv.CSVReader(data)  # type: ignore
        self.assertEqual(
            [pymarc_csv.parse_csv_to_dict(pymarc_csv.as_csv(rec)) for rec in reader][0],
            comp,
        )


class csvTest(unittest.TestCase):
    def setUp(self):
        self._test_fh = open("test/test.dat", "rb")  # noqa: SIM115
        self.reader = pymarc.MARCReader(self._test_fh)
        self._record = Record()
        field = Field(
            tag="245",
            indicators=Indicators("1", "0"),
            subfields=[
                Subfield(code="a", value="Python"),
                Subfield(code="c", value="Guido"),
            ],
        )
        self._record.add_field(field)

    def tearDown(self) -> None:
        self._test_fh.close()

    def test_as_dict_single(self):
        _expected = {
            "fields": [
                {
                    "245": {
                        "ind1": "1",
                        "ind2": "0",
                        "subfields": [{"a": "Python"}, {"c": "Guido"}],
                    }
                }
            ],
            "leader": "          22        4500",
        }
        self.assertEqual(_expected, self._record.as_dict())

    def test_as_csv_types(self):
        rd = cast(dict[str, Any], self._record.as_dict())
        self.assertTrue(isinstance(rd, dict))
        self.assertTrue(isinstance(rd["leader"], str))
        self.assertTrue(isinstance(rd["fields"], list))
        self.assertTrue(isinstance(rd["fields"][0], dict))
        self.assertTrue(isinstance(rd["fields"][0], dict))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["ind1"], str))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["ind2"], str))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["subfields"], list))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["subfields"][0], dict))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["subfields"][0]["a"], str))
        self.assertTrue(isinstance(rd["fields"][0]["245"]["subfields"][1]["c"], str))

    def test_as_csv_simple(self):
        record = pymarc_csv.as_csv(self._record)
        record = pymarc_csv.parse_csv_to_dict(record)

        self.assertTrue("LDR" in record)
        self.assertEqual(record["LDR"], "          22        4500")

        self.assertTrue("field_order" in record)
        self.assertTrue("245" in record)
        self.assertEqual(record["245"], "10$aPython$cGuido")

    def test_as_csv_multiple(self):
        for record in self.reader:
            self.assertEqual(
                dict,
                pymarc_csv.parse_csv_to_dict(
                    pymarc_csv.as_csv(cast(Record, record))
                ).__class__,
            )  # type: ignore


class CSVWriterTest(unittest.TestCase):
    def setUp(self):
        self._record = Record()
        field = Field(
            tag="245",
            indicators=Indicators("1", "0"),
            subfields=[
                Subfield(code="a", value="Python"),
                Subfield(code="c", value="Guido"),
            ],
        )
        self._record.add_field(field)

        # Create a second record with multiple fields
        self._record2 = Record()
        self._record2.add_field(Field(tag="001", data="12345"))
        self._record2.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[Subfield(code="a", value="Test Title")],
            )
        )
        self._record2.add_field(
            Field(
                tag="650",
                indicators=Indicators(" ", "0"),
                subfields=[Subfield(code="a", value="Subject 1")],
            )
        )

    def test_write_single_record(self):
        """Test writing a single record to CSV."""
        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)
        writer.write(self._record)
        writer.close(close_fh=False)

        result = output.getvalue()
        self.assertIn("LDR", result)
        self.assertIn("245", result)
        self.assertIn("field_order", result)
        self.assertIn("10$aPython$cGuido", result)

    def test_write_multiple_records(self):
        """Test writing multiple records to CSV."""
        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)
        writer.write([self._record, self._record2])
        writer.close(close_fh=False)

        result = output.getvalue()
        lines = result.strip().split("\n")
        # Should have header + 2 data rows
        self.assertEqual(len(lines), 3)
        self.assertIn("LDR", lines[0])
        self.assertIn("245", lines[0])
        self.assertIn("field_order", lines[0])

    def test_write_one_without_tags(self):
        """Test write_one warns when no tags have been added."""
        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)

        with self.assertWarns(UserWarning):
            writer.write_one(self._record)
        writer.close(close_fh=False)

    def test_write_one_with_add_tags(self):
        """Test write_one with tags pre-added."""
        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)
        writer.add_tags(["245"])
        writer.write_one(self._record)
        writer.close(close_fh=False)

        result = output.getvalue()
        self.assertIn("245", result)
        self.assertIn("10$aPython$cGuido", result)

    def test_roundtrip_write_read(self):
        """Test that records can be written and read back correctly."""
        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)
        writer.write([self._record, self._record2])
        writer.close(close_fh=False)

        # Read back the CSV
        output.seek(0)
        reader = pymarc_csv.CSVReader(output)  # type: ignore
        records = list(reader)

        self.assertEqual(len(records), 2)
        # Check first record
        self.assertEqual(records[0]["245"]["a"], "Python")
        self.assertEqual(records[0]["245"]["c"], "Guido")
        # Check second record
        self.assertEqual(records[1]["001"].data, "12345")
        self.assertEqual(records[1]["245"]["a"], "Test Title")

    def test_duplicate_tags(self):
        """Test handling of duplicate field tags."""
        record = Record()
        record.add_field(
            Field(
                tag="650",
                indicators=Indicators(" ", "0"),
                subfields=[Subfield(code="a", value="Subject 1")],
            )
        )
        record.add_field(
            Field(
                tag="650",
                indicators=Indicators(" ", "0"),
                subfields=[Subfield(code="a", value="Subject 2")],
            )
        )

        output = io.StringIO(newline="")
        writer = pymarc_csv.CSVWriter(output)
        writer.write(record)
        writer.close(close_fh=False)

        result = output.getvalue()
        # Should have both 650 and 650_2 columns
        self.assertIn("650", result)
        self.assertIn("650_2", result)
        self.assertIn("Subject 1", result)
        self.assertIn("Subject 2", result)


class csvParse(unittest.TestCase):
    def setUp(self):
        self._one_dat_fh = open("test/one.dat", "rb")  # noqa: SIM115
        self._one_csv_fh = open("test/one.csv")  # noqa: SIM115
        self._batch_xml_fh = open("test/batch.xml")  # noqa: SIM115
        self._batch_csv_fh = open("test/batch.csv")  # noqa: SIM115

        self.reader_dat = pymarc.MARCReader(self._one_dat_fh)
        self.parse_csv = pymarc_csv.parse_csv_to_array(self._one_csv_fh)
        self.batch_xml = pymarc.parse_xml_to_array(self._batch_xml_fh)
        self.batch_csv = pymarc_csv.parse_csv_to_array(self._batch_csv_fh)

    def tearDown(self) -> None:
        self._one_dat_fh.close()
        self._one_csv_fh.close()
        self._batch_xml_fh.close()
        self._batch_csv_fh.close()

    def testRoundtrip(self):
        recs = list(self.reader_dat)
        self.assertEqual(
            len(self.parse_csv), len(recs), "Incorrect number of records found"
        )
        for from_dat, from_csv in zip(recs, self.parse_csv):
            assert isinstance(from_dat, Record)
            self.assertEqual(from_dat.as_marc(), from_csv.as_marc(), "Incorrect Record")

    def testParsecsvXml(self):
        self.assertEqual(
            len(self.batch_csv),
            len(self.batch_xml),
            "Incorrect number of parse records found",
        )
        for from_dat, from_csv in zip(self.batch_csv, self.batch_xml):
            self.assertEqual(from_dat.as_marc(), from_csv.as_marc(), "Incorrect Record")


if __name__ == "__main__":
    unittest.main()
