import { io } from 'socket.io-client'

export async function api(p, { method, body, form } = {}) {
  const r = await fetch('/api' + p, {
    method: method || (body || form ? 'POST' : 'GET'),
    credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: form || (body && JSON.stringify(body))
  })
  const j = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(j.error || 'Что-то пошло не так')
  return j
}

export const upload = f => {
  const fd = new FormData()
  fd.append('file', f)
  return api('/files', { form: fd })
}

export const sock = io({ autoConnect: false, withCredentials: true })

export const emit = (ev, d) => new Promise((ok, no) => {
  sock.timeout(15000).emit(ev, d, (err, r) => {
    if (err) return no(new Error('Нет связи с сервером'))
    if (r?.error) return no(new Error(r.error))
    ok(r?.data)
  })
})

export const fileUrl = id => '/f/' + id

export const acts = [
  ['пнуть', '👟'], ['ударить', '👊'], ['поцеловать', '💋'], ['обнять', '🤗'], ['щекотать', '🤭'], ['погладить', '🫳'],
  ['укусить', '🦷'], ['шлёпнуть', '🖐'], ['ущипнуть', '🤏'], ['тапок', '🩴'], ['пять', '✋'], ['подмигнуть', '😉'],
  ['накормить', '🍕'], ['чай', '☕'], ['похвалить', '🏆'], ['испугать', '👻'], ['взгляд', '😒']
]
export const hot = [
  ['соблазнить', '😏'], ['страстно', '🔥'], ['стена', '🧱'], ['раздеть', '👀'], ['попа', '🍑'], ['спальня', '🚪'], ['ошейник', '⛓'], ['массаж', '💆']
]
export const extra = [['help', '❓', 'все команды'], ['кубик', '🎲', 'бросить кубик'], ['монетка', '🪙', 'орёл или решка'], ['шар', '🎱', 'шар судьбы'], ['спек', '🤖', 'спросить ИИ']]

export const reacts = ['👍', '❤️', '😂', '😮', '😢', '🔥', '👏', '💀', '🤡', '👻']

export const emojis = {
  'Смайлы': '😀 😃 😄 😁 😆 😅 🤣 😂 🙂 🙃 😉 😊 😇 🥰 😍 🤩 😘 😗 😚 😋 😛 😜 🤪 😝 🤑 🤗 🤭 🫢 🤫 🤔 🫡 🤐 🤨 😐 😑 😶 🫥 😏 😒 🙄 😬 😮‍💨 🤥 😌 😔 😪 🤤 😴 😷 🤒 🤕 🤢 🤮 🥵 🥶 🥴 😵 🤯 🤠 🥳 🥸 😎 🤓 🧐 😕 🫤 😟 🙁 😮 😯 😲 😳 🥺 🥹 😦 😧 😨 😰 😥 😢 😭 😱 😖 😣 😞 😓 😩 😫 🥱 😤 😡 😠 🤬 😈 👿 💀 ☠️ 💩 🤡 👹 👺 👻 👽 👾 🤖',
  'Жесты': '👋 🤚 🖐 ✋ 🖖 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉 👆 👇 ☝️ 👍 👎 ✊ 👊 🤛 🤜 👏 🙌 🫶 👐 🤲 🤝 🙏 💪 🦾 🫵 👀 👅 👄 💋',
  'Сердца': '❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 💔 ❤️‍🔥 ❣️ 💕 💞 💓 💗 💖 💘 💝 💯 💢 💥 💫 💦 💨 🔥 ✨ ⭐ 🌟 ⚡',
  'Еда': '🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🌶 🌽 🥕 🧄 🧅 🥔 🍞 🥐 🧀 🍖 🍗 🥩 🌭 🍔 🍟 🍕 🥪 🌮 🌯 🥙 🧆 🍝 🍜 🍲 🍛 🍣 🍱 🥟 🍤 🍙 🍚 🍰 🎂 🍩 🍪 🍫 🍬 🍭 🍯 ☕ 🍵 🧃 🥤 🧋 🍺 🍷 🥂',
  'Звери': '🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🙈 🙉 🙊 🐔 🐧 🐦 🐤 🦆 🦅 🦉 🐺 🐗 🐴 🦄 🐝 🐛 🦋 🐌 🐞 🐢 🐍 🦖 🐙 🦑 🦀 🐠 🐬 🐳 🦈 🐊 🐅 🦓 🦒 🐘 🦛 🐪 🦘 🐕 🐈 🐓 🦚 🦜',
  'Разное': '⚽ 🏀 🏈 🎾 🏐 🎱 🏓 🥊 🎮 🕹 🎲 🎯 🎳 🎸 🎹 🎤 🎧 🎬 🏆 🥇 🚗 🏎 🚀 ✈️ 🛸 🏠 🏝 🌋 🌈 ☀️ 🌙 ⛄ 🌊 🎁 🎈 🎉 🎊 💎 💰 💸 📱 💻 ⌚ 📷 💡 🔑 🔒 🧨 💣 🪓 🗿 🚬 🍀 🌹 🌸 🌚 🌝'
}

export const emoStickers = '😂 🤣 😍 🥰 😎 🤯 😭 😱 🤡 💀 👻 🔥 💯 🙈 🥳 😤 🤬 😈 🫡 🤌 👀 🗿 💅 🐸'.split(' ')
