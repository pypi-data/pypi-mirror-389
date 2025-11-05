# pymarc_csv

CSV reader and writer for MARC records - an extension for [pymarc](https://gitlab.com/pymarc/pymarc).
This can be useful where there's any value in making MARC records editable
as a spreadsheet and for manipulating records with tools like Pandas.
I admit, however, that the CSV serlialization implemented here,
though far more readable than MARC21 itself, is still a bit
of an eyesore.

Note that for processing MARC records as CSV or Parquet files
there's also [marctable](https://github.com/sul-dlss/marctable).
The main advantage of _pymarc_csv_ is its integration with _pymarc_.

## Overview

`pymarc-csv` extends the [pymarc](https://pypi.org/project/pymarc/) library to provide CSV reading and writing capabilities for MARC21 bibliographic records. This allows you to work with MARC data in a more accessible CSV format while maintaining full compatibility with _pymarc_'s Record objects.

## Features

- **CSVReader**: Read MARC records from CSV files
- **CSVWriter**: Write MARC records to CSV format
- **CSV serialization**: Convert Record objects to/from CSV strings
- **Duplicate field handling**: Automatically handles repeated MARC fields (e.g., multiple 650 fields become `650`, `650_2`, `650_3`)
- **Field order preservation**: Maintains original field order through a `field_order` column
- **Full pymarc compatibility**: Works with existing pymarc Record objects

## Installation

```bash
pip install pymarc-csv
```

## Requirements

- Python >= 3.10
- pymarc >= 5.3.1

## Quick Start

### Reading CSV files

This is closely analogous to reading `JSON` and `XML` records
in _pymarc_.

```python
from pymarc_csv import CSVReader

# Read MARC records from CSV
with open('records.csv', 'r') as fh:
    reader = CSVReader(fh)
    for record in reader:
        print(record.title)
        print(record['245']['a'])
```

### Writing CSV files

This is where things get a bit more complicated
as compared to other file formats in _pymarc_.
In general, the main difference is that all Record
objects to be written should be collected as a list first.

```python
from pymarc_csv import CSVWriter


writer = CSVWriter(open('output.csv','wt'))
writer = CSVWriter(fh)
writer.write([record1, record2, record3])  # Write multiple at once
writer.close()
```

If you then wanted to add further records without introducing
any new CSV headings (so no new fields or unseen duplicate fields),
then before calling writer.close():

```python

record = Record()
record.add_field(
    Field(
        tag='245',
        indicators=Indicators('1', '0'),
        subfields=[
            Subfield(code='a', value='Python Programming'),
            Subfield(code='c', value='Guido van Rossum')
        ]
    )
)

# Write to CSV
writer.write(record)
writer.close()
```

To avoid having to store a large list of Records first, you could also
use the `add_tags` method and then write records one by one using `write_one`.
This is rather cumbersome, however, so you might be better off just using
_marctable_ at that point.

### Converting records to/from CSV strings

```python
from pymarc_csv import as_csv, parse_csv_to_dict

# Record to CSV string
csv_string = as_csv(record)

# CSV string back to dict
record_dict = parse_csv_to_dict(csv_string)
```

## CSV Format

The CSV format used by `pymarc-csv` has the following structure:

- **LDR column**: Contains the record leader
- **Field columns**: One column per MARC field (e.g., `001`, `245`, `650`)
- **Duplicate fields**: Numbered with suffixes (e.g., `650`, `650_2`, `650_3`)
- **field_order column**: Preserves the original order of fields

**Example CSV output** (showing one MARC record as a table for readability):

| Field           | Value                                                                     |
| --------------- | ------------------------------------------------------------------------- |
| **001**         | fol05731351                                                               |
| **003**         | IMchF                                                                     |
| **005**         | 20000613133448.0                                                          |
| **008**         | 000107s2000 nyua 001 0 eng                                                |
| **010**         | \\\$a 00020737                                                             |
| **020**         | \\\$a0471383147 (paper/cd-rom : alk. paper)                                |
| **040**         | \\\$aDLC\$cDLC\$dDLC                                                         |
| **042**         | \\\$apcc                                                                   |
| **050**         | 00\$aQA76.73.P22\$bM33 2000                                                 |
| **082**         | 00\$a005.13/3\$221                                                          |
| **100**         | 1\\\$aMartinsson, Tobias,\$d1976-                                            |
| **245**         | 10\$aActivePerl with ASP and ADO /\$cTobias Martinsson.                     |
| **260**         | \\\$aNew York :\$bJohn Wiley & Sons,\$c2000.                                 |
| **300**         | \\\$axxi, 289 p. :\$bill. ;\$c23 cm. +\$e1 computer laser disc (4 3/4 in.)    |
| **500**         | \\\$a"Wiley Computer Publishing."                                          |
| **630**         | 00\$aActive server pages.                                                  |
| **630\_2**       | 00\$aActiveX.                                                              |
| **650**         | \\0\$aPerl (Computer program language)                                      |
| **LDR**         | 00755cam 22002414a 4500                                                   |
| **field\_order** | 001 003 005 008 010 020 040 042 050 082 100 245 260 300 500 630 630\_2 650 |

An un-prettified version of this can be found in `test/one.csv`.

## Development

### Running Tests

```
python -m unittest
```

## License

BSD 2-Clause License (same as pymarc)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Built as an extension to the [pymarc](https://gitlab.com/pymarc/pymarc) library maintained by Ed Summers, Andrew Hankinson and contributors.
