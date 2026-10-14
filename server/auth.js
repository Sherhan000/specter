import jwt from 'jsonwebtoken'
import bcrypt from 'bcryptjs'
import crypto from 'crypto'
import { q, one } from './db.js'

const SECRET = process.env.JWT_SECRET || crypto.randomBytes(32).toString('hex')
if (!process.env.JWT_SECRET) console.warn('JWT_SECRET не задан, сессии сбросятся после перезапуска')

export const prod = process.env.NODE_ENV === 'production'
export const CK = 'sp'

let adminHash = null
export let botId = null
export let adminId = null

export async function setupUsers() {
  const login = (process.env.ADMIN_LOGIN || 'sher').toLowerCase()
  const pass = process.env.ADMIN_PASSWORD
  if (!pass) console.warn('ADMIN_PASSWORD не задан, вход админа выключен')
  else adminHash = await bcrypt.hash(pass, 11)

  let a = await one(`select id from users where kind='admin' and username=$1`, [login])
  if (!a) a = await one(`insert into users(kind,name,username) values('admin',$1,$2) returning id`, ['Шер', login])
  adminId = a.id

  let b = await one(`select id from users where kind='bot' and username='spec'`)
  if (!b) b = await one(`insert into users(kind,name,username,bio) values('bot','Спек','spec','ИИ, но с чувством юмора') returning id`)
  botId = b.id
}

export async function checkAdmin(login, pass) {
  const want = (process.env.ADMIN_LOGIN || 'sher').toLowerCase()
  if (!adminHash) return false
  const ok = await bcrypt.compare(String(pass || '').slice(0, 72), adminHash)
  return ok && String(login || '').toLowerCase().trim() === want
}

export function sign(u) {
  return jwt.sign({ id: u.id }, SECRET, { expiresIn: u.kind === 'guest' ? '2d' : '30d' })
}

export function setCookie(res, u) {
  const o = { httpOnly: true, sameSite: 'lax', secure: prod, path: '/' }
  if (u.kind !== 'guest') o.maxAge = 30 * 864e5
  res.cookie(CK, sign(u), o)
}

export function clearCookie(res) {
  res.clearCookie(CK, { httpOnly: true, sameSite: 'lax', secure: prod, path: '/' })
}

export async function userFromToken(t) {
  if (!t) return null
  try {
    const { id } = jwt.verify(t, SECRET)
    const u = await one('select * from users where id=$1', [id])
    if (!u || u.banned) return null
    return u
  } catch {
    return null
  }
}

export async function loadUser(req, res, next) {
  req.user = await userFromToken(req.cookies?.[CK])
  next()
}

export function need(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'Нужно войти' })
  next()
}

export function needAdmin(req, res, next) {
  if (req.user?.kind !== 'admin') return res.status(403).json({ error: 'Только для админа' })
  next()
}

export const pub = u => u && ({
  id: u.id, kind: u.kind, name: u.name, username: u.username, avatar: u.avatar, bio: u.bio
})

export const me = u => ({ ...pub(u), email: u.email, adult: u.adult })

export function hashCode(email, code) {
  return crypto.createHmac('sha256', SECRET).update(email + ':' + code).digest('hex')
}

const nouns = ['Призрак', 'Тень', 'Фантом', 'Дух', 'Странник', 'Енот', 'Кот', 'Лис']
export const guestName = () => nouns[crypto.randomInt(nouns.length)] + ' ' + crypto.randomInt(100, 1000)

export async function freeUsername(base) {
  let s = String(base || 'user').toLowerCase().replace(/[^a-z0-9_]/g, '').slice(0, 20)
  if (s.length < 3) s = 'user' + s
  let x = s, i = 0
  while (await one('select 1 from users where username=$1', [x])) x = s + crypto.randomInt(10, 9999) + (i++ ? i : '')
  return x
}

export async function purgeGuest(id) {
  const chats = await q(`select chat_id from members where user_id=$1`, [id])
  await q(`delete from chats where type='dm' and id in (select chat_id from members where user_id=$1)`, [id])
  await q(`delete from files where owner_id=$1`, [id])
  await q(`delete from users where id=$1 and kind='guest'`, [id])
  return chats.map(c => c.chat_id)
}
