"""标签管理 API 路由

提供标签管理相关的 API 接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DBSession
from app.schemas.common import ApiResponse, PageData
from app.schemas.system import TagCreate, TagResponse
from app.services.system_service import tag_service

router = APIRouter(prefix="/tags", tags=["标签管理"])


@router.get(
    "",
    response_model=ApiResponse[PageData[TagResponse]],
    summary="标签列表",
    description="获取标签列表，支持关键词搜索和分页",
)
async def get_tags(
    db: DBSession,
    keyword: str | None = Query(default=None, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> ApiResponse[PageData[TagResponse]]:
    """获取标签列表接口"""
    tags, total = await tag_service.get_list(
        db,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data=PageData.create(
            items=[TagResponse.model_validate(t) for t in tags],
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[TagResponse],
    summary="创建标签",
    description="创建新的标签",
)
async def create_tag(
    data: TagCreate,
    db: DBSession,
) -> ApiResponse[TagResponse]:
    """创建标签接口"""
    tag = await tag_service.create(db, data)
    return ApiResponse.success(
        data=TagResponse.model_validate(tag),
        message="创建成功",
    )