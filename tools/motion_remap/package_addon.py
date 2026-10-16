"""Build a source-only Blender add-on ZIP, excluding caches and game assets."""
import argparse
import hashlib
from pathlib import Path
import zipfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    out=Path(args.out).resolve()
    if out.exists():raise ValueError('Output exists')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ('__init__.py','core.py','engine.py','ui.py','batch.py','contacts.py','postprocess.py','sampling.py','controls.py','deform_export.py',
                     'README.md','example_preset.json','advanced_preset.json','control_profile_example.json'):
            archive.write(root/name,'motion_remap/'+name)
    print(out)
    print('SHA256',hashlib.sha256(out.read_bytes()).hexdigest())


if __name__=='__main__':main()
