from pathlib import Path
import sys,gc
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]/'levelscope-publish-20261014'))
import cached_reader
from levelscope import typetree,hierarchy
import UnityPy
def scripts(input_path,sources,cfg,log):
    reg=typetree.ScriptRegistry()
    env=UnityPy.load(str(root/'input_prepared/assets/bin/Data/data.unity3d'))
    reg.add_env(env,'data.unity3d',alias='data.unity3d')
    del env;gc.collect()
    log('[registry] Original APK script value index '+str(reg.count))
    return reg
hierarchy._script_registry=scripts
from levelscope.cli import main
main()
