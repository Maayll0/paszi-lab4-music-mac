import { defineConfig } from '@playwright/test'
import { randomBytes } from 'node:crypto'
import { resolve } from 'node:path'

process.env.MUSICACCESS_TEST_PASSWORD ??= `Aa1!${randomBytes(18).toString('hex')}`
const external = process.env.E2E_BASE_URL
const python = process.platform === 'win32' ? `"${resolve('../backend/.venv/Scripts/python.exe')}"` : 'python'
export default defineConfig({
  testDir: './e2e', workers: 1, timeout: 30000,
  use: { baseURL: external || 'http://127.0.0.1:5173',
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: external ? undefined : [
    { command: `${python} ../scripts/e2e_server.py`, url: 'http://127.0.0.1:8000/api/health', reuseExistingServer: false },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort', url: 'http://127.0.0.1:5173', reuseExistingServer: false },
  ],
})
