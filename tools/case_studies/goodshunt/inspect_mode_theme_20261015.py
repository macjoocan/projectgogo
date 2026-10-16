from pathlib import Path
import json
p=Path(__file__).resolve().parent
s=(p/'inspect_bomb_followup_20261015.py').read_text(encoding='utf-8').split('# Existing JSON exports only;')[0]
s=s.replace('for a in [0x21B2628,0x1E42490,0x21DF174,0x21DC248]:',"for a in [a for a, rr in methods.items() if any('class GMode' in r['class'] and 'GetMapTheme()' in r['signature'] for r in rr)]:")
s=s.replace("out/f'bomb_disasm_{a:08x}.txt'","out/f'mode_theme_disasm_{a:08x}.txt'")
s=s.replace("for a in [a for a, rr in methods.items() if any('class GMode' in r['class'] and 'GetMapTheme()' in r['signature'] for r in rr)]:", "for a in sorted(set([0x21F4920,0x21F448C,0x21F3A2C,0x21F445C,0x1EBACA4,0x1EBA338,0x1EBA44C,0x1EBB1AC]+[a for a,rr in methods.items() if any('class GMode' in r['class'] and 'GetMapTheme()' in r['signature'] for r in rr)])):")
exec(compile(s,str(p/'inspect_bomb_followup_20261015.py'),'exec'))
rows=[{'rva':hex(a),'declarations':rr,'disasm_file':f'mode_theme_disasm_{a:08x}.txt'} for a,rr in methods.items() if any('class GMode' in r['class'] and 'GetMapTheme()' in r['signature'] for r in rr)]
(out/'mode_theme_methods.json').write_text(json.dumps(rows,indent=1),encoding='utf-8')
for r in rows:
 print(r['declarations'],r['rva']); print((out/r['disasm_file']).read_text(encoding='utf-8')[:1600])
