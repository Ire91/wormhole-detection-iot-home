import sys

def test_python_version():
    # Require at least Python 3.8 for modern packaging
    assert sys.version_info >= (3, 8), f"Python version too old: {sys.version}"

def test_core_dependencies():
    import importlib
    for mod in ["flask", "flask_cors", "pytest", "pandas", "numpy"]:
        try:
            importlib.import_module(mod)
        except Exception as e:
            raise AssertionError(f"Module {mod} not available: {e}")
