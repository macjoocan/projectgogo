"""추출한 이미지에 **분류 꼬리표**를 붙인다 — 만 장을 사람이 훑을 수 있게.

스프라이트가 1만 장이 넘으면 `Sprite/` 폴더 하나에 다 들어가서 사실상 볼 수 없다.
이름 앞에 `아이콘_` · `이펙트_` 같은 분류를 붙이고 분류별 폴더에 넣으면, 파일 탐색기든
zip 뷰어든 그냥 열어도 묶여 보인다.

**규칙은 상상해서 만들지 않았다.** CookieRun: Crumble 의 실제 이름 10,443개에서 뽑았다:

    icon_*                                  920개
    tex_fx_* / fx* / vfx*                   이펙트
    sactx-0-512x512-ASTC 6x6-...atlas-...   327개 (Unity SpriteAtlas 텍스처)
    mapthemeS01_bg_sky / mapthemeD03_*      배경
    profile_image_pet0064_2                 프로필
    tex_CutScene_Episode_5_83               컷신
    ImgCookieTalkHeadBack_2 / PopupGnomesLei2   UI
    cookie0025_run_00 / mc0028_skill2_00    캐릭터 (게임 고유 — 설정으로 추가)

그래서 **확실한 것만 분류하고, 애매하면 `기타` 로 둔다.** 틀린 이름을 붙이는 건
안 붙이는 것보다 나쁘다 — 뷰어 아이콘 자동 매칭에서 이미 겪은 일이다(CLAUDE.md).
게임 고유 낱말(cookie·maptheme·clash 같은 것)은 `sprites.categories` 로 설정에 적는다.
"""
import json
import os
import re

#: 기본 규칙 — 위에서부터 먼저 맞는 것이 이긴다. (분류, [낱말 또는 "re:정규식"])
#: 낱말은 장르·게임을 가리지 않는 것만 둔다. 게임 고유어는 설정으로 받는다.
DEFAULT_RULES = [
    # Unity SpriteAtlas 가 만든 아틀라스 텍스처 — 개별 스프라이트가 아니라 원본 시트다
    ("아틀라스", ["re:^sactx[-_]", "atlas", "spriteatlas"]),
    ("이펙트", ["fx", "vfx", "eff", "effect", "effects", "particle", "particles"]),
    ("아이콘", ["ico", "icon", "icons"]),
    ("컷신", ["cutscene", "cutscenes", "cinematic"]),
    ("프로필", ["profile", "portrait", "avatar", "thumbnail", "thumb"]),
    ("배경", ["bg", "background", "backgrounds", "maptheme", "sky", "skybox"]),
    ("UI", ["ui", "img", "image", "popup", "btn", "button", "title", "frame",
            "banner", "panel", "window", "slot", "badge", "gauge", "progress"]),
    ("폰트", ["font", "fonts", "glyph"]),
    # 아래 둘은 게임이 아니라 **그래픽스 관용 이름**이라 장르를 가리지 않는다.
    # 셰이더·머티리얼이 쓰는 맵과 노이즈·패턴류. Royal Match 의 `Smooth_Noise_Out`,
    # `Crown_Base_color`, PixelFlow 의 `BayerMatrix` 같은 것들이 여기 들어온다.
    ("텍스처", ["noise", "basecolor", "base_color", "normalmap", "roughness",
              "metallic", "specular", "mask", "gradient", "ramp", "pattern",
              "ptn", "dither", "bayer", "voronoi", "lut", "ldr", "matcap",
              "texture", "tex"]),
    ("그림자", ["shadow", "shadows"]),
]

#: 분류가 안 된 것
FALLBACK = "기타"

#: 짧은 낱말은 **토큰이 정확히 같을 때만** 인정한다. 안 그러면 "ui" 가 "guild" 에,
#: "bg" 가 "bigbang" 에 걸린다 (실제로 이 게임에 guild 가 49개 있다).
_SHORT = 3

#: CamelCase 경계 두 가지를 모두 본다.
#:   소문자→대문자   ImgFoo → Img|Foo
#:   약어→단어       UISprite → UI|Sprite   (이걸 안 보면 'ui' 가 안 걸린다)
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SPLIT = re.compile(r"[^0-9A-Za-z]+")
_TRAIL_DIGITS = re.compile(r"\d+$")


def tokens_of(name):
    """이름 → 소문자 토큰 목록. 구분자와 CamelCase 경계를 모두 자른다.

    `ImgCookieTalkHeadBack_2` 처럼 구분자가 없는 이름도 갈라야 UI 로 잡힌다.
    """
    spaced = _CAMEL.sub(" ", str(name or ""))
    return [t.lower() for t in _SPLIT.split(spaced) if t]


def _matches(word, toks, flat):
    if word.startswith("re:"):
        return re.search(word[3:], flat, re.I) is not None
    w = word.lower()
    if w in toks:
        return True
    # `mapthemes01`·`fx01`·`icon2` 처럼 뒤에 번호만 붙은 토큰도 같은 것으로 본다
    if any(t.startswith(w) and _TRAIL_DIGITS.fullmatch(t[len(w):] or "0") for t in toks):
        return True
    # 긴 낱말은 붙여 쓴 이름 안에서도 찾는다 (`texcutsceneepisode...`)
    return len(w) > _SHORT and w in flat.replace("_", "").replace("-", "")


def compile_rules(extra=None):
    """설정 규칙 + 기본 규칙. 설정이 **먼저** 온다(게임 고유어가 우선).

    설정 형식:
        categories:
          - {name: 캐릭터, match: ["re:^cookie\\\\d+_", "re:^mc\\\\d+_", "pet"]}
    """
    rules = []
    for item in (extra or []):
        if isinstance(item, dict) and item.get("name"):
            words = item.get("match") or item.get("words") or []
            if isinstance(words, str):
                words = [words]
            rules.append((str(item["name"]), [str(w) for w in words]))
    return rules + [(n, list(w)) for n, w in DEFAULT_RULES]


def classify(name, rules):
    """(분류, 맞은 낱말) — 아무 규칙도 안 맞으면 (FALLBACK, None)."""
    toks = tokens_of(name)
    flat = str(name or "").lower()
    for cat, words in rules:
        for w in words:
            if _matches(w, toks, flat):
                return cat, w
    return FALLBACK, None


class Tally:
    """분류 결과를 세고, 근거를 남긴다.

    어떤 규칙이 몇 개를 잡았는지와 분류 못 한 이름 표본을 zip 에 함께 넣는다.
    분류가 마음에 안 들면 그걸 보고 `sprites.categories` 를 고치면 된다.
    """

    def __init__(self, rules, unmatched_sample=40):
        self.rules = rules
        self.counts = {}
        self.by_word = {}
        self.unmatched = []
        self._cap = unmatched_sample

    def add(self, name):
        cat, word = classify(name, self.rules)
        self.counts[cat] = self.counts.get(cat, 0) + 1
        if word:
            self.by_word[f"{cat} ← {word}"] = self.by_word.get(f"{cat} ← {word}", 0) + 1
        elif len(self.unmatched) < self._cap:
            self.unmatched.append(name)
        return cat

    def summary_line(self):
        top = sorted(self.counts.items(), key=lambda kv: -kv[1])
        return " · ".join(f"{k} {v:,}" for k, v in top)

    def to_json(self):
        return json.dumps({
            "counts": dict(sorted(self.counts.items(), key=lambda kv: -kv[1])),
            "matched_by": dict(sorted(self.by_word.items(), key=lambda kv: -kv[1])),
            "unmatched_sample": self.unmatched,
            "rules": [{"name": n, "match": w} for n, w in self.rules],
            "note": ("분류가 틀렸거나 '기타'가 많으면 설정의 sprites.categories 에 "
                     "규칙을 추가하세요. unmatched_sample 이 그 힌트입니다."),
        }, ensure_ascii=False, indent=1)


def known_names(rules):
    """규칙이 낼 수 있는 분류 이름 전부 (미분류 포함)."""
    return {n for n, _w in rules} | {FALLBACK}


def strip_label(stem, known):
    """이미 붙어 있는 분류 접두어를 뗀다.

    같은 zip 에 두 번 돌려도 결과가 같아야 한다 — 안 그러면
    `아이콘_아이콘_foo` 처럼 겹쳐 쌓인다.
    """
    s = str(stem or "")
    for cat in sorted(known, key=len, reverse=True):
        if s.startswith(cat + "_"):
            return s[len(cat) + 1:]
    return s


def relabel_zip(src, dst, rules, log=print):
    """이미 뽑아 둔 스프라이트 zip 의 **이름만** 다시 붙인다. Tally 를 반환.

    APK 를 다시 열지 않는다 — UnityPy 도, 번들 파싱도, 텍스처 디코드도 없다.
    엔트리를 하나씩 읽어 새 이름으로 다시 쓰기만 하므로 메모리는 PNG 한 장 수준이다.
    그래서 이미 만들어 둔 산출물을 나중에 분류만 입히는 데 쓸 수 있다.

    png 가 아닌 엔트리(manifest 같은 것)는 그대로 옮긴다. `_categories.json` 은
    새로 만든 것으로 바꾼다.
    """
    import zipfile

    tally = Tally(rules)
    known = known_names(rules)
    seen, n_png, n_other, n_dup = set(), 0, 0, 0
    with zipfile.ZipFile(src) as zin, \
            zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not name.lower().endswith(".png"):
                if os.path.basename(name) != "_categories.json":
                    zout.writestr(info, zin.read(info))
                    n_other += 1
                continue
            stem = strip_label(os.path.splitext(os.path.basename(name))[0], known)
            cat = tally.add(stem)
            key = f"{cat}/{cat}_{stem}"
            # 타입 폴더가 다르던 동명이인이 한 분류로 합쳐질 수 있다 — 덮어쓰면 안 된다.
            # **대소문자를 무시해서** 비교한다: Windows 는 대소문자를 구분하지 않아
            # `shadow` 와 `Shadow` 가 zip 에선 둘이어도 풀면 하나가 된다 (실측 151건).
            uniq, i = key, 2
            while uniq.lower() in seen:
                uniq = f"{key}_{i}"
                i += 1
            seen.add(uniq.lower())
            if uniq != key:
                n_dup += 1
            zout.writestr(uniq + ".png", zin.read(info))
            n_png += 1
        zout.writestr("_categories.json", tally.to_json())
    log(f"[recategorize] 이미지 {n_png:,}장 재분류"
        + (f" · 그 외 엔트리 {n_other}개 그대로" if n_other else ""))
    if n_dup:
        log(f"[recategorize] 이름이 대소문자만 다른 {n_dup}건에 _2 접미를 붙였습니다"
            " — 안 그러면 Windows 에서 풀 때 덮어써져 사라집니다")
    log(f"[recategorize] {tally.summary_line()}")
    if tally.unmatched:
        log(f"[recategorize] 분류 못 한 이름 표본: {', '.join(tally.unmatched[:4])}"
            " … (_categories.json 참고)")
    return tally
