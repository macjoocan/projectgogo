"""APK/XAPK 안의 FibMatrix Meta.bytes를 JSON/raw zip으로 추출한다."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from levelscope import container, fibmatrix


def _safe(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", name).strip("._") or "unnamed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="APK/XAPK/폴더")
    ap.add_argument("--glob", default="assets/Table/**/Meta.bytes")
    ap.add_argument("--out", required=True, help="출력 zip")
    args = ap.parse_args()

    found = None
    for source in container.iter_containers(args.input):
        try:
            names = source.glob(args.glob)
            if names:
                found = (source.label, names[0], source.read(names[0]))
                break
        finally:
            source.close()
    if found is None:
        raise SystemExit(f"Meta.bytes를 찾지 못함: {args.glob}")

    label, name, blob = found
    result = fibmatrix.decode(blob)
    index = {
        "source": f"{label}!{name}",
        "tables": {key: len(rows) for key, rows in result["tables"].items()},
        "raw": {key: len(value) for key, value in result["raw"].items()},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("_index.json", json.dumps(index, ensure_ascii=False, indent=1))
        for table_name, rows in result["tables"].items():
            zf.writestr(f"tables/{_safe(table_name)}.json",
                        json.dumps(rows, ensure_ascii=False, indent=1))
        for raw_name, value in result["raw"].items():
            zf.writestr(f"raw/{_safe(raw_name)}", value)
    print(f"{len(result['tables']):,}개 테이블 / {len(result['raw']):,}개 raw → {args.out}")


if __name__ == "__main__":
    main()
