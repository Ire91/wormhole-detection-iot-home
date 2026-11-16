#!/usr/bin/env python3
import sys

def check_import(name):
    try:
        mod = __import__(name)
        ver = getattr(mod, '__version__', None)
        return True, ver
    except Exception:
        return False, None

def main():
    print("Environment Check:")
    print("Python:", sys.version.split()[0])
    # Pip version (best-effort)
    try:
        import pip
        print("Pip:", getattr(pip, '__version__', 'unknown'))
    except Exception:
        print("Pip: not importable")

    reqs = ["flask", "flask_cors", "pytest", "pandas", "numpy"]
    for m in reqs:
        ok, ver = check_import(m)
        if ok:
            print(f"{m}: installed, version={ver}")
        else:
            print(f"{m}: NOT INSTALLED")

    # Basic version floor
    if sys.version_info < (3, 8):
        print("Warning: Python version below 3.8; consider upgrading for compatibility.")

if __name__ == '__main__':
    main()
