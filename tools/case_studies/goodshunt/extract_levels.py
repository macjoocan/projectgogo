from pathlib import Path
import sys, json, hashlib, collections, gc
import UnityPy
root = Path(__file__).resolve().parent
base = root / 'input_prepared/assets/aa/Android'
out = root / 'levels_json'
out.mkdir(exist_ok=True)
rows, errors = [], []
types = collections.Counter()
for idx, p in enumerate(sorted(base.glob('levels_assets_*.bundle')), 1):
    try:
        env = UnityPy.load(str(p))
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        for obj in env.objects:
            types[obj.type.name] += 1
            if obj.type.name != 'MonoBehaviour':
                continue
            d = obj.read_typetree()
            name = d.get('m_Name', '')
            if 'props' not in d or 'timer' not in d:
                errors.append(dict(source=p.name, path_id=obj.path_id, reason='unexpected schema', keys=list(d)))
                continue
            filename = f'{idx:04d}_{obj.path_id}.json'
            dest = out / filename
            dest.write_text(json.dumps(d, ensure_ascii=False, indent=1, allow_nan=False), encoding='utf-8')
            rows.append(dict(file=filename, name=name, source=p.name, file_id=obj.assets_file.name,
                             path_id=obj.path_id, source_sha256=sha,
                             json_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                             props=len(d['props']), timer=d['timer'], difficulty=d.get('levelDifficulty'),
                             game_mode=d.get('gameMode'), goal_types=d.get('goalMechanicTypes'),
                             goals=d.get('goalsUniqueIDs'), keys=list(d)))
        del env
        gc.collect()
    except Exception as e:
        errors.append(dict(source=p.name, reason=repr(e)))
    if idx % 100 == 0:
        print(idx, len(rows), len(errors), flush=True)
result = dict(bundle_count=idx, levels=rows, errors=errors, types=dict(types),
              total_props=sum(r['props'] for r in rows),
              difficulty_counts=dict(collections.Counter(str(r['difficulty']) for r in rows)),
              game_mode_counts=dict(collections.Counter(str(r['game_mode']) for r in rows)),
              duplicate_names={k:v for k,v in collections.Counter(r['name'] for r in rows).items() if v>1})
(root / 'level_index.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
print('levels', len(rows), 'errors', len(errors), 'props', result['total_props'])
sys.exit(bool(errors))
