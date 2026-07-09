import defaultCourseCover from '@/assets/course-cover-default.svg'

export const DEFAULT_COURSE_COVER = defaultCourseCover

export function resolveCourseCoverUrl(coverUrl?: string | null) {
  return coverUrl?.trim() || DEFAULT_COURSE_COVER
}
