"""文件上传服务模块。"""

import asyncio
import json
import shutil
from math import ceil
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ValidationException
from app.models.content import Resource
from app.models.course import Course, CourseMaterial
from app.schemas.upload import ChunkUploadCompleteRequest, ChunkUploadInitRequest


logger = get_logger(__name__)


class UploadService:
    """文件上传服务类。"""

    pending_delete_session_key = "pending_upload_deletions"

    class UploadPolicy(NamedTuple):
        subdir: str
        direct_max_size: int
        chunk_max_size: int

    allowed_image_extensions = {".jpg", ".jpeg", ".png"}
    allowed_image_content_types = {"image/jpeg", "image/jpg", "image/png"}
    allowed_avatar_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    allowed_avatar_content_types = {"image/jpeg", "image/jpg", "image/png", "image/gif"}
    allowed_video_extensions = {".mp4", ".mov", ".webm", ".ogg"}
    allowed_audio_extensions = {".mp3", ".wav", ".ogg"}
    allowed_document_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".csv",
        ".md",
        ".zip",
    }
    allowed_video_content_types = {
        "video/mp4",
        "video/quicktime",
        "video/webm",
        "video/ogg",
    }
    allowed_audio_content_types = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/ogg",
    }
    known_image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    allowed_document_content_types = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/markdown",
        "text/plain",
        "application/zip",
        "application/x-zip-compressed",
        "application/octet-stream",
    }

    def __init__(self) -> None:
        """初始化上传服务。"""
        self._upload_locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def _format_size_limit(size_in_bytes: int) -> str:
        """将字节数格式化为用于错误提示的大小文本。"""
        gib = 1024 * 1024 * 1024
        mib = 1024 * 1024
        kib = 1024

        if size_in_bytes >= gib and size_in_bytes % gib == 0:
            return f"{size_in_bytes // gib}GB"
        if size_in_bytes >= mib and size_in_bytes % mib == 0:
            return f"{size_in_bytes // mib}MB"
        if size_in_bytes >= kib and size_in_bytes % kib == 0:
            return f"{size_in_bytes // kib}KB"
        return f"{size_in_bytes}B"

    @classmethod
    def _size_limit_message(cls, size_in_bytes: int) -> str:
        """构造统一的文件大小超限提示。"""
        return f"文件大小不能超过{cls._format_size_limit(size_in_bytes)}"

    async def save_file(
        self,
        file: UploadFile,
    ) -> dict[str, str | int | None]:
        """保存上传文件并返回访问信息。"""
        policy = self._resolve_upload_policy(
            Path(file.filename or "").suffix.lower(),
            file.content_type.lower() if file.content_type else None,
        )
        return await self._save_upload_file(file, policy.subdir, policy.direct_max_size)

    async def save_avatar(
        self,
        file: UploadFile,
    ) -> dict[str, str | int | None]:
        """保存头像文件并返回访问信息。"""
        self._validate_avatar_image(file, "仅支持 JPG/PNG/GIF 格式头像")

        return await self._save_upload_file(
            file,
            settings.avatar_subdir,
            settings.course_cover_max_size,
        )

    async def save_feedback_image(
        self,
        file: UploadFile,
    ) -> dict[str, str | int | None]:
        """保存反馈截图并返回访问信息。"""
        self._validate_feedback_image(file)

        return await self._save_upload_file(
            file,
            settings.feedback_image_subdir,
            settings.course_cover_max_size,
        )

    def _validate_avatar_image(self, file: UploadFile, image_error_message: str) -> None:
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()
        content_type = file.content_type.lower() if file.content_type else None

        if extension not in self.allowed_avatar_extensions:
            if extension in self.known_image_extensions or (
                content_type and content_type.startswith("image/")
            ):
                raise ValidationException(image_error_message)
            raise ValidationException("不支持的文件类型")

        if content_type and content_type not in self.allowed_avatar_content_types:
            raise ValidationException(image_error_message)

    def _validate_feedback_image(self, file: UploadFile) -> None:
        self._validate_avatar_image(file, "仅支持 JPG/PNG/GIF 格式截图")

    async def _save_upload_file(
        self,
        file: UploadFile,
        subdir: str,
        max_size: int,
    ) -> dict[str, str | int | None]:
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()
        content = await file.read()
        if not content:
            raise ValidationException("上传文件不能为空")

        if len(content) > max_size:
            raise ValidationException(self._size_limit_message(max_size))

        upload_dir = settings.resolved_upload_dir / subdir
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_name = f"{uuid4().hex}{extension}"
        save_path = upload_dir / saved_name

        with save_path.open("wb") as output_file:
            output_file.write(content)

        file_url = f"{settings.upload_url_prefix.rstrip('/')}/{subdir}/{saved_name}"

        await file.close()

        return {
            "file_name": filename,
            "file_url": file_url,
            "url": file_url,
            "file_size": len(content),
            "content_type": file.content_type,
        }

    async def init_chunk_upload(
        self,
        data: ChunkUploadInitRequest,
    ) -> dict[str, str | int]:
        """初始化分片上传任务。"""
        extension = Path(data.file_name).suffix.lower()
        policy = self._resolve_upload_policy(
            extension,
            data.content_type.lower() if data.content_type else None,
        )

        if data.file_size > policy.chunk_max_size:
            raise ValidationException(self._size_limit_message(policy.chunk_max_size))

        upload_id = uuid4().hex
        total_chunks = ceil(data.file_size / data.chunk_size)
        session_dir = self._get_chunk_session_dir(upload_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "upload_id": upload_id,
            "file_name": data.file_name,
            "file_size": data.file_size,
            "chunk_size": data.chunk_size,
            "total_chunks": total_chunks,
            "content_type": data.content_type,
            "biz_type": data.biz_type,
            "status": "uploading",
            "received_chunks": [],
        }
        self._write_manifest(session_dir, manifest)

        return {
            "upload_id": upload_id,
            "chunk_size": data.chunk_size,
            "total_chunks": total_chunks,
        }

    async def save_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_file: UploadFile,
    ) -> dict[str, int]:
        """保存单个分片。"""
        lock = self._get_upload_lock(upload_id)
        try:
            async with lock:
                session_dir = self._get_chunk_session_dir(upload_id)
                manifest = self._read_manifest(session_dir)
                status = str(manifest.get("status") or "uploading")
                if status == "merging":
                    raise ValidationException("上传任务正在合并，无法继续上传分片")
                if status == "completed":
                    raise ValidationException("上传任务已完成，无法继续上传分片")

                total_chunks = int(manifest["total_chunks"])
                if chunk_index >= total_chunks:
                    raise ValidationException("chunk_index 超出范围")

                content = await chunk_file.read()
                if not content:
                    raise ValidationException("上传分片不能为空")

                chunk_path = session_dir / f"{chunk_index}.part"
                with chunk_path.open("wb") as output_file:
                    output_file.write(content)

                # 同一个 upload_id 的 save/complete 共用任务锁，避免 chunk 写入
                # 与 complete 合并过程交叉。同时仍以磁盘上的真实分片为准同步状态。
                manifest["status"] = "uploading"
                manifest["received_chunks"] = self._get_received_chunks(session_dir)
                self._write_manifest(session_dir, manifest)

                return {"chunk_index": chunk_index}
        finally:
            await chunk_file.close()

    async def complete_chunk_upload(
        self,
        data: ChunkUploadCompleteRequest,
    ) -> dict[str, str | int | None]:
        """合并并完成分片上传。"""
        lock = self._get_upload_lock(data.upload_id)
        async with lock:
            session_dir = self._get_chunk_session_dir(data.upload_id)
            manifest = self._read_manifest(session_dir)
            status = str(manifest.get("status") or "uploading")
            if status == "completed":
                raise ValidationException("上传任务已完成")
            if status == "merging":
                raise ValidationException("上传任务正在合并，请稍后重试")

            manifest["status"] = "merging"
            self._write_manifest(session_dir, manifest)

            try:
                if manifest["file_name"] != data.file_name:
                    raise ValidationException("file_name 与初始化信息不一致")

                total_chunks = int(manifest["total_chunks"])
                if total_chunks != data.total_chunks:
                    raise ValidationException("total_chunks 与初始化信息不一致")

                expected_chunks = list(range(total_chunks))
                received_chunks = self._get_received_chunks(session_dir)
                manifest["received_chunks"] = received_chunks
                self._write_manifest(session_dir, manifest)
                if received_chunks != expected_chunks:
                    raise ValidationException("分片未上传完成，无法合并")

                extension = Path(data.file_name).suffix.lower()
                content_type = manifest.get("content_type")
                policy = self._resolve_upload_policy(
                    extension,
                    content_type.lower() if isinstance(content_type, str) else None,
                )

                upload_dir = settings.resolved_upload_dir / policy.subdir
                upload_dir.mkdir(parents=True, exist_ok=True)
                saved_name = f"{uuid4().hex}{extension}"
                save_path = upload_dir / saved_name

                with save_path.open("wb") as output_file:
                    for chunk_index in expected_chunks:
                        chunk_path = session_dir / f"{chunk_index}.part"
                        if not chunk_path.exists():
                            raise ValidationException("分片文件缺失，无法合并")
                        output_file.write(chunk_path.read_bytes())

                final_size = save_path.stat().st_size
                if final_size != int(manifest["file_size"]):
                    save_path.unlink(missing_ok=True)
                    raise ValidationException("合并后的文件大小校验失败")

                file_url = f"{settings.upload_url_prefix.rstrip('/')}/{policy.subdir}/{saved_name}"

                shutil.rmtree(session_dir, ignore_errors=True)

                return {
                    "file_name": data.file_name,
                    "file_url": file_url,
                    "url": file_url,
                    "file_size": final_size,
                    "content_type": content_type,
                }
            except Exception:
                if session_dir.exists():
                    manifest["status"] = "uploading"
                    manifest["received_chunks"] = self._get_received_chunks(session_dir)
                    self._write_manifest(session_dir, manifest)
                raise

    def _resolve_upload_policy(
        self,
        extension: str,
        content_type: str | None,
    ) -> UploadPolicy:
        """根据扩展名和 MIME 类型决定存储目录与普通/分片大小限制。"""
        if extension in self.allowed_image_extensions:
            if content_type and content_type not in self.allowed_image_content_types:
                raise ValidationException("仅支持 JPG/PNG 格式图片")
            return self.UploadPolicy(
                subdir=settings.course_cover_subdir,
                direct_max_size=settings.course_cover_max_size,
                chunk_max_size=settings.course_cover_max_size,
            )

        if extension in self.allowed_document_extensions:
            if content_type and content_type not in self.allowed_document_content_types:
                raise ValidationException("不支持的文件类型")
            return self.UploadPolicy(
                subdir=settings.general_upload_subdir,
                direct_max_size=settings.general_file_max_size,
                chunk_max_size=settings.chunk_file_max_size,
            )

        if extension in self.allowed_video_extensions:
            if content_type and content_type not in self.allowed_video_content_types:
                raise ValidationException("不支持的文件类型")
            return self.UploadPolicy(
                subdir=settings.general_upload_subdir,
                direct_max_size=settings.general_file_max_size,
                chunk_max_size=settings.chunk_file_max_size,
            )

        if extension in self.allowed_audio_extensions:
            if content_type and content_type not in self.allowed_audio_content_types:
                raise ValidationException("不支持的文件类型")
            return self.UploadPolicy(
                subdir=settings.general_upload_subdir,
                direct_max_size=settings.general_file_max_size,
                chunk_max_size=settings.chunk_file_max_size,
            )

        if extension in self.known_image_extensions or (
            content_type and content_type.startswith("image/")
        ):
            raise ValidationException("仅支持 JPG/PNG 格式图片")

        raise ValidationException("不支持的文件类型")

    def _get_chunk_session_dir(self, upload_id: str) -> Path:
        """返回分片上传任务目录。"""
        return settings.resolved_upload_dir / settings.chunk_upload_tmp_subdir / upload_id

    def _get_manifest_path(self, session_dir: Path) -> Path:
        """返回 manifest 路径。"""
        return session_dir / "manifest.json"

    def _read_manifest(self, session_dir: Path) -> dict:
        """读取 manifest。"""
        manifest_path = self._get_manifest_path(session_dir)
        if not manifest_path.exists():
            raise ValidationException("上传任务不存在")

        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, session_dir: Path, manifest: dict) -> None:
        """写入 manifest。"""
        manifest_path = self._get_manifest_path(session_dir)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_received_chunks(self, session_dir: Path) -> list[int]:
        """根据磁盘上的分片文件返回已收到的分片索引。"""
        chunk_indexes: list[int] = []
        for chunk_path in session_dir.glob("*.part"):
            try:
                chunk_indexes.append(int(chunk_path.stem))
            except ValueError:
                continue

        return sorted(set(chunk_indexes))

    def _get_upload_lock(self, upload_id: str) -> asyncio.Lock:
        """获取 upload_id 级别的任务锁。"""
        lock = self._upload_locks.get(upload_id)
        if lock is None:
            lock = asyncio.Lock()
            self._upload_locks[upload_id] = lock
        return lock

    def queue_file_deletions(
        self,
        session: AsyncSession,
        file_urls: list[str] | tuple[str, ...] | set[str],
    ) -> None:
        """登记事务提交后需要删除的上传文件 URL。"""
        pending_urls = session.info.setdefault(self.pending_delete_session_key, set())
        pending_urls.update(file_url for file_url in file_urls if file_url)

    def consume_queued_file_deletions(self, session: AsyncSession) -> None:
        """在事务提交成功后删除已登记的上传文件。"""
        pending_urls = session.info.pop(self.pending_delete_session_key, set())
        for file_url in pending_urls:
            try:
                self.delete_file_by_url(file_url)
            except Exception as exc:
                logger.warning(
                    "提交后清理上传文件失败: file_url=%s path=%s error=%s",
                    file_url,
                    self._resolve_uploaded_file_path(file_url),
                    exc,
                )

    def delete_file_by_url(self, file_url: str | None) -> bool:
        """按上传 URL 删除本地文件。"""
        file_path = self._resolve_uploaded_file_path(file_url)
        if file_path is None or not file_path.is_file():
            return False

        file_path.unlink(missing_ok=True)
        return True

    async def filter_deletable_file_urls(
        self,
        db: AsyncSession,
        file_urls: list[str] | tuple[str, ...] | set[str],
        *,
        excluded_course_id: int,
    ) -> list[str]:
        """过滤出在排除当前课程后已无剩余引用的本地上传 URL。"""
        deletable_urls: list[str] = []
        unique_urls = list(dict.fromkeys(file_url for file_url in file_urls if file_url))
        for file_url in unique_urls:
            if self._resolve_uploaded_file_path(file_url) is None:
                continue
            if await self._has_remaining_references(db, file_url, excluded_course_id):
                continue
            deletable_urls.append(file_url)
        return deletable_urls

    async def _has_remaining_references(
        self,
        db: AsyncSession,
        file_url: str,
        excluded_course_id: int,
    ) -> bool:
        """判断排除当前课程后，指定 URL 是否仍被任何课程数据引用。"""
        course_result = await db.execute(
            select(func.count())
            .select_from(Course)
            .where(Course.cover_url == file_url, Course.id != excluded_course_id)
        )
        if (course_result.scalar() or 0) > 0:
            return True

        material_result = await db.execute(
            select(func.count())
            .select_from(CourseMaterial)
            .where(
                CourseMaterial.file_url == file_url,
                CourseMaterial.course_id != excluded_course_id,
            )
        )
        if (material_result.scalar() or 0) > 0:
            return True

        resource_result = await db.execute(
            select(func.count())
            .select_from(Resource)
            .where(
                Resource.file_url == file_url,
                Resource.course_id != excluded_course_id,
            )
        )
        return (resource_result.scalar() or 0) > 0

    def _resolve_uploaded_file_path(self, file_url: str | None) -> Path | None:
        """将上传 URL 安全解析为本地文件路径。"""
        if not file_url:
            return None

        parsed = urlparse(file_url)
        url_path = parsed.path or file_url
        prefix = settings.upload_url_prefix.rstrip("/")
        normalized_prefix = prefix if prefix.startswith("/") else f"/{prefix}"

        if not url_path.startswith(f"{normalized_prefix}/"):
            return None

        relative_path = url_path[len(normalized_prefix) :].lstrip("/")
        if not relative_path:
            return None

        upload_root = settings.resolved_upload_dir.resolve()
        candidate = (upload_root / relative_path).resolve()
        try:
            candidate.relative_to(upload_root)
        except ValueError:
            return None

        return candidate


upload_service = UploadService()
