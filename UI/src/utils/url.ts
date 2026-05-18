/**
 * 处理来自后端的上传文件 URL。
 *
 * 历史数据里可能存的是绝对 URL，例如 `http://localhost:8000/uploads/files/xxx.pdf`。
 * 这种值在浏览器从 Vite dev server (127.0.0.1:3000 / localhost:3000) 访问时
 * 会直接打到 8000 端口，绕开 Vite 的 `/uploads` 代理并触发跨域。
 *
 * 这里做兜底：当 URL 是绝对 URL 且 path 指向 `/uploads/...`，
 * 就剥成相对路径，让浏览器走当前 origin（Vite 代理会转发到后端）。
 * 其它绝对 URL（外部 CDN、第三方资源）保持原样。
 */
const UPLOAD_PATH_PREFIX = '/uploads/'

export function normalizeUploadUrl(value: string): string
export function normalizeUploadUrl(value: null | undefined): ''
export function normalizeUploadUrl(value: string | null | undefined): string
export function normalizeUploadUrl(value: string | null | undefined): string {
  if (!value) return ''
  if (value.startsWith(UPLOAD_PATH_PREFIX)) return value

  try {
    const url = new URL(value)
    if ((url.protocol === 'http:' || url.protocol === 'https:') && url.pathname.startsWith(UPLOAD_PATH_PREFIX)) {
      return `${url.pathname}${url.search}${url.hash}`
    }
  } catch {
    // not a parseable absolute URL, return as-is
  }
  return value
}
