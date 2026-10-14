import { useEffect, useRef, useState } from 'react'

export default function Intro({ done }) {
  const cv = useRef()
  const [out, setOut] = useState(false)

  useEffect(() => {
    const c = cv.current, x = c.getContext('2d')
    const dpr = Math.min(devicePixelRatio || 1, 2)
    let W, H, pts = [], raf, t0 = performance.now(), gone = false

    const build = () => {
      W = innerWidth; H = innerHeight
      c.width = W * dpr; c.height = H * dpr
      x.setTransform(dpr, 0, 0, dpr, 0, 0)
      const o = document.createElement('canvas'), ox = o.getContext('2d')
      const fs = Math.min(W / 5.2, 150)
      o.width = W; o.height = H
      ox.fillStyle = '#fff'
      ox.font = `800 ${fs}px Unbounded, Manrope, sans-serif`
      ox.textAlign = 'center'; ox.textBaseline = 'middle'
      ox.fillText('SPECTER', W / 2, H / 2)
      const d = ox.getImageData(0, 0, W, H).data
      const step = Math.max(3, Math.round(fs / 26))
      const tg = []
      for (let yy = 0; yy < H; yy += step) for (let xx = 0; xx < W; xx += step) if (d[(yy * W + xx) * 4 + 3] > 128) tg.push([xx, yy])
      pts = tg.map(([tx, ty]) => {
        const a = Math.random() * Math.PI * 2, r = Math.max(W, H) * (.5 + Math.random() * .6)
        return { x: W / 2 + Math.cos(a) * r, y: H / 2 + Math.sin(a) * r, tx, ty, d: Math.random() * .35, hue: 250 + (tx / W) * 60, s: Math.random() * 1.4 + .8 }
      })
    }
    build()

    const ease = k => 1 - Math.pow(1 - k, 4)
    const frame = now => {
      const t = (now - t0) / 1000
      x.fillStyle = 'rgba(8,9,15,0.28)'
      x.fillRect(0, 0, W, H)
      x.globalCompositeOperation = 'lighter'
      for (const p of pts) {
        let k = Math.min(1, Math.max(0, (t - p.d) / 1.6))
        k = ease(k)
        let px = p.x + (p.tx - p.x) * k, py = p.y + (p.ty - p.y) * k
        if (t > 2.6) {
          const f = (t - 2.6) * 1.8
          py -= f * f * 40 * (p.s * .6)
          px += Math.sin(p.ty * .05 + t * 3) * f * 12
        }
        const shimmer = k > .98 ? Math.sin(t * 6 + p.tx * .04) * .3 + .7 : .6
        x.fillStyle = `hsla(${p.hue},95%,${62 + shimmer * 14}%,${t > 2.6 ? Math.max(0, 1 - (t - 2.6) * 1.1) : .9})`
        x.fillRect(px, py, p.s, p.s)
      }
      x.globalCompositeOperation = 'source-over'
      if (t > 3.5 && !gone) {
        gone = true
        setOut(true)
        setTimeout(done, 450)
      }
      raf = requestAnimationFrame(frame)
    }
    document.fonts?.ready.then(() => { build(); raf = requestAnimationFrame(frame) }) || (raf = requestAnimationFrame(frame))
    addEventListener('resize', build)
    return () => {
      cancelAnimationFrame(raf)
      removeEventListener('resize', build)
    }
  }, [])

  return (
    <div className={'intro' + (out ? ' out' : '')} onClick={done}>
      <canvas ref={cv} />
      <div className="intro-tag">чат, который видит больше</div>
      <div className="intro-skip">нажми, чтобы пропустить</div>
    </div>
  )
}
