import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Literal, cast

from utils._assets import _assets


class _file:
    """
    https://www.rarlab.com/download.htm
    """
    COMPRESS_TYPE = Literal["zip", "rar"]
    DECOMPRESS_TYPE = Literal["zip", "rar"]

    @staticmethod
    def compress(
            path: str,
            compress_type: COMPRESS_TYPE | None = None,
            compress_file_path: str | None = None
    ) -> str | None:
        path_p = Path(path).absolute()
        path = str(path_p)

        if compress_file_path:
            compress_file_path_p = Path(compress_file_path).absolute()
            compress_file_path = str(compress_file_path_p)
            if compress_type is None:
                compress_type = compress_file_path_p.suffix[1:]
        else:
            if compress_type is None:
                compress_type = "zip"
            compress_file_path_p = path_p.parent / (path_p.stem + ("." + compress_type))
            compress_file_path = str(compress_file_path_p)

        if compress_type == "zip":
            with zipfile.ZipFile(compress_file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                if path_p.is_dir():
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if (file_path := os.path.join(root, file)) == compress_file_path:
                                continue
                            rel_file_path = os.path.relpath(file_path, path)
                            zf.write(file_path, arcname=rel_file_path)
                else:
                    rel_file_path = path_p.stem
                    zf.write(path, arcname=rel_file_path)
            return compress_file_path

        if compress_type == "rar":
            if sys.platform.startswith("win"):
                x = _assets.get_assets_file_path(str(Path("win") / "Rar.exe"))
            elif sys.platform == "darwin":
                x = _assets.get_assets_file_path(str(Path("mac") / "rar"))
            elif sys.platform.startswith("linux"):
                x = _assets.get_assets_file_path(str(Path("linux") / "rar"))
            else:
                return None
            args = [
                x,
                "a",
                "-r",
                "-inul",
                "-ep1",
                compress_file_path,
            ]
            if path_p.is_dir():
                args.append(str(path_p / "*"))
            else:
                args.append(path)
            if subprocess.run(args).returncode == 0:
                return compress_file_path

        return None

    @staticmethod
    def decompress(
            compress_file_path: str,
            path: str | None = None
    ) -> str | None:
        if not os.path.isfile(compress_file_path):
            return None

        compress_file_path_p = Path(compress_file_path).absolute()
        compress_file_path = str(compress_file_path_p)

        if path:
            path_p = Path(path).absolute()
        else:
            path_p = compress_file_path_p.parent
        path = str(path_p)
        path_p.mkdir(parents=True, exist_ok=True)

        with open(compress_file_path, "rb") as file:
            data = file.read(8)
        text = data.hex()
        if text in ("504b030414000000",):
            decompress_type = "zip"
        elif text in ("526172211a070100", "526172211a0700cf"):
            decompress_type = "rar"
        elif text in ('377abcaf271c0004',):
            decompress_type = "7z"
        else:
            return None

        if decompress_type == "zip":
            with zipfile.ZipFile(compress_file_path, "r") as zf:
                zf.extractall(path)
            return path

        if decompress_type == "rar":
            if sys.platform.startswith("win"):
                x = _assets.get_assets_file_path(str(Path("win") / "UnRAR.exe"))
            elif sys.platform == "darwin":
                x = _assets.get_assets_file_path(str(Path("mac") / "unrar"))
            elif sys.platform.startswith("linux"):
                x = _assets.get_assets_file_path(str(Path("linux") / "unrar"))
            else:
                return None
            args = [
                x,
                "x",
                "-o+",
                "-inul",
                compress_file_path,
                path
            ]
            if subprocess.run(args).returncode == 0:
                return path

        return None

    @staticmethod
    def get_file_paths_and_dir_paths(path: str) -> tuple[list[str], list[str]]:
        file_paths = []
        dir_paths = []

        path = str(Path(path).absolute())
        with os.scandir(path) as entries:
            for entry in entries:
                System = Literal["Windows", "Linux", "Darwin"]
                system: System = cast(System, platform.system())
                if system == "Windows":
                    from nt import DirEntry
                elif system == "Linux":
                    from posix import DirEntry
                elif system == "Darwin":
                    from posix import DirEntry
                else:
                    raise TypeError(
                        f"Invalid type for 'system': "
                        f"Expected `Literal[\"Windows\",\"Linux\",\"Darwin\"]`, "
                        f"but got {type(system).__name__!r} (value: {system!r})"
                    )

                entry: DirEntry
                if entry.is_file():
                    file_paths.append(entry.path)
                elif entry.is_dir():
                    dir_paths.append(entry.path)
                    sub_file_paths, sub_dir_paths = _file.get_file_paths_and_dir_paths(entry.path)
                    file_paths.extend(sub_file_paths)
                    dir_paths.extend(sub_dir_paths)

        return file_paths, dir_paths


__all__ = [
    "_file"
]
