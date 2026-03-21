"""业务逻辑服务模块

导出所有服务类。
"""

from app.services.course_service import (
    CourseService,
    MaterialService,
    course_service,
    material_service,
)

__all__ = [
    "CourseService",
    "MaterialService",
    "course_service",
    "material_service",
]