import { useEffect, useState } from 'react'
import { api } from '../api'
import { Ava, when, preview, toast } from './ui'

export default function Side({ ctx }) {
  const { me, s, open, setDlg, logout, d, live } = ctx
  const [qq, setQ] = useState('')
  const [found, setFound] = useState([])
  const [menu, setMenu] = useState(false)

  useEffect(() => {
    const v = qq.trim()
    if (v.length < 2) return setFound([])
    const t = setTimeout(() => api('/users?q=' + encodeURIComponent(v)).then(r => setFound(r.users)).catch(() => {}), 250)
    return () => clearTimeout(t)
  }, [qq])

  const list = Object.values(s.chats).sort((a, b) => new Date(b.last?.created_at || 0) - new Date(a.last?.created_at || 0))
  const ql = qq.trim().toLowerCase()
  const shown = ql ? list.filter(c => (c.title || c.peer?.name || '').toLowerCase().includes(ql)) : list

  const dm = async u => {
    try {
      const r = await api('/chats/dm', { body: { userId: u.id } })
      d({ t: 'chat', c: r.chat })
      setQ('')
      open(r.chat.id)
    } catch (e) {
      toast(e.message, true)
    }
  }

  const item = (k, fn) => () => { setMenu(false); fn ? fn() : setDlg(k) }

  return (
    <aside className="side">
      <div className="side-top">
        <button className="ib burger" onClick={() => setMenu(!menu)}>☰</button>
        <div className="search">
          <span>🔍</span>
          <input placeholder="Поиск людей и чатов" value={qq} onChange={e => setQ(e.target.value)} />
          {qq && <button className="ib sm" onClick={() => setQ('')}>✕</button>}
        </div>
      </div>

      {menu && <>
        <div className="menu-veil" onClick={() => setMenu(false)} />
        <div className="menu">
          <div className="menu-me" onClick={item('profile')}>
            <Ava u={me} size={52} />
            <div><b>{me.name}</b><small>@{me.username}{me.kind === 'guest' ? ' · гость' : me.kind === 'admin' ? ' · админ' : ''}</small></div>
          </div>
          <button onClick={item('profile')}>👤 Профиль</button>
          {me.kind !== 'guest' && <button onClick={item('group')}>👥 Создать группу</button>}
          {me.kind !== 'guest' && <button onClick={item('packs')}>🎨 Мои стикеры</button>}
          <button onClick={item(null, () => { setQ('spec') })}>👻 Написать Спеку (ИИ)</button>
          {me.kind === 'admin' && <button onClick={item('admin')}>🛡 Админ-панель</button>}
          {me.kind === 'guest' && <button onClick={item('login')}>✨ Зарегистрироваться</button>}
          <button className="red" onClick={item(null, logout)}>🚪 Выйти</button>
        </div>
      </>}

      {!live && <div className="conn">Соединение…</div>}
      {me.kind === 'guest' && <div className="guest-bar" onClick={() => setDlg('login')}>👻 Ты гость, после выхода всё удалится. <u>Зарегистрироваться</u></div>}

      <div className="list">
        {shown.map(c => {
          const t = c.type === 'dm' ? c.peer : c
          const typing = s.typing[c.id]
          return (
            <div key={c.id} className={'row' + (s.active === c.id ? ' on' : '')} onClick={() => open(c.id)}>
              <Ava u={c.type === 'dm' ? c.peer : c} online={c.type === 'dm' && c.peer?.online && c.peer.kind !== 'bot'} />
              <div className="row-mid">
                <div className="row-top">
                  <b>{c.type === 'group' && <span className="gi">👥</span>}{t?.title || t?.name || 'Удалённый'}{t?.kind === 'bot' && <span className="tag">ИИ</span>}</b>
                  <small>{c.last && when(c.last.created_at)}</small>
                </div>
                <div className="row-bot">
                  <span className={typing ? 'typing-t' : ''}>
                    {typing ? `${c.type === 'group' ? typing.name + ' ' : ''}печатает…`
                      : c.last ? <>{c.type === 'group' && c.last.kind !== 'system' && c.last.kind !== 'action' && <em>{c.last.user_id === me.id ? 'Вы' : c.last.name}: </em>}{preview(c.last)}</> : 'Нет сообщений'}
                  </span>
                  {c.unread > 0 && <i className="badge">{c.unread > 99 ? '99+' : c.unread}</i>}
                </div>
              </div>
            </div>
          )
        })}

        {ql.length >= 2 && <>
          <div className="sec">Люди</div>
          {found.length === 0 && <div className="muted pad">Никого не нашли</div>}
          {found.map(u => (
            <div key={'u' + u.id} className="row" onClick={() => dm(u)}>
              <Ava u={u} online={u.online && u.kind !== 'bot'} />
              <div className="row-mid">
                <div className="row-top"><b>{u.name}{u.kind === 'bot' && <span className="tag">ИИ</span>}</b></div>
                <div className="row-bot"><span>@{u.username}</span></div>
              </div>
            </div>
          ))}
        </>}

        {!ql && list.length === 0 && (
          <div className="hello">
            <div className="hello-g">👻</div>
            <b>Тут пока пусто</b>
            <p>Найди друзей по нику через поиск сверху{me.kind !== 'guest' ? ' или создай группу' : ''}.</p>
            {me.kind !== 'guest' && <button className="btn" onClick={() => setDlg('group')}>Создать группу</button>}
            <button className="btn ghost" onClick={() => setQ('spec')}>Поболтать со Спеком</button>
          </div>
        )}
      </div>
    </aside>
  )
}
