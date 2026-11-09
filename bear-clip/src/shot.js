const {chromium}=require('playwright');
(async()=>{const [,,html,out,t]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+html);await p.evaluate(t=>render(+t),t);await p.screenshot({path:out});await b.close();})();
