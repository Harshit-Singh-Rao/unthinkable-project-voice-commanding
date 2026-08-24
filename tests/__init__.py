"""Test suite for EchoList.

Uses stdlib `unittest` rather than pytest, so there is no test framework to
install. pytest discovers and runs `unittest.TestCase` classes natively, so
`pytest` works too if it happens to be present.

The suite does still need the *runtime* dependencies, because it exercises the
real model and templates instead of mocks: `test_commands` and `test_hindi`
pull `onnxruntime` (via `intent.py`) and `test_render` pulls `Jinja2` (via
`render.py`). Run `pip install -r requirements.txt` first. The other four
modules - `test_nlp`, `test_search`, `test_state`, `test_data_integrity` - are
pure standard library.

    python -m unittest discover        # from the repo root
    python -m unittest tests.test_nlp  # one module
    python tests/test_nlp.py           # one file directly

Each test module bootstraps `server/` onto sys.path itself (see `_server_path`
below) rather than relying on this package being imported first, so all three
invocations above work. Modules import as `nlp`, `state`, ... exactly as they
do under gunicorn, where the working directory is `/app/server`.
"""
import os
import sys


def _server_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "server")


SERVER = _server_path()
if SERVER not in sys.path:
    sys.path.insert(0, SERVER)
