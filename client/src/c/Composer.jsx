import { useEffect, useRef, useState } from 'react'
import { api, emit, upload, fileUrl, emojis, emoStickers, acts, hot, extra } from '../api'
import { toast } from './ui'

function Picker({ ctx, chat, onEmoji, onSend, close }) {
  const [tab, setTab] = useState(() => { try { return localStorage.getItem('sp_tab') || 'emoji' } catch { return 'emoji' } })
  const [packs, setPacks] = useState(null)
  const [gq, setGq] = useState('')
  const [gifs, setGifs] = useState(null)
  const [cat, setCat] = useState(0)

  useEffect(() => { try { localStorage.setItem('sp_tab', tab) } catch {} }, [tab])
  useEffect(() => { if (tab === 'st' && !packs) api('/packs').then(r => setPacks(r.packs)).catch(() => setPacks([])) }, [tab])
  useEffect(() => {
    if (tab !== 'gif') return
    const t = setTimeout(() => api('/gifs?q=' + encodeURIComponent(gq)).then(r => setGifs(r.gifs)).catch(() => setGifs([])), gq ? 350 : 0)
    return () => clearTimeout(t)
  }, [tab, gq])

  const ec = Object.keys(emojis)
  const st = chat.settings

  return (
    <div className="picker">
      <div className="pk-tabs">
        <button className={tab === 'emoji' ? 'on' : ''} onClick={() => setTab('emoji')}>Эмодзи</button>
        <button className={tab === 'st' ? 'on' : ''} onClick={() => setTab('st')}>Стикеры</button>
        <button className={tab === 'gif' ? 'on' : ''} onClick={() => setTab('gif')}>GIF</button>
        <button className="ib sm" onClick={close}>✕</button>
      </div>

      {tab === 'emoji' && <>
        <div className="pk-cats">{ec.map((k, i) => <button key={k} className={cat === i ? 'on' : ''} onClick={() => setCat(i)}>{k}</button>)}</div>
        <div className="pk-grid emo">{emojis[ec[cat]].split(' ').map(e => <button key={e} onClick={() => onEmoji(e)}>{e}</button>)}</div>
      </>}

      {tab === 'st' && <div className="pk-scroll">
        {st.stickers === false && <div className="muted pad">Стикеры в этом чате выключены</div>}
        <div className="pk-sec">Specter</div>
        <div className="pk-grid stk">{emoStickers.map(e => <button key={e} className="emo-btn" onClick={() => onSend('sticker', { file: 'e:' + e })}>{e}</button>)}</div>
        {packs?.map(p => <div key={p.id}>
          <div className="pk-sec">{p.title}</div>
          <div className="pk-grid stk">{p.stickers.map(s => <button key={s.id} onClick={() => onSend('sticker', { file: s.file })}><img src={fileUrl(s.file)} alt={s.emoji} loading="lazy" /></button>)}</div>
        </div>)}
        {ctx.me.kind !== 'guest' && <button className="btn sm ghost pk-add" onClick={() => { close(); ctx.setDlg('packs') }}>+ Свои стикеры</button>}
      </div>}

      {tab === 'gif' && <div className="pk-scroll">
        {!ctx.cfg?.gifs ? <div className="muted pad">Гифки не настроены. Админу нужно добавить GIPHY_API_KEY в .env</div> : <>
          <input className="inp sm" placeholder="Поиск GIF" value={gq} onChange={e => setGq(e.target.value)} autoFocus />
          <div className="pk-gifs">
            {gifs?.map(g => <button key={g.id} onClick={() => onSend('gif', { url: g.url, w: g.w, h: g.h })}><img src={g.url} alt="" loading="lazy" /></button>)}
          </div>
          {gifs && !gifs.length && <div className="muted pad">Ничего не нашлось</div>}
        </>}
      </div>}
    </div>
  )
}

export default function Composer({ ctx, chat, reply, setReply, edit, setEdit }) {
  const { me } = ctx
  const [t, setT] = useState('')
  const [pk, setPk] = useState(false)
  const [busy, setBusy] = useState(false)
  const ta = useRef()
  const fi = useRef()
  const lastTyping = useRef(0)

  useEffect(() => {
    if (edit) { setT(edit.body); ta.current?.focus() }
  }, [edit])
  useEffect(() => { if (reply) ta.current?.focus() }, [reply])
  useEffect(() => {
    const el = ta.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [t])

  const nsfw = chat.type === 'group' && chat.settings.nsfw && me.adult && me.kind !== 'guest'
  const cmds = t.startsWith('/') && !t.includes(' ')
    ? [...extra, ...acts.map(([k, e]) => [k, e, 'действие']), ...(nsfw ? hot.map(([k, e]) => [k, e, '18+']) : [])].filter(([k]) => k.startsWith(t.slice(1).toLowerCase())).slice(0, 8)
    : []

  const blocked = chat.type === 'group' && me.kind === 'guest' && !chat.settings.guests

  async function send(kind = 'text', meta) {
    if (busy) return
    if (kind === 'text' && !t.trim()) return
    setBusy(true)
    try {
      if (edit) {
        await emit('edit', { id: edit.id, body: t })
        setEdit(null)
      } else {
        await emit('send', { chatId: chat.id, kind, body: kind === 'text' ? t : '', meta, replyTo: reply?.id })
        setReply(null)
      }
      if (kind === 'text') setT('')
      if (kind !== 'text') setPk(false)
    } catch (e) {
      toast(e.message, true)
    }
    setBusy(false)
    ta.current?.focus()
  }

  async function pic(f) {
    if (!f) return
    if (f.size > 5 * 1024 * 1024) return toast('Файл больше 5 МБ', true)
    setBusy(true)
    try {
      const { id } = await upload(f)
      const dim = await new Promise(ok => {
        const i = new Image()
        i.onload = () => ok({ w: i.naturalWidth, h: i.naturalHeight })
        i.onerror = () => ok({})
        i.src = URL.createObjectURL(f)
      })
      await emit('send', { chatId: chat.id, kind: 'image', body: t, meta: { file: id, ...dim }, replyTo: reply?.id })
      setT('')
      setReply(null)
    } catch (e) {
      toast(e.message, true)
    }
    setBusy(false)
  }

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (cmds.length && t.length > 1 && !cmds.some(c => c[0] === t.slice(1))) return setT('/' + cmds[0][0] + ' ')
      send()
    }
    if (e.key === 'Escape') { setReply(null); setEdit(null); if (edit) setT('') }
  }

  const onChange = e => {
    setT(e.target.value)
    if (Date.now() - lastTyping.current > 2500) {
      lastTyping.current = Date.now()
      emit('typing', { chatId: chat.id }).catch(() => {})
    }
  }

  if (blocked) return <div className="composer locked">Гостям тут писать нельзя. <button className="link" onClick={() => ctx.setDlg('login')}>Зарегистрироваться</button></div>

  return (
    <div className="composer-wrap">
      {pk && <Picker ctx={ctx} chat={chat} close={() => setPk(false)} onSend={send} onEmoji={e => { setT(v => v + e); ta.current?.focus() }} />}
      {cmds.length > 0 && <div className="cmds">
        {cmds.map(([k, e, h]) => <button key={k} onMouseDown={ev => { ev.preventDefault(); setT('/' + k + ' ') }}><i>{e}</i><b>/{k}</b><small>{h}</small></button>)}
      </div>}
      {(reply || edit) && <div className="bar">
        <span className="bar-i">{edit ? '✏️' : '↩'}</span>
        <div><b>{edit ? 'Редактирование' : reply.u?.name}</b><span>{(edit || reply).kind === 'text' ? (edit || reply).body : 'Медиа'}</span></div>
        <button className="ib sm" onClick={() => { setReply(null); if (edit) { setEdit(null); setT('') } }}>✕</button>
      </div>}
      <div className="composer">
        <button className={'ib' + (pk ? ' on' : '')} title="Эмодзи, стикеры, GIF" onClick={() => setPk(!pk)}>😊</button>
        <textarea ref={ta} rows={1} value={t} placeholder="Сообщение… (/help для команд)" maxLength={4000} onChange={onChange} onKeyDown={onKey} />
        {chat.settings.media !== false && !edit && <>
          <button className="ib" title="Фото" onClick={() => fi.current.click()} disabled={busy}>📎</button>
          <input ref={fi} type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden onChange={e => { pic(e.target.files[0]); e.target.value = '' }} />
        </>}
        <button className="send" onClick={() => send()} disabled={busy || !t.trim()}>{edit ? '✓' : '➤'}</button>
      </div>
    </div>
  )
}
