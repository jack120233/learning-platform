import { existsSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
import { spawn } from 'node:child_process'

const viteCacheDir = resolve(process.cwd(), 'node_modules', '.vite')
const maxAttempts = 5
const retryDelayMs = 400

function sleep(ms) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, ms))
}

async function removeViteCache() {
  if (!existsSync(viteCacheDir)) {
    return
  }

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      rmSync(viteCacheDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
      return
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error
      }

      console.warn(
        `[dev-start] Failed to remove Vite cache on attempt ${attempt}/${maxAttempts}. Retrying...`,
      )
      await sleep(retryDelayMs)
    }
  }
}

async function main() {
  try {
    await removeViteCache()
  } catch (error) {
    console.warn('[dev-start] Could not fully clean node_modules/.vite before startup.')
    console.warn(`[dev-start] ${error.message}`)
  }

  const viteCommand =
    process.platform === 'win32'
      ? resolve(process.cwd(), 'node_modules', '.bin', 'vite.cmd')
      : resolve(process.cwd(), 'node_modules', '.bin', 'vite')
  const launchCommand = `"${viteCommand}" --force`

  const child = spawn(launchCommand, {
    cwd: process.cwd(),
    stdio: 'inherit',
    shell: true,
  })

  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal)
      return
    }

    process.exit(code ?? 0)
  })

  child.on('error', (error) => {
    console.error(`[dev-start] Failed to start Vite: ${error.message}`)
    process.exit(1)
  })
}

main()
