const puppeteer = require('puppeteer-core');
(async()=>{
  const b=await puppeteer.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage','--force-color-profile=srgb','--font-render-hinting=none']});
  const p=await b.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push('ERR '+e.message));
  p.on('console',m=>{if(m.type()==='error')errs.push('CON '+m.text());});
  await p.setViewport({width:390,height:800,deviceScaleFactor:2,isMobile:true,hasTouch:true});
  await p.goto('https://om2025p.github.io/8gfrswwwvvv853ftygd444---hgcfhooodd/family-lab/index.html',{waitUntil:'load',timeout:60000});
  await p.evaluate(()=>localStorage.clear());
  await p.reload({waitUntil:'load'});
  await new Promise(r=>setTimeout(r,2500));

  await p.evaluate(async()=>{
    document.querySelector('#seg button[data-v="table"]').click();
    await new Promise(r=>setTimeout(r,400));
    const q=document.getElementById('q'); q.value='علی رضایی'; q.dispatchEvent(new Event('input',{bubbles:true}));
    await new Promise(r=>setTimeout(r,400));
    document.querySelector('.tbl tbody tr[data-id]').click();
    await new Promise(r=>setTimeout(r,250));
    const sd = document.getElementById('sheetDeck');
    if (sd) { sd.click(); await new Promise(r=>setTimeout(r,400)); }
    document.querySelector('#seg button[data-v="tree"]').click();
    await new Promise(r=>setTimeout(r,1200));
  });

  const R = await p.evaluate(()=>{
    const nodes=[...document.querySelectorAll('.tnode')];
    const rects=nodes.map(n=>n.getBoundingClientRect());
    let ov=0;
    for(let i=0;i<rects.length;i++)for(let j=i+1;j<rects.length;j++){
      const a=rects[i],c=rects[j];
      if(a.left<c.right-2&&c.left<a.right-2&&a.top<c.bottom-2&&c.top<a.bottom-2)ov++;
    }
    const kin=n=>nodes.find(x=>x.querySelector('.tnm').textContent===n)?.querySelector('.tjb').textContent;
    return {
      badges:[...document.querySelectorAll('.side-badge')].map(x=>x.textContent),
      count:nodes.length, overlaps:ov,
      note:(document.querySelector('.marriage-note')||{}).innerText||'',
      omo:kin('کریم رضایی'), amme:kin('فاطمه رضایی'),
      daii:kin('رضا موسوی'), khale:kin('زینب موسوی'),
      cousin:kin('امیرحسین رضایی')
    };
  });
  // capture
  await p.evaluate(()=>{
    const s=document.querySelector('.tree-scroll'); s.style.overflow='visible';
    s.style.width=document.querySelector('.tree-canvas').style.width;
  });
  await new Promise(r=>setTimeout(r,400));
  const el=await p.$('#treeCanvas');
  await el.screenshot({path:'/tmp/uibuild/shots/LT_both.png'});
  console.log(JSON.stringify({R,errs},null,1));
  await b.close();
})();
