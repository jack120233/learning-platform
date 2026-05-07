# 首页课程卡片点击跳转 undefined 问题复盘文档

**日期**: 2026-04-08
**项目**: 在线教育学习视频播放平台前端
**涉及模块**: 首页课程列表、课程卡片组件、API 接口定义

---

## 一、问题现象

在首页（`http://localhost:3000/`）点击课程卡片时，页面跳转到了错误的 URL `http://localhost:3000/courses/undefined`，导致课程详情页无法正常加载。

## 二、原因分析

通过抓包核对首页接口 `http://localhost:3000/api/v1/courses/homepage` 的返回结构：

**后端返回数据 (关键部分)**：
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Python入门",
        ...
      }
    ]
  }
}
```

**问题根因**：
1. **字段名不一致**：后端课程主键字段名为 `id`，而前端 `CourseCard.vue` 使用了 `course_id` 属性进行跳转。
2. **类型定义缺失**：前端 `src/api/course.ts` 中的 `CourseBaseItem` 接口仅定义了 `course_id` 字段，未定义 `id` 字段，且没有设置字段可选，导致类型检查虽然通过逻辑却错误。

## 三、修复方案

遵循 **"兼容性优先"** 和 **"接口对齐"** 的开发规范进行修复：

### 1. 接口类型兼容 (src/api/course.ts)
在 `CourseBaseItem` 接口中增加 `id` 字段，并让 `course_id` 变为可选，以兼容不同端（讲师端 vs 学员端）的接口返回。

```ts
export interface CourseBaseItem {
  id?: number          // ✅ 增加后端物理主键
  course_id?: number   // ✅ 变为可选
  title: string
  ...
}
```

### 2. 跳转逻辑健壮性 (src/components/common/CourseCard.vue)
在处理点击事件时，优先使用 `course_id`，若不存在则回退使用 `id`。

```ts
const handleClick = () => {
  const courseId = props.data.course_id || props.data.id
  if (courseId) {
    router.push(`/courses/${courseId}`)
  } else {
    console.warn('Course ID is missing', props.data)
  }
}
```

### 3. 循环 Key 优化 (src/views/home/components/CourseListSection.vue)
同步更新 `v-for` 中的 `key` 绑定，确保虚拟 DOM 渲染性能和稳定性。

---

## 四、开发规范建议

### 1. 字段对齐规范 (API Field Mapping)
- 在定义 API Response 类型时，必须通过 Network 面板核对后端真实的返回结构。
- 对于主键 ID，若后端存在 `id` 和 `xxx_id` 混用的情况，前端接口类型应尽量通过可选字段形式进行兼容。

### 2. 字段访问防御性编程
- 在进行路由跳转等关键业务逻辑时，访问 ID 字段应具备 fallback 机制：`const id = item.xxx_id || item.id`。
- 增加必要的空值校验，避免跳转到 `undefined` 或 `NaN` 地址。

### 3. 文档归类说明
- 此类接口字段不匹配问题，应记录在 `docs/` 下的复盘文档中，供后续开发参考。

---

**文档编写**: Antigravity
**日期**: 2026-04-08
