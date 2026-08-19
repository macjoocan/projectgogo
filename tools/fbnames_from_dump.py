"""IL2CppDumper 의 dump.cs → FlatBuffers 필드 이름 지도.

FlatBuffers 버퍼에는 필드 이름이 없어서 `flatbuf` 는 슬롯 번호(f0·f1…)로 낸다.
그런데 **생성 코드가 앱 안에 그대로 남아 있다** — `FTiledLevel`·`FTiledGrid`·
`FTiledCell` 같은 클래스의 프로퍼티가 곧 슬롯이고, 선언 순서가 곧 슬롯 순서다.
여기서 그걸 읽어 `flatbuffers.names` 로 쓸 수 있는 지도를 만든다.

이름을 지어내지 않는다 — 덤프에 있는 것만 쓴다. 못 찾은 클래스는 슬롯 번호로 남는다.

    python tools/fbnames_from_dump.py --dump <dump.cs> --root FTiledLevel \
           --out configs/_names_royalmatch.yaml
"""
import argparse
import re

#: `XxxLength` 프로퍼티는 벡터다 — 길이 접근자라서 이름 끝의 Length 를 뗀다.
_LEN = re.compile(r"Length$")


def properties(src, cls):
    """클래스의 get 프로퍼티를 선언 순서대로 → [(타입, 이름)]. ByteBuffer 는 뺀다."""
    m = re.search(r"public (?:sealed )?(?:class|struct) " + re.escape(cls)
                  + r"\b[^{]*\{(.*?)\n\}\n", src, re.S)
    if not m:
        return []
    body = re.sub(r"\n\t*// RVA[^\n]*", "", m.group(1))
    out = []
    for t, n in re.findall(r"public\s+([\w<>\[\]?]+)\s+(\w+)\s*\{\s*get;", body):
        if n == "ByteBuffer":
            continue
        out.append((t, n))
    return out


def _inner(t):
    """`Nullable<FTiledGrid>` → `FTiledGrid`, 아니면 None."""
    m = re.match(r"Nullable<(\w+)>$", t)
    return m.group(1) if m else (t if t.startswith("F") and t[1:2].isupper() else None)


def element_types(src, cls):
    """{필드명: 원소 클래스} — 벡터 원소 타입은 프로퍼티가 아니라 **인덱서**에 있다.

    생성 코드는 길이만 프로퍼티(`CellsLength`)로 내고 원소는
    `public Nullable<FTiledCell> Cells(int j)` 로 낸다. 이걸 안 보면 셀 테이블
    이름이 통째로 빠진다.
    """
    m = re.search(r"public (?:sealed )?(?:class|struct) " + re.escape(cls)
                  + r"\b[^{]*\{(.*?)\n\}\n", src, re.S)
    if not m:
        return {}
    body = re.sub(r"\n\t*// RVA[^\n]*", "", m.group(1))
    out = {}
    for t, n in re.findall(r"public\s+([\w<>\[\]?]+)\s+(\w+)\s*\(\s*int\s+\w+\s*\)\s*\{", body):
        c = _inner(t)
        if c:
            out[n] = c
    return out


def build(src, root, log=print):
    """{name_path: [필드 이름…]} — flatbuf.decode(names=…) 에 그대로 넣는다.

    벡터 원소 경로는 `부모.필드[]` 다 (flatbuf 가 그렇게 만든다).
    """
    names, seen = {}, set()

    def walk(cls, path):
        if (cls, path) in seen or len(seen) > 400:
            return
        seen.add((cls, path))
        props = properties(src, cls)
        if not props:
            log(f"  ! {cls} 를 덤프에서 못 찾음 — 이 아래는 슬롯 번호로 남는다")
            return
        elems = element_types(src, cls)
        labels = []
        for t, n in props:
            base = _LEN.sub("", n)
            labels.append(base)
            sub = f"{path}.{base}" if path else base
            child = _inner(t)
            if child:                      # 단일 테이블 필드
                walk(child, sub)
            if base in elems:              # 테이블 벡터 — 원소 경로는 `…[]`
                walk(elems[base], sub + "[]")
        names[path] = labels

    walk(root, "")
    # 벡터 원소 경로는 부모 이름을 그대로 쓰므로 중복 제거만 하면 된다
    return {k: v for k, v in names.items() if v}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--root", default="FTiledLevel")
    ap.add_argument("--out")
    a = ap.parse_args()
    src = open(a.dump, encoding="utf-8", errors="replace").read()
    names = build(src, a.root)
    print(f"[fbnames] 경로 {len(names)}개")
    if a.out:
        import json
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("# IL2CppDumper dump.cs 에서 자동 생성 — tools/fbnames_from_dump.py\n")
            f.write("flatbuffers:\n  names:\n")
            for k in sorted(names):
                f.write(f"    {json.dumps(k, ensure_ascii=False)}: "
                        f"{json.dumps(names[k], ensure_ascii=False)}\n")
        print(f"[fbnames] 저장: {a.out}")


if __name__ == "__main__":
    main()
