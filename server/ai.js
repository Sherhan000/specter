import { q, getKv } from './db.js'

const KEY = process.env.GROQ_API_KEY
let models = [...new Set([process.env.GROQ_MODEL, 'llama-3.3-70b-versatile', 'openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'llama-3.1-8b-instant'].filter(Boolean))]
export const aiOn = !!KEY

const base = `Ты Спек, участник чата Specter. Общаешься как живой человек: коротко, по-разговорному, с юмором и подколками, но без злобы и оскорблений.
Пишешь на языке собеседника (чаще русский, бывает таджикский или английский), можешь вставить сленг и эмодзи, но без перебора.
Не пиши длинные лекции, обычно 1-3 предложения. Не начинай с приветствия каждый раз. Не используй длинное тире.
Если кто-то всерьёз спрашивает, бот ли ты, не ври: ты ИИ Спек, просто с характером.
Не помогай с опасными вещами, не пиши откровенный сексуальный контент, не раскрывай личные данные людей.`

export async function maybeLearn(text) {
  if (!text || text.length < 8 || text.length > 220 || text.startsWith('/') || /https?:\/\/|@\w+\.\w+|\d{6,}/.test(text)) return
  if (Math.random() > 0.2) return
  await q('insert into ai_samples(text) values($1)', [text])
  await q('delete from ai_samples where id not in (select id from ai_samples order by id desc limit 600)')
}

export async function reply(chatId, botId) {
  if (!KEY) return null
  const cfg = await getKv('ai', {})
  const hist = await q(`select m.body, m.kind, m.user_id, u.name from messages m join users u on u.id=m.user_id
    where m.chat_id=$1 and m.kind in ('text','action') order by m.id desc limit 30`, [chatId])
  const style = await q('select text from ai_samples order by random() limit 14')
  const sys = [base,
    cfg.persona ? 'Доп. указания от админа: ' + cfg.persona : '',
    style.length ? 'Так пишут люди в этом чате, перенимай манеру и словечки (не повторяй дословно):\n' + style.map(s => '- ' + s.text).join('\n') : ''
  ].filter(Boolean).join('\n\n')
  const msgs = [{ role: 'system', content: sys }]
  for (const m of hist.reverse()) {
    if (m.user_id === botId) msgs.push({ role: 'assistant', content: m.body })
    else msgs.push({ role: 'user', content: `${m.name}: ${m.body}`.slice(0, 1500) })
  }
  try {
    let r
    while (models.length) {
      const model = models[0]
      const body = { model, messages: msgs, temperature: 0.95, max_tokens: 400 }
      if (model.startsWith('openai/')) body.reasoning_effort = 'low'
      r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + KEY },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(25000)
      })
      if (r.ok) break
      const txt = (await r.text()).slice(0, 200)
      console.error('groq', model, r.status, txt)
      if ((r.status === 404 || r.status === 403 || /model/i.test(txt)) && models.length > 1) models.shift()
      else return null
    }
    const j = await r.json()
    let t = j.choices?.[0]?.message?.content?.trim()
    if (!t) return null
    t = t.replace(/^Спек:\s*/i, '').replace(/—/g, '-')
    return t.slice(0, 2000)
  } catch (e) {
    console.error('groq', e.message)
    return null
  }
}
