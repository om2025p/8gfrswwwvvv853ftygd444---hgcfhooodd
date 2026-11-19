const puppeteer = require('puppeteer-core');
(async()=>{
  const b=await puppeteer.launch({executablePath:'/usr/bin/chromium',
    args:['--no-sandbox','--disable-dev-shm-usage','--force-color-profile=srgb','--font-render-hinting=none','--disable-lcd-text']});
  const report=[];
  for (const m of ['m1','m2','m3','m4','m5','m6']) {
    const p=await b.newPage();
    const errs=[]; p.on('pageerror',e=>errs.push('ERR '+e.message));
    p.on('console',c=>{if(c.type()==='error')errs.push('CON '+c.text());});
    await p.setViewport({width:1400,height:1000,deviceScaleFactor:1});
    await p.goto(`http://127.0.0.1:12099/tree-samples/${m}.html`,{waitUntil:'networkidle0',timeout:30000});
    await new Promise(r=>setTimeout(r,600));

    const dim = await p.evaluate(()=>{
      const cv=document.getElementById('cv');
      return {w:Math.ceil(parseFloat(cv.style.width)), h:Math.ceil(parseFloat(cv.style.height))};
    });
    // resize viewport to fit the whole canvas, no scrollbars
    await p.setViewport({width:dim.w+8, height:dim.h+8, deviceScaleFactor:2});
    await p.evaluate(()=>{
      document.querySelector('.wrap').style.overflow='visible';
      document.querySelector('.wrap').style.padding='0';
      document.querySelector('.wrap').style.width='auto';
      document.querySelector('.cv').style.margin='0';
      document.body.style.overflow='hidden';
      window.scrollTo(0,0);
    });
    await new Promise(r=>setTimeout(r,500));

    const info = await p.evaluate(()=>{
      const cv=document.getElementById('cv'), cr=cv.getBoundingClientRect();
      const nodes=[...document.querySelectorAll('.nd')];
      const rs=nodes.map(n=>n.getBoundingClientRect());
      let ov=0;
      for(let i=0;i<rs.length;i++)for(let j=i+1;j<rs.length;j++){
        const a=rs[i],c=rs[j];
        if(a.left<c.right-2&&c.left<a.right-2&&a.top<c.bottom-2&&c.top<a.bottom-2)ov++;
      }
      const out = rs.filter(r=>r.left<cr.left-2||r.right>cr.right+2||r.top<cr.top-2||r.bottom>cr.bottom+2).length;
      return {nodes:nodes.length, overlaps:ov, outsideCanvas:out};
    });
    const el=await p.$('#cv');
    await el.screenshot({path:`/tmp/uibuild/shots/H_${m}.png`});
    report.push({m, ...info, dim, errs:errs.length?errs:'clean'});
    await p.close();
  }
  console.log(JSON.stringify(report,null,1));
  await b.close();
})();
