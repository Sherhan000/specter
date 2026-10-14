import { fileUrl } from '../api'
import { Ava } from './ui'

const rx = /(https?:\/\/[^\s<]+[^\s<.,:;"')\]!?])|(@[a-z0-9_]{3,32})/gi

export function Txt({ t }) {
  const out = []
  let i = 0, m
  rx.lastIndex = 0
  while ((m = rx.exec(t))) {
    if (m.index > i) out.push(t.slice(i, m.index))
    if (m[1]) out.push(<a key={m.index} href={m[1]} target="_blank" rel="noopener noreferrer nofollow">{m[1]}</a>)
    else out.push(<b key={m.index} className="mention">{m[2]}</b>)
    i = m.index + m[0].length
  }
  if (i < t.length) out.push(t.slice(i))
  return out
}

const hm = d => new Date(d).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })

export default function Msg({ m, me, group, first, last, read, onMenu, onReact, onReplyClick, onImg }) {
  if (m.kind === 'system') return <div className={'sys' + (m.meta?.eph ? ' eph' : '')}><span>{m.body}</span></div>
  if (m.kind === 'action') return (
    <div className="act" onContextMenu={e => onMenu(e, m)}>
      <span><i>{m.meta?.e}</i>{m.body}</span>
    </div>
  )

  const mine = m.user_id === me.id
  const bare = m.kind === 'sticker' || m.kind === 'gif'
  const r = m.meta?.r || {}
  const rk = Object.keys(r)

  return (
    <div className={'m' + (mine ? ' mine' : '') + (last ? ' last' : '') + (first ? ' first' : '')}>
      {group && !mine && <div className="m-ava">{last && <Ava u={m.u} size={34} />}</div>}
      <div className="m-col">
      <div className={'bub' + (bare ? ' bare' : '') + (m.kind === 'image' ? ' pic' : '')} onContextMenu={e => onMenu(e, m)} onClick={e => onMenu(e, m, true)}>
        {group && !mine && first && !bare && <div className="m-name" style={{ color: `hsl(${(m.user_id * 67) % 360},75%,70%)` }}>{m.u?.name}{m.u?.kind === 'bot' && <span className="tag">ИИ</span>}{m.u?.kind === 'admin' && <span className="tag adm">админ</span>}</div>}
        {m.reply && <div className="m-reply" onClick={e => { e.stopPropagation(); onReplyClick(m.reply.id) }}><b>{m.reply.name}</b><span>{m.reply.kind === 'text' ? m.reply.body : m.reply.kind === 'sticker' ? 'Стикер' : m.reply.kind === 'gif' ? 'GIF' : m.reply.kind === 'image' ? 'Фото' : m.reply.body}</span></div>}
        {m.kind === 'text' && <div className="m-text"><Txt t={m.body} /></div>}
        {m.kind === 'sticker' && (m.meta.file.startsWith('e:')
          ? <div className="emo-st">{m.meta.file.slice(2)}</div>
          : <img className="st" src={fileUrl(m.meta.file)} alt="стикер" loading="lazy" />)}
        {m.kind === 'gif' && <img className="gif" src={m.meta.url} alt="gif" loading="lazy" style={m.meta.w ? { aspectRatio: m.meta.w + '/' + m.meta.h } : null} />}
        {m.kind === 'image' && <>
          <img className="img" src={fileUrl(m.meta.file)} alt="" loading="lazy" onClick={e => { e.stopPropagation(); onImg(m.meta.file) }} />
          {m.body && <div className="m-text"><Txt t={m.body} /></div>}
        </>}
        <span className="m-meta">
          {m.edited && 'изм. '}{hm(m.created_at)}
          {mine && read !== undefined && <i className={'tick' + (read ? ' rd' : '')}>{read ? '✓✓' : '✓'}</i>}
        </span>
      </div>
      {rk.length > 0 && <div className="reacts">
        {rk.map(e => <button key={e} className={'rc' + (r[e].includes(me.id) ? ' on' : '')} onClick={() => onReact(m, e)}>{e} {r[e].length}</button>)}
      </div>}
      </div>
    </div>
  )
}
