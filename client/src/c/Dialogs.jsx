import { useEffect, useState } from 'react'
import { api, upload, fileUrl } from '../api'
import { Ava, Modal, Tog, toast } from './ui'
import { UserPicker } from './Info'

export function Profile({ ctx, onClose }) {
  const { me, setMe, logout, setDlg } = ctx
  const [f, setF] = useState({ name: me.name, username: me.username, bio: me.bio || '', adult: me.adult })
  const [busy, setBusy] = useState(false)
  const guest = me.kind === 'guest'

  const save = async (extra = {}) => {
    setBusy(true)
    try {
      const body = { name: f.name, bio: f.bio, ...extra }
      if (!guest) { body.username = f.username; body.adult = f.adult }
      const r = await api('/me', { method: 'PATCH', body })
      setMe(r.user)
      if (!Object.keys(extra).length) { toast('Сохранено'); onClose() }
    } catch (e) { toast(e.message, true) }
    setBusy(false)
  }

  const ava = async e => {
    const x = e.target.files[0]
    if (!x) return
    try {
      const { id } = await upload(x)
      await save({ avatar: id })
    } catch (er) { toast(er.message, true) }
  }

  return (
    <Modal title="Профиль" onClose={onClose}>
      <div className="prof-top">
        <label className="ava-up"><Ava u={me} size={88} /><input type="file" accept="image/*" hidden onChange={ava} /><span>сменить</span></label>
        {me.email && <small className="muted">{me.email}</small>}
      </div>
      <label className="fld">Имя<input className="inp" value={f.name} maxLength={40} onChange={e => setF({ ...f, name: e.target.value })} /></label>
      <label className="fld">Ник<input className="inp" value={f.username} disabled={guest} maxLength={24} onChange={e => setF({ ...f, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })} /></label>
      <label className="fld">О себе<textarea className="inp" rows={2} value={f.bio} maxLength={200} onChange={e => setF({ ...f, bio: e.target.value })} /></label>
      {!guest && <Tog label="Мне есть 18 лет" hint="Нужно для 18+ команд в группах, где их включил админ" on={f.adult} set={v => setF({ ...f, adult: v })} />}
      {guest && <div className="note">Ты гость. Чтобы сохранить ник и переписки, <button className="link" onClick={() => setDlg('login')}>зарегистрируйся</button>.</div>}
      <div className="row-btns">
        <button className="btn" disabled={busy} onClick={() => save()}>Сохранить</button>
        <button className="btn ghost red" onClick={logout}>Выйти</button>
      </div>
    </Modal>
  )
}

export function NewGroup({ ctx, onClose }) {
  const [title, setTitle] = useState('')
  const [sel, setSel] = useState([])
  const [busy, setBusy] = useState(false)

  const go = async () => {
    setBusy(true)
    try {
      const r = await api('/chats/group', { body: { title, members: sel.map(u => u.id) } })
      ctx.d({ t: 'chat', c: r.chat })
      ctx.open(r.chat.id)
      onClose()
    } catch (e) { toast(e.message, true) }
    setBusy(false)
  }

  return (
    <Modal title="Новая группа" onClose={onClose}>
      <label className="fld">Название<input className="inp" value={title} maxLength={60} onChange={e => setTitle(e.target.value)} autoFocus placeholder="Например, Пацаны с района" /></label>
      {sel.length > 0 && <div className="chips">{sel.map(u => <span key={u.id} className="chip" onClick={() => setSel(sel.filter(x => x.id !== u.id))}>{u.name} ✕</span>)}</div>}
      <div className="fld">Добавить людей</div>
      <UserPicker skip={sel.map(u => u.id)} onPick={u => setSel([...sel, u])} />
      <small className="muted">Потом можно позвать кого угодно по ссылке-приглашению</small>
      <div className="row-btns"><button className="btn" disabled={busy || !title.trim()} onClick={go}>Создать</button></div>
    </Modal>
  )
}

export function Packs({ onClose }) {
  const [packs, setPacks] = useState(null)
  const [nt, setNt] = useState('')
  const [busy, setBusy] = useState(false)
  const load = () => api('/packs').then(r => setPacks(r.packs)).catch(e => toast(e.message, true))
  useEffect(() => { load() }, [])

  const add = async (p, files) => {
    setBusy(true)
    for (const f of files) {
      try {
        const { id } = await upload(f)
        await api(`/packs/${p.id}/stickers`, { body: { file: id } })
      } catch (e) { toast(e.message, true) }
    }
    setBusy(false)
    load()
  }

  return (
    <Modal title="Мои стикеры" onClose={onClose} wide>
      <div className="newpack">
        <input className="inp sm" placeholder="Название нового пака" value={nt} maxLength={40} onChange={e => setNt(e.target.value)} />
        <button className="btn sm" disabled={!nt.trim()} onClick={async () => {
          try { await api('/packs', { body: { title: nt } }); setNt(''); load() } catch (e) { toast(e.message, true) }
        }}>Создать</button>
      </div>
      <small className="muted">Загружай PNG, WEBP или GIF, лучше квадратные 512×512 с прозрачным фоном. Импорт паков прямо из Телеграма появится вместе с мостом.</small>
      {busy && <div className="spin" />}
      {packs?.map(p => (
        <div key={p.id} className="pack">
          <div className="pack-h">
            <b>{p.title}</b>
            {p.mine
              ? <label className="btn sm ghost">+ Стикеры<input type="file" multiple accept="image/png,image/webp,image/gif" hidden onChange={e => { add(p, [...e.target.files]); e.target.value = '' }} /></label>
              : <span className="tag">сохранён</span>}
            <button className="ib sm" title="Удалить пак" onClick={async () => { if (confirm('Удалить пак?')) { await api('/packs/' + p.id, { method: 'DELETE' }); load() } }}>🗑</button>
          </div>
          <div className="pk-grid stk">
            {p.stickers.map(s => <div key={s.id} className="pk-it">
              <img src={fileUrl(s.file)} alt="" />
              {p.mine && <button className="x" onClick={async () => { await api(`/packs/${p.id}/stickers/${s.id}`, { method: 'DELETE' }); load() }}>✕</button>}
            </div>)}
            {!p.stickers.length && <div className="muted pad">Пусто</div>}
          </div>
        </div>
      ))}
      {packs && !packs.length && <div className="muted pad">Паков пока нет, создай первый</div>}
    </Modal>
  )
}
