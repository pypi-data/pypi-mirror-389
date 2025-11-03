import inspect
import os
from pathlib import Path


class _assets:
    @staticmethod
    def get_assets_file_path(path: str) -> str:
        assets_dir_path_p = Path(__file__).absolute().parent / Path(__file__).absolute().stem
        caller_dir_path_p = Path(inspect.stack()[1].filename).parent / Path(inspect.stack()[1].filename).stem

        mid_dir_path = os.path.relpath(caller_dir_path_p, assets_dir_path_p).lstrip(os.path.pardir + os.path.sep)
        assets_file_path = str(assets_dir_path_p / mid_dir_path / path)
        return assets_file_path


__all__ = [
    "_assets"
]
