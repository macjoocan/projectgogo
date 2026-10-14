"""FibMatrix ``Meta.bytes`` 설정 묶음 디코더.

Top Heroes의 ``FMCommon.dll``에 포함된 ``FibMatrix.Config.ConfigFormatter``
포맷을 게임 코드를 실행하지 않고 읽는다. 바깥 래퍼는 gzip이고, 안쪽은 공통
상수 풀과 이름 붙은 테이블/원시 바이트 블록으로 구성된다.
"""
from __future__ import annotations

import gzip
import struct


class FibMatrixError(ValueError):
    """잘렸거나 지원하지 않는 FibMatrix 데이터를 만났을 때."""


_INT = 1
_FLOAT = 2
_LONG = 3
_DOUBLE = 4
_STRING = 5
_INT_ARRAY = 6
_FLOAT_ARRAY = 7
_STRING_ARRAY = 8


def _need(data: bytes, pos: int, size: int) -> None:
    if pos < 0 or size < 0 or pos + size > len(data):
        raise FibMatrixError(f"범위를 벗어난 읽기: {pos}+{size} / {len(data)}")


def _u32(data: bytes, pos: int) -> int:
    _need(data, pos, 4)
    return struct.unpack_from("<I", data, pos)[0]


def _i32(data: bytes, pos: int) -> int:
    _need(data, pos, 4)
    return struct.unpack_from("<i", data, pos)[0]


def _read_7bit(data: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    while shift < 35:
        _need(data, pos, 1)
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise FibMatrixError("잘못된 7비트 정수")


def _read_string(data: bytes, pos: int) -> tuple[str, int]:
    size, pos = _read_7bit(data, pos)
    _need(data, pos, size)
    try:
        return data[pos:pos + size].decode("utf-8"), pos + size
    except UnicodeDecodeError as exc:
        raise FibMatrixError(f"UTF-8 문자열 오류 @{pos}: {exc}") from exc


def _read_n(data: bytes, pos: int, size: int, *, signed: bool = False) -> tuple[int, int]:
    if not size:
        return 0, pos
    _need(data, pos, size)
    value = int.from_bytes(data[pos:pos + size], "little", signed=False)
    if signed and size == 4 and value >= 0x80000000:
        value -= 0x100000000
    return value, pos + size


def _unwrap(data: bytes) -> bytes:
    if not data:
        raise FibMatrixError("빈 FibMatrix 파일")
    if data[0] == 0:
        return data[1:]
    if data[0] != 1:
        raise FibMatrixError(f"알 수 없는 압축 플래그: {data[0]}")
    expected = _u32(data, 1)
    try:
        raw = gzip.decompress(data[5:])
    except (OSError, EOFError) as exc:
        raise FibMatrixError(f"gzip 해제 실패: {exc}") from exc
    if len(raw) != expected:
        raise FibMatrixError(f"gzip 크기 불일치: {len(raw)} != {expected}")
    return raw


def _constant_pools(data: bytes, pos: int, size: int):
    end = pos + size
    _need(data, pos, size)

    count = _i32(data, pos)
    pos += 4
    strings = []
    for _ in range(count):
        value, pos = _read_string(data, pos)
        strings.append(value)

    def numbers(fmt: str, width: int):
        nonlocal pos
        count = _i32(data, pos)
        pos += 4
        _need(data, pos, count * width)
        values = list(struct.unpack_from(f"<{count}{fmt}", data, pos)) if count else []
        pos += count * width
        return values

    ints = numbers("i", 4)
    longs = numbers("q", 8)
    floats = numbers("f", 4)
    doubles = numbers("d", 8)
    if pos != end:
        raise FibMatrixError(f"상수 풀 크기 불일치: {pos} != {end}")
    return (strings, ints, longs, floats, doubles)


def _decode_block(data: bytes, pos: int) -> tuple[bytes, int]:
    _need(data, pos, 5)
    flags = data[pos]
    stored = _u32(data, pos + 1)
    if flags & 1:
        _need(data, pos + 5, 4 + stored)
        expected = _u32(data, pos + 5)
        try:
            import lz4.block
            block = lz4.block.decompress(data[pos + 9:pos + 9 + stored],
                                         uncompressed_size=expected)
        except Exception as exc:
            raise FibMatrixError(f"LZ4 블록 해제 실패: {exc}") from exc
        return block, pos + 9 + stored
    _need(data, pos + 5, stored)
    return data[pos + 5:pos + 5 + stored], pos + 5 + stored


def _array(block: bytes, pos: int, kind: int, pools):
    strings, _ints, _longs, floats, _doubles = pools
    count, pos = _read_7bit(block, pos)
    values = []
    if count >= 4:
        code_pos = pos
        pos += (count + 3) // 4
        for i in range(count):
            code = (block[code_pos + i // 4] >> ((i % 4) * 2)) & 3
            size = (0, 1, 2, 4)[code] if kind == _INT_ARRAY else code
            value, pos = _read_n(block, pos, size, signed=(kind == _INT_ARRAY))
            values.append(value)
    else:
        for _ in range(count):
            value, pos = _read_7bit(block, pos)
            if kind == _INT_ARRAY and value >= 0x80000000:
                value -= 0x100000000
            values.append(value)
    if kind == _FLOAT_ARRAY:
        return [floats[index] for index in values]
    if kind == _STRING_ARRAY:
        return [strings[index] for index in values]
    return values


def _table(block: bytes, pools) -> list[dict]:
    strings, _ints, longs, floats, doubles = pools
    _need(block, 0, 9)
    rows = _i32(block, 1)
    cols = _i32(block, 5)
    if rows < 0 or cols < 0:
        raise FibMatrixError("음수 행/열 수")
    pos = 9
    names = []
    for _ in range(cols):
        index = _i32(block, pos)
        pos += 4
        names.append(strings[index])
    type_pos = pos
    type_size = (cols + 1) // 2
    _need(block, type_pos, type_size)
    kinds = [((block[type_pos + i // 2] >> (4 * (i % 2))) & 0xf)
             for i in range(cols)]
    pos += type_size
    offsets = []
    for _ in range(rows):
        offsets.append(_i32(block, pos))
        pos += 4
    area_size = _i32(block, pos)
    area_start = pos + 4
    _need(block, area_start, area_size)

    decoded = []
    for row_index, relative in enumerate(offsets):
        row_pos = area_start + relative
        value_count, value_pos = _read_7bit(block, row_pos)
        if value_count > cols:
            raise FibMatrixError(f"행 {row_index} 값 수가 열 수보다 큼")
        code_pos = value_pos
        value_pos += (value_count + 3) // 4
        raw_values = []
        present = []
        for col in range(value_count):
            code = (block[code_pos + col // 4] >> ((col % 4) * 2)) & 3
            kind = kinds[col]
            size = (0, 1, 2, 4)[code] if kind in (
                _INT, _INT_ARRAY, _FLOAT_ARRAY, _STRING_ARRAY) else code
            value, value_pos = _read_n(block, value_pos, size, signed=(kind == _INT))
            raw_values.append(value)
            present.append(size != 0)
        _extra_size, extra_start = _read_7bit(block, value_pos)

        row = {}
        for col, raw_value in enumerate(raw_values):
            if not present[col]:
                row[names[col]] = None
                continue
            kind = kinds[col]
            if kind == _INT:
                value = raw_value
            elif kind == _FLOAT:
                value = floats[raw_value]
            elif kind == _LONG:
                value = longs[raw_value]
            elif kind == _DOUBLE:
                value = doubles[raw_value]
            elif kind == _STRING:
                value = strings[raw_value]
            elif kind in (_INT_ARRAY, _FLOAT_ARRAY, _STRING_ARRAY):
                value = _array(block, extra_start + raw_value, kind, pools)
            else:
                value = None
            row[names[col]] = value
        decoded.append(row)
    return decoded


def decode(data: bytes) -> dict:
    """FibMatrix 파일을 ``tables``와 ``raw`` 딕셔너리로 디코딩한다."""
    payload = _unwrap(data)
    pool_size = _i32(payload, 0)
    pools = _constant_pools(payload, 4, pool_size)
    pos = 4 + pool_size

    table_count = _i32(payload, pos)
    pos += 4
    tables = {}
    for _ in range(table_count):
        name, pos = _read_string(payload, pos)
        block, pos = _decode_block(payload, pos)
        tables[name] = _table(block, pools)

    raw_count = _i32(payload, pos)
    pos += 4
    raw = {}
    for _ in range(raw_count):
        name, pos = _read_string(payload, pos)
        raw[name], pos = _decode_block(payload, pos)
    if pos != len(payload):
        raise FibMatrixError(f"파일 끝에 {len(payload) - pos}바이트가 남음")
    return {"tables": tables, "raw": raw}
