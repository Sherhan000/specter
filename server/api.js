import express from 'express'
import crypto from 'crypto'
import multer from 'multer'
import rateLimit from 'express-rate-limit'
import { z } from 'zod'
import { fileTypeFromBuffer } from 'file-type'
import { OAuth2Client } from 'google-auth-library'
import { q, one, getKv, setKv } from './db.js'
import {
  need, needAdmin, setCookie, clearCookie, pub, me, hashCode, guestName, freeUsername,
  purgeGuest, checkAdmin, botId, adminId
} from './auth.js'
import { sendCode, mailOn } from './mail.js'
import { aiOn } from './ai.js'
import { io, online, sets, DEF, chatList, chatOne, getMsgs, member, emitChat, joinRoom, system } from './hub.js'

const r = express.Router()
const GID = process.env.GOOGLE_CLIENT_ID
const gc = GID ? new OAuth2Client(GID) : null
const GIPHY = process.env.GIPHY_API_KEY

const lim = (n, min, key) => rateLimit({
  windowMs: min * 60e3, limit: n, standardHeaders: 'draft-7', legacyHeaders: false,
  keyGenerator: key, message: { error: 'Слишком много попыток, подожди немного' }
})

const h = fn => (req, res, next) => fn(req, res, next).catch(e => {
  if (e instanceof z.ZodError) return res.status(400).json({ error: 'Неверные данные' })
  if (e.status) return res.status(e.status).json({ error: e.message })
  next(e)
})
const bad = (m, s = 400) => Object.assign(new Error(m), { status: s })
const isAdm = u => u?.kind === 'admin'

r.get('/config', (req, res) => res.json({ google: GID || null, email: mailOn, gifs: !!GIPHY, ai: aiOn }))

r.get('/me', (req, res) => res.json({ user: req.user ? me(req.user) : null }))

const login = async (res, u) => {
  await q('update users set last_seen=now() where id=$1', [u.id])
  setCookie(res, u)
  res.json({ user: me(u) })
}

const emailS = z.string().trim().toLowerCase().email().max(120)

r.post('/auth/email/send', lim(5, 15), h(async (req, res) => {
  const email = emailS.parse(req.body.email)
  const prev = await one('select expires from codes where email=$1', [email])
  if (prev && new Date(prev.expires) - Date.now() > 9 * 60e3) throw bad('Код уже отправлен, подожди минуту', 429)
  const code = String(crypto.randomInt(100000, 1000000))
  await q(`insert into codes(email,hash,expires,tries) values($1,$2,now()+interval '10 minutes',0)
    on conflict (email) do update set hash=$2, expires=now()+interval '10 minutes', tries=0`, [email, hashCode(email, code)])
  await sendCode(email, code)
  res.json({ ok: true })
}))

r.post('/auth/email/verify', lim(20, 15), h(async (req, res) => {
  const email = emailS.parse(req.body.email)
  const code = z.string().regex(/^\d{6}$/).parse(String(req.body.code || '').trim())
  const c = await one('select * from codes where email=$1', [email])
  if (!c || new Date(c.expires) < new Date()) throw bad('Код истёк, запроси новый')
  if (c.tries >= 5) throw bad('Слишком много ошибок, запроси новый код', 429)
  const a = Buffer.from(c.hash), b = Buffer.from(hashCode(email, code))
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    await q('update codes set tries=tries+1 where email=$1', [email])
    throw bad('Неверный код')
  }
  await q('delete from codes where email=$1', [email])
  let u = await one('select * from users where email=$1', [email])
  if (!u) u = await one(`insert into users(kind,email,name,username) values('user',$1,$2,$3) returning *`,
    [email, email.split('@')[0].slice(0, 30), await freeUsername(email.split('@')[0])])
  if (u.banned) throw bad('Аккаунт заблокирован', 403)
  if (req.user?.kind === 'guest') await dropGuest(req.user.id)
  await login(res, u)
}))

r.post('/auth/google', lim(20, 15), h(async (req, res) => {
  if (!gc) throw bad('Вход через Google не настроен')
  const t = await gc.verifyIdToken({ idToken: z.string().max(4096).parse(req.body.credential), audience: GID }).catch(() => null)
  const p = t?.getPayload()
  if (!p?.sub || !p.email_verified) throw bad('Google не подтвердил аккаунт', 401)
  const email = p.email.toLowerCase()
  let u = await one('select * from users where google_id=$1', [p.sub])
  if (!u) {
    u = await one('select * from users where email=$1', [email])
    if (u) await q('update users set google_id=$1 where id=$2', [p.sub, u.id])
    else u = await one(`insert into users(kind,email,google_id,name,username) values('user',$1,$2,$3,$4) returning *`,
      [email, p.sub, (p.name || email.split('@')[0]).slice(0, 40), await freeUsername(email.split('@')[0])])
  }
  if (u.banned) throw bad('Аккаунт заблокирован', 403)
  if (req.user?.kind === 'guest') await dropGuest(req.user.id)
  await login(res, u)
}))

async function makeGuest(name) {
  const n = z.string().trim().min(2).max(30).safeParse(name)
  return one(`insert into users(kind,name,username) values('guest',$1,$2) returning *`,
    [n.success ? n.data : guestName(), await freeUsername('guest' + crypto.randomInt(1e5, 1e6))])
}

r.post('/auth/guest', lim(10, 15), h(async (req, res) => {
  if (req.user) return res.json({ user: me(req.user) })
  await login(res, await makeGuest(req.body.name))
}))

r.post('/auth/admin', lim(5, 15), h(async (req, res) => {
  if (!(await checkAdmin(req.body.login, req.body.password))) throw bad('Неверный логин или пароль', 401)
  await login(res, await one('select * from users where id=$1', [adminId]))
}))

async function dropGuest(id) {
  const chats = await purgeGuest(id)
  for (const c of chats) {
    io.to('c:' + c).emit('purged', { chatId: c, userId: id })
    const still = await one('select 1 from chats where id=$1', [c])
    if (still) emitChat(c).catch(() => {})
  }
  io.in('u:' + id).disconnectSockets(true)
}

r.post('/auth/logout', h(async (req, res) => {
  if (req.user?.kind === 'guest') await dropGuest(req.user.id)
  clearCookie(res)
  res.json({ ok: true })
}))

r.patch('/me', need, h(async (req, res) => {
  const b = z.object({
    name: z.string().trim().min(1).max(40).optional(),
    username: z.string().trim().toLowerCase().regex(/^[a-z0-9_]{3,24}$/).optional(),
    bio: z.string().trim().max(200).optional(),
    adult: z.boolean().optional(),
    avatar: z.string().regex(/^[a-f0-9]{24}$/).nullable().optional()
  }).parse(req.body)
  const u = req.user
  if (u.kind === 'guest' && (b.adult || b.username)) throw bad('Гостям это недоступно, зарегистрируйся')
  if (u.kind === 'bot') throw bad('Нельзя')
  if (b.username && b.username !== u.username) {
    if (['spec', 'admin', 'sher', 'specter', 'support'].includes(b.username) && u.kind !== 'admin') throw bad('Этот ник занят')
    if (await one('select 1 from users where username=$1 and id<>$2', [b.username, u.id])) throw bad('Этот ник занят')
  }
  if (b.avatar && !(await one('select 1 from files where id=$1 and owner_id=$2', [b.avatar, u.id]))) throw bad('Нет такого файла')
  const f = Object.entries(b).filter(([, v]) => v !== undefined)
  if (f.length) await q(`update users set ${f.map(([k], i) => `${k}=$${i + 2}`).join(',')} where id=$1`, [u.id, ...f.map(x => x[1])])
  res.json({ user: me(await one('select * from users where id=$1', [u.id])) })
}))

r.get('/users', need, h(async (req, res) => {
  const s = z.string().trim().max(40).parse(req.query.q || '').replace(/^@/, '').toLowerCase()
  if (s.length < 2) return res.json({ users: [] })
  const like = '%' + s.replace(/[%_\\]/g, '\\$&') + '%'
  const l = await q(`select * from users where banned=false and kind<>'guest' and id<>$1 and (username like $2 or lower(name) like $2)
    order by (username=$3) desc, kind='bot' desc, id limit 20`, [req.user.id, like, s])
  res.json({ users: l.map(u => ({ ...pub(u), online: online.has(u.id) || u.kind === 'bot' })) })
}))

r.get('/chats', need, h(async (req, res) => res.json({ chats: await chatList(req.user.id) })))

r.post('/chats/dm', need, h(async (req, res) => {
  const pid = z.coerce.number().int().parse(req.body.userId)
  const p = await one('select * from users where id=$1 and banned=false', [pid])
  if (!p || p.id === req.user.id) throw bad('Пользователь не найден', 404)
  if (p.kind === 'guest' && req.user.kind !== 'admin') throw bad('Гостям нельзя писать в личку')
  const key = [req.user.id, p.id].sort((a, b) => a - b).join(':')
  let c = await one('select * from chats where dm_key=$1', [key])
  if (!c) {
    c = await one(`insert into chats(type,dm_key,settings) values('dm',$1,$2) returning *`, [key, JSON.stringify({ ai: p.kind === 'bot' })])
    await q('insert into members(chat_id,user_id) values($1,$2),($1,$3)', [c.id, req.user.id, p.id])
    joinRoom(req.user.id, c.id)
    joinRoom(p.id, c.id)
    io.to('u:' + p.id).emit('chat', await chatOne(c.id, p.id))
  }
  res.json({ chat: await chatOne(c.id, req.user.id) })
}))

const newInvite = () => crypto.randomBytes(12).toString('base64url')

r.post('/chats/group', need, h(async (req, res) => {
  if (req.user.kind === 'guest') throw bad('Гости не могут создавать группы')
  const b = z.object({
    title: z.string().trim().min(1).max(60),
    members: z.array(z.coerce.number().int()).max(200).default([])
  }).parse(req.body)
  const c = await one(`insert into chats(type,title,owner_id,invite,settings) values('group',$1,$2,$3,$4) returning *`,
    [b.title, req.user.id, newInvite(), JSON.stringify(DEF)])
  await q(`insert into members(chat_id,user_id,role) values($1,$2,'owner')`, [c.id, req.user.id])
  joinRoom(req.user.id, c.id)
  const ids = [...new Set(b.members)].filter(x => x !== req.user.id && x !== botId)
  if (ids.length) await addMembers(c.id, ids)
  await system(c.id, `${req.user.name} создал(а) группу «${b.title}»`)
  res.json({ chat: await chatOne(c.id, req.user.id) })
}))

async function addMembers(chatId, ids) {
  const ok = await q(`select id, name from users where id = any($1::int[]) and banned=false and kind in ('user','admin')`, [ids])
  for (const u of ok) {
    const x = await one(`insert into members(chat_id,user_id) values($1,$2) on conflict do nothing returning user_id`, [chatId, u.id])
    if (x) {
      joinRoom(u.id, chatId)
      io.to('u:' + u.id).emit('chat', await chatOne(chatId, u.id))
    }
  }
  return ok
}

async function chatFor(req, id) {
  const c = await one('select * from chats where id=$1', [+id])
  if (!c) throw bad('Чат не найден', 404)
  const m = await member(c.id, req.user.id)
  if (!m && !isAdm(req.user)) throw bad('Ты не в этом чате', 403)
  return { c, m }
}

const canManage = (req, c) => isAdm(req.user) || c.owner_id === req.user.id

r.get('/chats/:id', need, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const ms = await q(`select u.*, m.role, m.muted_until, exists(select 1 from bans b where b.chat_id=m.chat_id and b.user_id=u.id) as banned_here
    from members m join users u on u.id=m.user_id where m.chat_id=$1 order by m.role='owner' desc, u.kind='admin' desc, m.joined_at`, [c.id])
  const out = {
    id: c.id, type: c.type, title: c.title, avatar: c.avatar, owner_id: c.owner_id, settings: sets(c),
    members: ms.map(u => ({ ...pub(u), role: u.role, muted_until: u.muted_until, banned_here: u.banned_here, online: online.has(u.id) || u.kind === 'bot' }))
  }
  if (c.type === 'group' && canManage(req, c)) out.invite = c.invite
  res.json({ chat: out })
}))

r.get('/chats/:id/messages', need, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const before = req.query.before ? z.coerce.number().int().parse(req.query.before) : null
  res.json({ messages: (await getMsgs(c.id, before)).reverse() })
}))

r.patch('/chats/:id', need, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  if (c.type !== 'group' || !canManage(req, c)) throw bad('Нет прав', 403)
  const b = z.object({
    title: z.string().trim().min(1).max(60).optional(),
    avatar: z.string().regex(/^[a-f0-9]{24}$/).nullable().optional()
  }).parse(req.body)
  if (b.title) await q('update chats set title=$1 where id=$2', [b.title, c.id])
  if (b.avatar !== undefined) await q('update chats set avatar=$1 where id=$2', [b.avatar, c.id])
  await emitChat(c.id)
  res.json({ ok: true })
}))

r.patch('/chats/:id/settings', need, needAdmin, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const b = z.object({
    guests: z.boolean(), media: z.boolean(), stickers: z.boolean(), gifs: z.boolean(),
    nsfw: z.boolean(), ai: z.boolean(), add: z.boolean(), slow: z.number().int().min(0).max(3600)
  }).partial().parse(req.body)
  const s = { ...sets(c), ...b }
  await q('update chats set settings=$1 where id=$2', [JSON.stringify(s), c.id])
  if (b.nsfw !== undefined && b.nsfw !== sets(c).nsfw) await system(c.id, b.nsfw ? 'Админ включил 18+ команды. Работают только у тех, кто подтвердил возраст. /help' : 'Админ выключил 18+ команды')
  await emitChat(c.id)
  res.json({ settings: s })
}))

r.post('/chats/:id/members', need, h(async (req, res) => {
  const { c, m } = await chatFor(req, req.params.id)
  if (c.type !== 'group') throw bad('Это не группа')
  if (!canManage(req, c) && !(sets(c).add && m && req.user.kind !== 'guest')) throw bad('Нет прав', 403)
  const ids = z.array(z.coerce.number().int()).min(1).max(100).parse(req.body.userIds)
  const banned = (await q('select user_id from bans where chat_id=$1', [c.id])).map(x => x.user_id)
  const added = await addMembers(c.id, ids.filter(x => !banned.includes(x)))
  if (added.length) await system(c.id, `${req.user.name} добавил(а): ${added.map(x => x.name).join(', ')}`)
  await emitChat(c.id)
  res.json({ ok: true })
}))

r.delete('/chats/:id/members/:uid', need, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const uid = +req.params.uid
  const self = uid === req.user.id
  if (!self && !isAdm(req.user)) throw bad('Выгонять может только админ', 403)
  const u = await one('select * from users where id=$1', [uid])
  if (!u) throw bad('Нет такого', 404)
  if (c.type === 'dm') {
    if (!self && !isAdm(req.user)) throw bad('Нет прав', 403)
    await q('delete from chats where id=$1', [c.id])
    io.to('c:' + c.id).emit('chat:del', { chatId: c.id })
    io.in('c:' + c.id).socketsLeave('c:' + c.id)
    return res.json({ ok: true })
  }
  await q('delete from members where chat_id=$1 and user_id=$2', [c.id, uid])
  io.to('u:' + uid).emit('chat:del', { chatId: c.id })
  io.in('u:' + uid).socketsLeave('c:' + c.id)
  await system(c.id, self ? `${u.name} вышел(ла) из группы` : `Админ выгнал(а) ${u.name}`)
  await emitChat(c.id)
  res.json({ ok: true })
}))

r.post('/chats/:id/ban/:uid', need, needAdmin, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const uid = +req.params.uid
  const on = req.body.on !== false
  const u = await one('select * from users where id=$1', [uid])
  if (!u || u.kind === 'admin') throw bad('Нельзя')
  if (on) {
    await q('insert into bans values($1,$2) on conflict do nothing', [c.id, uid])
    await q('delete from members where chat_id=$1 and user_id=$2', [c.id, uid])
    io.to('u:' + uid).emit('chat:del', { chatId: c.id })
    io.in('u:' + uid).socketsLeave('c:' + c.id)
    await system(c.id, `${u.name} забанен(а)`)
  } else await q('delete from bans where chat_id=$1 and user_id=$2', [c.id, uid])
  await emitChat(c.id)
  res.json({ ok: true })
}))

r.post('/chats/:id/mute/:uid', need, needAdmin, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  const min = z.number().int().min(0).max(60 * 24 * 30).parse(req.body.minutes)
  const u = await one('select name from users where id=$1', [+req.params.uid])
  const until = min ? new Date(Date.now() + min * 60e3).toISOString() : null
  await q('update members set muted_until=$1 where chat_id=$2 and user_id=$3', [until, c.id, +req.params.uid])
  if (u) await system(c.id, min ? `${u.name} в муте на ${min} мин` : `С ${u.name} сняли мут`)
  res.json({ ok: true })
}))

r.post('/chats/:id/invite', need, h(async (req, res) => {
  const { c } = await chatFor(req, req.params.id)
  if (c.type !== 'group' || !canManage(req, c)) throw bad('Нет прав', 403)
  const inv = newInvite()
  await q('update chats set invite=$1 where id=$2', [inv, c.id])
  res.json({ invite: inv })
}))

r.get('/invite/:t', h(async (req, res) => {
  const c = await one(`select id, title, avatar, (select count(*) from members where chat_id=chats.id)::int as cnt from chats where invite=$1 and type='group'`, [String(req.params.t).slice(0, 40)])
  if (!c) throw bad('Ссылка недействительна', 404)
  res.json({ chat: c })
}))

r.post('/invite/:t/join', lim(30, 15), h(async (req, res) => {
  const c = await one(`select * from chats where invite=$1 and type='group'`, [String(req.params.t).slice(0, 40)])
  if (!c) throw bad('Ссылка недействительна', 404)
  let u = req.user
  if (!u) {
    u = await makeGuest(req.body?.name)
    setCookie(res, u)
  }
  if (await one('select 1 from bans where chat_id=$1 and user_id=$2', [c.id, u.id])) throw bad('Тебя забанили в этой группе', 403)
  const x = await one('insert into members(chat_id,user_id) values($1,$2) on conflict do nothing returning user_id', [c.id, u.id])
  if (x) {
    joinRoom(u.id, c.id)
    await system(c.id, `${u.name} присоединил(ась) по ссылке${u.kind === 'guest' ? ' как гость' : ''}`)
    await emitChat(c.id)
  }
  res.json({ user: me(u), chatId: c.id })
}))

const up = multer({ storage: multer.memoryStorage(), limits: { fileSize: 5 * 1024 * 1024, files: 1 } })
const IMG = ['image/png', 'image/jpeg', 'image/webp', 'image/gif']

r.post('/files', need, lim(40, 10, req => 'f' + req.user?.id), up.single('file'), h(async (req, res) => {
  if (!req.file) throw bad('Нет файла')
  const t = await fileTypeFromBuffer(req.file.buffer)
  if (!t || !IMG.includes(t.mime)) throw bad('Можно только PNG, JPG, WEBP или GIF')
  const used = await one('select coalesce(sum(size),0)::int as s from files where owner_id=$1', [req.user.id])
  if (used.s > (req.user.kind === 'guest' ? 20 : 300) * 1024 * 1024) throw bad('Закончилось место для файлов')
  const id = crypto.randomBytes(12).toString('hex')
  await q('insert into files(id,owner_id,mime,size,data) values($1,$2,$3,$4,$5)', [id, req.user.id, t.mime, req.file.size, req.file.buffer])
  res.json({ id })
}))

r.get('/gifs', need, lim(60, 1, req => 'g' + req.user?.id), h(async (req, res) => {
  if (!GIPHY) return res.json({ gifs: [] })
  const s = z.string().trim().max(50).parse(req.query.q || '')
  const u = new URL('https://api.giphy.com/v1/gifs/' + (s ? 'search' : 'trending'))
  u.search = new URLSearchParams({ api_key: GIPHY, limit: '30', rating: 'pg-13', lang: 'ru', ...(s ? { q: s } : {}) })
  const j = await fetch(u, { signal: AbortSignal.timeout(8000) }).then(x => x.json()).catch(() => ({ data: [] }))
  res.json({
    gifs: (j.data || []).map(g => {
      const f = g.images?.fixed_height
      return f && { id: g.id, url: f.webp || f.url, w: +f.width, h: +f.height }
    }).filter(Boolean).filter(g => /^https:\/\/media\d?\.giphy\.com\//.test(g.url)).map(g => ({ ...g, url: g.url.split('?')[0] }))
  })
}))

r.get('/packs', need, h(async (req, res) => {
  const ps = await q(`select p.*, (p.owner_id=$1) as mine from packs p where p.owner_id=$1 or p.id in (select pack_id from saved_packs where user_id=$1) order by p.id`, [req.user.id])
  const st = ps.length ? await q('select * from stickers where pack_id = any($1::int[]) order by id', [ps.map(p => p.id)]) : []
  res.json({ packs: ps.map(p => ({ id: p.id, title: p.title, mine: p.mine, stickers: st.filter(s => s.pack_id === p.id).map(s => ({ id: s.id, file: s.file_id, emoji: s.emoji })) })) })
}))

r.post('/packs', need, h(async (req, res) => {
  if (req.user.kind === 'guest') throw bad('Гости не могут создавать стикерпаки')
  const title = z.string().trim().min(1).max(40).parse(req.body.title)
  const n = await one('select count(*)::int as n from packs where owner_id=$1', [req.user.id])
  if (n.n >= 30) throw bad('Максимум 30 паков')
  res.json({ pack: await one('insert into packs(owner_id,title) values($1,$2) returning id, title', [req.user.id, title]) })
}))

r.post('/packs/:id/stickers', need, h(async (req, res) => {
  const p = await one('select * from packs where id=$1 and owner_id=$2', [+req.params.id, req.user.id])
  if (!p) throw bad('Пак не найден', 404)
  const file = z.string().regex(/^[a-f0-9]{24}$/).parse(req.body.file)
  if (!(await one('select 1 from files where id=$1 and owner_id=$2', [file, req.user.id]))) throw bad('Нет такого файла')
  const n = await one('select count(*)::int as n from stickers where pack_id=$1', [p.id])
  if (n.n >= 120) throw bad('В паке максимум 120 стикеров')
  const emoji = z.string().max(8).default('').parse(req.body.emoji || '')
  res.json({ sticker: await one('insert into stickers(pack_id,file_id,emoji) values($1,$2,$3) returning id, file_id as file, emoji', [p.id, file, emoji]) })
}))

r.delete('/packs/:id/stickers/:sid', need, h(async (req, res) => {
  await q('delete from stickers where id=$1 and pack_id in (select id from packs where id=$2 and owner_id=$3)', [+req.params.sid, +req.params.id, req.user.id])
  res.json({ ok: true })
}))

r.delete('/packs/:id', need, h(async (req, res) => {
  await q('delete from packs where id=$1 and owner_id=$2', [+req.params.id, req.user.id])
  await q('delete from saved_packs where pack_id=$1 and user_id=$2', [+req.params.id, req.user.id])
  res.json({ ok: true })
}))

r.post('/stickers/:file/save', need, h(async (req, res) => {
  const s = await one('select pack_id from stickers where file_id=$1 limit 1', [req.params.file])
  if (!s) throw bad('Стикер не найден', 404)
  await q('insert into saved_packs values($1,$2) on conflict do nothing', [req.user.id, s.pack_id])
  res.json({ ok: true })
}))

r.get('/admin/stats', need, needAdmin, h(async (req, res) => {
  res.json(await one(`select (select count(*) from users where kind='user')::int as users, (select count(*) from users where kind='guest')::int as guests,
    (select count(*) from chats where type='group')::int as groups, (select count(*) from messages)::int as messages,
    (select count(*) from ai_samples)::int as samples, ${online.size} as online`))
}))

r.get('/admin/users', need, needAdmin, h(async (req, res) => {
  const s = '%' + z.string().max(40).parse(req.query.q || '').toLowerCase().replace(/[%_\\]/g, '\\$&') + '%'
  const l = await q(`select * from users where username like $1 or lower(name) like $1 or coalesce(email,'') like $1 order by id desc limit 100`, [s])
  res.json({ users: l.map(u => ({ ...me(u), banned: u.banned, created_at: u.created_at, online: online.has(u.id) })) })
}))

r.post('/admin/users/:id/ban', need, needAdmin, h(async (req, res) => {
  const u = await one('select * from users where id=$1', [+req.params.id])
  if (!u || u.kind === 'admin' || u.kind === 'bot') throw bad('Нельзя')
  await q('update users set banned=$1 where id=$2', [req.body.on !== false, u.id])
  if (req.body.on !== false) io.in('u:' + u.id).disconnectSockets(true)
  res.json({ ok: true })
}))

r.get('/admin/chats', need, needAdmin, h(async (req, res) => {
  res.json({ chats: await q(`select c.id, c.title, c.settings, c.created_at, (select count(*) from members where chat_id=c.id)::int as cnt,
    (select count(*) from messages where chat_id=c.id)::int as msgs, exists(select 1 from members where chat_id=c.id and user_id=$1) as inside
    from chats c where type='group' order by c.id desc limit 200`, [req.user.id]) })
}))

r.post('/admin/chats/:id/enter', need, needAdmin, h(async (req, res) => {
  const c = await one(`select * from chats where id=$1 and type='group'`, [+req.params.id])
  if (!c) throw bad('Нет такой группы', 404)
  await q('insert into members(chat_id,user_id) values($1,$2) on conflict do nothing', [c.id, req.user.id])
  joinRoom(req.user.id, c.id)
  res.json({ chat: await chatOne(c.id, req.user.id) })
}))

r.delete('/admin/chats/:id', need, needAdmin, h(async (req, res) => {
  const id = +req.params.id
  io.to('c:' + id).emit('chat:del', { chatId: id })
  io.in('c:' + id).socketsLeave('c:' + id)
  await q(`delete from chats where id=$1`, [id])
  res.json({ ok: true })
}))

r.get('/admin/ai', need, needAdmin, h(async (req, res) => {
  res.json({ ai: await getKv('ai', { persona: '', chance: 0.03 }), on: aiOn, samples: await q('select id, text from ai_samples order by id desc limit 50') })
}))

r.put('/admin/ai', need, needAdmin, h(async (req, res) => {
  const b = z.object({ persona: z.string().max(2000), chance: z.number().min(0).max(0.5) }).parse(req.body)
  await setKv('ai', b)
  res.json({ ai: b })
}))

r.delete('/admin/ai/samples/:id', need, needAdmin, h(async (req, res) => {
  await q('delete from ai_samples where id=$1', [+req.params.id])
  res.json({ ok: true })
}))

export default r
export { dropGuest }
