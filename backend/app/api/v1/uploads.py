"""文件上传 API 路由。"""

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.dependencies import CurrentUserId, DBSession
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.upload import (
    ChunkUploadChunkResponse,
    ChunkUploadCompleteRequest,
    ChunkUploadInitRequest,
    ChunkUploadInitResponse,
    UploadFileResponse,
)
from app.services.upload_service import upload_service

router = APIRouter(prefix="/upload", tags=["文件上传"])


async def _ensure_upload_permission(db: DBSession, user_id: CurrentUserId) -> None:
    """校验上传权限。"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")

    if user.status != "active" or user.role not in {"teacher", "admin"}:
        raise ForbiddenException("仅讲师或管理员可上传课程封面")


@router.post(
    "/file",
    response_model=ApiResponse[UploadFileResponse],
    summary="上传文件",
    description="上传课程封面、文档或常见音视频资源，返回统一文件信息",
)
async def upload_file(
    request: Request,
    db: DBSession,
    user_id: CurrentUserId,
    file: UploadFile = File(..., description="上传文件"),
) -> ApiResponse[UploadFileResponse]:
    """统一文件上传接口。"""
    await _ensure_upload_permission(db, user_id)

    upload_result = await upload_service.save_file(
        file=file,
        base_url=str(request.base_url),
    )

    return ApiResponse.success(
        data=UploadFileResponse(**upload_result),
        message="上传成功",
    )


@router.post(
    "/init",
    response_model=ApiResponse[ChunkUploadInitResponse],
    summary="初始化分片上传",
    description="创建分片上传任务并返回 upload_id、分片大小和总片数",
)
async def init_chunk_upload(
    data: ChunkUploadInitRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[ChunkUploadInitResponse]:
    """初始化分片上传。"""
    await _ensure_upload_permission(db, user_id)
    result = await upload_service.init_chunk_upload(data)
    return ApiResponse.success(
        data=ChunkUploadInitResponse(**result),
        message="初始化成功",
    )


@router.post(
    "/chunk",
    response_model=ApiResponse[ChunkUploadChunkResponse],
    summary="上传分片",
    description="上传指定 upload_id 的单个分片",
)
async def upload_chunk(
    db: DBSession,
    user_id: CurrentUserId,
    upload_id: str = Form(..., description="上传任务 ID"),
    chunk_index: int = Form(..., ge=0, description="分片索引"),
    chunk: UploadFile = File(..., description="分片内容"),
) -> ApiResponse[ChunkUploadChunkResponse]:
    """上传单个分片。"""
    await _ensure_upload_permission(db, user_id)
    result = await upload_service.save_chunk(
        upload_id=upload_id,
        chunk_index=chunk_index,
        chunk_file=chunk,
    )
    return ApiResponse.success(
        data=ChunkUploadChunkResponse(**result),
        message="分片上传成功",
    )


@router.post(
    "/complete",
    response_model=ApiResponse[UploadFileResponse],
    summary="完成分片上传",
    description="校验并合并所有分片，返回统一文件信息",
)
async def complete_chunk_upload(
    request: Request,
    data: ChunkUploadCompleteRequest,
    db: DBSession,
    user_id: CurrentUserId,
) -> ApiResponse[UploadFileResponse]:
    """完成分片上传。"""
    await _ensure_upload_permission(db, user_id)
    result = await upload_service.complete_chunk_upload(
        data=data,
        base_url=str(request.base_url),
    )
    return ApiResponse.success(
        data=UploadFileResponse(**result),
        message="上传成功",
    )
