import argparse
import shutil
from pathlib import Path
import sys

try:
    from importlib import resources
except Exception:
    import importlib_resources as resources  # type: ignore


def copy_notebooks(dest: Path) -> None:
    dest = Path(dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    pkg = "dwm_notebooks"
    copied = []

    try:
        root = resources.files(pkg)
        for res in root.iterdir():
            if res.name.endswith(".ipynb"):
                try:
                    with resources.as_file(res) as src_path:
                        shutil.copy(src_path, dest / res.name)
                except Exception:
                    with resources.open_binary(pkg, res.name) as fh:
                        (dest / res.name).write_bytes(fh.read())
                copied.append(res.name)
    except Exception:
        for name in resources.contents(pkg):
            if name.endswith(".ipynb"):
                with resources.open_binary(pkg, name) as fh:
                    (dest / name).write_bytes(fh.read())
                copied.append(name)

    if not copied:
        print("No notebook files found in package data.")
    else:
        print(f"Copied {len(copied)} files to: {dest}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract bundled notebooks to a destination folder.")
    parser.add_argument("--dest", "-d", default="~/dwm_notebooks", help="Destination folder (defaults to ~/dwm_notebooks)")
    args = parser.parse_args(argv)
    try:
        copy_notebooks(args.dest)
    except Exception as e:
        print("Error while extracting notebooks:", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
