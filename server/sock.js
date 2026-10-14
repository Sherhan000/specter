import { Server } from 'socket.io'
import cookie from 'cookie'
import { z } from 'zod'
import { q, one } from './db.js'
import { CK, userFromToken } from './auth.js'
import { setIo, online, send, getMsg, member } from './hub.js'

const sendS = z.object({
  chatId: z.coerce.number().int().positive(),
  kind: z.enum(['text', 'sticker', 'gif', 'image']),
  body: z.string().max(4000).default(''),
  meta: z.record(z.any()).optional(),
  replyTo: z.coerce.number().int().positive().nullish()
})

const REACTS = ['👍', '❤️', '😂', '😮', '😢', '🔥', '👏', '💀', '🤡', '👻']

function clean(d) {
  const x = sendS.parse(d)
  if (x.kind === 'text') {
    x.body = x.body.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F‮‭]/g, '').trim()
    if (!x.body) throw new Error('Пустое сообщение')
    x.meta = {}
  } else if (x.kind === 'sticker') {
    const id = String(x.meta?.file || '')
    if (!/^[a-f0-9]{24}$/.test(id) && !/^e:.{1,16}$/u.test(id)) throw new Error('Плохой стикер')
    x.meta = { file: id }
    x.body = ''
  } else if (x.kind === 'image') {
    const id = String(x.meta?.file || '')
    if (!/^[a-f0-9]{24}$/.test(id)) throw new Error('Плохое фото')
    x.meta = { file: id, w: +x.meta?.w || 0, h: +x.meta?.h || 0 }
    x.body = x.body.slice(0, 1000)
  } else if (x.kind === 'gif') {
    const u = String(x.meta?.url || '')
    if (!/^https:\/\/media\d?\.giphy\.com\/[\w\-./]+$/.test(u)) throw new Error('Плохая гифка')
    x.meta = { url: u, w: +x.meta?.w || 0, h: +x.meta?.h || 0 }
    x.body = ''
  }
  return x
}

function bucket(n, per) {
  let t = n, last = Date.now()
  return () => {
    const now = Date.now()
    t = Math.min(n, t + (now - last) / per)
    last = now
    if (t < 1) return false
    t -= 1
    return true
  }
}

export function initSock(http, origin) {
  const io = new Server(http, {
    maxHttpBufferSize: 64e3,
    cors: origin ? { origin, credentials: true } : undefined,
    pingInterval: 20000
  })
  setIo(io)

  io.use(async (s, next) => {
    const c = cookie.parse(s.handshake.headers.cookie || '')
    const u = await userFromToken(c[CK])
    if (!u) return next(new Error('auth'))
    s.data.uid = u.id
    next()
  })

  io.on('connection', async s => {
    const uid = s.data.uid
    const me = () => one('select * from users where id=$1', [uid])
    s.join('u:' + uid)
    const chats = await q('select chat_id from members where user_id=$1', [uid])
    for (const c of chats) s.join('c:' + c.chat_id)
    const n = (online.get(uid) || 0) + 1
    online.set(uid, n)
    if (n === 1) for (const c of chats) s.to('c:' + c.chat_id).emit('presence', { userId: uid, online: true })

    const ok = bucket(10, 700)
    const wrap = fn => async (d, ack) => {
      const cb = typeof ack === 'function' ? ack : () => {}
      if (!ok()) return cb({ error: 'Слишком быстро, притормози' })
      try {
        const u = await me()
        if (!u || u.banned) {
          s.disconnect(true)
          return
        }
        cb({ ok: true, data: await fn(d || {}, u) })
      } catch (e) {
        cb({ error: e.issues ? 'Неверные данные' : e.message })
      }
    }

    s.on('send', wrap(async (d, u) => {
      const m = await send(s, u, clean(d))
      return m?.id
    }))

    s.on('edit', wrap(async (d, u) => {
      const body = z.string().min(1).max(4000).parse(d.body).trim()
      const m = await one('select * from messages where id=$1', [+d.id])
      if (!m || m.user_id !== u.id || m.kind !== 'text') throw new Error('Нельзя')
      if (Date.now() - new Date(m.created_at) > 48 * 3600e3) throw new Error('Слишком старое')
      await q('update messages set body=$1, edited=true where id=$2', [body, m.id])
      io.to('c:' + m.chat_id).emit('upd', await getMsg(m.id))
    }))

    s.on('del', wrap(async (d, u) => {
      const m = await one('select * from messages where id=$1', [+d.id])
      if (!m) return
      if (m.user_id !== u.id && u.kind !== 'admin') throw new Error('Удалять чужое может только админ')
      await q('delete from messages where id=$1', [m.id])
      io.to('c:' + m.chat_id).emit('del', { chatId: m.chat_id, id: m.id })
    }))

    s.on('react', wrap(async (d, u) => {
      if (!REACTS.includes(d.e)) throw new Error('Нет такой реакции')
      const m = await one('select * from messages where id=$1', [+d.id])
      if (!m || !(await member(m.chat_id, u.id))) throw new Error('Нельзя')
      const r = m.meta.r || {}
      const l = new Set(r[d.e] || [])
      l.has(u.id) ? l.delete(u.id) : l.add(u.id)
      if (l.size) r[d.e] = [...l]
      else delete r[d.e]
      await q('update messages set meta=$1 where id=$2', [JSON.stringify({ ...m.meta, r }), m.id])
      io.to('c:' + m.chat_id).emit('upd', await getMsg(m.id))
    }))

    s.on('typing', wrap(async (d, u) => {
      const id = +d.chatId
      if (!s.rooms.has('c:' + id)) return
      s.to('c:' + id).emit('typing', { chatId: id, user: { id: u.id, name: u.name } })
    }))

    s.on('read', wrap(async (d, u) => {
      const id = +d.chatId, mid = +d.id
      if (!s.rooms.has('c:' + id) || !mid) return
      await q('update members set last_read=greatest(last_read,$1) where chat_id=$2 and user_id=$3', [mid, id, u.id])
      s.to('c:' + id).emit('read', { chatId: id, userId: u.id, id: mid })
    }))

    s.on('disconnect', async () => {
      const k = (online.get(uid) || 1) - 1
      if (k > 0) return online.set(uid, k)
      online.delete(uid)
      await q('update users set last_seen=now() where id=$1', [uid]).catch(() => {})
      const cs = await q('select chat_id from members where user_id=$1', [uid]).catch(() => [])
      for (const c of cs) io.to('c:' + c.chat_id).emit('presence', { userId: uid, online: false })
    })
  })
  return io
}
