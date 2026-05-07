import { rm } from 'node:fs/promises'
import { resolve } from 'node:path'
import process from 'node:process'

const cacheDirs = [
  resolve(process.cwd(), '.vite-cache'),
  resolve(process.cwd(), 'node_modules', '.vite'),
]

for (const dir of cacheDirs) {
  try {
    await rm(dir, {
      recursive: true,
      force: true,
      maxRetries: 5,
      retryDelay: 200,
    })
    console.log(`[vite-cache] cleaned ${dir}`)
  } catch (error) {
    console.warn(`[vite-cache] failed to clean ${dir}:`, error)
  }
}
