import { ref, computed, onMounted, onUnmounted } from 'vue'

// 断点定义（与 _variables.scss 保持一致）
const BREAKPOINTS = {
  xs: 480,
  sm: 768,
  md: 1024,
  lg: 1280,
  xl: 1440,
  '2xl': 1920,
} as const

type Breakpoint = keyof typeof BREAKPOINTS

/**
 * 响应式断点检测 composable
 * 提供响应式的屏幕尺寸状态，用于条件渲染和样式切换
 */
export function useBreakpoint() {
  // 当前窗口宽度
  const width = ref(typeof window !== 'undefined' ? window.innerWidth : 1440)

  // 设备类型判断
  const isMobile = computed(() => width.value < BREAKPOINTS.sm) // < 768px
  const isTablet = computed(() => width.value >= BREAKPOINTS.sm && width.value < BREAKPOINTS.lg) // 768px - 1280px
  const isDesktop = computed(() => width.value >= BREAKPOINTS.lg) // >= 1280px

  // 具体断点判断
  const isXs = computed(() => width.value < BREAKPOINTS.xs) // < 480px
  const isSm = computed(() => width.value >= BREAKPOINTS.xs && width.value < BREAKPOINTS.sm) // 480px - 768px
  const isMd = computed(() => width.value >= BREAKPOINTS.sm && width.value < BREAKPOINTS.md) // 768px - 1024px
  const isLg = computed(() => width.value >= BREAKPOINTS.md && width.value < BREAKPOINTS.lg) // 1024px - 1280px
  const isXl = computed(() => width.value >= BREAKPOINTS.lg && width.value < BREAKPOINTS.xl) // 1280px - 1440px
  const is2xl = computed(() => width.value >= BREAKPOINTS.xl) // >= 1440px

  // 当前断点名称
  const currentBreakpoint = computed((): Breakpoint => {
    if (width.value < BREAKPOINTS.xs) return 'xs'
    if (width.value < BREAKPOINTS.sm) return 'sm'
    if (width.value < BREAKPOINTS.md) return 'md'
    if (width.value < BREAKPOINTS.lg) return 'lg'
    if (width.value < BREAKPOINTS.xl) return 'xl'
    return '2xl'
  })

  // 是否小于指定断点
  const isBelow = (breakpoint: Breakpoint): boolean => {
    return width.value < BREAKPOINTS[breakpoint]
  }

  // 是否大于等于指定断点
  const isAbove = (breakpoint: Breakpoint): boolean => {
    return width.value >= BREAKPOINTS[breakpoint]
  }

  // 更新宽度
  const updateWidth = () => {
    width.value = window.innerWidth
  }

  // 防抖处理
  let resizeTimer: ReturnType<typeof setTimeout> | null = null
  const handleResize = () => {
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }
    resizeTimer = setTimeout(updateWidth, 100)
  }

  // 生命周期
  onMounted(() => {
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }
  })

  return {
    // 响应式宽度
    width,

    // 设备类型
    isMobile,
    isTablet,
    isDesktop,

    // 具体断点
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2xl,

    // 当前断点
    currentBreakpoint,

    // 工具方法
    isBelow,
    isAbove,
  }
}

/**
 * 仅用于 CSS 媒体查询时的断点值
 * 与 SCSS 变量保持同步
 */
export const BREAKPOINT_VALUES = { ...BREAKPOINTS } as const