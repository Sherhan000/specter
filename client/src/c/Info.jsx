import { useEffect, useState } from 'react'
import { api, upload } from '../api'
import { Ava, Tog, toast, seen } from './ui'

function Picker({ onPick, skip }) {
  const [qq, setQ] = useState('')
  const [l, setL] = useState([])
  useEffect(() => {
    if (qq.trim().length < 2) return setL([])
    const t = setTimeout(() => api('/users?q=' + encodeURIComponent(qq.trim())).then(r => setL(r.users.filter(u => u.kind !== 'bot' && !skip.includes(u.id)))), 250)
    return () => clearTimeout(t)
  }, [qq])
  return <>
    <input className="inp sm" placeholder="Ник или имя" value={qq} onChange={e => setQ(e.target.value)} autoFocus />
    {l.map(u => <div key={u.id} className="mrow" onClick={() => { onPick(u); setQ('') }}><Ava u={u} size={36} /><div><b>{u.name}</b><small>@{u.username}</small></div><span className="plus">+</span></div>)}
  </>
}

export { Picker as UserPicker }

export default function Info({ ctx, chat, close }) {
  const { me, d } = ctx
  const [c, setC] = useState(null)
  const [adding, setAdding] = useState(false)
  const [title, setTitle] = useState('')
  const [um, setUm] = useState(null)
  const adm = me.kind === 'admin'
  const own = adm || chat.owner_id === me.id
  const group = chat.type === 'group'

  const load = () => api('/chats/' + chat.id).then(r => { setC(r.chat); setTitle(r.chat.title || '') }).catch(e => toast(e.message, true))
  useEffect(() => { load() }, [chat.id, chat.cnt, chat.title, JSON.stringify(chat.settings)])

  const set = async (k, v) => {
    try {
      const r = await api(`/chats/${chat.id}/settings`, { method: 'PATCH', body: { [k]: v } })
      setC(x => ({ ...x, settings: r.settings }))
    } catch (e) { toast(e.message, true) }
  }

  const call = async (p, o, ok) => {
    try {
      await api(p, o)
      if (ok) toast(ok)
      load()
    } catch (e) { toast(e.message, true) }
  }

  const link = c?.invite && `${location.origin}/join/${c.invite}`

  if (!c) return <aside className="info"><div className="spin" /></aside>

  const peer = !group && c.members.find(m => m.id !== me.id)

  return (
    <aside className="info">
      <div className="info-h"><b>{group ? 'Группа' : 'Профиль'}</b><button className="ib" onClick={close}>✕</button></div>
      <div className="info-top">
        <label className={own && group ? 'ava-up' : ''}>
          <Ava u={group ? c : peer} size={96} />
          {own && group && <input type="file" accept="image/*" hidden onChange={async e => {
            const f = e.target.files[0]
            if (!f) return
            try { const { id } = await upload(f); await call(`/chats/${chat.id}`, { method: 'PATCH', body: { avatar: id } }) } catch (er) { toast(er.message, true) }
          }} />}
        </label>
        {group && own
          ? <input className="inp title-inp" value={title} maxLength={60} onChange={e => setTitle(e.target.value)} onBlur={() => title.trim() && title !== c.title && call(`/chats/${chat.id}`, { method: 'PATCH', body: { title } }, 'Название обновлено')} />
          : <h3>{group ? c.title : peer?.name}</h3>}
        <small className="muted">{group ? `${c.members.length} участников` : peer ? '@' + peer.username + ' · ' + seen(peer) : ''}</small>
        {peer?.bio && <p className="bio">{peer.bio}</p>}
      </div>

      {link && <div className="card">
        <div className="card-t">Ссылка-приглашение</div>
        <div className="invite" onClick={() => { navigator.clipboard?.writeText(link); toast('Ссылка скопирована') }}>{link}</div>
        <small className="muted">Кто перейдёт без аккаунта, зайдёт гостем и сразу сможет писать</small>
        <button className="link" onClick={() => call(`/chats/${chat.id}/invite`, { body: {} }, 'Старая ссылка больше не работает')}>Сбросить ссылку</button>
      </div>}

      {group && adm && <div className="card">
        <div className="card-t">Разрешения <span className="tag adm">только админ</span></div>
        <Tog label="Гости могут писать" on={c.settings.guests} set={v => set('guests', v)} />
        <Tog label="Участники добавляют людей" on={c.settings.add} set={v => set('add', v)} />
        <Tog label="Фото" on={c.settings.media} set={v => set('media', v)} />
        <Tog label="Стикеры" on={c.settings.stickers} set={v => set('stickers', v)} />
        <Tog label="GIF" on={c.settings.gifs} set={v => set('gifs', v)} />
        <Tog label="ИИ Спек в чате" on={c.settings.ai} set={v => set('ai', v)} />
        <Tog label="18+ команды" hint="Только для тех, кто подтвердил возраст, гостям недоступно" on={c.settings.nsfw} set={v => set('nsfw', v)} />
        <label className="slow">Медленный режим
          <select value={c.settings.slow} onChange={e => set('slow', +e.target.value)}>
            {[0, 5, 10, 30, 60, 300, 900].map(v => <option key={v} value={v}>{v ? (v < 60 ? v + ' сек' : v / 60 + ' мин') : 'выкл'}</option>)}
          </select>
        </label>
      </div>}

      {group && <div className="card">
        <div className="card-t">Участники {(own || (c.settings.add && me.kind !== 'guest')) && <button className="link" onClick={() => setAdding(!adding)}>{adding ? 'Готово' : '+ Добавить'}</button>}</div>
        {adding && <Picker skip={c.members.map(m => m.id)} onPick={u => call(`/chats/${chat.id}/members`, { body: { userIds: [u.id] } }, u.name + ' добавлен(а)')} />}
        {c.members.map(m => (
          <div key={m.id} className="mrow" onClick={() => adm && m.id !== me.id && m.kind !== 'admin' && setUm(um === m.id ? null : m.id)}>
            <Ava u={m} size={36} online={m.online && m.kind !== 'bot'} />
            <div>
              <b>{m.name}{m.kind === 'guest' && <span className="tag gst">гость</span>}{m.kind === 'admin' && <span className="tag adm">админ</span>}{m.role === 'owner' && <span className="tag">создатель</span>}</b>
              <small>{m.online ? 'в сети' : '@' + m.username}{m.muted_until && new Date(m.muted_until) > new Date() ? ' · в муте' : ''}</small>
            </div>
            {um === m.id && <div className="mact" onClick={e => e.stopPropagation()}>
              <button onClick={() => call(`/chats/${chat.id}/mute/${m.id}`, { body: { minutes: 60 } }, 'Мут на час')}>🔇 Мут 1ч</button>
              <button onClick={() => call(`/chats/${chat.id}/mute/${m.id}`, { body: { minutes: 0 } }, 'Мут снят')}>🔊 Снять мут</button>
              <button onClick={() => call(`/chats/${chat.id}/members/${m.id}`, { method: 'DELETE' }, 'Выгнан(а)')}>👢 Выгнать</button>
              <button className="red" onClick={() => call(`/chats/${chat.id}/ban/${m.id}`, { body: { on: true } }, 'Забанен(а)')}>⛔ Бан</button>
            </div>}
          </div>
        ))}
      </div>}

      <div className="card">
        {group
          ? <button className="btn wide red-btn" onClick={async () => {
            if (!confirm('Выйти из группы?')) return
            await api(`/chats/${chat.id}/members/${me.id}`, { method: 'DELETE' }).catch(e => toast(e.message, true))
            d({ t: 'unchat', id: chat.id })
          }}>Выйти из группы</button>
          : <button className="btn wide red-btn" onClick={async () => {
            if (!confirm('Удалить чат у обоих?')) return
            await api(`/chats/${chat.id}/members/${me.id}`, { method: 'DELETE' }).catch(e => toast(e.message, true))
            d({ t: 'unchat', id: chat.id })
          }}>Удалить чат</button>}
      </div>
    </aside>
  )
}
