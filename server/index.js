import 'dotenv/config'
import express from 'express'
import http from 'http'
import path from 'path'
import fs from 'fs'
import helmet from 'helmet'
import cookieParser from 'cookie-parser'
import rateLimit from 'express-rate-limit'
import { initDb, q, one, shut } from './db.js'
import { setupUsers, loadUser, prod } from './auth.js'
import { initSock } from './sock.js'
import { online } from './hub.js'
import api, { dropGuest } from './api.js'

await initDb()
await setupUsers()

const app = express()
app.set('trust proxy', 1)
app.disable('x-powered-by')

app.use(helmet({
  contentSecurityPolicy: {
    useDefaults: false,
    directives: {
      'default-src': ["'self'"],
      'script-src': ["'self'", 'https://accounts.google.com/gsi/client'],
      'style-src': ["'self'", "'unsafe-inline'", 'https://accounts.google.com/gsi/style', 'https://fonts.googleapis.com'],
      'font-src': ["'self'", 'https://fonts.gstatic.com'],
      'img-src': ["'self'", 'data:', 'blob:', 'https://*.giphy.com', 'https://*.googleusercontent.com'],
      'media-src': ["'self'", 'blob:', 'https://*.giphy.com'],
      'connect-src': ["'self'", 'https://accounts.google.com/gsi/'],
      'frame-src': ['https://accounts.google.com/gsi/'],
      'object-src': ["'none'"],
      'base-uri': ["'self'"],
      'form-action': ["'self'"],
      'frame-ancestors': ["'none'"],
      ...(prod ? { 'upgrade-insecure-requests': [] } : {})
    }
  },
  crossOriginOpenerPolicy: { policy: 'same-origin-allow-popups' },
  crossOriginEmbedderPolicy: false,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  hsts: prod
}))

const okOrigins = new Set([process.env.APP_URL, prod ? null : 'http://localhost:5173'].filter(Boolean).map(s => s.replace(/\/$/, '')))

app.use('/api', (req, res, next) => {
  if (req.method === 'GET' || req.method === 'HEAD') return next()
  const o = req.headers.origin
  if (!o) return next()
  const host = req.headers['x-forwarded-host'] || req.headers.host
  try {
    if (new URL(o).host === host || okOrigins.has(o)) return next()
  } catch {}
  res.status(403).json({ error: 'Чужой источник запроса' })
})

app.use('/api', rateLimit({ windowMs: 60e3, limit: 400, standardHeaders: 'draft-7', legacyHeaders: false }))
app.use(express.json({ limit: '64kb' }))
app.use(cookieParser())
app.use(loadUser)
app.use('/api', (req, res, next) => {
  res.set('Cache-Control', 'no-store')
  next()
})
app.use('/api', api)

app.get('/f/:id', async (req, res) => {
  if (!/^[a-f0-9]{24}$/.test(req.params.id)) return res.sendStatus(404)
  const f = await one('select mime, data from files where id=$1', [req.params.id]).catch(() => null)
  if (!f) return res.sendStatus(404)
  res.set({
    'Content-Type': f.mime,
    'Cache-Control': 'public, max-age=31536000, immutable',
    'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'",
    'Content-Disposition': 'inline'
  })
  res.end(Buffer.from(f.data))
})

const dist = path.resolve('client/dist')
if (fs.existsSync(dist)) {
  app.use(express.static(dist, { index: false, maxAge: '7d', setHeaders: (res, p) => p.endsWith('.html') && res.set('Cache-Control', 'no-cache') }))
  app.get(/^\/(?!api|f\/|socket\.io).*/, (req, res) => res.sendFile(path.join(dist, 'index.html')))
}

app.use((err, req, res, next) => {
  if (err?.code === 'LIMIT_FILE_SIZE') return res.status(400).json({ error: 'Файл больше 5 МБ' })
  if (err?.type === 'entity.too.large') return res.status(413).json({ error: 'Слишком большой запрос' })
  console.error(err)
  res.status(500).json({ error: 'Ошибка сервера' })
})

const srv = http.createServer(app)
initSock(srv, prod ? null : 'http://localhost:5173')

const sweep = async () => {
  try {
    const gs = await q(`select id from users where kind='guest' and last_seen < now() - interval '2 days'`)
    for (const g of gs) if (!online.has(g.id)) await dropGuest(g.id)
    await q('delete from codes where expires < now()')
  } catch (e) {
    console.error('sweep', e.message)
  }
}
setInterval(sweep, 3600e3).unref()
sweep()

const port = +process.env.PORT || 3000
srv.listen(port, () => console.log(`Specter: http://localhost:${port}`))

const stop = async () => {
  srv.close()
  await shut()
  process.exit(0)
}
process.on('SIGINT', stop)
process.on('SIGTERM', stop)
