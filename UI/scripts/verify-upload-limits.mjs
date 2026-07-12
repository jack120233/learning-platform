import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const uiRoot = path.resolve(scriptDir, '..')
const uploadLimitsPath = path.join(uiRoot, 'src', 'utils', 'uploadLimits.ts')

async function loadUploadLimitsModule() {
  const source = await readFile(uploadLimitsPath, 'utf8')
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText

  return import(`data:text/javascript;charset=utf-8,${encodeURIComponent(compiled)}`)
}

const uploadLimits = await loadUploadLimitsModule()
const chunkSize = 10 * 1024 * 1024

const scenarios = [
  {
    name: '<=500MB 走普通上传',
    fileSize: uploadLimits.DIRECT_UPLOAD_LIMIT_BYTES,
    expectedMode: 'direct',
  },
  {
    name: '>500MB 走分片上传',
    fileSize: uploadLimits.DIRECT_UPLOAD_LIMIT_BYTES + 1,
    expectedMode: 'chunked',
  },
  {
    name: '>5GB 前端拦截',
    fileSize: uploadLimits.TOTAL_UPLOAD_LIMIT_BYTES + 1,
    expectedMode: 'blocked',
  },
]

for (const scenario of scenarios) {
  assert.equal(uploadLimits.resolveUploadMode(scenario.fileSize), scenario.expectedMode, scenario.name)
}

const chunkPayload = uploadLimits.buildChunkUploadInitPayload(
  {
    name: 'lesson.mp4',
    size: uploadLimits.DIRECT_UPLOAD_LIMIT_BYTES + 1,
    type: 'video/mp4',
  },
  chunkSize,
)

assert.deepEqual(chunkPayload, {
  file_name: 'lesson.mp4',
  file_size: uploadLimits.DIRECT_UPLOAD_LIMIT_BYTES + 1,
  chunk_size: chunkSize,
  content_type: 'video/mp4',
})

const payloadWithoutMime = uploadLimits.buildChunkUploadInitPayload(
  {
    name: 'lesson.pdf',
    size: uploadLimits.DIRECT_UPLOAD_LIMIT_BYTES + 1,
    type: '',
  },
  chunkSize,
)

assert.ok(!('content_type' in payloadWithoutMime))

console.log(JSON.stringify({
  success: true,
  command: 'npm run verify:upload-limits',
  scenarios: scenarios.map(({ name, expectedMode }) => ({ name, expectedMode })),
  chunkPayload,
  blockedMessage: uploadLimits.getUploadSizeExceededMessage(),
}, null, 2))
