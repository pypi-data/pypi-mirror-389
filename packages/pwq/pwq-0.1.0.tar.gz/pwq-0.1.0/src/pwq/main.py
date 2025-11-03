from __future__ import annotations

import subprocess
import sys
import threading
from typing import Any, Generator, Sequence, Tuple, Union, Literal, overload
from pathlib import Path
from tempfile import TemporaryDirectory
import tarfile
import re
from contextlib import contextmanager
import io
import shutil
import os

OptionStringOrPath = Union[str, Path, None]
StringOrPath = Union[str, Path]


class PackError(ValueError):
    pass

@overload
def run_command(command: Sequence[str], *, cwd: OptionStringOrPath = None, stream: Literal[True]) -> None: ...

@overload
def run_command(command: Sequence[str], *, cwd: OptionStringOrPath = None, stream: Literal[False] = False) -> Tuple[str, str]: ...


def run_command(command: Sequence[str], *, cwd: OptionStringOrPath = None, stream: bool = False):
    """Run a command.

    When stream=True, stdout/stderr are inherited by the current process and no value is returned.
    When stream=False, stdout/stderr are captured and returned as strings.
    """
    if stream:
        subprocess.run(command, check=True, cwd=cwd)
        return None
    completed = subprocess.run(command, check=True, cwd=cwd, text=True, capture_output=True)
    return completed.stdout, completed.stderr

def build_project(output_folder: StringOrPath, *, root_path: OptionStringOrPath = None) -> None:
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        run_command(["pdm", "build", "--no-wheel", "-d", str(tmp_path)], cwd=root_path, stream=True)

        pylock_path = Path(root_path) / "pylock.toml" if root_path is not None else Path("./pylock.toml")
        if not Path(pylock_path).exists():
            raise PackError(f"pylock.toml not found in current path or {root_path}")

        tar_files = list(tmp_path.glob("*.tar.gz"))
        if len(tar_files) != 1:
            raise PackError(f"Expected exactly one built tar.gz, got {len(tar_files)}")
        tar_path = tar_files[0]

        os.makedirs(output_folder, exist_ok=True)
        # out_path = Path(output_folder) / tar_path.name.replace(".tar.gz", ".qwq")
        out_path = Path(output_folder) / tar_path.name
        with tarfile.open(tar_path, mode="r:gz") as src, tarfile.open(out_path, mode="w:gz") as tf:
            tf.add(pylock_path, arcname=f"{tar_path.name.replace('.tar.gz', '')}/pylock.toml")
            for member in src.getmembers():
                if member.name == "pylock.toml":
                    continue
                tf.addfile(member, src.extractfile(member))


def init_project(*, cwd: OptionStringOrPath = None) -> None:
    stdout, stderr = run_command(["pdm", "venv", "create"], cwd=cwd)
    stdout, stderr = run_command(["pdm", "use", "./.venv/bin/python3"], cwd=cwd)
    stdout, stderr = run_command(["pdm", "sync", "--fail-fast", "--prod"], cwd=cwd)

def run_task_base(args: Sequence[str], cwd: OptionStringOrPath = None):
    run_command(["pdm", "run", "-p", str(cwd) if cwd else './', "python", "-m", *args], stream=True)



def extract(src: Path, tar: Path):
    with tarfile.open(src, mode="r:gz") as tf:
        tf.extractall(path=tar)
    top_dirs = [p for p in tar.iterdir() if p.is_dir()]
    if len(top_dirs) != 1:
        raise PackError(f"Expected 1 top directory, got {len(top_dirs)}")
    top_dir_name = top_dirs[0].name
    return tar / top_dir_name

@contextmanager
def extract_and_setup(target: StringOrPath):
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cwd = extract(Path(target), tmp_path)
        init_project(cwd=cwd)
        yield cwd


def cli() -> int:
    argv: list[str] = sys.argv[1:]
    if len(argv) == 0:
        print("hello")
        return 0
    elif len(argv) == 1:
        build_project(argv[0])
        return 0
    if len(argv) < 2:
        raise PackError("Usage: hello-pack <archive.tar.gz> <module> [args...]")
    target: str = argv[0]
    module_and_args: list[str] = argv[1:]
    with extract_and_setup(target) as cwd:
        run_task_base(module_and_args, cwd=cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
