import { q, one, getKv } from './db.js'
import { botId, adminId } from './auth.js'
import { parse, help, findAct, fun, render } from './actions.js'
import { reply, maybeLearn, aiOn } from './ai.js'

export let io = null
export const setIo = x => { io = x }
export const online = new Map()

export const DEF = { guests: true, media: true, stickers: true, gifs: true, nsfw: false, ai: true, slow: 0, add: true }
export const sets = c => ({ ...DEF, ...(c?.settings || {}) })

const MSEL = `select m.id, m.chat_id, m.user_id, m.kind, m.body, m.meta, m.reply_to, m.edited, m.created_at,
  json_build_object('id',u.id,'name',u.name,'username',u.username,'avatar',u.avatar,'kind',u.kind) as u,
  (select json_build_object('id',r.id,'name',ru.name,'body',left(r.body,140),'kind',r.kind) from messages r join users ru on ru.id=r.user_id where r.id=m.reply_to) as reply
  from messages m join users u on u.id=m.user_id`

export const getMsgs = (chatId, before, n = 50) => before
  ? q(`${MSEL} where m.chat_id=$1 and m.id<$2 order by m.id desc limit $3`, [chatId, before, n])
  : q(`${MSEL} where m.chat_id=$1 order by m.id desc limit $2`, [chatId, n])

export const getMsg = id => one(`${MSEL} where m.id=$1`, [id])

export const member = (chatId, uid) => one('select * from members where chat_id=$1 and user_id=$2', [chatId, uid])

export async function chatList(uid) {
  const rows = await q(`select c.id, c.type, c.title, c.avatar, c.owner_id, c.settings, m.role, m.last_read,
    (select row_to_json(x) from (select mm.id, mm.kind, mm.body, mm.user_id, mm.created_at, u.name from messages mm join users u on u.id=mm.user_id where mm.chat_id=c.id order by mm.id desc limit 1) x) as last,
    (select count(*) from messages mm where mm.chat_id=c.id and mm.id>m.last_read and mm.user_id<>$1)::int as unread,
    (select row_to_json(p) from (select u.id,u.name,u.username,u.avatar,u.kind,u.last_seen,m2.last_read as read from members m2 join users u on u.id=m2.user_id where m2.chat_id=c.id and m2.user_id<>$1 limit 1) p) as peer,
    (select count(*) from members m3 where m3.chat_id=c.id)::int as cnt
    from chats c join members m on m.chat_id=c.id where m.user_id=$1`, [uid])
  for (const r of rows) {
    r.settings = sets(r)
    if (r.peer) r.peer.online = online.has(r.peer.id) || r.peer.kind === 'bot'
    if (r.type === 'dm') delete r.cnt
    else delete r.peer
  }
  return rows.sort((a, b) => new Date(b.last?.created_at || 0) - new Date(a.last?.created_at || 0))
}

export async function chatOne(chatId, uid) {
  const l = await chatList(uid)
  return l.find(c => c.id === chatId)
}

export async function emitChat(chatId) {
  const ms = await q('select user_id from members where chat_id=$1', [chatId])
  for (const m of ms) io.to('u:' + m.user_id).emit('chat', await chatOne(chatId, m.user_id))
}

export function joinRoom(uid, chatId) {
  io.in('u:' + uid).socketsJoin('c:' + chatId)
}

export async function post(chatId, uid, kind, body = '', meta = {}, replyTo = null) {
  const r = await one(`insert into messages(chat_id,user_id,kind,body,meta,reply_to) values($1,$2,$3,$4,$5,$6) returning id`,
    [chatId, uid, kind, body, JSON.stringify(meta), replyTo])
  const m = await getMsg(r.id)
  io.to('c:' + chatId).emit('msg', m)
  return m
}

const say = (sock, chatId, text) => sock.emit('msg', {
  id: 'e' + Date.now(), chat_id: chatId, kind: 'system', body: text, meta: { eph: true }, created_at: new Date().toISOString(),
  u: { id: 0, name: 'Specter', kind: 'bot' }
})

const slow = new Map()
const busy = new Set()

export async function send(sock, u, d) {
  const chatId = +d.chatId
  const chat = await one('select * from chats where id=$1', [chatId])
  if (!chat) throw new Error('Чат не найден')
  const mem = await member(chatId, u.id)
  if (!mem) throw new Error('Ты не в этом чате')
  const s = sets(chat)
  const boss = u.kind === 'admin'
  if (!boss) {
    if (await one('select 1 from bans where chat_id=$1 and user_id=$2', [chatId, u.id])) throw new Error('Ты забанен в этом чате')
    if (mem.muted_until && new Date(mem.muted_until) > new Date()) throw new Error('Ты в муте до ' + new Date(mem.muted_until).toLocaleTimeString('ru'))
    if (chat.type === 'group' && u.kind === 'guest' && !s.guests) throw new Error('Гостям писать нельзя, зарегистрируйся')
    if (d.kind === 'image' && !s.media) throw new Error('Фото тут выключены')
    if (d.kind === 'sticker' && !s.stickers) throw new Error('Стикеры тут выключены')
    if (d.kind === 'gif' && !s.gifs) throw new Error('Гифки тут выключены')
    if (s.slow > 0) {
      const k = chatId + ':' + u.id, t = slow.get(k) || 0
      if (Date.now() - t < s.slow * 1000) throw new Error(`Медленный режим: раз в ${s.slow} сек`)
      slow.set(k, Date.now())
    }
  }

  let replyTo = null
  if (d.replyTo) {
    const r = await one('select id, user_id from messages where id=$1 and chat_id=$2', [+d.replyTo, chatId])
    if (r) replyTo = r
  }

  if (d.kind === 'text' && d.body.startsWith('/')) {
    const c = parse(d.body)
    if (c) {
      const adult = chat.type === 'group' && s.nsfw && u.adult && u.kind !== 'guest'
      if (c.cmd === 'help' || c.cmd === 'помощь' || c.cmd === 'start') return say(sock, chatId, help(adult))
      const f = fun(c.cmd, c.rest)
      if (f) return post(chatId, u.id, 'action', render(f, u.name), { e: f.e })
      const a = findAct(c.cmd, adult)
      if (a === 'locked') return say(sock, chatId, '18+ команды тут недоступны. Их включает админ в группе, и только для тех, кто подтвердил 18+ в профиле.')
      if (a) {
        let t = null
        const at = /@([a-z0-9_]{3,32})/i.exec(c.rest)
        if (at) t = await one(`select u.* from users u join members m on m.user_id=u.id and m.chat_id=$1 where u.username=$2`, [chatId, at[1].toLowerCase()])
        else if (replyTo) t = await one('select * from users where id=$1', [replyTo.user_id])
        else if (chat.type === 'dm') t = await one('select u.* from users u join members m on m.user_id=u.id where m.chat_id=$1 and u.id<>$2', [chatId, u.id])
        if (at && !t) return say(sock, chatId, 'Такого человека нет в этом чате')
        if (findAct(c.cmd, false) === 'locked' && t && (!t.adult || t.kind === 'guest' || t.kind === 'bot'))
          return say(sock, chatId, `${t.name} не подтвердил(а) 18+, так нельзя`)
        return post(chatId, u.id, 'action', render(a, u.name, t?.name), { e: a.e, to: t?.id || null }, replyTo?.id)
      }
      if (c.cmd === 'спек' || c.cmd === 'spec' || c.cmd === 'ии') {
        const m = await post(chatId, u.id, 'text', d.body, {}, replyTo?.id)
        ai(chat, s, true)
        return m
      }
    }
  }

  const m = await post(chatId, u.id, d.kind, d.body, d.meta || {}, replyTo?.id)
  if (d.kind === 'text') {
    if (u.kind !== 'guest' && chat.type === 'group' && s.ai) maybeLearn(d.body).catch(() => {})
    const isBotDm = chat.type === 'dm' && await member(chatId, botId)
    const call = /(^|\s)@spec\b/i.test(d.body) || /^спек[,!\s]/i.test(d.body) || replyTo?.user_id === botId
    const cfg = await getKv('ai', {})
    if (isBotDm || (s.ai && chat.type === 'group' && (call || Math.random() < (cfg.chance ?? 0.03)))) ai(chat, s, true)
  }
  return m
}

async function ai(chat) {
  if (!aiOn || busy.has(chat.id)) return
  busy.add(chat.id)
  try {
    io.to('c:' + chat.id).emit('typing', { chatId: chat.id, user: { id: botId, name: 'Спек' } })
    const t = await reply(chat.id, botId)
    if (t) await post(chat.id, botId, 'text', t)
  } catch (e) {
    console.error('ai', e.message)
  } finally {
    busy.delete(chat.id)
  }
}

export async function system(chatId, text) {
  return post(chatId, adminId, 'system', text)
}
