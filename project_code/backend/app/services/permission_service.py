"""角色权限管理服务。"""

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, ValidationException
from app.models.permission import Permission, RolePermission
from app.schemas.permission import RoleName


@dataclass(frozen=True)
class PermissionSeed:
    """默认权限种子定义。"""

    id: int
    name: str
    code: str
    description: str
    parent_id: int | None
    sort_order: int


DEFAULT_PERMISSIONS: tuple[PermissionSeed, ...] = (
    PermissionSeed(1, "学习中心", "learn", "学员基础学习权限集合", None, 10),
    PermissionSeed(11, "课程学习", "learn.course", "查看课程并参与学习", 1, 11),
    PermissionSeed(12, "学习记录", "learn.progress", "查看个人学习记录与进度", 1, 12),
    PermissionSeed(13, "个人中心", "learn.profile", "管理个人资料与账户信息", 1, 13),
    PermissionSeed(14, "反馈提交", "feedback.submit", "提交反馈与问题", 1, 14),
    PermissionSeed(2, "老师中心", "teacher", "老师工作台权限集合", None, 20),
    PermissionSeed(21, "课程管理", "teacher.course", "创建、编辑与维护课程", 2, 21),
    PermissionSeed(22, "内容管理", "teacher.content", "维护章节、小节和资源", 2, 22),
    PermissionSeed(23, "文件上传", "teacher.upload", "上传课程封面和教学资源", 2, 23),
    PermissionSeed(3, "管理后台", "admin", "管理员后台权限集合", None, 30),
    PermissionSeed(31, "用户管理", "admin.user", "管理平台用户和账户状态", 3, 31),
    PermissionSeed(32, "老师审核", "admin.teacher_audit", "审核老师申请", 3, 32),
    PermissionSeed(33, "管理员申请审核", "admin.admin_application", "审核管理员申请", 3, 33),
    PermissionSeed(34, "角色权限管理", "admin.role_permission", "维护角色权限配置", 3, 34),
    PermissionSeed(35, "公告管理", "admin.announcement", "发布和维护系统公告", 3, 35),
    PermissionSeed(36, "反馈处理", "admin.feedback", "查看并处理用户反馈", 3, 36),
    PermissionSeed(37, "系统消息", "admin.message", "发送系统消息和站内通知", 3, 37),
    PermissionSeed(38, "分类管理", "admin.category", "维护课程分类", 3, 38),
    PermissionSeed(39, "标签管理", "admin.tag", "维护课程标签", 3, 39),
)

DEFAULT_ROLE_PERMISSION_IDS: dict[RoleName, tuple[int, ...]] = {
    "student": (1, 11, 12, 13, 14),
    "teacher": (1, 11, 12, 13, 14, 2, 21, 22, 23),
    "admin": (1, 11, 12, 13, 14, 2, 21, 22, 23, 3, 31, 32, 33, 35, 36, 37, 38, 39),
}

VALID_ROLES: tuple[RoleName, ...] = ("student", "teacher", "admin")


class PermissionService:
    """角色权限管理服务类。"""

    async def ensure_schema_and_seed(self, db: AsyncSession) -> None:
        """确保权限相关表存在，并写入默认权限。"""
        await self._ensure_tables(db)
        await self._seed_permissions(db)
        await self._seed_role_permissions(db)

    async def get_permission_tree(self, db: AsyncSession) -> list[dict]:
        """获取权限树。"""
        await self.ensure_schema_and_seed(db)

        result = await db.execute(
            select(Permission).order_by(Permission.sort_order.asc(), Permission.id.asc())
        )
        permissions = list(result.scalars().all())

        tree_map = {
            permission.id: {
                "permission_id": permission.id,
                "name": permission.name,
                "code": permission.code,
                "description": permission.description or "",
                "parent_id": permission.parent_id,
                "children": [],
            }
            for permission in permissions
        }

        roots: list[dict] = []
        for permission in permissions:
            node = tree_map[permission.id]
            if permission.parent_id and permission.parent_id in tree_map:
                tree_map[permission.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return roots

    async def get_role_permissions(self, db: AsyncSession, role: RoleName) -> list[int]:
        """获取角色的权限ID列表。"""
        await self.ensure_schema_and_seed(db)
        self._validate_role(role)

        result = await db.execute(
            select(RolePermission.permission_id)
            .where(RolePermission.role == role)
            .order_by(RolePermission.permission_id.asc())
        )
        return list(result.scalars().all())

    async def get_role_permission_codes(self, db: AsyncSession, role: RoleName) -> list[str]:
        """获取角色的权限编码列表。"""
        await self.ensure_schema_and_seed(db)
        self._validate_role(role)

        result = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role == role)
            .order_by(Permission.sort_order.asc(), Permission.id.asc())
        )
        return list(result.scalars().all())

    async def update_role_permissions(
        self,
        db: AsyncSession,
        role: RoleName,
        permission_ids: list[int],
    ) -> list[int]:
        """更新角色权限配置。"""
        await self.ensure_schema_and_seed(db)
        self._validate_role(role)

        normalized_permission_ids = await self._normalize_permission_ids(db, permission_ids)

        await db.execute(delete(RolePermission).where(RolePermission.role == role))
        db.add_all(
            [
                RolePermission(role=role, permission_id=permission_id)
                for permission_id in normalized_permission_ids
            ]
        )
        await db.flush()
        return normalized_permission_ids

    def ensure_admin(self, role: str, message: str = "仅管理员可管理角色权限") -> None:
        """校验当前用户是否为管理员。"""
        if role != "admin":
            raise ForbiddenException(message)

    async def ensure_permission(
        self,
        db: AsyncSession,
        role: str,
        permission_code: str,
        message: str = "无权访问该资源",
    ) -> None:
        """校验当前角色是否拥有指定权限编码。"""
        self._validate_role(role)
        permission_codes = await self.get_role_permission_codes(db, role)
        if permission_code not in permission_codes:
            raise ForbiddenException(message)

    async def _ensure_tables(self, db: AsyncSession) -> None:
        """按需创建权限相关表。"""

        def _create(sync_session) -> None:
            bind = sync_session.get_bind()
            Permission.__table__.create(bind, checkfirst=True)
            RolePermission.__table__.create(bind, checkfirst=True)

        await db.run_sync(_create)

    async def _seed_permissions(self, db: AsyncSession) -> None:
        """初始化默认权限定义。"""
        result = await db.execute(select(func.count()).select_from(Permission))
        count = result.scalar() or 0
        if count > 0:
            return

        db.add_all(
            [
                Permission(
                    id=seed.id,
                    name=seed.name,
                    code=seed.code,
                    description=seed.description,
                    parent_id=seed.parent_id,
                    sort_order=seed.sort_order,
                )
                for seed in DEFAULT_PERMISSIONS
            ]
        )
        await db.flush()

    async def _seed_role_permissions(self, db: AsyncSession) -> None:
        """初始化默认角色权限映射。"""
        result = await db.execute(select(func.count()).select_from(RolePermission))
        count = result.scalar() or 0
        if count > 0:
            return

        db.add_all(
            [
                RolePermission(role=role, permission_id=permission_id)
                for role, permission_ids in DEFAULT_ROLE_PERMISSION_IDS.items()
                for permission_id in permission_ids
            ]
        )
        await db.flush()

    async def _normalize_permission_ids(self, db: AsyncSession, permission_ids: list[int]) -> list[int]:
        """校验权限ID并自动补齐父级节点。"""
        unique_permission_ids = sorted(set(permission_ids))
        if not unique_permission_ids:
            return []

        result = await db.execute(
            select(Permission.id, Permission.parent_id).order_by(Permission.id.asc())
        )
        permission_rows = result.all()
        permission_parent_map = {permission_id: parent_id for permission_id, parent_id in permission_rows}

        missing_permission_ids = [
            permission_id
            for permission_id in unique_permission_ids
            if permission_id not in permission_parent_map
        ]
        if missing_permission_ids:
            raise ValidationException(
                "存在无效的权限ID",
                details={"invalid_permissions": missing_permission_ids},
            )

        normalized_ids = set(unique_permission_ids)
        for permission_id in unique_permission_ids:
            parent_id = permission_parent_map[permission_id]
            while parent_id is not None:
                normalized_ids.add(parent_id)
                parent_id = permission_parent_map.get(parent_id)

        return sorted(normalized_ids)

    def _validate_role(self, role: str) -> None:
        """校验角色编码。"""
        if role not in VALID_ROLES:
            raise ValidationException(
                "角色类型无效",
                details={"allowed_roles": list(VALID_ROLES)},
            )


permission_service = PermissionService()
