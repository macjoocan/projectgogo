"""단일 HTML 레벨 뷰어 생성 (보드 캔버스 렌더 + 카드 + 상세 모달)."""
import base64
import json
import os
import re

_CH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _rle(s):
    out, i = [], 0
    while i < len(s):
        c, j = s[i], i
        while j < len(s) and s[j] == c:
            j += 1
        n = j - i
        out.append("~%s%x;" % (c, n) if n >= 4 else c * n)
        i = j
    return "".join(out)


def encode_board(board):
    """board(dict) -> (w,h,rle,ov_fill,ov_outline). 없으면 None"""
    if not board:
        return None
    w, h = board["w"], board["h"]
    grid = ["."] * (w * h)
    for x, y, m in board["cells"]:
        if 0 <= x < w and 0 <= y < h and isinstance(m, int) and 0 <= m < len(_CH):
            grid[y * w + x] = _CH[m]
    fill, outline = [], []
    for ov in board["overlays"].values():
        dst = outline if ov["style"] == "outline" else fill
        for x, y in ov["points"]:
            if x is not None and y is not None:
                dst.extend((x, y))
    return w, h, _rle("".join(grid)), fill, outline


_MIME = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg",
         "jpeg": "image/jpeg", "svg": "image/svg+xml"}


def _data_url(path):
    mime = _MIME.get(path.rsplit(".", 1)[-1].lower(), "image/png")
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def _load_icons(icon_dir, wanted=None):
    """icon_dir의 이미지를 data URL로. wanted가 있으면 그 이름들만 (HTML 비대화 방지).

    타일 이미지가 수십 장인 게임(SheepNSheep의 card0~32)에서 뱃지용으로 전부 싣지
    않도록 badges가 실제로 참조하는 것만 넣는다.
    """
    icons = {}
    if not icon_dir or not os.path.isdir(icon_dir):
        return icons
    for f in sorted(os.listdir(icon_dir)):
        if not f.lower().endswith((".webp", ".png", ".jpg", ".jpeg", ".svg")):
            continue
        key = os.path.splitext(f)[0]
        if wanted is not None and key not in wanted:
            continue
        icons[key] = _data_url(os.path.join(icon_dir, f))
    return icons


def _load_tile_type_images(vcfg, cfg):
    """viewer.tile_type_pattern("card{}") + icon_dir 을 훑어 {타입번호: data URL}.

    타일 얼굴 이미지가 타입 번호로 이름 붙어 있는 게임용 (예: 블록타입 3 → card3.png).
    explicit 지정(viewer.tile_type_images: {3: card3})도 함께 반영한다.
    """
    out = {}
    icon_dir = vcfg.get("icon_dir")
    if icon_dir and not os.path.isabs(icon_dir):
        icon_dir = os.path.join(cfg["_config_dir"], icon_dir)
    if not icon_dir or not os.path.isdir(icon_dir):
        return out
    pattern = vcfg.get("tile_type_pattern")
    if pattern and "{}" in pattern:
        pre, _, suf = pattern.partition("{}")
        rx = re.compile(re.escape(pre) + r"(\d+)" + re.escape(suf) +
                        r"\.(?:png|webp|jpe?g)$", re.I)
        for f in sorted(os.listdir(icon_dir)):
            m = rx.fullmatch(f)
            if m:
                out[m.group(1)] = _data_url(os.path.join(icon_dir, f))
    for tp, fn in (vcfg.get("tile_type_images") or {}).items():
        for ext in ("", ".png", ".webp", ".jpg"):
            p = os.path.join(icon_dir, str(fn) + ext)
            if os.path.isfile(p):
                out[str(tp)] = _data_url(p)
                break
    return out


def _load_tile_images(vcfg, cfg):
    """viewer.tile_images: {키: 파일명} → data URL (icon_dir 기준)"""
    out = {}
    icon_dir = vcfg.get("icon_dir")
    if icon_dir and not os.path.isabs(icon_dir):
        icon_dir = os.path.join(cfg["_config_dir"], icon_dir)
    for key, fn in (vcfg.get("tile_images") or {}).items():
        for ext in ("", ".webp", ".png", ".jpg"):
            p = os.path.join(icon_dir or "", str(fn) + ext)
            if os.path.isfile(p):
                out[key] = _data_url(p)
                break
    return out


def build_viewer(records, cfg, palette, mat_names, out_path, log=print):
    """records: [{set,level,row,board_enc,extra_viewer}] 리스트.

    viewer.render: "grid"(기본) — 셀 그리드 렌더 / "tiles" — 스프라이트 타일 스택 렌더
    (타일 매칭 장르: extra_viewer['tl'] = [l,x,y,type,flags,...] 플랫 배열,
     viewer.tile_images {base, ice, box}, viewer.tile_span(기본 2))
    """
    vcfg = cfg.get("viewer") or {}
    diff_field = vcfg.get("difficulty_field")
    diff_order = vcfg.get("difficulty_order") or []
    badge_map = vcfg.get("badges") or {}        # counts 컬럼 -> 아이콘 키
    labels = vcfg.get("labels") or {}           # counts 컬럼 -> 표시 이름
    tag_legend = vcfg.get("entity_tags") or {}  # 태그코드 -> [이모지, 라벨]
    icon_dir = vcfg.get("icon_dir")
    if icon_dir and not os.path.isabs(icon_dir):
        icon_dir = os.path.join(cfg["_config_dir"], icon_dir)
    icons = _load_icons(icon_dir, wanted=set(badge_map.values()) or None)
    count_cols = list((cfg.get("fields", {}).get("counts") or {}).keys())
    stat_cols = vcfg.get("card_stats") or []

    sets, sidx = [], {}
    for r in records:
        if r["set"] not in sidx:
            sidx[r["set"]] = len(sets)
            sets.append(r["set"])
    set_counts = [0] * len(sets)
    levels = []
    for r in sorted(records, key=lambda r: (sidx[r["set"]], str(r["level"]).zfill(8))):
        set_counts[sidx[r["set"]]] += 1
        row = r["row"]
        d = diff_order.index(row.get(diff_field)) if diff_field and row.get(diff_field) in diff_order else -1
        gm = {c: row[c] for c in count_cols if row.get(c)}
        enc = r.get("board_enc")
        ex = r.get("extra_viewer") or {}
        w = ex.get("tw", enc[0] if enc else 0)
        h = ex.get("th", enc[1] if enc else 0)
        levels.append([sidx[r["set"]], r["level"], d, w, h,
                       enc[2] if enc else "",
                       enc[3] if enc else [], enc[4] if enc else [], gm,
                       {c: row.get(c) for c in stat_cols}, 1 if row.get("isValid", True) else 0,
                       ex.get("ma", []), ex.get("sq", []),
                       ex.get("tl", []), ex.get("lc", 0)])
    data = {"sets": sets, "setCounts": set_counts, "levels": levels,
            "title": vcfg.get("title") or cfg.get("game", "Level Viewer"),
            "subtitle": vcfg.get("subtitle", ""), "diffs": diff_order,
            "statCols": stat_cols, "statLabels": vcfg.get("stat_labels") or {},
            "mode": vcfg.get("render", "grid"), "tileSpan": vcfg.get("tile_span", 2),
            "queueTitle": vcfg.get("queue_title", ""), "queueHint": vcfg.get("queue_hint", ""),
            # 카드/모달 렌더 영역(px)과 타일을 자기 칸보다 얼마나 줄여 그릴지(0~0.5)
            "cardPx": list(vcfg.get("card_px") or (230, 190)),
            "modalPx": list(vcfg.get("modal_px") or (480, 560)),
            "tileInset": vcfg.get("tile_inset", 0),
            # 타일 1개를 그릴 최대 px. 보드가 몇 타일 안 되는 게임은 이게 없으면
            # 타일이 카드를 꽉 채워 과하게 커진다 (SheepNSheep 43px vs Zen Match 24px)
            "tilePx": vcfg.get("tile_px", 0),
            "tilePxModal": vcfg.get("tile_px_modal", 0)}
    html = (_TEMPLATE
            .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            .replace("__PAL__", json.dumps(palette))
            .replace("__MATN__", json.dumps(mat_names))
            .replace("__ICONS__", json.dumps(icons))
            .replace("__TIMG__", json.dumps(_load_tile_images(vcfg, cfg)))
            .replace("__TTIMG__", json.dumps(_load_tile_type_images(vcfg, cfg)))
            .replace("__BADGE__", json.dumps(badge_map))
            .replace("__LBL__", json.dumps(labels, ensure_ascii=False))
            .replace("__TAGE__", json.dumps(tag_legend, ensure_ascii=False)))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"[html] 저장: {out_path} ({os.path.getsize(out_path) / 1e6:.1f}MB, {len(levels)}레벨)")


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Level Viewer</title>
<style>
:root{--bg:#12141c;--card:#1c1f2b;--card2:#232738;--line:#2e3348;--tx:#e8eaf2;--tx2:#9aa1b8;--ac:#5b8cff}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--tx);font:14px/1.5 'Segoe UI','Noto Sans KR',sans-serif}
header{position:sticky;top:0;z-index:10;background:rgba(18,20,28,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:14px 22px}
h1{font-size:18px;font-weight:700}h1 small{color:var(--tx2);font-weight:400;margin-left:8px;font-size:13px}
.controls{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px;align-items:center}
select,input[type=text]{background:var(--card2);color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:13px}
input[type=text]{width:110px}
.chip{cursor:pointer;user-select:none;border:1px solid var(--line);border-radius:20px;padding:4px 12px;font-size:12px;color:var(--tx2);background:var(--card)}
.chip.on{color:#fff;border-color:transparent}
.chip[data-d="0"].on{background:#2e7d32}.chip[data-d="1"].on{background:#9e7c1a}.chip[data-d="2"].on{background:#d2691e}.chip[data-d="3"].on{background:#b03030}.chip[data-d="4"].on{background:#7b2fbe}.chip[data-d="5"].on{background:#455}
.count{color:var(--tx2);font-size:12px;margin-left:auto}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;padding:18px 22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;transition:transform .1s,border-color .1s}
.card:hover{transform:translateY(-2px);border-color:var(--ac)}
.cv{display:flex;align-items:center;justify-content:center;background:#0d0f16;height:var(--cvh,200px)}
canvas{image-rendering:pixelated}
.hd{display:flex;align-items:center;gap:8px;padding:8px 12px 2px}
.lv{font-weight:700;font-size:15px}
.diff{font-size:10.5px;font-weight:600;padding:2px 8px;border-radius:10px;color:#fff}
.d0{background:#2e7d32}.d1{background:#9e7c1a}.d2{background:#d2691e}.d3{background:#b03030}.d4{background:#7b2fbe}.d5{background:#455}
.inv{font-size:10.5px;padding:2px 7px;border-radius:10px;background:#442;color:#fa5}
.setname{font-size:10px;color:var(--tx2);margin-left:auto}
.stats{display:flex;flex-wrap:wrap;gap:4px 12px;padding:4px 12px;color:var(--tx2);font-size:11.5px}
.stats b{color:var(--tx);font-weight:600}
.badges{display:flex;flex-wrap:wrap;gap:5px;padding:6px 12px 11px;min-height:22px}
.bdg{display:inline-flex;align-items:center;gap:4px;background:var(--card2);border:1px solid var(--line);border-radius:7px;padding:2px 7px;font-size:11px}
.bdg img{width:20px;height:20px;object-fit:contain}
.cbar{display:flex;height:7px;border-radius:4px;overflow:hidden;margin:5px 12px 0}
#modal{position:fixed;inset:0;background:rgba(0,0,0,.72);display:none;align-items:center;justify-content:center;z-index:99;padding:20px}
#modal.on{display:flex}
.mbox{background:var(--card);border:1px solid var(--line);border-radius:16px;max-width:1060px;width:100%;max-height:92vh;overflow:auto;padding:22px;display:flex;gap:22px;flex-wrap:wrap}
.mleft{flex:1 1 380px;display:flex;align-items:flex-start;justify-content:center;background:#0d0f16;border-radius:12px;padding:14px}
.mright{flex:1 1 320px;min-width:300px}
.mright h2{font-size:20px;margin-bottom:4px}
.mright table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
.mright td{padding:4px 6px;border-bottom:1px solid var(--line)}
.mright td:first-child{color:var(--tx2);width:44%}
.mbadges{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.mbadges .bdg{font-size:12px}.mbadges .bdg img{width:26px;height:26px}
.mclose{position:fixed;top:18px;right:26px;font-size:26px;color:#fff;cursor:pointer;opacity:.7;z-index:100}
.legend{display:flex;flex-wrap:wrap;gap:4px;margin-top:10px}
.sw{width:16px;height:16px;border-radius:4px;border:1px solid rgba(255,255,255,.15)}
.mshoot{flex:1 1 100%;border-top:1px solid var(--line);padding-top:14px}
.mshoot h3{font-size:14px;margin-bottom:2px}
.mshoot .sub{color:var(--tx2);font-size:11.5px;margin-bottom:10px}
.qrow{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
.qlab{flex:0 0 92px;font-size:12px;color:var(--tx2);padding-top:7px;text-align:right}
.qlab b{color:var(--tx)}
.qs{display:flex;flex-wrap:wrap;gap:5px}
.sq{position:relative;width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;border:1px solid rgba(255,255,255,.18)}
.sq.dark{color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.6)}.sq.light{color:#1a1a1a}
.sq .tg{position:absolute;top:-6px;right:-6px;font-size:11px;filter:drop-shadow(0 1px 1px rgba(0,0,0,.7))}
.sq .tg2{position:absolute;bottom:-6px;right:-6px;font-size:11px;filter:drop-shadow(0 1px 1px rgba(0,0,0,.7))}
.sq.img{width:42px;height:42px;background:#f4efe4 center/78% no-repeat;align-items:flex-end;justify-content:flex-end}
.sq.img .n{background:rgba(0,0,0,.62);color:#fff;font-size:10.5px;line-height:1;padding:2px 3px;border-radius:5px;margin:2px}
.tglegend{display:flex;flex-wrap:wrap;gap:4px 14px;color:var(--tx2);font-size:11.5px;margin-top:8px}
footer{color:var(--tx2);font-size:11.5px;padding:8px 22px 26px}
</style></head><body>
<header><h1 id="t"></h1>
<div class="controls">
  <select id="fset"></select><span id="fdiffs"></span>
  <select id="fgim"><option value="">요소: 전체</option></select>
  <select id="fvalid"><option value="">isValid: 전체</option><option value="1">valid만</option><option value="0">invalid만</option></select>
  <input type="text" id="fq" placeholder="레벨 번호">
  <span class="count" id="cnt"></span>
</div></header>
<div id="grid"></div>
<footer id="ft"></footer>
<div id="modal"><span class="mclose" onclick="closeModal()">✕</span><div class="mbox" id="mbox"></div></div>
<script>
const DATA=__DATA__, PAL=__PAL__, MATN=__MATN__, ICONS=__ICONS__, TIMG=__TIMG__, TTIMG=__TTIMG__, BADGE=__BADGE__, LBL=__LBL__, TAGE=__TAGE__;
const DIFFS=DATA.diffs, STATS=DATA.statCols, SLBL=DATA.statLabels, MODE=DATA.mode, SPAN=DATA.tileSpan||2;
const CARDPX=DATA.cardPx||[230,190], MODALPX=DATA.modalPx||[480,560], TINSET=DATA.tileInset||0;
const TILEPX=DATA.tilePx||0, TILEPXM=DATA.tilePxModal||0;
document.documentElement.style.setProperty('--cvh',(CARDPX[1]+16)+'px');
const CH='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
document.getElementById('t').innerHTML=DATA.title+(DATA.subtitle?` <small>${DATA.subtitle}</small>`:'');
document.getElementById('ft').textContent='levelscope 생성 · 총 '+DATA.levels.length+'레벨'+(MODE==='tiles'?' · 타일 원본 스프라이트 렌더 · 모달에서 레이어 슬라이더로 겹침 확인':' · 색상 팔레트 '+PAL.length+'색');
function unrle(s){return s.replace(/~(.)([0-9a-f]+);/g,(m,c,n)=>c.repeat(parseInt(n,16)));}
const L=DATA.levels.map(r=>({si:r[0],l:r[1],d:r[2],w:r[3],h:r[4],g:r[5],wl:r[6],ky:r[7],gm:r[8],st:r[9],iv:r[10],ma:r[11],sq:r[12],tl:r[13],lc:r[14]}));
const setShort=DATA.sets.map(s=>String(s).slice(0,6)+'…');
const IMG={}, FACE={};
for(const k in TIMG){const im=new Image();im.src=TIMG[k];IMG[k]=im;}
for(const k in TTIMG){const im=new Image();im.src=TTIMG[k];FACE[k]=im;}
function ready(im){return im&&im.complete&&im.naturalWidth>0;}
function drawFit(ctx,im,bx,by,bw,bh){
  // 원본 비율 유지하며 박스 안에 맞춘다 (카드 아이콘이 정사각형이 아닌 게 섞여 있다)
  const s=Math.min(bw/im.naturalWidth,bh/im.naturalHeight);
  const w=im.naturalWidth*s,h=im.naturalHeight*s;
  ctx.drawImage(im,bx+(bw-w)/2,by+(bh-h)/2,w,h);
}
function renderTiles(cv,x,scale,maxLayer){
  // x.tl = [l,gx,gy,type,flags]*, 좌표는 0기준 정규화, 타일은 SPAN×SPAN 유닛 점유
  // type: -1 = 런타임 랜덤 배정(얼굴 없음), 그 외 = 고정 블록 → FACE[type] 그림
  const w=x.w,h=x.h;
  if(!w||!h||!x.tl.length){cv.width=cv.height=10;return;}
  let u=scale||Math.max(2,Math.min(CARDPX[0]/w,CARDPX[1]/h));
  if(!scale&&TILEPX) u=Math.max(0.5,Math.min(u,TILEPX/SPAN));   // 타일 최대 px 제한
  cv.width=Math.ceil(w*u+u); cv.height=Math.ceil(h*u+u);
  const ctx=cv.getContext('2d');
  ctx.fillStyle='#0d0f16';ctx.fillRect(0,0,cv.width,cv.height);
  const Lmax=Math.max(1,x.lc), lim=(maxLayer===undefined?Lmax:maxLayer);
  const base=IMG.base, ice=IMG.ice, box=IMG.box;
  // 타일을 자기 칸(SPAN×SPAN)보다 TINSET 만큼 줄여 그린다 — 겹친 타일 경계가 구분된다
  const cell=SPAN*u, ts=cell*(1-TINSET), off=(cell-ts)/2, skirt=ts*0.18, pad=ts*0.14;
  for(let li=0;li<lim;li++){
    const dim=0.45+0.55*((li+1)/Lmax);
    ctx.filter=`brightness(${dim.toFixed(3)})`;
    for(let i=0;i<x.tl.length;i+=5){
      if(x.tl[i]!==li)continue;
      const gx=x.tl[i+1], gy=x.tl[i+2], tp=x.tl[i+3], fl=x.tl[i+4];
      const px=gx*u+off, py=(h-gy-SPAN)*u+off - li*u*0.14;
      if(ready(base)){
        ctx.drawImage(base,px,py,ts,ts+skirt);
      }else{
        ctx.fillStyle='#f4efe4';ctx.beginPath();ctx.roundRect(px,py,ts,ts,ts*0.2);ctx.fill();
        ctx.strokeStyle='rgba(0,0,0,.25)';ctx.stroke();
      }
      const face=FACE[tp];
      if(ready(face)){
        drawFit(ctx,face,px+pad,py+pad,ts-2*pad,ts-2*pad);
      }else if(tp>=0&&ts>=14){
        ctx.filter='none';
        ctx.fillStyle='#5a4632';ctx.font=`bold ${Math.max(9,ts*0.34)}px sans-serif`;
        ctx.textAlign='center';ctx.textBaseline='middle';
        ctx.fillText(tp,px+ts/2,py+ts/2);
        ctx.filter=`brightness(${dim.toFixed(3)})`;
      }
      if(fl&1 && ready(ice)) ctx.drawImage(ice,px,py,ts,ts+skirt);
      if(fl&2 && ready(box)) ctx.drawImage(box,px,py,ts,ts+skirt);
    }
  }
  ctx.filter='none';
}
function render(cv,x,scale,maxLayer){
  if(MODE==='tiles'){renderTiles(cv,x,scale,maxLayer);return;}
  if(!x.w||!x.h){cv.width=cv.height=10;return;}
  const g=unrle(x.g),w=x.w,h=x.h;
  const cs=scale||Math.max(1,Math.floor(Math.min(CARDPX[0]/w,CARDPX[1]/h)));
  cv.width=w*cs;cv.height=h*cs;
  const ctx=cv.getContext('2d');
  ctx.fillStyle='#0d0f16';ctx.fillRect(0,0,cv.width,cv.height);
  for(let y=0;y<h;y++)for(let xx=0;xx<w;xx++){
    const c=g[y*w+xx];if(c==='.')continue;
    ctx.fillStyle=PAL[CH.indexOf(c)]||'#888';
    ctx.fillRect(xx*cs,(h-1-y)*cs,cs,cs);
  }
  ctx.fillStyle='rgba(120,120,135,0.85)';
  for(let i=0;i<x.wl.length;i+=2){ctx.fillRect(x.wl[i]*cs,(h-1-x.wl[i+1])*cs,cs,cs);}
  if(cs>=3){ctx.strokeStyle='rgba(0,0,0,.35)';for(let i=0;i<x.wl.length;i+=2){const X=x.wl[i],Y=x.wl[i+1];ctx.beginPath();ctx.moveTo(X*cs,(h-Y)*cs);ctx.lineTo((X+1)*cs,(h-1-Y)*cs);ctx.stroke();}}
  ctx.strokeStyle='#ffd54a';ctx.lineWidth=Math.max(1,cs*0.18);
  for(let i=0;i<x.ky.length;i+=2){ctx.strokeRect(x.ky[i]*cs+1,(h-1-x.ky[i+1])*cs+1,cs-2,cs-2);}
}
function badgeHtml(x,lim){
  const ks=Object.keys(x.gm);
  return ks.slice(0,lim===undefined?ks.length:lim).map(k=>{
    const ic=ICONS[BADGE[k]];
    return `<span class="bdg" title="${k}${LBL[k]?' ('+LBL[k]+')':''}">${ic?`<img loading="lazy" src="${ic}">`:''}${ic?'':k+' '}${x.gm[k]}</span>`;
  }).join('')+(lim!==undefined&&ks.length>lim?`<span class="bdg">+${ks.length-lim}</span>`:'');
}
function cbar(x){
  if(!x.ma||!x.ma.length)return'';
  return `<div class="cbar">`+x.ma.map(([m,a])=>`<span style="flex:${a};background:${PAL[m]}" title="${MATN[m]||m} ${a}"></span>`).join('')+`</div>`;
}
function lum(hex){return .299*parseInt(hex.slice(1,3),16)+.587*parseInt(hex.slice(3,5),16)+.114*parseInt(hex.slice(5,7),16);}
function tagInfo(t){const c=t[0],n=t.slice(1),e=TAGE[c]||['❔',c];let lab=e[1];if(n)lab+=' '+n;return [e[0],lab];}
function shooterHtml(x){
  if(!x.sq||!x.sq.length)return'';
  const used=new Set();
  const rows=x.sq.map(([lab,lst])=>{
    // 라벨 규약: 'Q<n>'=대기열, 'P<id>'=파이프, 그 외는 플러그인이 준 문구를 그대로 쓴다
    const name=/^Q\d+$/.test(lab)?`대기열 <b>${lab}</b>`
              :(/^P\S+$/.test(lab)?`파이프 <b>#${lab.slice(1)}</b>`:`<b>${lab}</b>`);
    const chips=lst.map(s=>{
      const [id,a,m]=s,tags=(s[3]||'').split(',').filter(Boolean);
      tags.forEach(t=>used.add(t[0]));
      const em=tags.slice(0,2).map((t,i)=>`<span class="${i?'tg2':'tg'}">${tagInfo(t)[0]}</span>`).join('');
      const url=TTIMG[id];
      if(url){   // 타일 얼굴 이미지가 있는 게임 — 실제 리소스로 칩을 그린다
        return `<span class="sq img" style="background-image:url(${url})" title="타입 ${id} · ${a}개">`
              +`<span class="n">${a}</span>${em}</span>`;
      }
      const hex=PAL[m]||'#888',cls=lum(hex)>150?'light':'dark';
      const tt=[`id ${id}`,MATN[m]||('mat'+m),`ammo ${a}`].concat(tags.map(t=>tagInfo(t)[1])).join(' · ');
      return `<span class="sq ${cls}" style="background:${hex}" title="${tt}">${a}${em}</span>`;
    }).join('');
    return `<div class="qrow"><span class="qlab">${name} · ${lst.length}</span><div class="qs">${chips}</div></div>`;
  }).join('');
  const leg=[...used].filter(c=>TAGE[c]).map(c=>`<span>${TAGE[c][0]} ${TAGE[c][1]}</span>`).join('');
  return `<div class="mshoot"><h3>${DATA.queueTitle||'슈터/엔티티 대기열'}</h3>`
        +`<div class="sub">${DATA.queueHint||'칸 안 숫자 = ammo · 색 = 색상 · 마우스 오버로 상세'}</div>`
        +`${rows}${leg?`<div class="tglegend">${leg}</div>`:''}</div>`;
}
function card(x,i){
  const el=document.createElement('div');el.className='card';el.dataset.i=i;
  const stats=STATS.map(c=>`<span>${SLBL[c]||c} <b>${x.st[c]??''}</b></span>`).join('');
  el.innerHTML=`<div class="cv"><canvas></canvas></div>
  <div class="hd"><span class="lv">Lv ${x.l}</span>${x.d>=0?`<span class="diff d${x.d}">${DIFFS[x.d]}</span>`:''}${x.iv?'':'<span class="inv">invalid</span>'}<span class="setname">${setShort[x.si]}</span></div>
  ${cbar(x)}<div class="stats"><span>보드 <b>${x.w}×${x.h}</b></span>${stats}</div>
  <div class="badges">${badgeHtml(x,6)}</div>`;
  el.onclick=()=>openModal(x);
  return el;
}
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){const el=e.target;render(el.querySelector('canvas'),L[+el.dataset.i]);io.unobserve(el);}})},{rootMargin:'400px'});
const fset=document.getElementById('fset'),fgim=document.getElementById('fgim'),fvalid=document.getElementById('fvalid'),fq=document.getElementById('fq'),fdiffs=document.getElementById('fdiffs');
fset.innerHTML=`<option value="">세트: 전체 (${L.length})</option>`+DATA.sets.map((s,i)=>`<option value="${i}">${String(s).slice(0,10)}… (${DATA.setCounts[i]})</option>`).join('');
const gset=new Set();L.forEach(x=>Object.keys(x.gm).forEach(k=>gset.add(k)));
fgim.innerHTML+=[...gset].sort().map(k=>`<option value="${k}">${k}${LBL[k]?' · '+LBL[k]:''}</option>`).join('');
let diffOn=new Set(DIFFS.map((_,i)=>i));diffOn.add(-1);
if(DIFFS.length){fdiffs.innerHTML=DIFFS.map((d,i)=>`<span class="chip on" data-d="${i}">${d}</span>`).join('');
fdiffs.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{const d=+c.dataset.d;const all=DIFFS.length+1;
if(diffOn.has(d)&&diffOn.size>=all){diffOn=new Set([d]);}else if(diffOn.has(d)){diffOn.delete(d);if(diffOn.size<=1){diffOn=new Set(DIFFS.map((_,i)=>i));diffOn.add(-1);}}else diffOn.add(d);
fdiffs.querySelectorAll('.chip').forEach(cc=>cc.classList.toggle('on',diffOn.has(+cc.dataset.d)));apply();});}
function apply(){
  const si=fset.value===''?null:+fset.value,gk=fgim.value||null,vv=fvalid.value,q=fq.value.trim();
  let list=L.map((x,i)=>[x,i]).filter(([x])=>(si===null||x.si===si)&&diffOn.has(x.d)&&(!gk||x.gm[gk])&&(vv===''||x.iv===+vv)&&(!q||String(x.l)===q||String(x.l).startsWith(q)));
  document.getElementById('cnt').textContent=list.length+' / '+L.length+' 레벨';
  const grid=document.getElementById('grid');grid.innerHTML='';
  const frag=document.createDocumentFragment();
  list.forEach(([x,i])=>{const el=card(x,i);frag.appendChild(el);io.observe(el);});
  grid.appendChild(frag);
}
[fset,fgim,fvalid].forEach(e=>e.onchange=apply);fq.oninput=apply;
function openModal(x){
  const mb=document.getElementById('mbox');
  const rows=[['세트',DATA.sets[x.si]],['보드 크기',x.w+' × '+x.h]].concat(STATS.map(c=>[SLBL[c]||c,x.st[c]??''])).concat([['isValid',x.iv?'true':'false']]);
  const slider=(MODE==='tiles'&&x.lc>1)?`<div style="margin-top:10px"><input type="range" id="lyr" min="1" max="${x.lc}" value="${x.lc}" style="width:100%"><div style="color:var(--tx2);font-size:12px" id="lyrlab">레이어 ${x.lc} / ${x.lc} 표시 — 슬라이더를 내리면 위 레이어부터 벗겨집니다</div></div>`:'';
  mb.innerHTML=`<div class="mleft" style="flex-direction:column"><canvas id="mcv"></canvas>${slider}</div><div class="mright"><h2>Level ${x.l} ${x.d>=0?`<span class="diff d${x.d}">${DIFFS[x.d]}</span>`:''}${x.iv?'':' <span class="inv">invalid</span>'}</h2>
  <table>${rows.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>
  ${cbar(x)}<div class="legend">${(x.ma||[]).map(([m,a])=>`<span class="sw" style="background:${PAL[m]}" title="${MATN[m]||m}: ${a}"></span>`).join('')}</div>
  <div class="mbadges">${badgeHtml(x)}</div></div>${shooterHtml(x)}`;
  let cs=Math.max(2,Math.min(MODALPX[0]/(x.w||1),MODALPX[1]/(x.h||1)));
  if(MODE==='tiles'&&TILEPXM) cs=Math.max(0.5,Math.min(cs,TILEPXM/SPAN));
  render(document.getElementById('mcv'),x,cs);
  const ly=document.getElementById('lyr');
  if(ly)ly.oninput=()=>{document.getElementById('lyrlab').textContent=`레이어 ${ly.value} / ${x.lc} 표시 — 슬라이더를 내리면 위 레이어부터 벗겨집니다`;render(document.getElementById('mcv'),x,cs,+ly.value);};
  document.getElementById('modal').classList.add('on');
}
function closeModal(){document.getElementById('modal').classList.remove('on');}
document.getElementById('modal').onclick=e=>{if(e.target.id==='modal')closeModal();};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
Promise.all(Object.values(IMG).map(im=>im.decode?im.decode().catch(()=>{}):Promise.resolve())).then(apply);
</script></body></html>"""
