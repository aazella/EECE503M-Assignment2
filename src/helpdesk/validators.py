# validators.py
#
# validators for file uploads, etc.

import logging

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from PIL import Image as _PILImage

from helpdesk import settings as helpdesk_settings

upload_log = logging.getLogger("helpdesk.uploads")

# Extension -> format Pillow must report after decoding.
IMAGE_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF"}
MAX_IMAGE_PIXELS = 12_000_000  # about 4000x3000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_PILImage.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def _reject(message, code, value):
    """Log the decision (check code and size, never name or contents), then
    return the ValidationError to raise. Logging here covers every entry point
    (form, model, API), including ones that fail before process_attachments."""
    upload_log.warning(
        "upload rejected check=%s size=%s", code, getattr(value, "size", "unknown")
    )
    return ValidationError(message, code=code)


def validate_file_extension(value):
    import os

    ext = os.path.splitext(value.name)[1]

    if not helpdesk_settings.HELPDESK_VALIDATE_ATTACHMENT_TYPES:
        return

    if value.size > MAX_UPLOAD_BYTES:
        raise _reject(_("File too large."), "too_large", value)

    if "\x00" in value.name:
        raise _reject(_("Invalid file name."), "bad_name", value)

    if ext.lower() not in helpdesk_settings.HELPDESK_VALID_EXTENSIONS:
        raise _reject(_("Unsupported file type."), "bad_extension", value)

    # only one dot allowed
    if os.path.basename(value.name).count(".") > 1:
        raise _reject(_("Unsupported file name."), "bad_name", value)

    # reject hidden files
    if os.path.basename(value.name).startswith("."):
        raise _reject(_("Unsupported file name."), "bad_name", value)

    # content check for images
    if ext.lower() in IMAGE_FORMATS:
        from PIL import Image

        try:
            value.seek(0)
            with Image.open(value) as img:
                if img.format != IMAGE_FORMATS[ext.lower()]:
                    raise _reject(
                        _("File content does not match its extension."),
                        "content_mismatch",
                        value,
                    )
                if img.width * img.height > MAX_IMAGE_PIXELS:
                    raise _reject(
                        _("Image dimensions are too large."), "too_many_pixels", value
                    )
                img.load()  # full decode, not just a header parse
        except ValidationError:
            raise
        except Exception:
            raise _reject(_("Uploaded file is not a valid image."), "not_image", value)
        finally:
            value.seek(0)


def reencode_image(uploaded):
    """Decode and re-save an image so only pixel data survives. Call after validation."""
    import io
    import os

    from django.core.files.base import ContentFile
    from PIL import Image, ImageOps

    fmt = IMAGE_FORMATS.get(os.path.splitext(uploaded.name)[1].lower())
    if fmt is None:
        return uploaded

    try:
        uploaded.seek(0)
        with Image.open(uploaded) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            if fmt == "JPEG" and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format=fmt)  # no metadata passed, so none is written
    except Exception:
        raise _reject(_("Uploaded file is not a valid image."), "not_image", uploaded)
    return ContentFile(buf.getvalue(), name=os.path.basename(uploaded.name))