import { useEffect, useReducer, useState, useCallback, useRef } from 'react'
import { api, sock } from './api'
import Intro from './c/Intro'
import Login from './c/Login'
import Side from './c/Side'
import Chat from './c/Chat'
import { Toasts, toast } from './c/ui'
import { Profile, NewGroup, Packs } from './c/Dialogs'
import Admin from './c/Admin'

const init = { chats: {}, msgs: {}, more: {}, typing: {}, active: null }

function red(s, a) {
  switch (a.t) {
    case 'chats': return { ...s, chats: Object.fromEntries(a.l.map(c => [c.id, c.id === s.active ? { ...c, unread: 0 } : c])) }
    case 'chat': return a.c ? { ...s, chats: { ...s.chats, [a.c.id]: { ...s.chats[a.c.id], ...a.c, ...(a.c.id === s.active ? { unread: 0 } : {}) } } } : s
    case 'unchat': {
      const c = { ...s.chats }; delete c[a.id]
      return { ...s, chats: c, active: s.active === a.id ? null : s.active }
    }
    case 'open': {
      const c = s.chats[a.id]
      return { ...s, active: a.id, chats: c ? { ...s.chats, [a.id]: { ...c, unread: 0 } } : s.chats }
    }
    case 'close': return { ...s, active: null }
    case 'hist': {
      const old = s.msgs[a.id] || []
      const ids = new Set(old.map(m => m.id))
      const l = a.before ? [...a.l.filter(m => !ids.has(m.id)), ...old] : a.l
      return { ...s, msgs: { ...s.msgs, [a.id]: l }, more: { ...s.more, [a.id]: a.l.length >= 50 } }
    }
    case 'msg': {
      const m = a.m, id = m.chat_id
      const l = s.msgs[id]
      const msgs = l && !l.some(x => x.id === m.id) ? { ...s.msgs, [id]: [...l, m] } : s.msgs
      const c = s.chats[id]
      if (!c || m.meta?.eph) return { ...s, msgs }
      const unread = s.active === id || m.user_id === a.me ? c.unread : (c.unread || 0) + 1
      const ty = { ...s.typing }; if (ty[id]?.id === m.user_id) delete ty[id]
      return { ...s, msgs, typing: ty, chats: { ...s.chats, [id]: { ...c, unread, last: { id: m.id, kind: m.kind, body: m.body, user_id: m.user_id, created_at: m.created_at, name: m.u?.name } } } }
    }
    case 'upd': {
      const l = s.msgs[a.m.chat_id]
      return l ? { ...s, msgs: { ...s.msgs, [a.m.chat_id]: l.map(x => x.id === a.m.id ? a.m : x) } } : s
    }
    case 'del': {
      const l = s.msgs[a.chatId]
      return l ? { ...s, msgs: { ...s.msgs, [a.chatId]: l.filter(x => x.id !== a.id) } } : s
    }
    case 'purged': {
      const l = s.msgs[a.chatId]
      return l ? { ...s, msgs: { ...s.msgs, [a.chatId]: l.filter(x => x.user_id !== a.userId) } } : s
    }
    case 'typing': return { ...s, typing: { ...s.typing, [a.chatId]: a.u ? { ...a.u, at: Date.now() } : undefined } }
    case 'presence': {
      const chats = { ...s.chats }
      for (const k in chats) if (chats[k].peer?.id === a.userId) chats[k] = { ...chats[k], peer: { ...chats[k].peer, online: a.online, last_seen: a.online ? chats[k].peer.last_seen : new Date().toISOString() } }
      return { ...s, chats }
    }
    case 'read': {
      const c = s.chats[a.chatId]
      if (!c?.peer || c.peer.id !== a.userId) return s
      return { ...s, chats: { ...s.chats, [a.chatId]: { ...c, peer: { ...c.peer, read: Math.max(c.peer.read || 0, a.id) } } } }
    }
    case 'reset': return init
    default: return s
  }
}

export default function App() {
  const [intro, setIntro] = useState(() => { try { return !localStorage.getItem('sp_intro') } catch { return true } })
  const [cfg, setCfg] = useState(null)
  const [me, setMe] = useState(undefined)
  const [s, d] = useReducer(red, init)
  const [dlg, setDlg] = useState(null)
  const [live, setLive] = useState(false)
  const [pend, setPend] = useState(null)
  const sr = useRef(s)
  sr.current = s

  const endIntro = useCallback(() => {
    setIntro(false)
    try { localStorage.setItem('sp_intro', '1') } catch {}
  }, [])

  useEffect(() => {
    api('/config').then(setCfg).catch(() => setCfg({}))
    const j = /^\/join\/([\w-]{6,40})$/.exec(location.pathname)
    const boot = async () => {
      if (j) {
        try {
          const r = await api(`/invite/${j[1]}/join`, { body: {} })
          history.replaceState(null, '', '/')
          setMe(r.user)
          return r.chatId
        } catch (e) {
          history.replaceState(null, '', '/')
          toast(e.message, true)
        }
      }
      const r = await api('/me').catch(() => ({ user: null }))
      setMe(r.user)
    }
    boot().then(id => id && setPend(id))
  }, [])

  const loadChats = useCallback(() => api('/chats').then(r => d({ t: 'chats', l: r.chats })).catch(() => {}), [])

  useEffect(() => {
    if (!me) return
    loadChats()
    const on = {
      connect: () => { setLive(true); loadChats() },
      disconnect: () => setLive(false),
      connect_error: e => { setLive(false); if (e.message === 'auth') { setMe(null); d({ t: 'reset' }) } },
      msg: m => {
        d({ t: 'msg', m, me: me.id })
        if (!sr.current.chats[m.chat_id] && !m.meta?.eph) loadChats()
      },
      upd: m => d({ t: 'upd', m }),
      del: x => d({ t: 'del', ...x }),
      chat: c => d({ t: 'chat', c }),
      'chat:del': x => d({ t: 'unchat', id: x.chatId }),
      purged: x => d({ t: 'purged', ...x }),
      typing: x => x.user.id !== me.id && d({ t: 'typing', chatId: x.chatId, u: x.user }),
      presence: x => d({ t: 'presence', ...x }),
      read: x => d({ t: 'read', ...x })
    }
    for (const k in on) sock.on(k, on[k])
    sock.connect()
    return () => {
      for (const k in on) sock.off(k, on[k])
      sock.disconnect()
    }
  }, [me?.id])

  useEffect(() => {
    const t = setInterval(() => {
      for (const k in s.typing) if (s.typing[k] && Date.now() - s.typing[k].at > 4500) d({ t: 'typing', chatId: k, u: null })
    }, 1500)
    return () => clearInterval(t)
  }, [s.typing])

  const open = id => {
    d({ t: 'open', id })
    if (!s.msgs[id]) api(`/chats/${id}/messages`).then(r => d({ t: 'hist', id, l: r.messages })).catch(e => toast(e.message, true))
  }

  useEffect(() => {
    if (pend && s.chats[pend]) {
      open(pend)
      setPend(null)
    }
  }, [pend, s.chats])

  const logout = async () => {
    if (me.kind === 'guest' && !confirm('Ты гость. После выхода все твои сообщения и чаты удалятся. Выйти?')) return
    await api('/auth/logout', { body: {} }).catch(() => {})
    sock.disconnect()
    d({ t: 'reset' })
    setDlg(null)
    setMe(null)
  }

  const ctx = { me, setMe, s, d, open, cfg, setDlg, logout, loadChats, live }

  if (intro) return <Intro done={endIntro} />
  if (me === undefined) return <div className="boot"><img src="/ghost.svg" alt="" /></div>
  if (!me) return <><Login cfg={cfg} onUser={setMe} /><Toasts /></>

  const chat = s.active && s.chats[s.active]

  return (
    <div className={'app' + (chat ? ' has-chat' : '')}>
      <Side ctx={ctx} />
      {chat ? <Chat key={chat.id} ctx={ctx} chat={chat} /> : <div className="empty-main"><div><img src="/ghost.svg" alt="" /><p>Выбери чат или найди людей через поиск</p></div></div>}
      {dlg === 'profile' && <Profile ctx={ctx} onClose={() => setDlg(null)} />}
      {dlg === 'group' && <NewGroup ctx={ctx} onClose={() => setDlg(null)} />}
      {dlg === 'packs' && <Packs ctx={ctx} onClose={() => setDlg(null)} />}
      {dlg === 'admin' && <Admin ctx={ctx} onClose={() => setDlg(null)} />}
      {dlg === 'login' && <div className="veil"><Login cfg={cfg} upgrade onUser={u => { setDlg(null); setMe(u); d({ t: 'reset' }) }} onClose={() => setDlg(null)} /></div>}
      <Toasts />
    </div>
  )
}

