"""한 파일에 Unity 번들이 **여러 개 이어붙어** 있는 배포를 펼친다.

Clash of Critters(`com.farlightgames.pgame.gp`)는 Addressables 콘텐츠 전부를
`assets/aa/Android/inpackage_aa_1.lpak` 한 파일에 넣는다. 확장자가 낯설어서
커스텀 포맷처럼 보이지만 **암호화도 커스텀 헤더도 아니다** — 평범한 `UnityFS`
번들 1,369개를 그냥 연달아 붙인 것이다(실측: 세그먼트 합계가 113,816,320 바이트 =
파일 크기의 100.0000%, 남는 꼬리 0바이트).

그래서 그냥 열면 **UnityPy가 첫 번들만 읽고 멈춘다.** 오브젝트 16개짜리 첫
세그먼트만 잡히고 나머지 108MB가 조용히 사라진다(survey 가 실제로 그랬다).
"열렸으니 다 읽었다"로 오해하기 가장 쉬운 형태다.

펼치는 자리를 **컨테이너 층으로 잡은 이유**가 있다. `names()`/`read()` 아래에서
세그먼트를 가상 엔트리로 보여주면 discover·sprites·assets·hierarchy·extract·
`--split` 이 전부 고칠 것 없이 동작한다. 이걸 각 소비자 쪽에 넣으면 여섯 군데를
똑같이 고쳐야 하고, 한 곳을 빠뜨리면 그 단계만 조용히 3%를 뽑는다.

가상 엔트리 이름은 `<원래이름>#0000` 이다.

    for c in container.iter_containers(apk):
        for n in c.names():           # ...lpak#0000, ...lpak#0001, ...
            data = c.read(n)          # 그 세그먼트 bytes 만

**탐지는 공짜다.** UnityFS 헤더에는 자기 번들의 전체 크기가 적혀 있으니, 앞
64바이트만 읽어서 "적힌 크기 < 파일 크기" 인지만 본다. 그럴 때만 전체를 읽어
헤더를 따라 걸어간다. 보통 번들은 앞 64바이트만 보고 지나간다.
"""
import struct

#: 가상 엔트리 이름 구분자. glob 메타문자가 아니어서 패턴 매칭을 깨지 않는다.
SEP = "#"

#: 번들 매직 — 이어붙이기를 쓰는 배포는 전부 UnityFS 다.
#: (UnityWeb/UnityRaw 는 웹플레이어 시절 포맷이라 이런 팩에 쓰이지 않는다.)
MAGIC = b"UnityFS\x00"

#: 헤더를 파싱하기에 충분한 앞부분 길이.
#: 매직 8 + 버전 4 + 버전문자열 2개 + int64 크기. 버전 문자열이 길어도
#: (`2022.3.62f3`) 40바이트 안에 끝나므로 64면 넉넉하다.
HEAD = 64

#: 이보다 작은 세그먼트는 번들일 수 없다 (헤더만으로도 이보다 크다).
MIN_SEGMENT = 64

#: 세그먼트 수 상한. 넘으면 펼치기를 **포기하고 원본을 그대로 준다** —
#: 조용히 잘라내면 "일부만 뽑혔다"를 알 수 없기 때문이다. 호출자가 로그를 남긴다.
MAX_SEGMENTS = 20000


def header_size(head):
    """UnityFS 헤더에 적힌 **이 번들 전체 크기**. 헤더가 아니면 None.

    UnityFS 헤더 배치:
        magic cstring · version uint32(BE) · unityVersion cstring ·
        unityRevision cstring · size int64(BE)

    `head` 가 짧아 크기 필드에 못 닿으면 None 을 준다 (예외를 내지 않는다).
    """
    b = bytes(head or b"")
    if not b.startswith(MAGIC):
        return None
    p = len(MAGIC) + 4                       # 매직 + version uint32
    for _ in range(2):                       # unityVersion, unityRevision
        e = b.find(b"\x00", p)
        if e < 0:
            return None
        p = e + 1
    if p + 8 > len(b):
        return None
    size = struct.unpack_from(">q", b, p)[0]
    return size if size > 0 else None


def looks_concat(head, total):
    """앞부분 `head` 와 전체 크기 `total` 만 보고 "이어붙인 파일" 후보인가.

    전체를 읽지 않는다. 첫 번들에 적힌 크기가 파일보다 **뚜렷하게 작으면**
    뒤에 뭔가 더 있다는 뜻이다.
    """
    first = header_size(head)
    if first is None:
        return False
    return first + MIN_SEGMENT <= total


def segments(data):
    """이어붙인 bytes → [(offset, length)]. 이어붙인 게 아니면 빈 목록.

    각 번들 헤더의 크기 필드를 따라 걸어간다. 도중에 매직이 안 맞거나 크기가
    범위를 벗어나면 **빈 목록**을 준다 — 절반만 인정하면 "일부만 뽑힌 것"이
    정상처럼 보인다. 전부 맞아떨어질 때만 펼친다.
    """
    out, off, n = [], 0, len(data)
    while off < n:
        size = header_size(data[off:off + HEAD])
        if size is None or size < MIN_SEGMENT or off + size > n:
            return []
        out.append((off, size))
        off += size
        if len(out) > MAX_SEGMENTS:
            return []
    return out if len(out) > 1 else []


def sub_name(name, i):
    """i 번째 세그먼트의 가상 엔트리 이름."""
    return f"{name}{SEP}{i:04d}"


def parent_of(name):
    """가상 엔트리 이름 → (원래 이름, 인덱스). 가상 엔트리가 아니면 (name, None).

    `#` 뒤가 숫자일 때만 세그먼트로 본다. 원래 파일 이름에 `#` 이 들어 있어도
    (드물지만 가능하다) 잘못 자르지 않는다.
    """
    base, sep, tail = str(name).rpartition(SEP)
    if not sep or not tail.isdigit():
        return str(name), None
    return base, int(tail)
