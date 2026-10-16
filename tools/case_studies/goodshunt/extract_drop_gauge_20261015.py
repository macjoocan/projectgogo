from pathlib import Path
import json,re,bisect,hashlib,UnityPy,struct,zipfile
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/"drop_gauge_audit_20261015";dump=p/"code_audit_20261014/dump.cs"
methods={};cur="";pending=None;want=[]
for line in dump.open(encoding="utf-8"):
 if "// TypeDefIndex:" in line and not line.startswith("\t"):cur=line.strip();pending=None
 m=re.search(r"RVA: (0x[0-9A-F]+)",line)
 if m:pending=int(m[1],16)
 elif pending and "{ }" in line:
  a=pending;pending=None;methods.setdefault(a,[]).append({"class":cur,"signature":line.strip()})
  if "class AlternativeLinearProgressBar " in cur or "class HoleSizeUpgrade " in cur:want.append(a)
ks=sorted(methods)
lib=p/"ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so"
with lib.open("rb") as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s["p_type"]=="PT_LOAD"];md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
 for a in want:
  n=min(8192,ks[bisect.bisect_right(ks,a)]-a);seg=next(s for s in ss if s["p_vaddr"]<=a<s["p_vaddr"]+s["p_filesz"]);off=a-seg["p_vaddr"]+seg["p_offset"];f.seek(off);b=f.read(n)
  ls=[str(methods[a]),f"RVA={a:#x} ELF_offset={off:#x} next_declared_bound={a+n:#x}; not necessarily exact symbol size"]
  for i in md.disasm(b,a):
   anno=""
   if i.mnemonic in ["bl","b"] and i.op_str.startswith("#0x"):anno=" ; "+str(methods.get(int(i.op_str[1:],16),[]))
   ls.append(f"{i.address:08x} {i.mnemonic:8} {i.op_str}{anno}")
  (out/f"disasm_{a:08x}.txt").write_text("\n".join(ls),encoding="utf-8")
env=UnityPy.load(str(p/"input_prepared/assets/bin/Data/data.unity3d"));objs={(o.assets_file.name,o.path_id):o for o in env.objects};records={}
structured=zipfile.ZipFile(p/"results/GoodsHunt_structured_objects.zip")
existing={}
for line in (p/"results/native_object_index.jsonl").open(encoding="utf-8"):
 rr=json.loads(line)
 if rr.get("json_file"):existing[(rr["serialized_file"],rr["path_id"])]=rr
def add(ob):
 key=f"{ob.assets_file.name}#{ob.path_id}"
 if key not in records:
  rawsha=hashlib.sha256(ob.get_raw_data()).hexdigest();mode="UnityPy_native_typetree";err=None
  try:data=ob.read_typetree()
  except ValueError as exc:
   err=str(exc);rr=existing[(ob.assets_file.name,ob.path_id)]
   assert rawsha==rr["raw_sha256"], (key,"fallback_raw_sha_mismatch")
   data=json.loads(structured.read(rr["json_file"]));mode="previous_structured_schema_raw_sha_matched"
  records[key]={"file":ob.assets_file.name,"path_id":str(ob.path_id),"type":ob.type.name,"fields":data,"raw_sha256":rawsha,"decode_mode":mode,"native_typetree_error":err}
 return records[key]
def ref(ob,ptr):
 if not ptr.get("m_PathID"):return None
 name=ob.assets_file.name;fid=ptr.get("m_FileID",0)
 if fid:
  ext=ob.assets_file.externals[fid-1];name=ext.path.rsplit("/",1)[-1]
 return objs.get((name,ptr["m_PathID"]))
player=objs[("sharedassets3.assets",1893)];pd=add(player)["fields"];bar=ref(player,pd["energyFill"]);bd=add(bar)["fields"]
seed=[bar,ref(player,pd["canvasProgressRT"]),ref(player,pd["txtHoleSizeBitMap"]),objs[("sharedassets3.assets",1833)]]
seed += [ref(bar,bd[k]) for k in ["rectProgressBar","rectMask","imgBorder","imgBG","imgFill"]]
for st in [pd["normalPropressUI"],pd["boosterPropressUI"]]:seed += [ref(player,st["ProgressBarInnerT2D"]),ref(player,st["ArrowT2D"])]
# Walk UI reference GO/TR/component chain only; no texture pixel decode or full extraction.
for ob in seed:
 if ob is None:continue
 r=add(ob);d=r["fields"]
 for k in ["m_Sprite"]:
  if k in d:
   o=ref(ob,d[k])
   if o:add(o)
 if "m_GameObject" in d:
  go=ref(ob,d["m_GameObject"])
  if go:
   gd=add(go)["fields"]
   for comp in gd["m_Component"]:
    o=ref(go,comp.get("component",comp))
    if o:add(o)
# Parent chain of progress canvas RT: Canvas renderMode and native transforms.
root=ref(player,pd["canvasProgressRT"]);seen=set();parents=[]
while root and root.path_id not in seen:
 seen.add(root.path_id);d=add(root)["fields"];go=ref(root,d["m_GameObject"]);gd=add(go)["fields"]
 parents.append({"file":root.assets_file.name,"transform_id":str(root.path_id),"name":gd["m_Name"]})
 for c in gd["m_Component"]:
  o=ref(go,c.get("component",c))
  if o:add(o)
 root=ref(root,d["m_Father"])
report={"grade":"original_stored_values","player":{"file":"sharedassets3.assets","path_id":"1893"},"energy_bar":{"file":bar.assets_file.name,"path_id":str(bar.path_id)},"canvas_parent_chain":parents,"records":list(records.values())}
(out/"size_gauge_native_chain.json").write_text(json.dumps(report,ensure_ascii=False,indent=1,default=lambda v: {"bytes_hex":v.hex(),"byte_count":len(v)} if isinstance(v,bytes) else (_ for _ in ()).throw(TypeError(type(v).__name__))),encoding="utf-8")
print("records",len(records),"bar",bd,"parents",parents)
