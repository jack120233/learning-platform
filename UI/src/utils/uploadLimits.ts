export const DIRECT_UPLOAD_LIMIT_BYTES = 500 * 1024 * 1024
export const TOTAL_UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024 * 1024
export const DIRECT_UPLOAD_LIMIT_TEXT = '500MB'
export const TOTAL_UPLOAD_LIMIT_TEXT = '5GB'

export type UploadMode = 'direct' | 'chunked' | 'blocked'

export interface ChunkUploadInitPayload {
  file_name: string
  file_size: number
  chunk_size: number
  content_type?: string
}

export function resolveUploadMode(fileSize: number): UploadMode {
  if (fileSize > TOTAL_UPLOAD_LIMIT_BYTES) {
    return 'blocked'
  }
  if (fileSize > DIRECT_UPLOAD_LIMIT_BYTES) {
    return 'chunked'
  }
  return 'direct'
}

export function getUploadSizeExceededMessage() {
  return `文件大小不能超过 ${TOTAL_UPLOAD_LIMIT_TEXT}`
}

export function buildChunkUploadInitPayload(
  file: Pick<File, 'name' | 'size' | 'type'>,
  chunkSize: number,
): ChunkUploadInitPayload {
  return {
    file_name: file.name,
    file_size: file.size,
    chunk_size: chunkSize,
    ...(file.type ? { content_type: file.type } : {}),
  }
}
