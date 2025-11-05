import csv
from io import StringIO

from pymarc import record


def as_csv(rec: record.Record, **kwargs) -> str:
    """Serialize a record as CSV. Standalone function equivalent to Record.as_marc() method in pymarc."""
    # serializing as a string corresponding to a csv,
    # with lines separated by /n, and with columns for
    # the record leader ("LDR") and each field.
    # Duplicate field tags are given their own column,
    # e.g. "100_2", "100_3", etc.
    # column "field_order" records order in which fields appeared in record
    # (CSV serialization gives records sorted by tag).
    output = StringIO(newline="")
    csv_record = {}
    csv_fields = []
    tag_counts = {}
    csv_record["LDR"] = rec.leader.leader
    for marc_field in rec.get_fields():
        cur_tag = marc_field.tag
        tag_counts[cur_tag] = tag_counts.get(cur_tag, 0) + 1
        if tag_counts[cur_tag] > 1:
            cur_tag = f"{cur_tag}_{tag_counts[cur_tag]}"
        csv_fields.append(cur_tag)
        # deal with indicators
        indicator1 = marc_field.indicator1 if marc_field.indicator1 != " " else "\\"
        indicator2 = marc_field.indicator2 if marc_field.indicator2 != " " else "\\"
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

    writer = csv.DictWriter(
        output,
        fieldnames=(sorted(csv_record)),
        delimiter=",",
        lineterminator="\n",
        **kwargs,
    )
    writer.writeheader()
    writer.writerow(csv_record)
    return output.getvalue()
