"""用户管理相关 Pydantic 模型

定义用户管理模块的请求和响应模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ==================== 用户信息模型 ====================

class UserProfileUpdate(BaseModel):
    """更新个人信息请求"""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="用户名",
    )
    bio: str | None = Field(
        default=None,
        max_length=500,
        description="个人简介",
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="手机号码",
    )


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(
        ...,
        min_length=6,
        description="原密码",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=50,
        description="新密码",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v) and not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含大写字母或数字")
        return v


class UserResponse(BaseModel):
    """用户信息响应"""

    id: int = Field(description="用户ID")
    user_id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    original_username: str | None = Field(default=None, description="历史用户名记录")
    username_change_remaining: int = Field(description="剩余用户名修改次数")
    can_change_username: bool = Field(description="是否可修改用户名")
    email: str = Field(description="邮箱")
    phone: str | None = Field(default=None, description="手机号码")
    bio: str | None = Field(default=None, description="个人简介")
    role: str = Field(description="角色")
    status: str = Field(description="状态")
    created_at: datetime = Field(description="注册时间")
    last_login_at: datetime | None = Field(default=None, description="最后登录时间")

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """用户列表响应（管理员视图）"""

    id: int = Field(description="用户ID")
    user_id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    original_username: str | None = Field(default=None, description="历史用户名记录")
    username_change_remaining: int = Field(description="剩余用户名修改次数")
    can_change_username: bool = Field(description="是否可修改用户名")
    email: str = Field(description="邮箱")
    role: str = Field(description="角色")
    status: str = Field(description="状态")
    created_at: datetime = Field(description="注册时间")
    last_login_at: datetime | None = Field(default=None, description="最后登录时间")

    model_config = {"from_attributes": True}


class TeacherOptionResponse(BaseModel):
    """老师选择项响应。"""

    teacher_id: int = Field(description="老师用户ID")
    username: str = Field(description="用户名")


class UserStatusUpdate(BaseModel):
    """更新用户状态请求"""

    status: Literal["active", "disabled"] = Field(
        ...,
        description="用户状态",
    )


# ==================== 学习记录模型 ====================

class LearningRecordDeleteRequest(BaseModel):
    """删除/隐藏学习记录请求。"""

    record_ids: list[int] = Field(..., min_length=1, description="学习记录ID列表")


class LearningRecordDeleteResponse(BaseModel):
    """删除/隐藏学习记录响应。"""

    deleted_count: int = Field(description="隐藏的记录数量")


class LearningRecordResponse(BaseModel):
    """学习记录响应"""

    id: int = Field(description="记录ID")
    course_id: int = Field(description="课程ID")
    course_title: str = Field(description="课程标题")
    course_name: str | None = Field(default=None, description="课程名称")
    course_cover: str | None = Field(default=None, description="课程封面")
    progress: float = Field(description="学习进度（百分比）")
    total_duration: int = Field(description="累计学习时长（秒）")
    last_section_id: int | None = Field(default=None, description="最后学习的小节ID")
    last_section_title: str = Field(default="", description="最后学习的小节标题")
    last_learn_at: datetime = Field(description="最后学习时间")
    course_status: str = Field(description="课程状态")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    created_at: datetime = Field(description="开始学习时间")
    updated_at: datetime = Field(description="最后学习时间")

    model_config = {"from_attributes": True}


# ==================== 老师审核模型 ====================

class TeacherAuditApply(BaseModel):
    """老师申请请求"""

    real_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="真实姓名",
    )
    phone: str = Field(
        ...,
        min_length=11,
        max_length=20,
        description="联系电话",
    )
    email: EmailStr = Field(
        ...,
        description="联系邮箱",
    )
    organization: str | None = Field(
        default=None,
        max_length=100,
        description="所属机构",
    )
    title: str | None = Field(
        default=None,
        max_length=50,
        description="职称/头衔",
    )
    introduction: str | None = Field(
        default=None,
        max_length=1000,
        description="个人简介",
    )
    certificate_urls: list[str] | None = Field(
        default=None,
        description="证书/资质图片URLs",
    )


class TeacherAuditReview(BaseModel):
    """老师审核请求"""

    approve: bool = Field(
        ...,
        description="是否通过",
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="审核意见",
    )


class TeacherAuditResponse(BaseModel):
    """老师审核记录响应"""

    id: int = Field(description="审核ID")
    user_id: int = Field(description="申请人ID")
    username: str | None = Field(default=None, description="申请人用户名")
    real_name: str = Field(description="真实姓名")
    phone: str = Field(description="联系电话")
    email: str = Field(description="联系邮箱")
    organization: str | None = Field(default=None, description="所属机构")
    title: str | None = Field(default=None, description="职称/头衔")
    introduction: str | None = Field(default=None, description="个人简介")
    certificate_urls: list[str] | None = Field(default=None, description="证书URLs")
    status: str = Field(description="审核状态")
    review_comment: str | None = Field(default=None, description="审核意见")
    created_at: datetime = Field(description="申请时间")
    reviewed_at: datetime | None = Field(default=None, description="审核时间")

    model_config = {"from_attributes": True}


# ==================== 管理员申请模型 ====================

class AdminApplicationCreate(BaseModel):
    """管理员申请请求"""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="申请理由",
    )
    department: str | None = Field(
        default=None,
        max_length=100,
        description="所属部门",
    )


class AdminApplicationReview(BaseModel):
    """管理员申请审核请求"""

    approve: bool = Field(
        ...,
        description="是否通过",
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="审核意见",
    )


class AdminApplicationResponse(BaseModel):
    """管理员申请记录响应"""

    id: int = Field(description="申请ID")
    user_id: int = Field(description="申请人ID")
    username: str | None = Field(default=None, description="申请人用户名")
    reason: str = Field(description="申请理由")
    department: str | None = Field(default=None, description="所属部门")
    status: str = Field(description="审核状态")
    review_comment: str | None = Field(default=None, description="审核意见")
    created_at: datetime = Field(description="申请时间")
    reviewed_at: datetime | None = Field(default=None, description="审核时间")

    model_config = {"from_attributes": True}
