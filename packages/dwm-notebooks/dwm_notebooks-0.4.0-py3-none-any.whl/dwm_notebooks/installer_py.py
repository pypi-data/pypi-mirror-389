import argparse
import shutil
import sys
from pathlib import Path

try:
    from importlib import resources
except Exception:  # pragma: no cover
    import importlib_resources as resources  # type: ignore


def copy_py_files(dest: Path) -> None:
    dest = Path(dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    pkg = "dwm_notebooks"
    copied = []

    try:
        root = resources.files(pkg)
        for res in root.iterdir():
            # copy from solutionpy subpackage if present
            if res.is_dir() and res.name == 'solutionpy':
                for child in res.iterdir():
                    if child.name.endswith('.py'):
                        try:
                            with resources.as_file(child) as src_path:
                                shutil.copy(src_path, dest / child.name)
                        except Exception:
                            with resources.open_binary(f"{pkg}.solutionpy", child.name) as fh:
                                (dest / child.name).write_bytes(fh.read())
                        copied.append(child.name)
    except Exception:
        # fallback for older importlib.resources API
        try:
            for name in resources.contents(f"{pkg}.solutionpy"):
                if name.endswith('.py'):
                    with resources.open_binary(f"{pkg}.solutionpy", name) as fh:
                        (dest / name).write_bytes(fh.read())
                    copied.append(name)
        except Exception:
            pass

    if not copied:
        print("No .py solution files found in package data.")
    else:
        print(f"Copied {len(copied)} files to: {dest}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract bundled .py solution files to a destination folder.")
    parser.add_argument("--dest", "-d", default="~/dwm_notebooks_py", help="Destination folder (defaults to ~/dwm_notebooks_py)")
    args = parser.parse_args(argv)
    try:
        copy_py_files(args.dest)
    except Exception as exc:
        print("Error while extracting .py files:", exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
