from pathlib import Path
import sys
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]/'levelscope-publish-20261014'))
import cached_reader
from levelscope.cli import main
main()
