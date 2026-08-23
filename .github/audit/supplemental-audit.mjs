import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';

const BASE='https://oolita.es';
const report={generated_at:new Date().toISOString(),source_build_status:process.env.SOURCE_BUILD_STATUS||'unknown',visible_dates:{},mobile:{},books:{},sundays:{},navigation:{},accessibility:{},errors:[]};
const pass=(o,k,ok,detail=null)=>o[k]={pass:Boolean(ok),detail};
const norm=s=>(s||'').replace(/\s+/g,' ').trim();
const dateMatches=s=>[...new Set((s.match(/\b(?:\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+\d{2,4}|\d{2}\.\d{2}\.(?:\d{2}|\d{4}))\b/g)||[]))];

function intersects(a,b){
  const x=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left));
  const y=Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
  return x*y>25;
}

async function inspect(browser,path,width,height=844,withAxe=false){
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  const consoleErrors=[]; const pageErrors=[];
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text().slice(0,250));});
  page.on('pageerror',e=>pageErrors.push(String(e).slice(0,250)));
  const resp=await page.goto(BASE+path,{waitUntil:'networkidle',timeout:45000});
  const data=await page.evaluate(()=>{
    const r=e=>{if(!e)return null;const b=e.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,width:b.width,height:b.height};};
    const visible=e=>{const s=getComputedStyle(e),b=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&b.width>1&&b.height>1;};
    const candidates=[...document.querySelectorAll('h1,h2,h3,p,.grande,.glosa,.rot,.art-manifesto')].filter(visible).filter(e=>![...e.children].some(c=>/^(H1|H2|H3|P)$/.test(c.tagName)));
    const collisions=[];
    for(let i=0;i<candidates.length;i++)for(let j=i+1;j<candidates.length;j++){
      const a=candidates[i],b=candidates[j];
      if(a.contains(b)||b.contains(a))continue;
      const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
      const x=Math.max(0,Math.min(ar.right,br.right)-Math.max(ar.left,br.left));
      const y=Math.max(0,Math.min(ar.bottom,br.bottom)-Math.max(ar.top,br.top));
      if(x*y>25)collisions.push({a:(a.textContent||'').trim().slice(0,80),b:(b.textContent||'').trim().slice(0,80),area:Math.round(x*y)});
    }
    const outside=[...document.querySelectorAll('body *')].filter(visible).map(e=>({e,b:e.getBoundingClientRect()})).filter(x=>x.b.left<-1||x.b.right>innerWidth+1).filter(x=>getComputedStyle(x.e).position!=='fixed').slice(0,20).map(x=>({tag:x.e.tagName,cls:x.e.className?.toString().slice(0,80)||'',text:(x.e.textContent||'').trim().slice(0,60),left:Math.round(x.b.left),right:Math.round(x.b.right)}));
    const footer=document.querySelector('footer,.pie');
    const footerLinks=footer?[...footer.querySelectorAll('a')].filter(visible).map(a=>({text:(a.textContent||'').trim(),rect:r(a)})):[];
    const footerOverlaps=[];
    for(let i=0;i<footerLinks.length;i++)for(let j=i+1;j<footerLinks.length;j++){
      const a=footerLinks[i].rect,b=footerLinks[j].rect;
      const x=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left));
      const y=Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
      if(x*y>4)footerOverlaps.push([footerLinks[i].text,footerLinks[j].text]);
    }
    const hero=document.querySelector('main section,main .tramo,.hero,.art-hero');
    const year=document.querySelector('.mobile-2027-clear');
    let yearStyle=null;
    if(year){const s=getComputedStyle(year),bf=getComputedStyle(year,'::before'),af=getComputedStyle(year,'::after');yearStyle={text:year.textContent,textDecoration:s.textDecorationLine,background:s.backgroundColor,before:bf.content,after:af.content,rect:r(year)};}
    const grid=document.querySelector('.sunday-field-grid');
    const tiles=[...document.querySelectorAll('[data-sunday-tile]')].map(e=>({n:e.dataset.sunday,href:e.getAttribute('href'),rect:r(e)}));
    const anchors=[...document.querySelectorAll('a[href]')].filter(visible).map(a=>({text:(a.innerText||a.textContent||'').replace(/\s+/g,' ').trim(),href:a.getAttribute('href')}));
    const menuNums=[];
    for(const a of anchors){const m=a.text.match(/^(0[1-9]|1[0-4])(?:\b|\s|·|—|-)/);if(m&&!menuNums.some(x=>x.n===m[1]))menuNums.push({n:m[1],text:a.text.slice(0,120),href:a.href});}
    return {innerWidth,innerHeight,scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,bodyText:document.body.innerText.replace(/\s+/g,' ').trim(),collisions:collisions.slice(0,30),outside,header:r(document.querySelector('header')),hero:r(hero),footer:r(footer),footerOverlaps,footerLinks,yearStyle,grid:r(grid),tiles,menuNums,menuGroups:[...document.querySelectorAll('.menu-group-label')].map(x=>x.textContent.trim()),images:[...document.images].map(i=>({alt:i.getAttribute('alt'),ok:i.complete&&i.naturalWidth>0,w:i.naturalWidth,rect:r(i)})),bookSpec:[...document.querySelectorAll('.k')].map(k=>({k:k.textContent.trim(),v:k.nextElementSibling?.textContent?.trim()||''})),excerpt:Boolean(document.querySelector('#extracto-libro')),excerptLanguages:[...document.querySelectorAll('#extracto-libro [lang]')].map(x=>x.getAttribute('lang')),styleMarkers:[...document.querySelectorAll('style[id]')].map(x=>x.id)};
  });
  data.status=resp?.status()||null; data.consoleErrors=consoleErrors; data.pageErrors=pageErrors;
  if(withAxe){const ax=await new AxeBuilder({page}).analyze();data.axe=ax.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}));}
  await page.close(); return data;
}

try{
  const browser=await chromium.launch({headless:true});
  try{
    // Visible English dates: inspect rendered text, not hidden source/script strings.
    const enDesktop=await inspect(browser,'/en/',1280,900,false);
    const enBookDesktop=await inspect(browser,'/en/editions/book/',1280,900,false);
    report.visible_dates.home=dateMatches(enDesktop.bodyText);
    report.visible_dates.book=dateMatches(enBookDesktop.bodyText);
    pass(report.visible_dates,'english_home_unambiguous',enDesktop.bodyText.includes('3 Jan 2027')&&enDesktop.bodyText.includes('9 Aug 26')&&!enDesktop.bodyText.includes('03.01.2027'),report.visible_dates.home);
    pass(report.visible_dates,'english_book_unambiguous',!enBookDesktop.bodyText.includes('31.01.27')&&!enBookDesktop.bodyText.includes('03.01.27'),report.visible_dates.book);

    // Correct mobile viewport checks.
    for(const [lang,path] of [['en','/en/'],['es','/']]){
      report.mobile[lang]=[];
      for(const width of [360,390,412]){
        const d=await inspect(browser,path,width,844,width===390);
        report.mobile[lang].push({width,innerWidth:d.innerWidth,scrollWidth:d.scrollWidth,overflow:d.overflow,outside:d.outside,collisions:d.collisions,header:d.header,hero:d.hero,footer:d.footer,footerOverlaps:d.footerOverlaps,yearStyle:d.yearStyle,consoleErrors:d.consoleErrors,pageErrors:d.pageErrors,axe:d.axe||[]});
      }
    }
    const en390=report.mobile.en.find(x=>x.width===390);
    pass(report.mobile,'english_2027_line_gone',en390?.yearStyle?.text==='2027'&&en390.yearStyle.textDecoration==='none'&&en390.yearStyle.before==='none'&&en390.yearStyle.after==='none'&&!/rgba\(0, 0, 0, 0\)|transparent/.test(en390.yearStyle.background||''),en390?.yearStyle||null);
    pass(report.mobile,'english_overflow',report.mobile.en.every(x=>x.innerWidth===x.width&&!x.overflow&&x.outside.length===0),report.mobile.en.map(x=>({width:x.width,innerWidth:x.innerWidth,scrollWidth:x.scrollWidth,outside:x.outside}))); 
    pass(report.mobile,'spanish_overflow',report.mobile.es.every(x=>x.innerWidth===x.width&&!x.overflow&&x.outside.length===0),report.mobile.es.map(x=>({width:x.width,innerWidth:x.innerWidth,scrollWidth:x.scrollWidth,outside:x.outside})));
    pass(report.mobile,'english_text_collisions',report.mobile.en.every(x=>x.collisions.length===0),report.mobile.en.flatMap(x=>x.collisions.map(c=>({width:x.width,...c}))));
    pass(report.mobile,'spanish_text_collisions',report.mobile.es.every(x=>x.collisions.length===0),report.mobile.es.flatMap(x=>x.collisions.map(c=>({width:x.width,...c}))));
    pass(report.mobile,'footer_layout', [...report.mobile.en,...report.mobile.es].every(x=>x.footer&&x.footer.left>=-1&&x.footer.right<=x.innerWidth+1&&x.footerOverlaps.length===0), [...report.mobile.en,...report.mobile.es].map(x=>({width:x.width,footer:x.footer,overlaps:x.footerOverlaps})));
    pass(report.mobile,'javascript_clean',[...report.mobile.en,...report.mobile.es].every(x=>x.consoleErrors.length===0&&x.pageErrors.length===0),[...report.mobile.en,...report.mobile.es].filter(x=>x.consoleErrors.length||x.pageErrors.length));

    // Book mobile and availability.
    const enBook=await inspect(browser,'/en/editions/book/',390,844,true); const esBook=await inspect(browser,'/ediciones/libro/',390,844,true);
    report.books={en:{status:enBook.status,overflow:enBook.overflow,outside:enBook.outside,collisions:enBook.collisions,dates:dateMatches(enBook.bodyText),spec:enBook.bookSpec,excerpt:enBook.excerpt,languages:enBook.excerptLanguages,badImages:enBook.images.filter(x=>!x.ok),axe:enBook.axe},es:{status:esBook.status,overflow:esBook.overflow,outside:esBook.outside,collisions:esBook.collisions,spec:esBook.bookSpec,excerpt:esBook.excerpt,languages:esBook.excerptLanguages,badImages:esBook.images.filter(x=>!x.ok),axe:esBook.axe}};
    pass(report.books,'page_count_48',enBook.bookSpec.some(x=>/^Pages$/i.test(x.k)&&x.v==='48')&&esBook.bookSpec.some(x=>/^Páginas$/i.test(x.k)&&x.v==='48'),{en:enBook.bookSpec,es:esBook.bookSpec});
    pass(report.books,'bilingual_excerpt',enBook.excerpt&&esBook.excerpt&&enBook.excerptLanguages.includes('es')&&enBook.excerptLanguages.includes('en')&&esBook.excerptLanguages.includes('es')&&esBook.excerptLanguages.includes('en'));
    pass(report.books,'cat_fable',enBook.bodyText.includes('The fable follows a real cat')&&esBook.bodyText.includes('La fábula sigue a un gato de verdad'));
    pass(report.books,'availability_consistent',/31 (?:Jan|January) (?:27|2027)/.test(enBook.bodyText)&&/31(?: de)? enero(?: de)? 2027/i.test(esBook.bodyText),{enDates:dateMatches(enBook.bodyText),enExcerpt:enBook.bodyText.match(/.{0,90}31 (?:Jan|January) (?:27|2027).{0,120}/)?.[0]||null,esExcerpt:esBook.bodyText.match(/.{0,90}31(?: de)? enero(?: de)? 2027.{0,120}/i)?.[0]||null});
    pass(report.books,'mobile_clean',!enBook.overflow&&!esBook.overflow&&enBook.outside.length===0&&esBook.outside.length===0&&enBook.collisions.length===0&&esBook.collisions.length===0,{enOutside:enBook.outside,esOutside:esBook.outside,enCollisions:enBook.collisions,esCollisions:esBook.collisions});
    pass(report.books,'images_loaded',enBook.images.every(x=>x.ok)&&esBook.images.every(x=>x.ok),{enBad:enBook.images.filter(x=>!x.ok),esBad:esBook.images.filter(x=>!x.ok)});

    // Sundays real mobile grid.
    const enSun=await inspect(browser,'/en/sundays/',390,844,true), esSun=await inspect(browser,'/domingos/',390,844,true);
    const active=enSun.tiles.filter(x=>x.href); const expected=Date.now()<Date.parse('2026-08-23T17:00:00Z')?2:3;
    report.sundays={expected,active:active.map(x=>x.n),enGrid:enSun.grid,esGrid:esSun.grid,enOverflow:enSun.overflow,esOverflow:esSun.overflow,enOutside:enSun.outside,esOutside:esSun.outside,enCollisions:enSun.collisions,esCollisions:esSun.collisions,axeEn:enSun.axe,axeEs:esSun.axe};
    pass(report.sundays,'count_and_state',active.length===expected&&enSun.tiles.length===22&&esSun.tiles.length===22&&enSun.tiles.every(x=>Number(x.n)<=expected?Boolean(x.href):!x.href),{active:active.map(x=>x.n),total:enSun.tiles.length});
    pass(report.sundays,'mobile_grid',!enSun.overflow&&!esSun.overflow&&enSun.outside.length===0&&esSun.outside.length===0&&enSun.grid?.right<=390.5&&esSun.grid?.right<=390.5,{enGrid:enSun.grid,esGrid:esSun.grid,enOutside:enSun.outside,esOutside:esSun.outside});

    // Navigation includes primary 01–03 and secondary 04–14.
    report.navigation={enNumbers:enDesktop.menuNums,esNumbers:(await inspect(browser,'/',1280,900,false)).menuNums,enGroups:enDesktop.menuGroups};
    const wanted=Array.from({length:14},(_,i)=>String(i+1).padStart(2,'0'));
    const enSet=new Set(report.navigation.enNumbers.map(x=>x.n)),esSet=new Set(report.navigation.esNumbers.map(x=>x.n));
    pass(report.navigation,'numbers_01_14',wanted.every(n=>enSet.has(n)&&esSet.has(n)),{missingEn:wanted.filter(n=>!enSet.has(n)),missingEs:wanted.filter(n=>!esSet.has(n)),en:report.navigation.enNumbers,es:report.navigation.esNumbers});
    pass(report.navigation,'groups',['Read and understand','Elsewhere','Project'].every(x=>enDesktop.menuGroups.includes(x)),enDesktop.menuGroups);

    const allAxe=[...report.mobile.en.find(x=>x.width===390).axe.map(v=>({path:'/en/',...v})),...report.mobile.es.find(x=>x.width===390).axe.map(v=>({path:'/',...v})),...(enBook.axe||[]).map(v=>({path:'/en/editions/book/',...v})),...(esBook.axe||[]).map(v=>({path:'/ediciones/libro/',...v})),...(enSun.axe||[]).map(v=>({path:'/en/sundays/',...v})),...(esSun.axe||[]).map(v=>({path:'/domingos/',...v}))];
    const severe=allAxe.filter(v=>['serious','critical'].includes(v.impact||''));
    report.accessibility={all:allAxe,severe};
    pass(report.accessibility,'no_serious_critical_mobile',severe.length===0,severe);
  }finally{await browser.close();}
}catch(e){report.errors.push(String(e?.stack||e));}

await fs.mkdir('audit-results',{recursive:true});
await fs.writeFile('audit-results/production-audit-supplemental.json',JSON.stringify(report,null,2));
const lines=[`# OOLITA supplemental production audit`,`Generated: ${report.generated_at}`,`Source build: ${report.source_build_status}`,''];
for(const [section,obj] of Object.entries(report)){
  if(!obj||typeof obj!=='object'||Array.isArray(obj)||['errors'].includes(section))continue;
  const found=Object.entries(obj).filter(([,v])=>v&&typeof v==='object'&&'pass'in v);
  if(!found.length)continue; lines.push(`## ${section}`); for(const [k,v] of found)lines.push(`${k}: ${v.pass?'PASS':'FAIL'}${v.detail!==null?` — ${typeof v.detail==='string'?v.detail:JSON.stringify(v.detail)}`:''}`); lines.push('');
}
lines.push('## Errors',...(report.errors.length?report.errors:['None']));
await fs.writeFile('audit-results/production-audit-supplemental.md',lines.join('\n'));
