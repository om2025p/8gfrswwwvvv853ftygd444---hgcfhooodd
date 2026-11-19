const puppeteer = require('puppeteer-core');
(async()=>{
  const b=await puppeteer.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
  const out=[];
  for (const m of ['m1','m2','m3','m4','m5','m6']) {
    const p=await b.newPage();
    await p.setViewport({width:1400,height:1000});
    await p.goto(`http://127.0.0.1:12099/tree-samples/${m}.html`,{waitUntil:'networkidle0'});
    await new Promise(r=>setTimeout(r,500));
    const R=await p.evaluate(()=>{
      const names=[...document.querySelectorAll('.nm')];
      const kins=[...document.querySelectorAll('.kin')];
      const clippedN=names.filter(n=>n.scrollWidth>n.clientWidth+1).length;
      const clippedK=kins.filter(n=>n.scrollWidth>n.clientWidth+1).length;
      const emptyK=kins.filter(n=>!n.textContent.trim()).length;
      // tiny fonts?
      const fs=[...document.querySelectorAll('.nm')].map(n=>parseFloat(getComputedStyle(n).fontSize));
      const kfs=[...document.querySelectorAll('.kin')].map(n=>parseFloat(getComputedStyle(n).fontSize));
      return {names:names.length, clippedN, clippedK, emptyK,
              minNameFont:Math.min(...fs), minKinFont:Math.min(...kfs)};
    });
    out.push({m,...R});
    await p.close();
  }
  console.table(out);
  await b.close();
})();
