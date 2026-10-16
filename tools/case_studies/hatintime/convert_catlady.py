from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'convert_hatkid_v2.py').read_text(encoding='utf-8');ls=s.splitlines();ls.insert(1,"sources=p/'raw/Maps/DLC_CatMetro/DLC_Metro/DLC_Metro';dest=p/'preview_catlady';dest.mkdir(exist_ok=True)");s='\n'.join(ls)
s=s.replace("('HatKidBody','HatKidHead','HatKidLegs')","('catLady_skm',)")
a=s.index("animbase=next(sources.rglob('HatKidV2_Anims'))");b=s.index('clipreports=[]',a)
s=s[:a]+"choices=[('Scale_Dialogue',next(sources.rglob('CatLady_anims/Elevator_button_idle.md5anim')))]\n"+s[b:]
s=s.replace('HatKid_five_motions','CatLady_scale_motion')
exec(compile(s,str(p/'convert_hatkid_v2.py'),'exec'),dict(__file__=str(p/'convert_hatkid_v2.py'),__name__='__main__'))
