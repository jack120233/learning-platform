"""上传接口测试。"""

import json
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import create_access_token
from app.models.user import User
from tests.test_courses import create_upload_test_user


async def create_avatar_test_user(
    db_session: AsyncSession,
    status: str = "active",
) -> dict[str, str]:
    unique_suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"avatar_{status}_{unique_suffix}",
        email=f"avatar_{status}_{unique_suffix}@example.com",
        password_hash="test-password-hash",
        nickname="avatar-tester",
        role="student",
        status=status,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


class TestUploadFile:
    """通用文件上传测试。"""

    @pytest.mark.asyncio
    async def test_upload_file_supports_course_cover_png(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试上传 PNG 封面图。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        file_content = b"fake-png-content"

        response = await client.post(
            "/api/v1/upload/file",
            headers=teacher_headers,
            files={"file": ("course-cover.png", file_content, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["data"]["file_name"] == "course-cover.png"
        assert data["data"]["file_size"] == len(file_content)
        assert data["data"]["url"] == data["data"]["file_url"]
        assert data["data"]["file_url"].startswith(
            "/uploads/course-covers/"
        )

        upload_path = urlparse(data["data"]["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()

        preview_response = await client.get(upload_path)
        assert preview_response.status_code == 200
        assert preview_response.content == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_file_supports_material_pdf(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试上传 PDF 资料。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        file_content = b"%PDF-1.4 fake content"

        response = await client.post(
            "/api/v1/upload/file",
            headers=teacher_headers,
            files={"file": ("lesson-outline.pdf", file_content, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["data"]["file_name"] == "lesson-outline.pdf"
        assert data["data"]["file_size"] == len(file_content)
        assert data["data"]["content_type"] == "application/pdf"
        assert data["data"]["url"] == data["data"]["file_url"]
        assert data["data"]["file_url"].startswith("/uploads/files/")
        assert "/course-covers/" not in data["data"]["file_url"]

        upload_path = urlparse(data["data"]["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()

        preview_response = await client.get(upload_path)
        assert preview_response.status_code == 200
        assert preview_response.content == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_file_rejects_unsupported_extension(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试拒绝不支持的文件类型。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")

        response = await client.post(
            "/api/v1/upload/file",
            headers=teacher_headers,
            files={"file": ("script.exe", b"fake-exe", "application/octet-stream")},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["message"] == "不支持的文件类型"


class TestAvatarUpload:
    """头像上传测试。"""

    @pytest.mark.asyncio
    async def test_student_can_upload_avatar_gif(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试学生可上传 GIF 头像。"""
        auth_headers = await create_avatar_test_user(db_session)
        file_content = b"GIF89a fake content"

        response = await client.post(
            "/api/v1/upload/avatar",
            headers=auth_headers,
            files={"file": ("avatar.gif", file_content, "image/gif")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["data"]["file_name"] == "avatar.gif"
        assert data["data"]["file_size"] == len(file_content)
        assert data["data"]["content_type"] == "image/gif"
        assert data["data"]["url"] == data["data"]["file_url"]
        assert data["data"]["file_url"].startswith("/uploads/avatars/")

        upload_path = urlparse(data["data"]["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()

        preview_response = await client.get(upload_path)
        assert preview_response.status_code == 200
        assert preview_response.content == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_avatar_requires_authentication(self, client: AsyncClient):
        """测试未登录不能上传头像。"""
        response = await client.post(
            "/api/v1/upload/avatar",
            files={"file": ("avatar.png", b"fake-png-content", "image/png")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_disabled_user_cannot_upload_avatar(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试非 active 用户不能上传头像。"""
        auth_headers = await create_avatar_test_user(db_session, status="disabled")

        response = await client.post(
            "/api/v1/upload/avatar",
            headers=auth_headers,
            files={"file": ("avatar.png", b"fake-png-content", "image/png")},
        )

        assert response.status_code == 403
        assert response.json()["message"] == "当前账号不可上传头像"


class TestFeedbackImageUpload:
    """反馈截图上传测试。"""

    @pytest.mark.asyncio
    async def test_student_can_upload_feedback_image(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试学生可上传反馈截图。"""
        auth_headers = await create_avatar_test_user(db_session)
        file_content = b"fake-feedback-image"

        response = await client.post(
            "/api/v1/upload/feedback-image",
            headers=auth_headers,
            files={"file": ("feedback.png", file_content, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["data"]["file_name"] == "feedback.png"
        assert data["data"]["file_size"] == len(file_content)
        assert data["data"]["content_type"] == "image/png"
        assert data["data"]["url"] == data["data"]["file_url"]
        assert data["data"]["file_url"].startswith("/uploads/feedback-images/")

        upload_path = urlparse(data["data"]["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()

        preview_response = await client.get(upload_path)
        assert preview_response.status_code == 200
        assert preview_response.content == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_disabled_user_cannot_upload_feedback_image(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试非 active 用户不能上传反馈截图。"""
        auth_headers = await create_avatar_test_user(db_session, status="disabled")

        response = await client.post(
            "/api/v1/upload/feedback-image",
            headers=auth_headers,
            files={"file": ("feedback.png", b"fake-png-content", "image/png")},
        )

        assert response.status_code == 403
        assert response.json()["message"] == "当前账号不可上传反馈截图"


class TestChunkUpload:
    """分片上传测试。"""

    @pytest.mark.asyncio
    async def test_init_chunk_upload_returns_upload_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试初始化分片上传。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")

        response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": 25,
                "chunk_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["upload_id"]
        assert data["chunk_size"] == 10
        assert data["total_chunks"] == 3

        session_dir = Path(settings.upload_dir) / settings.chunk_upload_tmp_subdir / data["upload_id"]
        assert session_dir.exists()
        shutil.rmtree(session_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_upload_chunk_saves_single_part(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试上传单个分片。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        init_response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": 20,
                "chunk_size": 10,
            },
        )
        upload_id = init_response.json()["data"]["upload_id"]

        response = await client.post(
            "/api/v1/upload/chunk",
            headers=teacher_headers,
            files={
                "upload_id": (None, upload_id),
                "chunk_index": (None, "0"),
                "chunk": ("chunk-0.part", b"1234567890", "application/octet-stream"),
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["chunk_index"] == 0

        chunk_path = (
            Path(settings.upload_dir)
            / settings.chunk_upload_tmp_subdir
            / upload_id
            / "0.part"
        )
        assert chunk_path.exists()
        assert chunk_path.read_bytes() == b"1234567890"

        shutil.rmtree(chunk_path.parent, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_chunk_upload_merges_parts(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试完成分片上传并合并文件。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        file_content = b"0123456789abcdefghij"
        init_response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": len(file_content),
                "chunk_size": 10,
            },
        )
        upload_id = init_response.json()["data"]["upload_id"]

        for chunk_index in range(2):
            start = chunk_index * 10
            end = start + 10
            chunk_bytes = file_content[start:end]
            chunk_response = await client.post(
                "/api/v1/upload/chunk",
                headers=teacher_headers,
                files={
                    "upload_id": (None, upload_id),
                    "chunk_index": (None, str(chunk_index)),
                    "chunk": ("chunk.part", chunk_bytes, "application/octet-stream"),
                },
            )
            assert chunk_response.status_code == 200

        response = await client.post(
            "/api/v1/upload/complete",
            headers=teacher_headers,
            json={
                "upload_id": upload_id,
                "file_name": "lesson-video.mp4",
                "total_chunks": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["file_name"] == "lesson-video.mp4"
        assert data["file_size"] == len(file_content)
        assert data["file_url"].startswith("/uploads/files/")

        upload_path = urlparse(data["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()
        assert file_path.read_bytes() == file_content

        session_dir = Path(settings.upload_dir) / settings.chunk_upload_tmp_subdir / upload_id
        assert not session_dir.exists()

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_complete_chunk_upload_rejects_missing_chunks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试缺少分片时不能完成上传。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        init_response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": 20,
                "chunk_size": 10,
            },
        )
        upload_id = init_response.json()["data"]["upload_id"]

        chunk_response = await client.post(
            "/api/v1/upload/chunk",
            headers=teacher_headers,
            files={
                "upload_id": (None, upload_id),
                "chunk_index": (None, "0"),
                "chunk": ("chunk.part", b"0123456789", "application/octet-stream"),
            },
        )
        assert chunk_response.status_code == 200

        response = await client.post(
            "/api/v1/upload/complete",
            headers=teacher_headers,
            json={
                "upload_id": upload_id,
                "file_name": "lesson-video.mp4",
                "total_chunks": 2,
            },
        )

        assert response.status_code == 422
        assert response.json()["message"] == "分片未上传完成，无法合并"

        session_dir = Path(settings.upload_dir) / settings.chunk_upload_tmp_subdir / upload_id
        manifest_path = session_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["status"] == "uploading"

        shutil.rmtree(session_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_chunk_upload_uses_chunk_files_when_manifest_is_stale(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试 manifest 状态滞后时仍可根据真实分片完成上传。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        file_content = b"0123456789abcdefghij"
        init_response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": len(file_content),
                "chunk_size": 10,
            },
        )
        upload_id = init_response.json()["data"]["upload_id"]
        session_dir = Path(settings.upload_dir) / settings.chunk_upload_tmp_subdir / upload_id

        for chunk_index in range(2):
            start = chunk_index * 10
            end = start + 10
            chunk_bytes = file_content[start:end]
            chunk_response = await client.post(
                "/api/v1/upload/chunk",
                headers=teacher_headers,
                files={
                    "upload_id": (None, upload_id),
                    "chunk_index": (None, str(chunk_index)),
                    "chunk": ("chunk.part", chunk_bytes, "application/octet-stream"),
                },
            )
            assert chunk_response.status_code == 200

        manifest_path = session_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["received_chunks"] = [0]
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        response = await client.post(
            "/api/v1/upload/complete",
            headers=teacher_headers,
            json={
                "upload_id": upload_id,
                "file_name": "lesson-video.mp4",
                "total_chunks": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        upload_path = urlparse(data["file_url"]).path
        file_path = (
            Path(settings.upload_dir)
            / Path(upload_path.lstrip("/")).relative_to("uploads")
        )
        assert file_path.exists()
        assert file_path.read_bytes() == file_content

        file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_chunk_rejects_when_task_is_merging(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试合并中的上传任务会拒绝迟到分片。"""
        teacher_headers = await create_upload_test_user(db_session, "teacher")
        init_response = await client.post(
            "/api/v1/upload/init",
            headers=teacher_headers,
            json={
                "file_name": "lesson-video.mp4",
                "file_size": 20,
                "chunk_size": 10,
            },
        )
        upload_id = init_response.json()["data"]["upload_id"]
        session_dir = Path(settings.upload_dir) / settings.chunk_upload_tmp_subdir / upload_id
        manifest_path = session_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = "merging"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        response = await client.post(
            "/api/v1/upload/chunk",
            headers=teacher_headers,
            files={
                "upload_id": (None, upload_id),
                "chunk_index": (None, "1"),
                "chunk": ("chunk.part", b"abcdefghij", "application/octet-stream"),
            },
        )

        assert response.status_code == 422
        assert response.json()["message"] == "上传任务正在合并，无法继续上传分片"

        shutil.rmtree(session_dir, ignore_errors=True)
