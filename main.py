import os
import subprocess
import sys
from pathlib import Path


os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def EnsureEnvironment() -> None:
    """Use project venv when IDE runs main.py with system Python (missing deps)."""
    try:
        import ttkbootstrap  # noqa: F401
        return
    except ImportError:
        pass

    ProjectRoot = Path(__file__).resolve().parent
    VenvPython = ProjectRoot / "venv" / "Scripts" / "python.exe"

    if VenvPython.is_file() and Path(sys.executable).resolve() != VenvPython.resolve():
        print(
            "Switching to project venv (dependencies are installed there)...",
            flush=True,
        )
        Completed = subprocess.run([str(VenvPython), str(Path(__file__).resolve()), *sys.argv[1:]])
        raise SystemExit(Completed.returncode)

    print(
        "\nMissing dependency: ttkbootstrap\n"
        "Install with:\n"
        "  pip install -r requirements.txt\n"
        "Or activate venv first:\n"
        "  .\\venv\\Scripts\\activate\n"
    )
    raise SystemExit(1)


def Main() -> None:
    """Entry point: start the desktop GUI."""
    from app import Application

    Application.CreateDefault().Run()


if __name__ == "__main__":
    EnsureEnvironment()
    Main()
