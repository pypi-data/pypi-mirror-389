import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pillow_avif  # type: ignore
from PIL import Image


class _image:
    @staticmethod
    def to_jpg(
            image_file_path: str,
            /,
            jpg_file_path: str | None = None,
            quality: int = 100,
            keep_original: bool = False
    ) -> str | None:
        try:
            image_file_path_p = Path(image_file_path).absolute()
            image_file_path = str(image_file_path_p)

            if jpg_file_path is None:
                jpg_file_path_p = image_file_path_p.parent / (image_file_path_p.stem + ".jpg")
            else:
                jpg_file_path_p = Path(jpg_file_path).absolute()
            jpg_file_path = str(jpg_file_path_p)

            if image_file_path == jpg_file_path:
                return jpg_file_path

            jpg_dir_path_p = jpg_file_path_p.parent
            jpg_dir_path = str(jpg_dir_path_p)
            jpg_dir_path_p.mkdir(parents=True, exist_ok=True)

            with Image.open(image_file_path) as image:
                if image.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode == "P":
                    image.seek(0)  # image.n_frames
                    image = image.convert("RGB")
                elif image.mode == "RGB":
                    pass
                else:
                    return None

                with NamedTemporaryFile(suffix=".jpg", delete=False, dir=jpg_dir_path) as ntf:
                    temp_file_path = ntf.name
                    image.save(temp_file_path, "JPEG", quality=quality)
                os.replace(temp_file_path, jpg_file_path)

            if not keep_original:
                p = Path(image_file_path)
                if p.exists() and str(p.resolve()) == str(p.absolute()):
                    os.remove(image_file_path)

            return jpg_file_path
        except Exception as e:  # noqa
            return None


__all__ = [
    "_image"
]
