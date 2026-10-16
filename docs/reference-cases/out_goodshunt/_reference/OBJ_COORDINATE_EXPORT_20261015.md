# OBJ coordinate export code audit

Scope: installed UnityPy exporter code inspection, no mesh re-extraction or asset parity test.

Source: `C:/Users/NHN/AppData/Local/Programs/Python/Python312/Lib/site-packages/UnityPy/export/MeshExporter.py`, `export_mesh_obj`.

- Vertex: native `(x,y,z)` -> OBJ `(-x,y,z)`.
- Normal: native `(nx,ny,nz)` -> OBJ `(-nx,ny,nz)`.
- UV0: `(u,v)` unchanged by this exporter.
- Face: native triangle `(a,b,c)` -> OBJ `(c+1,b+1,a+1)`; OBJ is 1-based.
- Groups: emitted per submesh; do not flatten away submesh boundaries when material slots matter.
- Floats formatted with `.9G`; NaN text replaced with zero. Export is not a raw byte-preserving mesh representation.

`UnityPy/helpers/MeshHelper.py:get_triangles` uses original index triples for Triangles topology. Strip and quad topologies are triangulated first, so these are not necessarily original triangle-index buffers.

To reconstruct native triangle order from an OBJ that has not already been modified by its importer: reflect position and normal X again, and reverse each face again (subtract OBJ index base if parsing text directly).

Rendering caveat: Three.js front-face convention and a wrapper's existing axis/negative-determinant transforms are separate from recovering native data. Native index order alone is not proof of the correct Three.js cull mode. Record native restoration separately from any render-only winding adjustment; do not recompute source normals as a side effect.

Boundary: this confirms installed exporter implementation. The old `D:/99.기타/levelscope/levelscope/assets.py` currently found is an older audio/material/font/text implementation without Mesh export, so it does not independently establish the exact historical caller or that every existing OBJ avoided subsequent processing. Existing completion receipt already identifies the OBJ files as UnityPy-derived coordinate exports; per-mesh parity has not been newly tested here.
