"""资源类型归一化工具。"""

from __future__ import annotations

from urllib.parse import urlparse


ALLOWED_RESOURCE_TYPES = {"video", "audio", "document", "image", "quiz"}

_RESOURCE_TYPE_BY_EXTENSION = {
    "mp4": "video",
    "mov": "video",
    "avi": "video",
    "mkv": "video",
    "webm": "video",
    "m4v": "video",
    "mpeg": "video",
    "mpg": "video",
    "wmv": "video",
    "flv": "video",
    "mp3": "audio",
    "wav": "audio",
    "m4a": "audio",
    "aac": "audio",
    "flac": "audio",
    "ogg": "audio",
    "oga": "audio",
    "wma": "audio",
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "bmp": "image",
    "webp": "image",
    "svg": "image",
    "ico": "image",
    "pdf": "document",
    "doc": "document",
    "docx": "document",
    "ppt": "document",
    "pptx": "document",
    "xls": "document",
    "xlsx": "document",
    "csv": "document",
    "txt": "document",
    "md": "document",
    "markdown": "document",
    "json": "document",
    "zip": "document",
    "rar": "document",
    "7z": "document",
}


def _extract_extension(value: str | None) -> str:
    if not value:
        return ""

    parsed = urlparse(value)
    candidate = parsed.path or value
    file_name = candidate.rsplit("/", 1)[-1]
    if "." not in file_name:
        return ""
    return file_name.rsplit(".", 1)[-1].lower()


def normalize_resource_type(
    resource_type: str | None,
    *,
    file_url: str | None = None,
    file_name: str | None = None,
) -> str:
    """按文件信息归一化资源类型，优先兼容历史脏数据。"""
    normalized_type = (resource_type or "").strip().lower()

    if normalized_type == "quiz":
        return "quiz"

    for candidate in (file_url, file_name):
        extension = _extract_extension(candidate)
        inferred_type = _RESOURCE_TYPE_BY_EXTENSION.get(extension)
        if inferred_type:
            return inferred_type

    if normalized_type in ALLOWED_RESOURCE_TYPES:
        return normalized_type

    return "document"
