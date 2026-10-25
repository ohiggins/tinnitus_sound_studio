"""HTML Web Audio player embedded inside a Streamlit component iframe."""
from dataclasses import asdict
import json

from audio_engine import AudioSettings


def html_for_player(settings: AudioSettings, minutes: int) -> str:
    settings.validate()
    if minutes not in (5, 10, 15, 30, 60):
        raise ValueError("Unsupported playback timer")
    cfg = json.dumps({**asdict(settings), "minutes": minutes})
    return r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root { color-scheme: light; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
         color:#183349; background:#f0f7f7; }
  .panel { padding:20px; background:linear-gradient(115deg,#effaf9,#edf3fa);
           border:1px solid #d6e6ea; border-radius:15px; }
  .bar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
  button { border:0; cursor:pointer; border-radius:9px; padding:11px 17px;
           font-weight:700; font-size:15px; }
  #start {background:#136b73; color:#fff;} #stop {background:#fff; border:1px solid #9db4bf; color:#264656;}
  button:disabled {opacity:.45; cursor:default;}
  #time { font-variant-numeric:tabular-nums; font-size:20px; font-weight:750; margin-left:auto; }
  #status { margin:12px 0 0; font-size:13px; color:#3a5865; min-height:21px; }
  .tiny {margin-top:12px; font-size:12px; color:#526e76}
</style>
</head>
<body>
<div class="panel">
  <div class="bar">
    <button id="start" type="button">▶ Start gentle sound</button>
    <button id="stop" type="button" disabled>■ Stop</button>
    <span id="time" aria-live="polite">00:00</span>
  </div>
  <p id="status" role="status">Ready. Lower your device volume before starting.</p>
  <div class="tiny">Sound is generated in your browser. The timer stops automatically. Changes to Streamlit controls will stop and reset playback.</div>
</div>
<script>
"use strict";
const cfg = __CONFIG__;
const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const timeEl = document.getElementById('time');
const statusEl = document.getElementById('status');
let ctx=null, source=null, oscillator=null, master=null, ticker=null;
let stopAt=0, playing=false;

// Standard noise-colouring approximations; not a clinical stimulus protocol.
function makeNoiseBuffer(audioCtx) {
  const n=Math.ceil(audioCtx.sampleRate * 12);
  const buf=audioCtx.createBuffer(1,n,audioCtx.sampleRate);
  const v=buf.getChannelData(0);
  let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0,brown=0;
  for(let i=0;i<n;i++) {
    const w=Math.random()*2-1;
    let s=w;
    if(cfg.sound_type==='Pink noise') {
      b0=0.99886*b0+w*0.0555179; b1=0.99332*b1+w*0.0750759;
      b2=0.96900*b2+w*0.1538520; b3=0.86650*b3+w*0.3104856;
      b4=0.55000*b4+w*0.5329522; b5=-0.7616*b5-w*0.0168980;
      s=(b0+b1+b2+b3+b4+b5+b6+w*0.5362)*0.11;
      b6=w*0.115926;
    } else if(cfg.sound_type==='Brown noise') {
      brown=(brown+0.02*w)/1.02;
      s=brown*3.5;
    }
    v[i]=s;
  }
  let peak=0;
  for(let i=0;i<n;i++) peak=Math.max(peak,Math.abs(v[i]));
  // Normalise sample peak, then apply a conservative overall gain separately.
  const inv=peak>0 ? 1/peak : 0;
  for(let i=0;i<n;i++) v[i]*=inv;
  // Silence briefly at each loop junction to prevent clicks.
  const fade=Math.floor(audioCtx.sampleRate*0.035);
  for(let i=0;i<fade;i++) {
    const t=i/fade;
    v[i]*=t;
    v[n-1-i]*=t;
  }
  return buf;
}
function fmt(ms) {
  const sec=Math.max(0,Math.ceil(ms/1000));
  return String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');
}
async function stopSound(reason='Stopped.') {
  playing=false;
  if(ticker){clearInterval(ticker); ticker=null;}
  if(master && ctx) master.gain.setTargetAtTime(0,ctx.currentTime,0.03);
  if(source){try{source.stop(ctx.currentTime+0.14);}catch(e){} source=null;}
  if(oscillator){try{oscillator.stop(ctx.currentTime+0.14);}catch(e){} oscillator=null;}
  const old=ctx; ctx=null; master=null;
  if(old) setTimeout(()=>old.close().catch(()=>{}),220);
  startBtn.disabled=false; stopBtn.disabled=true;
  statusEl.textContent=reason;
}
startBtn.addEventListener('click',async()=>{
  if(playing) return;
  startBtn.disabled=true;
  try {
    const AudioContextClass=window.AudioContext||window.webkitAudioContext;
    if(!AudioContextClass) throw new Error('Web Audio is not available in this browser.');
    ctx=new AudioContextClass();
    await ctx.resume();
    source=ctx.createBufferSource(); source.buffer=makeNoiseBuffer(ctx); source.loop=true;
    const hipass=ctx.createBiquadFilter(); hipass.type='highpass'; hipass.frequency.value=cfg.low_hz; hipass.Q.value=0.707;
    const lopass=ctx.createBiquadFilter(); lopass.type='lowpass'; lopass.frequency.value=cfg.high_hz; lopass.Q.value=0.707;
    const soundGain=ctx.createGain(); soundGain.gain.value=1-cfg.tone_mix_percent/100;
    master=ctx.createGain(); master.gain.value=0;
    source.connect(hipass); hipass.connect(lopass); lopass.connect(soundGain); soundGain.connect(master);
    if(cfg.tone_mix_percent>0){
      oscillator=ctx.createOscillator(); oscillator.type='sine'; oscillator.frequency.value=cfg.tone_hz;
      const tg=ctx.createGain(); tg.gain.value=cfg.tone_mix_percent/100;
      oscillator.connect(tg); tg.connect(master); oscillator.start();
    }
    master.connect(ctx.destination);
    source.start();
    master.gain.setTargetAtTime(cfg.digital_peak_percent/100,ctx.currentTime,0.06);
    playing=true; stopBtn.disabled=false;
    stopAt=Date.now()+cfg.minutes*60*1000;
    timeEl.textContent=fmt(cfg.minutes*60*1000);
    statusEl.textContent='Playing softly. Stop if the sound is unpleasant or makes tinnitus worse.';
    ticker=setInterval(()=>{
      const left=stopAt-Date.now(); timeEl.textContent=fmt(left);
      if(left<=0) stopSound('Session complete. Sound stopped automatically.');
    },250);
  } catch(e) {
    statusEl.textContent='Could not start audio: '+(e && e.message ? e.message : String(e));
    if(ctx) await ctx.close().catch(()=>{});
    ctx=null; source=null; oscillator=null; master=null; playing=false;
    startBtn.disabled=false; stopBtn.disabled=true;
  }
});
stopBtn.addEventListener('click',()=>stopSound());
window.addEventListener('pagehide',()=>{
  if(ticker) clearInterval(ticker);
  if(ctx) ctx.close().catch(()=>{});
});
</script>
</body>
</html>'''.replace('__CONFIG__', cfg)
