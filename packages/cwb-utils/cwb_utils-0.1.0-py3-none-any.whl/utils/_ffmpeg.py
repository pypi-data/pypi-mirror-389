import os
import sys

from utils._assets import _assets
from utils._file import _file
from utils._url import _url


class _ffmpeg:
    @staticmethod
    def get_ffmpeg_assets_file_path() -> str | None:
        if platform := sys.platform.startswith("win"):
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z"
            file_path = _assets.get_assets_file_path(f"win{os.sep}{os.path.basename(url)}")
            if not (file_path := _url.to_file_path(url, file_path=file_path, use_tqdm=True)):
                return None
            dir_path = _assets.get_assets_file_path(f"win{os.sep}ffmpeg")
            dir_path = _file.decompress(file_path, dir_path)
            if dir_path is None:
                return None
            return ""
        else:
            return None


__all__ = [
    "_ffmpeg"
]
