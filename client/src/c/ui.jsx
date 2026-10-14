import { useEffect, useState } from 'react'
import { fileUrl } from '../api'

const grads = [
  ['#ff6b8b', '#ff9a5a'], ['#7c6bff', '#b48bff'], ['#3ecf8e', '#1fa2a2'], ['#4fb5ff', '#5a6bff'],
  ['#ffb347', '#ff6f61'], ['#e86bff', '#8b5aff'], ['#5ee7df', '#3a8dff']
]

export function Ava({ u, size = 46, online }) {
  const n = (u?.title || u?.name || '?').trim()
  const g = grads[Math.abs(u?.id || 0) % grads.length]
  const ini = n.split(/\s+/).slice(0, 2).map(w => [...w][0]).join('').toUpperCase()
  return (
    <div className="ava" style={{ width: size, height: size, fontSize: size * .38 }}>
      {u?.avatar
        ? <img src={fileUrl(u.avatar)} alt="" />
        : u?.kind === 'bot'
          ? <div className="ava-in bot">👻</div>
          : <div className="ava-in" style={{ background: `linear-gradient(135deg,${g[0]},${g[1]})` }}>{ini}</div>}
      {online && <i className="dot" />}
    </div>
  )
}

export function Modal({ title, onClose, children, wide }) {
  useEffect(() => {
    const k = e => e.key === 'Escape' && onClose()
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  }, [onClose])
  return (
    <div className="veil" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className={'modal' + (wide ? ' wide' : '')}>
        <div className="modal-h">
          <b>{title}</b>
          <button className="ib" onClick={onClose}>✕</button>
        </div>
        <div className="modal-b">{children}</div>
      </div>
    </div>
  )
}

export function Tog({ on, set, label, hint, dis }) {
  return (
    <label className={'tog' + (dis ? ' dis' : '')}>
      <span><b>{label}</b>{hint && <small>{hint}</small>}</span>
      <input type="checkbox" checked={!!on} disabled={dis} onChange={e => set(e.target.checked)} />
      <i />
    </label>
  )
}

let push
export const toast = (t, bad) => push?.({ t, bad, id: Math.random() })

export function Toasts() {
  const [l, setL] = useState([])
  push = x => {
    setL(v => [...v, x])
    setTimeout(() => setL(v => v.filter(y => y.id !== x.id)), 3200)
  }
  return <div className="toasts">{l.map(x => <div key={x.id} className={'toast' + (x.bad ? ' bad' : '')}>{x.t}</div>)}</div>
}

export const when = d => {
  const t = new Date(d), n = new Date()
  if (t.toDateString() === n.toDateString()) return t.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
  if (n - t < 6 * 864e5) return t.toLocaleDateString('ru', { weekday: 'short' })
  return t.toLocaleDateString('ru', { day: '2-digit', month: '2-digit' })
}

export const seen = (p) => {
  if (!p) return ''
  if (p.kind === 'bot') return 'ИИ, всегда на связи'
  if (p.online) return 'в сети'
  if (!p.last_seen) return 'был(а) недавно'
  const m = (Date.now() - new Date(p.last_seen)) / 60e3
  if (m < 2) return 'был(а) только что'
  if (m < 60) return `был(а) ${Math.round(m)} мин назад`
  if (m < 1440) return `был(а) в ${new Date(p.last_seen).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })}`
  return 'был(а) ' + new Date(p.last_seen).toLocaleDateString('ru', { day: 'numeric', month: 'long' })
}

export const preview = m => {
  if (!m) return ''
  if (m.kind === 'sticker') return 'Стикер'
  if (m.kind === 'gif') return 'GIF'
  if (m.kind === 'image') return '🖼 Фото' + (m.body ? ', ' + m.body : '')
  return m.body
}
