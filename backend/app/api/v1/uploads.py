"""文件上传 API 路由。

提供课程封面图片上传接口。
"""

from fastapi import APIRouter, File, Request, UploadFile

from app.core.dependencies import CurrentUserId, DBSession
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.course import UploadFileResponse
from app.services.upload_service import upload_service

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post(
    "/file",
    response_model=ApiResponse[UploadFileResponse],
    summary="上传课程封面",
    description="上传课程封面图片，返回可直接写入 cover_url 的图片地址",
)
async def upload_course_cover(
    request: Request,
    db: DBSession,
    user_id: CurrentUserId,
    file: UploadFile = File(..., description="课程封面图片"),
) -> ApiResponse[UploadFileResponse]:
    """上传课程封面图片接口。"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("用户不存在")

    if user.status != "active" or user.role not in {"teacher", "admin"}:
        raise ForbiddenException("仅讲师或管理员可上传课程封面")

    upload_result = await upload_service.save_course_cover(
        file=file,
        base_url=str(request.base_url),
    )

    return ApiResponse.success(
        data=UploadFileResponse(**upload_result),
        message="上传成功",
    )
