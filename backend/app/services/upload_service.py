"""文件上传服务模块。

提供课程封面图片上传能力。
"""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import ValidationException


class UploadService:
    """文件上传服务类。"""

    allowed_image_extensions = {".jpg", ".jpeg", ".png"}
    allowed_image_content_types = {"image/jpeg", "image/jpg", "image/png"}

    async def save_course_cover(self, file: UploadFile, base_url: str) -> dict[str, str | int | None]:
        """保存课程封面图片并返回访问信息。"""
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()

        if extension not in self.allowed_image_extensions:
            raise ValidationException("仅支持 JPG/PNG 格式图片")

        if file.content_type and file.content_type.lower() not in self.allowed_image_content_types:
            raise ValidationException("仅支持 JPG/PNG 格式图片")

        content = await file.read()
        if not content:
            raise ValidationException("上传文件不能为空")

        if len(content) > settings.course_cover_max_size:
            raise ValidationException("文件大小不能超过10MB")

        upload_dir = Path(settings.upload_dir) / settings.course_cover_subdir
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_name = f"{uuid4().hex}{extension}"
        save_path = upload_dir / saved_name

        with save_path.open("wb") as output_file:
            output_file.write(content)

        relative_url = (
            f"{settings.upload_url_prefix.rstrip('/')}/"
            f"{settings.course_cover_subdir}/{saved_name}"
        )
        file_url = f"{base_url.rstrip('/')}{relative_url}"

        await file.close()

        return {
            "file_name": filename,
            "file_url": file_url,
            "url": file_url,
            "file_size": len(content),
            "content_type": file.content_type,
        }


upload_service = UploadService()
