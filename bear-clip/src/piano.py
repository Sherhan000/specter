import numpy as np, wave, sys
sr=44100; dur=6.5; out=np.zeros(int(sr*dur))
def note(f, t0, length, vel=0.3):
    n=int(sr*length); t=np.arange(n)/sr
    env=np.exp(-t*2.2)*(1-np.exp(-t*200))
    sig=sum(a*np.sin(2*np.pi*f*k*t)*np.exp(-t*k*0.8) for k,a in [(1,1),(2,.45),(3,.22),(4,.1),(5,.05)])
    i=int(t0*sr); seg=out[i:i+n]; L=len(seg); seg+=vel*env[:L]*sig[:L]
hz=lambda m:440*2**((m-69)/12)
# A minor: Am - F - C - E (slow, gentle)
chords=[(0,[45,52,57,60]),(1.6,[41,48,53,57]),(3.2,[48,55,60,64]),(4.8,[40,47,56,59])]
for t0,ch in chords:
    for j,m in enumerate(ch): note(hz(m), t0+j*0.09, 3.0, 0.12)
mel=[(0.4,76),(1.0,74),(1.3,72),(2.0,72),(2.6,71),(3.4,67),(4.0,72),(4.6,71),(5.2,68),(5.6,69)]
for t0,m in mel: note(hz(m), t0, 2.0, 0.18)
# simple reverb
for d,g in [(0.07,.35),(0.13,.25),(0.21,.18),(0.33,.1)]:
    k=int(d*sr); out[k:]+=g*out[:-k]
out*=np.minimum(1,(dur-np.arange(len(out))/sr)/1.0)  # fade out
out=out/np.abs(out).max()*0.7
w=wave.open(sys.argv[1],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
