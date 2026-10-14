import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api, emit, fileUrl, reacts, acts, hot } from '../api'
import { Ava, seen, toast } from './ui'
import Msg from './Msg'
import Composer from './Composer'
import Info from './Info'

const day = d => {
  const t = new Date(d), n = new Date()
  if (t.toDateString() === n.toDateString()) return 'Сегодня'
  if (new Date(n - 864e5).toDateString() === t.toDateString()) return 'Вчера'
  return t.toLocaleDateString('ru', { day: 'numeric', month: 'long', year: t.getFullYear() !== n.getFullYear() ? 'numeric' : undefined })
}

export default function Chat({ ctx, chat }) {
  const { me, s, d } = ctx
  const msgs = s.msgs[chat.id]
  const box = useRef()
  const stick = useRef(true)
  const prevH = useRef(0)
  const lastRead = useRef(0)
  const [reply, setReply] = useState(null)
  const [edit, setEdit] = useState(null)
  const [menu, setMenu] = useState(null)
  const [info, setInfo] = useState(false)
  const [img, setImg] = useState(null)
  const [loading, setLoading] = useState(false)
  const group = chat.type === 'group'
  const peer = chat.peer
  const typing = s.typing[chat.id]

  useLayoutEffect(() => {
    const b = box.current
    if (!b || !msgs) return
    if (prevH.current && loading === 'done') {
      b.scrollTop = b.scrollHeight - prevH.current
      setLoading(false)
    } else if (stick.current || msgs[msgs.length - 1]?.user_id === me.id) b.scrollTop = b.scrollHeight
    prevH.current = 0
  }, [msgs])

  useEffect(() => {
    if (!msgs?.length) return
    const l = [...msgs].reverse().find(m => typeof m.id === 'number')
    if (l && l.id > lastRead.current && document.visibilityState === 'visible') {
      lastRead.current = l.id
      emit('read', { chatId: chat.id, id: l.id }).catch(() => {})
    }
  }, [msgs])

  const onScroll = async () => {
    const b = box.current
    stick.current = b.scrollHeight - b.scrollTop - b.clientHeight < 120
    if (b.scrollTop < 80 && s.more[chat.id] && !loading && msgs?.length) {
      setLoading(true)
      prevH.current = b.scrollHeight
      try {
        const r = await api(`/chats/${chat.id}/messages?before=${msgs.find(m => typeof m.id === 'number')?.id}`)
        setLoading('done')
        d({ t: 'hist', id: chat.id, l: r.messages, before: true })
      } catch {
        setLoading(false)
      }
    }
  }

  const openMenu = (e, m, click) => {
    if (click && (window.getSelection()?.toString() || e.target.closest('a'))) return
    e.preventDefault()
    if (m.meta?.eph || typeof m.id !== 'number') return
    const x = Math.min(e.clientX, innerWidth - 250), y = Math.min(e.clientY, innerHeight - 380)
    setMenu({ m, x: Math.max(8, x), y: Math.max(8, y), acts: false })
  }

  const react = (m, e) => emit('react', { id: m.id, e }).catch(er => toast(er.message, true))
  const jump = id => {
    const el = box.current.querySelector(`[data-id="${id}"]`)
    if (el) {
      el.scrollIntoView({ block: 'center', behavior: 'smooth' })
      el.classList.add('flash')
      setTimeout(() => el.classList.remove('flash'), 1200)
    }
  }

  const doAct = async (cmd, m) => {
    setMenu(null)
    try {
      await emit('send', { chatId: chat.id, kind: 'text', body: '/' + cmd + (m.u?.username ? ' @' + m.u.username : ''), replyTo: m.id })
    } catch (e) { toast(e.message, true) }
  }

  const nsfw = group && chat.settings.nsfw && me.adult && me.kind !== 'guest'
  const sub = typing ? `${group ? typing.name + ' ' : ''}печатает…` : group ? `${chat.cnt || 0} участник${chat.cnt % 10 === 1 && chat.cnt % 100 !== 11 ? '' : [2, 3, 4].includes(chat.cnt % 10) && ![12, 13, 14].includes(chat.cnt % 100) ? 'а' : 'ов'}` : seen(peer)

  let prevDay = ''
  const rows = []
  msgs?.forEach((m, i) => {
    const dd = day(m.created_at)
    if (dd !== prevDay) { rows.push(<div key={'d' + m.id} className="day"><span>{dd}</span></div>); prevDay = dd }
    const p = msgs[i - 1], n = msgs[i + 1]
    const plain = x => x && x.kind !== 'system' && x.kind !== 'action'
    const first = !plain(p) || p.user_id !== m.user_id || day(p.created_at) !== dd
    const last = !plain(n) || n.user_id !== m.user_id || day(n.created_at) !== dd
    rows.push(<div key={m.id} data-id={m.id} className="mw">
      <Msg m={m} me={me} group={group} first={first} last={last}
        read={!group && peer?.kind !== 'bot' && m.user_id === me.id ? (peer?.read || 0) >= m.id : undefined}
        onMenu={openMenu} onReact={react} onReplyClick={jump} onImg={setImg} />
    </div>)
  })

  const mm = menu?.m
  const canDel = mm && (mm.user_id === me.id || me.kind === 'admin')

  return (
    <section className="chat">
      <header className="chat-h">
        <button className="ib back" onClick={() => d({ t: 'close' })}>←</button>
        <div className="chat-h-who" onClick={() => setInfo(!info)}>
          <Ava u={group ? chat : peer} size={40} />
          <div>
            <b>{group ? chat.title : peer?.name || 'Удалённый'}{peer?.kind === 'bot' && <span className="tag">ИИ</span>}</b>
            <small className={typing ? 'typing-t' : peer?.online ? 'on' : ''}>{sub}</small>
          </div>
        </div>
        <button className="ib" onClick={() => setInfo(!info)}>ⓘ</button>
      </header>

      <div className="chat-body">
        <div className="msgs" ref={box} onScroll={onScroll}>
          {loading === true && <div className="spin" />}
          {!msgs && <div className="spin" />}
          {msgs && !msgs.length && <div className="first-hi">
            <div className="emo-st">{peer?.kind === 'bot' ? '👻' : '👋'}</div>
            <p>{peer?.kind === 'bot' ? 'Спек на связи. Пиши что угодно.' : 'Сообщений пока нет. Напиши первым!'}</p>
          </div>}
          {rows}
          {typing && <div className="typing-bub"><i /><i /><i /></div>}
        </div>
        <Composer ctx={ctx} chat={chat} reply={reply} setReply={setReply} edit={edit} setEdit={setEdit} />
      </div>

      {info && <Info ctx={ctx} chat={chat} close={() => setInfo(false)} />}

      {menu && <>
        <div className="menu-veil" onClick={() => setMenu(null)} onContextMenu={e => { e.preventDefault(); setMenu(null) }} />
        <div className="ctx" style={{ left: menu.x, top: menu.y }}>
          {!menu.acts ? <>
            {mm.kind !== 'system' && <div className="ctx-re">{reacts.map(e => <button key={e} onClick={() => { react(mm, e); setMenu(null) }}>{e}</button>)}</div>}
            <button onClick={() => { setReply(mm); setEdit(null); setMenu(null) }}>↩ Ответить</button>
            {mm.user_id !== me.id && mm.kind !== 'system' && <button onClick={() => setMenu({ ...menu, acts: true })}>🎭 Действие ›</button>}
            {mm.kind === 'text' && <button onClick={() => { navigator.clipboard?.writeText(mm.body); setMenu(null); toast('Скопировано') }}>📋 Копировать</button>}
            {mm.kind === 'text' && mm.user_id === me.id && <button onClick={() => { setEdit(mm); setReply(null); setMenu(null) }}>✏️ Изменить</button>}
            {mm.kind === 'sticker' && !mm.meta.file.startsWith('e:') && me.kind !== 'guest' && <button onClick={() => { api(`/stickers/${mm.meta.file}/save`, { body: {} }).then(() => toast('Пак добавлен в твои стикеры')).catch(e => toast(e.message, true)); setMenu(null) }}>➕ Добавить пак</button>}
            {canDel && <button className="red" onClick={() => { emit('del', { id: mm.id }).catch(e => toast(e.message, true)); setMenu(null) }}>🗑 Удалить</button>}
          </> : <>
            <button onClick={() => setMenu({ ...menu, acts: false })}>‹ Назад</button>
            <div className="ctx-acts">
              {acts.map(([k, e]) => <button key={k} onClick={() => doAct(k, mm)}><i>{e}</i>{k}</button>)}
              {nsfw && hot.map(([k, e]) => <button key={k} className="hot" onClick={() => doAct(k, mm)}><i>{e}</i>{k}</button>)}
            </div>
          </>}
        </div>
      </>}

      {img && <div className="veil lightbox" onClick={() => setImg(null)}><img src={fileUrl(img)} alt="" /></div>}
    </section>
  )
}
