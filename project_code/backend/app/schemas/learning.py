"""学习模块相关 Pydantic 模型

定义学习模块的请求和响应模型，并兼容前端当前使用的字段命名。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ==================== 学习进度模型 ====================

class StartLearningRequest(BaseModel):
    """开始学习请求"""

    course_id: int = Field(..., description="课程ID")


class SaveProgressRequest(BaseModel):
    """保存进度请求"""

    course_id: int | None = Field(default=None, description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID，章节资源可为空")
    resource_id: int = Field(..., description="资源ID")
    position: int | None = Field(default=None, ge=0, description="播放位置（秒）")
    progress: float | None = Field(default=None, ge=0, le=100, description="学习进度（百分比）")
    current_time: int | None = Field(default=None, ge=0, description="当前播放时间（秒）")
    total_time: int | None = Field(default=None, ge=0, description="资源总时长（秒）")
    is_completed: bool = Field(default=False, description="是否完成")

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        current_time = normalized.get("current_time")
        position = normalized.get("position")
        total_time = normalized.get("total_time")
        progress = normalized.get("progress")
        is_completed = bool(normalized.get("is_completed", False))

        if current_time is None and position is not None:
            current_time = position
            normalized["current_time"] = current_time

        if normalized.get("position") is None and current_time is not None:
            normalized["position"] = current_time

        if progress is None:
            if is_completed:
                normalized["progress"] = 100.0
            elif current_time is not None and total_time:
                normalized["progress"] = min((current_time / total_time) * 100, 100)
            else:
                normalized["progress"] = 0.0

        return normalized


class ProgressResponse(BaseModel):
    """学习进度响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID")
    resource_id: int = Field(description="资源ID")
    progress: float = Field(description="学习进度（百分比）")
    position: int = Field(description="播放位置（秒）")
    current_time: int = Field(description="当前播放时间（秒）")
    total_time: int = Field(default=0, description="资源总时长（秒）")
    is_completed: bool = Field(description="是否完成")
    last_play_at: datetime | None = Field(default=None, description="最后播放时间")
    last_learn_at: datetime | None = Field(default=None, description="最后学习时间")


class ContinueLearningResponse(BaseModel):
    """继续学习响应"""

    course_id: int = Field(description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    section_id: int | None = Field(default=None, description="小节ID")
    resource_id: int | None = Field(default=None, description="资源ID")
    position: int = Field(default=0, description="播放位置（秒）")
    last_section_id: int | None = Field(default=None, description="最后学习的小节ID")
    last_section_title: str = Field(default="", description="最后学习的小节标题")
    last_resource_id: int | None = Field(default=None, description="最后学习的资源ID")
    last_resource_type: str = Field(default="", description="最后学习的资源类型")
    current_time: int = Field(default=0, description="当前播放时间（秒）")
    last_learn_at: datetime | None = Field(default=None, description="最后学习时间")


class LearningSessionRequest(BaseModel):
    """学习会话上报请求。"""

    session_id: str = Field(..., min_length=1, max_length=64, description="前端生成的幂等会话ID")
    resource_id: int = Field(..., ge=1, description="资源ID")
    started_at: datetime = Field(..., description="会话开始时间")
    ended_at: datetime = Field(..., description="会话结束时间")
    effective_duration_seconds: int = Field(..., ge=0, description="前端计算的有效学习秒数")
    start_position_seconds: int | None = Field(default=None, ge=0, description="媒体开始播放位置")
    end_position_seconds: int | None = Field(default=None, ge=0, description="媒体结束播放位置")
    progress_percent_at_end: float | None = Field(default=None, ge=0, le=100, description="结束时进度百分比")
    is_completed_at_end: bool = Field(default=False, description="结束时是否完成")
    end_reason: Literal[
        "switch_resource",
        "leave_page",
        "completed",
        "timeout",
        "beacon",
        "offline_retry",
        "manual_stop",
        "error",
    ] = Field(..., description="会话结束原因")

    @field_validator("session_id")
    @classmethod
    def strip_session_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("session_id 不能为空")
        return normalized


class LearningSessionResponse(BaseModel):
    """学习会话上报响应。"""

    session_id: str = Field(description="会话ID")
    accepted: bool = Field(description="是否接受")
    effective_duration_seconds: int = Field(description="后端接受的有效学习秒数")
    duplicate: bool = Field(description="是否重复提交")


class StudentStatisticsOverviewResponse(BaseModel):
    """学生个人学习统计概览响应。"""

    total_duration_seconds: int = Field(description="累计有效学习时长（秒）")
    last_7_days_duration_seconds: int = Field(description="近 7 个自然日有效学习时长（秒）")
    learning_course_count: int = Field(description="在学课程数")
    completed_course_count: int = Field(description="已完成课程数")
    continuous_learning_days: int = Field(description="连续学习天数")
    active_learning_days: int = Field(description="累计活跃学习天数")


class StudentStatisticsTrendItem(BaseModel):
    """学生每日学习趋势项。"""

    date: str = Field(description="自然日，格式 YYYY-MM-DD")
    duration_seconds: int = Field(description="当日有效学习时长（秒）")


class StudentStatisticsTrendResponse(BaseModel):
    """学生学习趋势响应。"""

    range: Literal["7d", "30d"] = Field(description="统计范围")
    items: list[StudentStatisticsTrendItem] = Field(description="每日趋势数据")


class StudentCourseDistributionResponse(BaseModel):
    """学生课程状态分布响应。"""

    learning_count: int = Field(description="在学课程数")
    completed_count: int = Field(description="已完成课程数")


# ==================== 讲师课程统计模型 ====================

class TeacherCourseStatisticsItem(BaseModel):
    """讲师课程统计列表项。"""

    course_id: int = Field(description="课程ID")
    course_title: str = Field(description="课程标题")
    course_cover: str | None = Field(default=None, description="课程封面")
    course_status: str = Field(description="课程状态")
    permission_type: Literal["owner", "authorized"] = Field(description="统计查看权限来源")
    started_student_count: int = Field(description="开始学习学生数")
    active_student_count_7d: int = Field(description="近 7 日活跃学生数")
    avg_progress: float = Field(description="平均学习进度")
    completion_rate: float = Field(description="完成率")
    total_duration_seconds: int = Field(description="累计有效学习时长（秒）")
    recent_learn_at: datetime | None = Field(default=None, description="最近学习时间")


class TeacherCourseStatisticsOverviewResponse(BaseModel):
    """讲师单门课程统计概览。"""

    course_id: int = Field(description="课程ID")
    course_title: str = Field(description="课程标题")
    range: Literal["7d", "30d"] = Field(description="统计范围")
    started_student_count: int = Field(description="开始学习学生数")
    active_student_count: int = Field(description="范围内活跃学生数")
    avg_progress: float = Field(description="平均学习进度")
    completion_rate: float = Field(description="完成率")
    avg_duration_seconds: int = Field(description="人均有效学习时长（秒）")
    total_duration_seconds: int = Field(description="累计有效学习时长（秒）")
    recent_learn_at: datetime | None = Field(default=None, description="最近学习时间")


class TeacherCourseStudentStatisticsItem(BaseModel):
    """讲师课程学生学习明细项。"""

    student_id: int = Field(description="学生ID")
    username: str = Field(description="用户名")
    progress: float = Field(description="课程学习进度")
    total_duration_seconds: int = Field(description="累计有效学习时长（秒）")
    last_learn_at: datetime | None = Field(default=None, description="最近学习时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    is_completed: bool = Field(description="是否完成")


# ==================== 管理员学习统计模型 ====================

class AdminLearningStatisticsOverviewResponse(BaseModel):
    """管理员平台学习统计概览。"""

    range: Literal["7d", "30d", "all"] = Field(description="统计范围")
    total_student_count: int = Field(description="曾开始学习学生数")
    active_student_count: int = Field(description="范围内活跃学生数")
    total_duration_seconds: int = Field(description="范围内有效学习时长（秒）")
    active_course_count: int = Field(description="范围内活跃课程数")
    new_started_course_count: int = Field(description="范围内新开始学习人课次数")
    new_completed_course_count: int = Field(description="范围内新完成课程人课次数")


class AdminLearningStatisticsTrendItem(BaseModel):
    """管理员学习趋势项。"""

    date: str = Field(description="自然日，格式 YYYY-MM-DD")
    value: int = Field(description="指标值")


class AdminLearningStatisticsTrendResponse(BaseModel):
    """管理员学习趋势响应。"""

    range: Literal["7d", "30d"] = Field(description="统计范围")
    metric: Literal["duration", "active_students", "completed_courses"] = Field(description="趋势指标")
    items: list[AdminLearningStatisticsTrendItem] = Field(description="趋势数据")


class AdminPopularCourseStatisticsItem(BaseModel):
    """管理员热门课程统计项。"""

    course_id: int = Field(description="课程ID")
    course_title: str = Field(description="课程标题")
    category_id: int | None = Field(default=None, description="分类ID")
    category_name: str | None = Field(default=None, description="分类名称")
    teacher_id: int = Field(description="讲师ID")
    teacher_username: str = Field(description="讲师用户名")
    active_student_count: int = Field(description="活跃学生数")
    total_duration_seconds: int = Field(description="有效学习时长（秒）")
    completion_rate: float = Field(description="完成率")
    recent_learn_at: datetime | None = Field(default=None, description="最近学习时间")


class AdminLowCompletionCourseStatisticsItem(BaseModel):
    """管理员低完成率课程统计项。"""

    course_id: int = Field(description="课程ID")
    course_title: str = Field(description="课程标题")
    teacher_id: int = Field(description="讲师ID")
    teacher_username: str = Field(description="讲师用户名")
    started_student_count: int = Field(description="开始学习学生数")
    completed_student_count: int = Field(description="完成学习学生数")
    completion_rate: float = Field(description="完成率")
    avg_progress: float = Field(description="平均进度")
    recent_learn_at: datetime | None = Field(default=None, description="最近学习时间")


# ==================== 播放与预览模型 ====================

class PlayUrlResponse(BaseModel):
    """播放地址响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    play_url: str = Field(description="播放地址")
    file_url: str = Field(description="资源文件地址")
    resource_type: str = Field(description="资源类型")
    file_name: str = Field(description="文件名")
    duration: int = Field(description="时长（秒）")
    is_free: bool = Field(description="是否免费")
    resolution: str | None = Field(default=None, description="分辨率")
    thumbnail_url: str | None = Field(default=None, description="缩略图地址")


class PreviewResponse(BaseModel):
    """文档预览响应"""

    resource_id: int = Field(description="资源ID")
    title: str = Field(description="资源标题")
    preview_url: str = Field(description="预览地址")
    file_type: str = Field(description="文件类型")
