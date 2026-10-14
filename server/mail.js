import nodemailer from 'nodemailer'

const H = process.env.SMTP_HOST
let tr = null
if (H) {
  tr = nodemailer.createTransport({
    host: H,
    port: +(process.env.SMTP_PORT || 465),
    secure: +(process.env.SMTP_PORT || 465) === 465,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
  })
}

export const mailOn = !!tr || process.env.NODE_ENV !== 'production'

export async function sendCode(to, code) {
  if (!tr) {
    console.log(`[dev] код для ${to}: ${code}`)
    return
  }
  await tr.sendMail({
    from: process.env.SMTP_FROM || process.env.SMTP_USER,
    to,
    subject: `Код входа в Specter: ${code}`,
    text: `Твой код: ${code}\nОн действует 10 минут. Если это был не ты, просто проигнорируй письмо.`,
    html: `<div style="font-family:sans-serif;background:#0b0d14;color:#e8eaf2;padding:32px;border-radius:16px;max-width:420px">
      <div style="font-size:13px;letter-spacing:4px;color:#8b7bff">SPECTER</div>
      <p style="margin:18px 0 6px">Твой код входа</p>
      <div style="font-size:34px;font-weight:700;letter-spacing:8px">${code}</div>
      <p style="color:#8a90a6;font-size:13px">Действует 10 минут. Если это был не ты, просто проигнорируй письмо.</p></div>`
  })
}
