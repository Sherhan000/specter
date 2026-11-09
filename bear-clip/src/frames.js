const {chromium}=require('playwright');
(async()=>{const [,,html,dir,dur,fps]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+html);const n=Math.round(dur*fps);
for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:`${dir}/f${String(i).padStart(4,'0')}.png`});}
await b.close();console.log('frames',n)})();
