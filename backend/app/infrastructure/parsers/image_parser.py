import io

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.core.exceptions import AppError
from app.domain.interfaces.parser import ExtractedDocument


class ImageParser:
    def parse(
        self,
        data: bytes,
        *,
        settings: Settings,
        force_ocr: bool = False,
    ) -> ExtractedDocument:
        del force_ocr
        image = load_image(data, settings)
        prepared = prepare_for_ocr(image)
        buffer = io.BytesIO()
        prepared.save(buffer, format="PNG")
        return ExtractedDocument([], 1, [buffer.getvalue()], [])


def load_image(data: bytes, settings: Settings) -> Image.Image:
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise AppError(400, "CORRUPTED_FILE", "La imagen está dañada o supera el límite de píxeles.") from exc
    return ImageOps.exif_transpose(image)


def prepare_for_ocr(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    gray = ImageOps.autocontrast(gray)
    if gray.width < 1000:
        scale = 2
        gray = gray.resize((gray.width * scale, gray.height * scale))
    max_side = max(gray.size)
    if max_side > 4000:
        ratio = 4000 / max_side
        gray = gray.resize((int(gray.width * ratio), int(gray.height * ratio)))
    return gray.filter(ImageFilter.SHARPEN)
