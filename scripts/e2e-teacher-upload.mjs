import { chromium } from 'playwright'
import { mkdir, readFile } from 'node:fs/promises'
import path from 'node:path'

const rootDir = 'e:/video_project/proj_ui'
const screenshotDir = path.join(rootDir, 'logs', 'playwright-e2e')
const coverPath = path.join(rootDir, 'logs', 'e2e-cover.png')
const materialPath = path.join(rootDir, 'logs', 'e2e-material.md')
const largePath = path.join(rootDir, 'logs', 'e2e-large.pdf')
const baseUrl = 'http://localhost:3000'
const apiBaseUrl = 'http://127.0.0.1:8000/api/v1'
const courseTitle = `PW联调课程-${Date.now()}`
const chapterTitle = 'Playwright 章节'
const sectionTitle = 'Playwright 小节'
const browserChannel = process.env.PW_CHANNEL || undefined

async function waitForToast(page, text, timeout = 30000) {
  await page.locator('.el-message').filter({ hasText: text }).first().waitFor({ state: 'visible', timeout })
}

async function waitForNetworkIdle(page) {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500)
}

async function selectFirstCategory(page) {
  await page.locator('.el-select').first().click()
  const option = page.locator('.el-select-dropdown__item').first()
  await option.waitFor({ state: 'visible', timeout: 10000 })
  await option.click()
}

async function selectFirstTag(page) {
  const firstTag = page.locator('.available-tag-item').first()
  await firstTag.waitFor({ state: 'visible', timeout: 10000 })
  await firstTag.click()
}

async function uploadCover(page) {
  const coverInput = page.locator('.cover-upload input[type="file"]')
  await coverInput.setInputFiles(coverPath)
  await page.getByRole('button', { name: '确认裁切并上传' }).click()
  await waitForToast(page, '封面上传成功')
}

async function uploadMaterial(page) {
  const materialInput = page.locator('.material-upload input[type="file"]')
  await materialInput.setInputFiles(materialPath)
  await waitForToast(page, '资料上传成功')
}

async function addChapter(page, title) {
  await page.getByRole('button', { name: '添加章节' }).click()
  const dialog = page.locator('.el-dialog').filter({ hasText: '添加章节' }).last()
  await dialog.locator('input[placeholder="请输入标题"]').fill(title)
  await dialog.locator('textarea').fill('Playwright 章节联调')
  await dialog.getByRole('button', { name: '确定' }).click()
  await waitForToast(page, '章节添加成功')
}

async function addSection(page, title) {
  await page.getByRole('button', { name: '添加小节' }).first().click()
  const dialog = page.locator('.el-dialog').filter({ hasText: '添加小节' }).last()
  await dialog.locator('input[placeholder="请输入标题"]').fill(title)
  await dialog.locator('textarea').fill('Playwright 小节联调')
  await dialog.getByRole('button', { name: '确定' }).click()
  await waitForToast(page, '小节添加成功')
}

async function getAccessToken(page) {
  const token = await page.evaluate(() => localStorage.getItem('access_token') || '')
  if (!token) {
    throw new Error('未获取到 access_token')
  }
  return token
}

function getCourseIdFromUrl(url) {
  const match = url.match(/\/teacher\/courses\/(\d+)\/edit/)
  if (!match) {
    throw new Error(`无法从 URL 解析课程 ID: ${url}`)
  }
  return Number(match[1])
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API ${response.status}: ${text}`)
  }
  return response
}

function unwrapPayload(payload) {
  return payload && typeof payload === 'object' && 'data' in payload ? payload.data : payload
}

async function uploadFileByApi(token, filePath, mimeType) {
  const bytes = await readFile(filePath)
  const formData = new FormData()
  formData.append('file', new Blob([bytes], { type: mimeType }), path.basename(filePath))
  const response = await apiRequest(`${apiBaseUrl}/upload/file`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  return unwrapPayload(await response.json())
}

async function uploadLargeFileByChunk(token) {
  const buffer = await readFile(largePath)
  const chunkSize = 10 * 1024 * 1024
  const initResponse = await apiRequest(`${apiBaseUrl}/upload/init`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_name: path.basename(largePath),
      file_size: buffer.length,
      chunk_size: chunkSize,
    }),
  })
  const initData = unwrapPayload(await initResponse.json())

  for (let index = 0; index < initData.total_chunks; index += 1) {
    const start = index * chunkSize
    const end = Math.min(start + chunkSize, buffer.length)
    const formData = new FormData()
    formData.append('upload_id', initData.upload_id)
    formData.append('chunk_index', String(index))
    formData.append(
      'chunk',
      new Blob([buffer.subarray(start, end)], { type: 'application/pdf' }),
      `${path.basename(largePath)}.part${index}`,
    )
    await apiRequest(`${apiBaseUrl}/upload/chunk`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })
  }

  const completeResponse = await apiRequest(`${apiBaseUrl}/upload/complete`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      upload_id: initData.upload_id,
      file_name: path.basename(largePath),
      total_chunks: initData.total_chunks,
    }),
  })
  return unwrapPayload(await completeResponse.json())
}

async function uploadResourcesByApi(page) {
  const token = await getAccessToken(page)
  const courseId = getCourseIdFromUrl(page.url())

  const detailResponse = await apiRequest(`${apiBaseUrl}/courses/${courseId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const detail = unwrapPayload(await detailResponse.json())
  const chapter = (detail.chapters || []).find(item => item.title === chapterTitle)
  const section = (chapter?.sections || []).find(item => item.title === sectionTitle)

  if (!chapter?.chapter_id || !section?.section_id) {
    throw new Error('未找到刚创建的章节或小节')
  }

  const smallFile = await uploadFileByApi(token, materialPath, 'text/markdown')
  await apiRequest(`${apiBaseUrl}/courses/${courseId}/sections/${section.section_id}/resources`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      resource_type: 'document',
      title: path.basename(materialPath),
      file_name: path.basename(materialPath),
      file_url: smallFile.file_url,
      file_size: (await readFile(materialPath)).length,
      sort_order: 0,
      is_free: false,
    }),
  })

  const largeFile = await uploadLargeFileByChunk(token)
  await apiRequest(`${apiBaseUrl}/courses/${courseId}/chapters/${chapter.chapter_id}/resources`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      resource_type: 'document',
      title: path.basename(largePath),
      file_name: path.basename(largePath),
      file_url: largeFile.file_url,
      file_size: (await readFile(largePath)).length,
      sort_order: 0,
      is_free: false,
    }),
  })
}

async function verifyResourcesInUi(page) {
  await page.reload({ waitUntil: 'domcontentloaded' })
  await waitForNetworkIdle(page)

  await page.getByRole('button', { name: '课件资源' }).first().click()
  let dialog = page.locator('.el-dialog').filter({ hasText: '资源管理' }).last()
  await dialog.getByText(path.basename(materialPath)).waitFor({ state: 'visible', timeout: 10000 })
  await dialog.locator('.el-dialog__headerbtn').click()

  await page.getByRole('button', { name: '整体资源管理' }).first().click()
  dialog = page.locator('.el-dialog').filter({ hasText: '资源管理' }).last()
  await dialog.getByText(path.basename(largePath)).waitFor({ state: 'visible', timeout: 10000 })
  await dialog.locator('.el-dialog__headerbtn').click()
}

async function main() {
  await mkdir(screenshotDir, { recursive: true })

  const browser = await chromium.launch({ headless: true, channel: browserChannel })
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } })
  const page = await context.newPage()

  try {
    console.log('Step 1: 打开登录页')
    await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded' })
    await waitForNetworkIdle(page)

    console.log('Step 2: 登录 teacher1')
    await page.getByPlaceholder('请输入邮箱').fill('teacher1@test.com')
    await page.getByPlaceholder('请输入密码').fill('Test123456')
    await page.locator('.submit-btn').click()
    await waitForToast(page, '登录成功')
    await page.waitForURL(url => !url.pathname.startsWith('/login'), { timeout: 30000 })

    console.log('Step 3: 进入创建课程页')
    await page.goto(`${baseUrl}/teacher/courses/create`, { waitUntil: 'domcontentloaded' })
    await waitForNetworkIdle(page)

    console.log('Step 4: 填写课程基本信息')
    await page.getByPlaceholder('请输入课程标题').fill(courseTitle)
    await uploadCover(page)
    await selectFirstCategory(page)
    await selectFirstTag(page)
    await page.getByPlaceholder('请输入课程简介（10-500 字符）').fill('这是一个通过 Playwright 触发的教师端联调课程，用于验证上传与保存流程。')
    await page.getByPlaceholder('请输入课程详细描述（可选）').fill('封面上传、课程资料上传、章节资源上传、小节资源上传、发布流程。')

    console.log('Step 5: 保存草稿')
    await page.getByRole('button', { name: '保存草稿' }).click()
    await waitForToast(page, '保存成功')
    await page.waitForURL(/\/teacher\/courses\/\d+\/edit/, { timeout: 30000 })
    await waitForNetworkIdle(page)

    console.log('Step 6: 上传课程资料')
    await uploadMaterial(page)

    console.log('Step 7: 添加章节与小节')
    await addChapter(page, chapterTitle)
    await addSection(page, sectionTitle)

    console.log('Step 8: 通过 API 补充小节与章节资源')
    await uploadResourcesByApi(page)

    console.log('Step 9: 在页面中校验资源已展示')
    await verifyResourcesInUi(page)

    console.log('Step 10: 发布课程')
    await page.getByRole('button', { name: '保存并发布' }).click()
    await waitForToast(page, '课程已发布')
    await page.waitForURL(/\/teacher\/courses$/, { timeout: 30000 })

    const finalScreenshot = path.join(screenshotDir, `teacher-upload-success-${Date.now()}.png`)
    await page.screenshot({ path: finalScreenshot, fullPage: true })

    const result = {
      success: true,
      courseTitle,
      finalUrl: page.url(),
      screenshot: finalScreenshot,
    }
    console.log(JSON.stringify(result, null, 2))
  } catch (error) {
    const errorScreenshot = path.join(screenshotDir, `teacher-upload-error-${Date.now()}.png`)
    await page.screenshot({ path: errorScreenshot, fullPage: true })
    console.error(JSON.stringify({
      success: false,
      courseTitle,
      url: page.url(),
      screenshot: errorScreenshot,
      error: error instanceof Error ? error.message : String(error),
    }, null, 2))
    process.exitCode = 1
  } finally {
    await context.close()
    await browser.close()
  }
}

main()
