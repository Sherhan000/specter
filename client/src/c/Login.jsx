import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function Login({ cfg, onUser, upgrade, onClose }) {
  const [mode, setMode] = useState('main')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [lg, setLg] = useState('')
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const gb = useRef()

  useEffect(() => {
    if (!cfg?.google || mode !== 'main') return
    const go = () => {
      const g = window.google?.accounts?.id
      if (!g || !gb.current) return
      g.initialize({
        client_id: cfg.google,
        callback: r => run(() => api('/auth/google', { body: { credential: r.credential } }))
      })
      g.renderButton(gb.current, { theme: 'filled_black', size: 'large', shape: 'pill', text: 'continue_with', locale: 'ru', width: 300 })
    }
    if (window.google?.accounts) return go()
    let s = document.querySelector('script[data-gsi]')
    if (!s) {
      s = document.createElement('script')
      s.src = 'https://accounts.google.com/gsi/client'
      s.async = true
      s.dataset.gsi = 1
      document.head.appendChild(s)
    }
    s.addEventListener('load', go)
    return () => s.removeEventListener('load', go)
  }, [cfg, mode])

  async function run(fn, next) {
    setErr('')
    setBusy(true)
    try {
      const r = await fn()
      if (next) next(r)
      else if (r?.user) onUser(r.user)
    } catch (e) {
      setErr(e.message)
    }
    setBusy(false)
  }

  const sub = f => e => { e.preventDefault(); f() }

  return (
    <div className="login">
      <div className="aurora" />
      <div className="login-card">
        {onClose && <button className="ib close" onClick={onClose}>✕</button>}
        <img src="/ghost.svg" className="login-logo" alt="" />
        <h1>Specter</h1>
        <p className="muted">{upgrade ? 'Зарегистрируйся, чтобы переписки не пропали' : 'Общайся с друзьями, создавай группы, кидай стикеры. Тут весело.'}</p>

        {mode === 'main' && <>
          {cfg?.google ? <div className="gbtn" ref={gb} /> : null}
          {cfg?.email && <button className="btn wide" onClick={() => setMode('email')}>✉️ Войти по почте</button>}
          {!upgrade && <button className="btn wide ghost" disabled={busy} onClick={() => setMode('guest')}>👻 Зайти как гость</button>}
          {!upgrade && <small className="muted center">Гость ничего не сохраняет: после выхода всё удаляется</small>}
          {!upgrade && <button className="link" onClick={() => setMode('admin')}>Вход для админа</button>}
        </>}

        {mode === 'email' && <form onSubmit={sub(() => run(() => api('/auth/email/send', { body: { email } }), () => setMode('code')))}>
          <input className="inp" type="email" placeholder="твоя@почта.com" value={email} onChange={e => setEmail(e.target.value)} autoFocus required />
          <button className="btn wide" disabled={busy}>Прислать код</button>
          <button type="button" className="link" onClick={() => setMode('main')}>Назад</button>
        </form>}

        {mode === 'code' && <form onSubmit={sub(() => run(() => api('/auth/email/verify', { body: { email, code } })))}>
          <p className="muted">Отправили 6 цифр на <b>{email}</b></p>
          <input className="inp code" inputMode="numeric" maxLength={6} placeholder="••••••" value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))} autoFocus />
          <button className="btn wide" disabled={busy || code.length !== 6}>Войти</button>
          <button type="button" className="link" onClick={() => setMode('email')}>Другая почта</button>
        </form>}

        {mode === 'guest' && <form onSubmit={sub(() => run(() => api('/auth/guest', { body: { name } })))}>
          <input className="inp" placeholder="Как тебя звать? (можно пусто)" maxLength={30} value={name} onChange={e => setName(e.target.value)} autoFocus />
          <button className="btn wide" disabled={busy}>Зайти</button>
          <button type="button" className="link" onClick={() => setMode('main')}>Назад</button>
        </form>}

        {mode === 'admin' && <form onSubmit={sub(() => run(() => api('/auth/admin', { body: { login: lg, password: pw } })))}>
          <input className="inp" placeholder="Логин" autoComplete="username" value={lg} onChange={e => setLg(e.target.value)} autoFocus />
          <input className="inp" type="password" placeholder="Пароль" autoComplete="current-password" value={pw} onChange={e => setPw(e.target.value)} />
          <button className="btn wide" disabled={busy}>Войти</button>
          <button type="button" className="link" onClick={() => setMode('main')}>Назад</button>
        </form>}

        {err && <div className="err">{err}</div>}
      </div>
    </div>
  )
}
