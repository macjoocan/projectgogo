import sys, json, hashlib, gc
from pathlib import Path
sys.path.insert(0, r'D:\99.기타\out_dkbi_probe\_deps')
import UnityPy
from UnityPy.streams import EndianBinaryWriter

OUT = Path(__file__).parent / 'shader_source'
sources = {
    'original_terrain': Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\SP\Resource\ECS-Map-High\ContentArchives\25f33c4faf67b7e10e7411fad9fab6fd'),
    'unity_textasset_control': Path(r'C:\00.SVN\Action\dkbi-replica\DKBI\reference\shader_bundle_template\container_template.bundle'),
}
results = {}
for label, path in sources.items():
    env = UnityPy.load(str(path))
    files = []
    for sf in env.assets:
        types = []
        for ty in sf.types:
            writer = EndianBinaryWriter()
            if ty.node:
                ty.node.dump_blob(writer, sf.header.version)
            blob = writer.bytes
            types.append({'class_id': ty.class_id, 'old_type_hash': bytes(ty.old_type_hash).hex(),
                          'tree_bytes': len(blob), 'tree_sha256': hashlib.sha256(blob).hexdigest()})
        objects = [{'class_id': o.type.value, 'path_id': str(o.path_id), 'bytes': o.byte_size} for o in sf.objects.values()]
        files.append({'unity_version': str(sf.unity_version), 'serialized_version': sf.header.version,
                      'target_platform': int(sf.target_platform), 'enable_type_tree': sf._enable_type_tree,
                      'types': types, 'objects': objects})
    results[label] = {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'files': files}
    del env
    gc.collect()
results['interpretation'] = {'unity_shader_control_available': False,
    'textasset_control_proves_shader_schema_compatible': False,
    'gpu_api_cause_confirmed': False,
    'scope': 'Small original archive and successful TextAsset control only. No Unity imports or mutations.'}
out = OUT / 'shader_compatibility_container_audit.json'
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
print(json.dumps(results, ensure_ascii=False))
