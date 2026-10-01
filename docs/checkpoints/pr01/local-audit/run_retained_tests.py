"""Local audit runner: retain all owned files instead of deleting them."""
import argparse
import importlib.resources
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--pattern', default='test*.py')
parser.add_argument('--report', required=True)
parser.add_argument('--installed', action='store_true')
args = parser.parse_args()
source = Path(args.source).resolve()
root = Path(__file__).resolve().parent / 'artifacts' / uuid.uuid4().hex
root.mkdir(parents=True)
archive = root / 'retained-unlinks'
archive.mkdir()
sys.dont_write_bytecode = True
os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8', TMP=str(root), TEMP=str(root))
tempfile.tempdir = str(root)
if args.installed:
    os.environ.pop('PYTHONPATH', None)
    os.environ.pop('PYTHONHOME', None)
    os.environ['PALETTE_TEST_CWD'] = str(root)
    os.chdir(root)
    import palette_lab
    installed_origin = Path(palette_lab.__file__).resolve()
    assert installed_origin.is_relative_to(Path(sys.prefix).resolve()), installed_origin
    assert not installed_origin.is_relative_to(source), installed_origin
    sys.path.insert(0, str(source / 'tests'))
    import test_exports
    test_exports.APP_JS = importlib.resources.files('palette_lab').joinpath('web', 'app.js')
else:
    sys.path.insert(0, str(source))
    os.chdir(source)

class RetainedDirectory:
    def __init__(self, *args, **kwargs):
        self.name = str(root / ('test-' + uuid.uuid4().hex))
        Path(self.name).mkdir()
    def __enter__(self):
        return self.name
    def __exit__(self, *args):
        pass
    def cleanup(self):
        pass

tempfile.TemporaryDirectory = RetainedDirectory
retained = []
def retain_unlink(path, missing_ok=False):
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise RuntimeError('Deletion prohibited outside owned audit root: ' + str(resolved))
    if not resolved.exists() and missing_ok:
        return
    destination = archive / (uuid.uuid4().hex + '-' + resolved.name)
    resolved.rename(destination)
    retained.append({'original': str(resolved), 'retained': str(destination)})
Path.unlink = retain_unlink
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(source / 'tests'), pattern=args.pattern))
out = {'tests': result.testsRun, 'failures': [str(t) for t,_ in result.failures],
       'errors': [str(t) for t,_ in result.errors], 'skipped': [str(t) for t,_ in result.skipped],
       'cleanup': 'not verified: all test-created directories and files retained',
       'artifact_root': str(root), 'retained_unlinks': retained}
Path(args.report).write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
