// Regenerates docs/screenshots from a running app (default http://localhost:8000).
//
//   node scripts/capture-screenshots.mjs [base-url]
//
// Drives a local headless Chrome over the DevTools protocol, using only Node's
// built-in fetch and WebSocket, and waits in real time so animations finish.

import { spawn } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = process.argv[2] ?? 'http://localhost:8000'
const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'docs', 'screenshots')
const CHROME = process.env.CHROME_PATH ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9333

const SHOTS = [
  { name: 'input', hash: '', height: 900 },
  { name: 'results-sales', hash: '#/examples/weekly_sales_report', fullPage: true },
  { name: 'results-intake', hash: '#/examples/intake_form', height: 1500 },
  { name: 'results-employee', hash: '#/examples/employee_review', height: 1500 },
  { name: 'how-it-works', hash: '#/how-it-works', height: 1400 },
]

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'shots-'))}`,
  '--hide-scrollbars', '--no-first-run', 'about:blank',
], { stdio: 'ignore' })

try {
  let target
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200)
    target = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).then((t) => t.find((x) => x.type === 'page')).catch(() => null)
  }
  if (!target) throw new Error('Chrome did not start')

  const ws = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((r) => ws.addEventListener('open', r, { once: true }))
  let id = 0
  const pending = new Map()
  ws.addEventListener('message', (e) => {
    const msg = JSON.parse(e.data)
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg)
      pending.delete(msg.id)
    }
  })
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id
    pending.set(n, (msg) => (msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result)))
    ws.send(JSON.stringify({ id: n, method, params }))
  })
  const viewport = (height) => send('Emulation.setDeviceMetricsOverride', { width: 1440, height, deviceScaleFactor: 2, mobile: false })

  await send('Page.enable')
  await send('Runtime.enable')
  for (const shot of SHOTS) {
    await viewport(shot.height ?? 900)
    await send('Page.navigate', { url: 'about:blank' })
    await send('Page.navigate', { url: `${BASE}/${shot.hash}` })
    await sleep(2500)
    if (shot.fullPage) {
      // The app scrolls inside <main>, so grow the viewport to fit its content.
      const { result } = await send('Runtime.evaluate', { expression: "document.querySelector('main').scrollHeight", returnByValue: true })
      await viewport(Math.ceil(result.value) + 1)
      await sleep(1500)
    }
    const { data } = await send('Page.captureScreenshot', { format: 'png' })
    writeFileSync(join(OUT, `${shot.name}.png`), Buffer.from(data, 'base64'))
    console.log(`saved ${shot.name}.png`)
  }
  ws.close()
} finally {
  chrome.kill()
}
