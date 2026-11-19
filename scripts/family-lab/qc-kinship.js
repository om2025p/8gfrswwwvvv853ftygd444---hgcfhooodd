const puppeteer = require('puppeteer-core');
(async()=>{
  const b=await puppeteer.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});
  const p=await b.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push('ERR '+e.message));
  p.on('console',m=>{if(m.type()==='error')errs.push('CON '+m.text());});
  await p.setViewport({width:390,height:800,deviceScaleFactor:2,isMobile:true,hasTouch:true});
  await p.goto('http://127.0.0.1:12099/family-lab/index.html',{waitUntil:'load'});
  await p.evaluate(()=>localStorage.clear());
  await p.reload({waitUntil:'load'});
  await new Promise(r=>setTimeout(r,800));

  const R = await p.evaluate(async()=>{
    const out={};
    document.querySelector('#seg button[data-v="table"]').click();
    await new Promise(r=>setTimeout(r,300));
    const q=document.getElementById('q'); q.value='علی رضایی'; q.dispatchEvent(new Event('input',{bubbles:true}));
    await new Promise(r=>setTimeout(r,300));
    document.querySelector('.tbl tbody tr[data-id]').click();
    await new Promise(r=>setTimeout(r,200));
    document.getElementById('sheetDeck').click();
    await new Promise(r=>setTimeout(r,300));
    document.querySelector('#seg button[data-v="tree"]').click();
    await new Promise(r=>setTimeout(r,900));

    out.badges=[...document.querySelectorAll('.side-badge')].map(x=>x.textContent);
    out.nodes=[...document.querySelectorAll('.tnode')].map(n=>({
      name:n.querySelector('.tnm').textContent, kin:n.querySelector('.tjb').textContent,
      x:Math.round(parseFloat(n.style.left)), y:Math.round(parseFloat(n.style.top))
    }));
    const rects=[...document.querySelectorAll('.tnode')].map(n=>n.getBoundingClientRect());
    let ov=0, pairs=[];
    for(let i=0;i<rects.length;i++)for(let j=i+1;j<rects.length;j++){
      const a=rects[i],c=rects[j];
      if(a.left<c.right-2&&c.left<a.right-2&&a.top<c.bottom-2&&c.top<a.bottom-2){
        ov++; pairs.push([out.nodes[i]?.name,out.nodes[j]?.name]);
      }
    }
    out.overlaps=ov; out.overlapPairs=pairs.slice(0,5);
    out.note=(document.querySelector('.marriage-note')||{}).innerText||'';
    // key kinship expectations
    const get=n=>out.nodes.find(x=>x.name===n)?.kin;
    out.check={
      father:get('رحیم رضایی'), mother:get('مریم موسوی'),
      omo:get('کریم رضایی'), amme:get('فاطمه رضایی'), daii:get('رضا موسوی'), khale:get('زینب موسوی'),
      sis:get('سارا رضایی'), bro:get('مجید رضایی'),
      cousin:get('امیرحسین رضایی'), khaleDau:get('حمیده صابری'),
      son:get('آوا رضایی'), grandson:get('بردیا رضایی'),
      grandpa:get('مظفر رضایی'), grandma:get('فاطمه صادقی'),
      self:get('علی رضایی')
    };
    return out;
  });
  console.log(JSON.stringify({R,errs},null,1));
  await b.close();
})();
