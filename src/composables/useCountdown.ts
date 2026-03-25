import { ref, onUnmounted, computed } from 'vue'

/**
 * 倒计时 Composable
 * @param seconds 倒计时秒数，默认 60 秒
 */
export function useCountdown(seconds: number = 60) {
  const countdown = ref(0)
  let timer: ReturnType<typeof setInterval> | null = null

  const isActive = computed(() => countdown.value > 0)

  function start() {
    if (isActive.value) return

    countdown.value = seconds
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        stop()
      }
    }, 1000)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    countdown.value = 0
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    stop()
  })

  return {
    countdown,
    isActive,
    start,
    stop,
  }
}