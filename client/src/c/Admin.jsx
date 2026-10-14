import { useEffect, useState } from 'react'
import { api } from '../api'
import { Ava, Modal, toast } from './ui'

export default function Admin({ ctx, onClose }) {
  const [tab, setTab] = useState('stats')
  const [st, setSt] = useState(null)
  const [users, setUsers] = useState([])
  const [uq, setUq] = useState('')
  const [chats, setChats] = useState([])
  const [ai, setAi] = useState(null)

  useEffect(() => {
    if (tab === 'stats') api('/admin/stats').then(setSt)
    if (tab === 'chats') api('/admin/chats').then(r => setChats(r.chats))
    if (tab === 'ai') api('/admin/ai').then(setAi)
  }, [tab])

  useEffect(() => {
    if (tab !== 'users') return
    const t = setTimeout(() => api('/admin/users?q=' + encodeURIComponent(uq)).then(r => setUsers(r.users)), 250)
    return () => clearTimeout(t)
  }, [tab, uq])

  const ban = async (u, on) => {
    try {
      await api(`/admin/users/${u.id}/ban`, { body: { on } })
      setUsers(l => l.map(x => x.id === u.id ? { ...x, banned: on } : x))
    } catch (e) { toast(e.message, true) }
  }

  return (
    <Modal title="Админ-панель" onClose={onClose} wide>
      <div className="tabs">
        {[['stats', 'Сводка'], ['users', 'Люди'], ['chats', 'Группы'], ['ai', 'ИИ']].map(([k, t]) => <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{t}</button>)}
      </div>

      {tab === 'stats' && st && <div className="stats">
        {[['Аккаунты', st.users], ['Гости', st.guests], ['Группы', st.groups], ['Сообщения', st.messages], ['В сети', st.online], ['Фраз выучил ИИ', st.samples]].map(([k, v]) =>
          <div key={k} className="stat"><b>{v}</b><small>{k}</small></div>)}
      </div>}

      {tab === 'users' && <>
        <input className="inp sm" placeholder="Поиск по нику, имени, почте" value={uq} onChange={e => setUq(e.target.value)} />
        {users.map(u => <div key={u.id} className="mrow">
          <Ava u={u} size={36} online={u.online} />
          <div><b>{u.name}{u.kind !== 'user' && <span className={'tag' + (u.kind === 'guest' ? ' gst' : u.kind === 'admin' ? ' adm' : '')}>{u.kind}</span>}</b><small>@{u.username}{u.email ? ' · ' + u.email : ''}</small></div>
          {u.kind !== 'admin' && u.kind !== 'bot' && (u.banned
            ? <button className="btn sm ghost" onClick={() => ban(u, false)}>Разбанить</button>
            : <button className="btn sm red-btn" onClick={() => ban(u, true)}>Бан</button>)}
        </div>)}
      </>}

      {tab === 'chats' && chats.map(c => <div key={c.id} className="mrow">
        <Ava u={c} size={36} />
        <div><b>{c.title}</b><small>{c.cnt} чел · {c.msgs} сообщ.{c.settings?.nsfw ? ' · 18+' : ''}</small></div>
        {!c.inside && <button className="btn sm ghost" onClick={async () => {
          const r = await api(`/admin/chats/${c.id}/enter`, { body: {} })
          ctx.d({ t: 'chat', c: r.chat }); ctx.open(c.id); onClose()
        }}>Войти</button>}
        {c.inside && <button className="btn sm ghost" onClick={() => { ctx.open(c.id); onClose() }}>Открыть</button>}
        <button className="ib sm" onClick={async () => {
          if (!confirm(`Удалить группу «${c.title}» со всеми сообщениями?`)) return
          await api('/admin/chats/' + c.id, { method: 'DELETE' })
          setChats(l => l.filter(x => x.id !== c.id))
        }}>🗑</button>
      </div>)}

      {tab === 'ai' && ai && <>
        {!ai.on && <div className="note">ИИ выключен: добавь GROQ_API_KEY в .env и перезапусти сервер</div>}
        <label className="fld">Характер Спека (доп. указания)
          <textarea className="inp" rows={4} maxLength={2000} value={ai.ai.persona || ''} onChange={e => setAi({ ...ai, ai: { ...ai.ai, persona: e.target.value } })} placeholder="Например: любит футбол, подкалывает Шера, иногда вставляет таджикские словечки" />
        </label>
        <label className="fld">Как часто Спек сам влезает в разговор: {Math.round((ai.ai.chance ?? .03) * 100)}%
          <input type="range" min="0" max="0.3" step="0.01" value={ai.ai.chance ?? .03} onChange={e => setAi({ ...ai, ai: { ...ai.ai, chance: +e.target.value } })} />
        </label>
        <button className="btn" onClick={() => api('/admin/ai', { method: 'PUT', body: { persona: ai.ai.persona || '', chance: ai.ai.chance ?? .03 } }).then(() => toast('Сохранено')).catch(e => toast(e.message, true))}>Сохранить</button>
        <div className="card-t" style={{ marginTop: 18 }}>Чему научился (последние фразы)</div>
        <small className="muted">Спек берёт случайные фразы из групп, где он включён, и перенимает манеру. Гостей не запоминает. Лишнее можно удалить.</small>
        {ai.samples.map(s => <div key={s.id} className="sample"><span>{s.text}</span><button className="ib sm" onClick={async () => {
          await api('/admin/ai/samples/' + s.id, { method: 'DELETE' })
          setAi({ ...ai, samples: ai.samples.filter(x => x.id !== s.id) })
        }}>✕</button></div>)}
      </>}
    </Modal>
  )
}
