#!/usr/bin/env python3
"""One-off: writes public/legacy-ids.json so links and stars from before stable
ids keep working.

Before ids, a detail page was /mappings/<array index> and a star was keyed by
partnerUni|||nusCourse1|||puCourse1|||faculty. Both were built from the
pre-id dataset, so this needs that file:

  git show <pre-id commit>:public/modules-data.json > /tmp/old.json
  python3 data/make_legacy_ids.py /tmp/old.json

Output:
  idx:  old array index -> new id (null if the row was dropped)
  keys: old star key -> new ids, only where the old key can't be recomputed
        from the new record's fields (i.e. a code or name was cleaned up)
"""
import json
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import build_data as b  # noqa: E402

OUT = Path(__file__).parent.parent / "public" / "legacy-ids.json"


def legacy_key(r):
    return "|||".join([r["partnerUni"], r["nusCourse1"], r["puCourse1"], r["faculty"]])


def main(old_path):
    old = json.loads(Path(old_path).read_text(encoding="utf-8"))
    new_ids = {r["id"] for r in json.loads(b.OUT.read_text(encoding="utf-8"))}
    wb = openpyxl.load_workbook(b.SRC, data_only=True)
    rows = list(b.read_rows(wb))
    if len(rows) != len(old):
        sys.exit(f"row count mismatch: workbook has {len(rows)}, old dataset has {len(old)}")

    idx, keys = [], {}
    for old_rec, (faculty, partner_raw, row) in zip(old, rows):
        new = b.build_record(faculty, partner_raw, row)
        new_id = b.mapping_id(new)
        if new_id not in new_ids:
            idx.append(None)
            continue
        idx.append(new_id)
        if legacy_key(old_rec) != legacy_key(new):
            keys.setdefault(legacy_key(old_rec), []).append(new_id)

    keys = {k: sorted(set(v)) for k, v in keys.items()}
    OUT.write_text(json.dumps({"idx": idx, "keys": keys}, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(idx)} indices and {len(keys)} changed keys to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
