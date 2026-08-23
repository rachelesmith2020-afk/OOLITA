import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';

const BASE='https://oolita.es';
const ACCOUNT=process.env.CLOUDFLARE_ACCOUNT_ID;
const TOKEN=process.env.CLOUDFLARE_API_TOKEN;
const DB='05b1cd1d-52fd-4a11-8142-13ab92a2c712';
const TARGET=process.env.TARGET_MAIN_SHA;
const RUN=process.env.GITHUB_RUN_ID||String(Date.now());
const auditEmail=`oolita-final-audit-${RUN}@example.com`;
const botEmail=`oolita-final-bot-${RUN}@example.com`;
const report={generated_at:new Date().toISOString(),target_main_sha:TARGET,deployment:{},cloudflare:{},corrections:{},mobile:{},signup:{},books:{},sundays:{},navigation:{},quality:{},errors:[]};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const pass=(obj,key,ok,detail=null)=>{obj[key]={pass:Boolean(ok),detail};return Boolean(ok);};
const norm=s=>(s||'').replace(/\s+/g,' ').trim();

async function cf(path,options={}){
  const r=await fetch(`https://api.cloudflare.com/client/v4${path}`,{...options,headers:{Authorization:`Bearer ${TOKEN}`,'Content-Type':'application/json',...(options.headers||{})}});
  const text=await r.text();let body;try{body=JSON.parse(text);}catch{body={raw:text.slice(0,400)}}
  if(!r.ok||body?.success===false)throw new Error(`Cloudflare ${r.status}: ${JSON.stringify(body?.errors||body).slice(0,600)}`);
  return body.result;
}
async function d1(sql,params=[]){const r=await cf(`/accounts/${ACCOUNT}/d1/database/${DB}/query`,{method:'POST',body:JSON.stringify({sql,params})});return Array.isArray(r)?r[0]:r;}
function dep(d){return d?{id:d.id,url:d.url,environment:d.environment,created_on:d.created_on,status:d.latest_stage?.status||null,branch:d.deployment_trigger?.metadata?.branch||null,commit_hash:d.deployment_trigger?.metadata?.commit_hash||null,commit_message:d.deployment_trigger?.metadata?.commit_message||null,aliases:d.aliases||[]}:null;}

async function fetchText(url){const r=await fetch(url,{redirect:'follow',headers:{'User-Agent':'OOLITA-final-production-audit/1.0','Cache-Control':'no-cache'}});return {status:r.status,url:r.url,text:await r.text()};}

async function inspect(browser,path,width=390,height=844,withAxe=false){
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  const consoleErrors=[],pageErrors=[];
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text().slice(0,300));});
  page.on('pageerror',e=>pageErrors.push(String(e).slice(0,300)));
  const resp=await page.goto(BASE+path,{waitUntil:'networkidle',timeout:45000});
  await sleep(150);
  const d=await page.evaluate(()=>{
    const rect=e=>{if(!e)return null;const b=e.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,width:b.width,height:b.height};};
    const visible=e=>{const s=getComputedStyle(e),b=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&b.width>1&&b.height>1;};
    const texts=[...document.querySelectorAll('h1,h2,h3,p,.grande,.glosa,.rot,.art-manifesto')].filter(visible);
    const collisions=[];
    for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){
      const a=texts[i],b=texts[j]; if(a.contains(b)||b.contains(a))continue;
      const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
      const x=Math.max(0,Math.min(ar.right,br.right)-Math.max(ar.left,br.left)),y=Math.max(0,Math.min(ar.bottom,br.bottom)-Math.max(ar.top,br.top));
      if(x*y>25)collisions.push({a:(a.textContent||'').trim().slice(0,70),b:(b.textContent||'').trim().slice(0,70),area:Math.round(x*y)});
    }
    const outside=[...document.querySelectorAll('body *')].filter(visible).map(e=>({e,b:e.getBoundingClientRect()})).filter(x=>getComputedStyle(x.e).position!=='fixed'&&(x.b.left<-1||x.b.right>innerWidth+1)).slice(0,25).map(x=>({tag:x.e.tagName,cls:(x.e.className||'').toString().slice(0,80),text:(x.e.textContent||'').trim().slice(0,60),left:Math.round(x.b.left),right:Math.round(x.b.right)}));
    const footer=document.querySelector('footer,.pie'),header=document.querySelector('header'),hero=document.querySelector('main section,main .tramo,.hero,.art-hero');
    const footerLinks=footer?[...footer.querySelectorAll('a')].filter(visible).map(a=>({text:(a.textContent||'').trim(),r:rect(a)})):[];
    const footerOverlaps=[];
    for(let i=0;i<footerLinks.length;i++)for(let j=i+1;j<footerLinks.length;j++){
      const a=footerLinks[i].r,b=footerLinks[j].r;const x=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)),y=Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));if(x*y>4)footerOverlaps.push([footerLinks[i].text,footerLinks[j].text]);
    }
    const year=document.querySelector('.mobile-2027-clear');let yearStyle=null;if(year){const s=getComputedStyle(year),bf=getComputedStyle(year,'::before'),af=getComputedStyle(year,'::after');yearStyle={text:year.textContent,textDecoration:s.textDecorationLine,background:s.backgroundColor,before:bf.content,after:af.content,rect:rect(year)};}
    const anchors=[...document.querySelectorAll('a[href]')].filter(visible).map(a=>({text:(a.innerText||a.textContent||'').replace(/\s+/g,' ').trim(),href:a.href,raw:a.getAttribute('href')}));
    const numbered=[];for(const a of anchors){const m=a.text.match(/^(0[1-9]|1[0-4])(?:\b|\s|·|—|-)/);if(m&&!numbered.some(x=>x.n===m[1]))numbered.push({n:m[1],text:a.text.slice(0,100),href:a.raw});}
    const sundayTiles=[...document.querySelectorAll('[data-sunday-tile]')].map(x=>({n:Number(x.dataset.sunday),date:x.dataset.date,href:x.getAttribute('href'),disabled:x.getAttribute('aria-disabled'),published:x.classList.contains('is-published'),current:x.classList.contains('is-current'),rect:rect(x)}));
    const grid=document.querySelector('.sunday-field-grid');
    return {status:null,innerWidth,innerHeight,scrollWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,outside,collisions,header:rect(header),hero:rect(hero),footer:rect(footer),footerOverlaps,yearStyle,bodyText:document.body.innerText.replace(/\s+/g,' ').trim(),title:document.title,description:document.querySelector('meta[name="description"]')?.content||null,canonical:document.querySelector('link[rel="canonical"]')?.href||null,hreflang:[...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(x=>({lang:x.hreflang,href:x.href})),h1:document.querySelectorAll('h1').length,headers:document.querySelectorAll('header').length,footers:document.querySelectorAll('footer,.pie').length,images:[...document.images].map(i=>({src:i.currentSrc||i.src,alt:i.getAttribute('alt'),ok:i.complete&&i.naturalWidth>0,naturalWidth:i.naturalWidth,rect:rect(i)})),anchors,numbered,groups:[...document.querySelectorAll('.menu-group-label')].map(x=>x.textContent.trim()),bookSpec:[...document.querySelectorAll('.k')].map(k=>({k:k.textContent.trim(),v:k.nextElementSibling?.textContent?.trim()||''})),excerpt:Boolean(document.querySelector('#extracto-libro')),excerptLangs:[...document.querySelectorAll('#extracto-libro [lang]')].map(x=>x.lang),sundayCount:document.querySelector('[data-sunday-count]')?.textContent?.trim()||null,sundayTiles,sundayGrid:rect(grid),styleIds:[...document.querySelectorAll('style[id]')].map(x=>x.id)};
  });
  d.status=resp?.status()||null;d.consoleErrors=consoleErrors;d.pageErrors=pageErrors;
  if(withAxe){const ax=await new AxeBuilder({page}).analyze();d.axe=ax.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length,help:v.help}));}
  await page.close();return d;
}

try{
  if(!ACCOUNT||!TOKEN||!TARGET)throw new Error('Missing final audit environment');

  // Wait for the exact final main commit to become Cloudflare production, then verify public origin fingerprint.
  let project=null,latest=null,matched=false;
  for(let attempt=1;attempt<=90;attempt++){
    project=await cf(`/accounts/${ACCOUNT}/pages/projects/oolita`);
    const deployments=await cf(`/accounts/${ACCOUNT}/pages/projects/oolita/deployments?env=production&per_page=10`);
    latest=Array.isArray(deployments)?deployments[0]:null;
    const hash=latest?.deployment_trigger?.metadata?.commit_hash||project?.canonical_deployment?.deployment_trigger?.metadata?.commit_hash||null;
    if(hash===TARGET&&latest?.latest_stage?.status==='success'){matched=true;break;}
    await sleep(10000);
  }
  report.deployment.latest=dep(latest);report.deployment.canonical=dep(project?.canonical_deployment);
  pass(report.deployment,'exact_main_is_production',matched,{target:TARGET,latest:dep(latest)});
  pass(report.deployment,'production_branch_main',project?.production_branch==='main',project?.production_branch||null);

  const d1cfg=project?.deployment_configs?.production?.d1_databases||{};
  report.cloudflare.pages_config={compatibility_date:project?.deployment_configs?.production?.compatibility_date||null,compatibility_flags:project?.deployment_configs?.production?.compatibility_flags||[],d1_databases:d1cfg,analytics_engine_datasets:project?.deployment_configs?.production?.analytics_engine_datasets||null};
  const cfgString=JSON.stringify(d1cfg);
  pass(report.cloudflare,'d1_binding',cfgString.includes('OOLITA_SUBSCRIBERS')&&cfgString.includes(DB),d1cfg);
  pass(report.cloudflare,'tracing_observability_clean',!JSON.stringify(project?.deployment_configs?.production||{}).toLowerCase().includes('observability')&&!JSON.stringify(project?.deployment_configs?.production||{}).toLowerCase().includes('tracing'),'No Pages production observability/tracing field');
  const wrangler=await fs.readFile('wrangler.toml','utf8');
  pass(report.cloudflare,'wrangler_clean',!/^\s*\[observability\]/m.test(wrangler)&&wrangler.includes('binding = "OOLITA_SUBSCRIBERS"')&&wrangler.includes(DB),'wrangler.toml has D1 production binding and no [observability] table');
  const health=await fetch(`${BASE}/api/subscribe?health=1`,{headers:{'Cache-Control':'no-cache'}});pass(report.cloudflare,'live_d1_health',health.status===204,`HTTP ${health.status}`);

  const sources={};for(const p of ['/','/en/','/ediciones/libro/','/en/editions/book/','/domingos/','/en/sundays/'])sources[p]=await fetchText(BASE+p+`?audit=${Date.now()}`);
  pass(report.deployment,'latest_main_live_fingerprint',sources['/en/'].text.includes('oolita-home-overlay-reset-v1')&&sources['/'].text.includes('oolita-home-overlay-reset-v1'),'Latest-main homepage overlay-reset marker is live in EN and ES');

  const browser=await chromium.launch({headless:true});
  try{
    const enDesk=await inspect(browser,'/en/',1280,900,false),esDesk=await inspect(browser,'/',1280,900,false),enBookDesk=await inspect(browser,'/en/editions/book/',1280,900,false),esBookDesk=await inspect(browser,'/ediciones/libro/',1280,900,false);
    const c=report.corrections;
    pass(c,'english_dates',enDesk.bodyText.includes('3 Jan 2027')&&enDesk.bodyText.includes('9 Aug 26')&&!/\b03\.01\.(?:27|2027)\b/.test(enDesk.bodyText),{sample:(enDesk.bodyText.match(/.{0,70}3 Jan 2027.{0,90}/)||[])[0]||null});
    pass(c,'follow_loading_honeypot',sources['/en/'].text.includes('data-follow-status aria-live="polite" hidden')&&sources['/en/'].text.includes('class="follow-honeypot" hidden aria-hidden="true"')&&sources['/'].text.includes('class="follow-honeypot" hidden aria-hidden="true"'));
    pass(c,'homepage_opening',enDesk.bodyText.includes('OOLITA begins with a three-metre classical labyrinth')&&esDesk.bodyText.includes('OOLITA comienza con un laberinto clásico de tres metros'));
    pass(c,'fable_cat',enBookDesk.bodyText.includes('The fable follows a real cat')&&esBookDesk.bodyText.includes('La fábula sigue a un gato de verdad'));
    pass(c,'free_3_january_reading',enDesk.bodyText.includes('From 3 January the whole book can be read free inside the 3D world')&&esDesk.bodyText.includes('Desde el 3 de enero se podrá leer entero, gratis, dentro del mundo 3D'));
    pass(c,'exists_now',enDesk.bodyText.includes('The stone labyrinth is already at Los Escullos')&&esDesk.bodyText.includes('El laberinto de piedra ya está en Los Escullos'));
    pass(c,'bilingual_excerpt_illustration',enBookDesk.excerpt&&esBookDesk.excerpt&&enBookDesk.excerptLangs.includes('es')&&enBookDesk.excerptLangs.includes('en')&&enBookDesk.images.some(i=>/laberinto|labyrinth|Electro/i.test(i.alt||''))&&esBookDesk.images.some(i=>/laberinto|labyrinth|Electro/i.test(i.alt||'')));
    pass(c,'sundays_archive',sources['/en/sundays/'].text.includes('id="sunday-field"')&&sources['/domingos/'].text.includes('id="sunday-field"'));
    pass(c,'navigation_hierarchy',['Read and understand','Elsewhere','Project'].every(x=>enDesk.groups.includes(x))&&['Leer y entender','Fuera de este sitio','Proyecto'].every(x=>esDesk.groups.includes(x)),{en:enDesk.groups,es:esDesk.groups});

    // Real mobile viewports.
    for(const [lang,path] of [['en','/en/'],['es','/']]){
      report.mobile[lang]=[];
      for(const width of [360,390,412]){
        const d=await inspect(browser,path,width,844,width===390);
        report.mobile[lang].push({width,innerWidth:d.innerWidth,scrollWidth:d.scrollWidth,overflow:d.overflow,outside:d.outside,collisions:d.collisions,header:d.header,hero:d.hero,footer:d.footer,footerOverlaps:d.footerOverlaps,yearStyle:d.yearStyle,axe:d.axe||[],consoleErrors:d.consoleErrors,pageErrors:d.pageErrors});
      }
    }
    const en390=report.mobile.en.find(x=>x.width===390);
    pass(report.mobile,'english_2027_line_gone',en390?.yearStyle?.text==='2027'&&en390.yearStyle.textDecoration==='none'&&en390.yearStyle.before==='none'&&en390.yearStyle.after==='none'&&!/transparent|rgba\(0, 0, 0, 0\)/.test(en390.yearStyle.background||''),en390?.yearStyle||null);
    pass(report.mobile,'english_spacing_overflow',report.mobile.en.every(x=>x.innerWidth===x.width&&!x.overflow&&x.outside.length===0&&x.collisions.length===0),report.mobile.en.map(x=>({width:x.width,innerWidth:x.innerWidth,scrollWidth:x.scrollWidth,outside:x.outside,collisions:x.collisions})));
    pass(report.mobile,'spanish_spacing_overflow',report.mobile.es.every(x=>x.innerWidth===x.width&&!x.overflow&&x.outside.length===0&&x.collisions.length===0),report.mobile.es.map(x=>({width:x.width,innerWidth:x.innerWidth,scrollWidth:x.scrollWidth,outside:x.outside,collisions:x.collisions})));
    pass(report.mobile,'footer_layout',[...report.mobile.en,...report.mobile.es].every(x=>x.footer&&x.footer.left>=-1&&x.footer.right<=x.innerWidth+1&&x.footerOverlaps.length===0),[...report.mobile.en,...report.mobile.es].map(x=>({width:x.width,footer:x.footer,overlaps:x.footerOverlaps})));

    // Signup end-to-end on final production.
    const apiPost=async payload=>{const r=await fetch(`${BASE}/api/subscribe`,{method:'POST',headers:{'Content-Type':'application/json','Origin':BASE},body:JSON.stringify(payload)});let body={};try{body=await r.json();}catch{}return{status:r.status,body};};
    const invalid=await apiPost({email:'not-an-email',language:'en',consent:true,website:'',source_path:'/en/',interests:[]});
    const bot=await apiPost({email:botEmail,language:'en',consent:true,website:'https://bot.invalid',source_path:'/en/',interests:[]});
    const formPage=await browser.newPage({viewport:{width:390,height:844}});await formPage.goto(`${BASE}/en/?finalsignup=${Date.now()}`,{waitUntil:'networkidle'});
    const runtime=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),statusHidden:document.querySelector('[data-follow-status]')?.hidden,buttonDisabled:document.querySelector('.follow-submit')?.disabled,honeypotHidden:document.querySelector('.follow-honeypot')?.hidden}));
    let delayed=false;await formPage.route('**/api/subscribe',async route=>{if(route.request().method()==='POST'&&!delayed){delayed=true;await sleep(600);return route.continue();}return route.continue();});
    await formPage.fill('input[name="email"]',auditEmail);await formPage.check('input[name="consent"]');await formPage.click('button[type="submit"]');
    await formPage.waitForFunction(()=>document.querySelector('[data-follow-status]')?.textContent?.includes('Saving'));
    const saving=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),disabled:document.querySelector('.follow-submit')?.disabled}));
    await formPage.waitForFunction(()=>document.querySelector('[data-follow-status]')?.textContent?.includes('You’re in'));
    const success=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),disabled:document.querySelector('.follow-submit')?.disabled}));
    const existing=await apiPost({email:auditEmail,language:'en',consent:true,website:'',source_path:'/en/',interests:['book','field']});
    const row=(await d1('SELECT email,status,verified_at,unsubscribed_at,language,interests FROM subscribers WHERE email = ?',[auditEmail]))?.results||[];
    const botRow=(await d1('SELECT email FROM subscribers WHERE email = ?',[botEmail]))?.results||[];
    await formPage.unroute('**/api/subscribe');await formPage.route('**/api/subscribe',async route=>{if(route.request().method()==='POST')return route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({ok:false,error:'audit_simulated'})});return route.continue();});
    await formPage.fill('input[name="email"]','ui-error-final@example.com');await formPage.check('input[name="consent"]');await formPage.click('button[type="submit"]');await formPage.waitForFunction(()=>document.querySelector('[data-follow-status]')?.textContent?.includes('We could not save this'));
    const errorState=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),disabled:document.querySelector('.follow-submit')?.disabled}));await formPage.close();
    report.signup={invalid,bot,runtime,saving,success,existing,stored:row[0]||null,botStored:botRow.length,errorState};
    pass(report.signup,'invalid_email',invalid.status===400&&invalid.body?.error==='invalid_email',invalid);
    pass(report.signup,'honeypot',bot.status===200&&bot.body?.state==='recorded'&&botRow.length===0,{response:bot,stored:botRow.length});
    pass(report.signup,'loading_state',runtime.status==='List active · choose what you want to follow.'&&runtime.statusHidden===false&&runtime.buttonDisabled===false&&runtime.honeypotHidden===true,runtime);
    pass(report.signup,'saving_state',saving.status==='Saving…'&&saving.disabled===true,saving);
    pass(report.signup,'success_state',/You’re in/.test(success.status||'')&&success.disabled===false,success);
    pass(report.signup,'valid_signup',row[0]?.status==='active',{row:row[0]||null});
    pass(report.signup,'existing_subscriber',existing.status===200&&existing.body?.state==='active',existing);
    pass(report.signup,'error_state',/We could not save this/.test(errorState.status||'')&&errorState.disabled===false,errorState);
    pass(report.signup,'double_opt_in_enabled',row[0]?.status!=='active'||row[0]?.verified_at!=null,{status:row[0]?.status||null,verified_at:row[0]?.verified_at??null,note:'Current implementation is single opt-in if status is active immediately with verified_at NULL.'});

    // Books final mobile/content.
    const enBook=await inspect(browser,'/en/editions/book/',390,844,true),esBook=await inspect(browser,'/ediciones/libro/',390,844,true);
    report.books={en:{status:enBook.status,overflow:enBook.overflow,outside:enBook.outside,collisions:enBook.collisions,spec:enBook.bookSpec,axe:enBook.axe,badImages:enBook.images.filter(x=>!x.ok),bodySample:(enBook.bodyText.match(/.{0,80}31 (?:Jan|January).{0,120}/)||[])[0]||null},es:{status:esBook.status,overflow:esBook.overflow,outside:esBook.outside,collisions:esBook.collisions,spec:esBook.bookSpec,axe:esBook.axe,badImages:esBook.images.filter(x=>!x.ok)}};
    pass(report.books,'page_count_48',enBook.bookSpec.some(x=>/^Pages$/i.test(x.k)&&x.v==='48')&&esBook.bookSpec.some(x=>/^Páginas$/i.test(x.k)&&x.v==='48'),{en:enBook.bookSpec,es:esBook.bookSpec});
    pass(report.books,'bilingual_excerpt',enBook.excerpt&&esBook.excerpt&&enBook.excerptLangs.includes('es')&&enBook.excerptLangs.includes('en'));
    pass(report.books,'cat_fable',enBook.bodyText.includes('The fable follows a real cat')&&esBook.bodyText.includes('La fábula sigue a un gato de verdad'));
    pass(report.books,'dates_availability',/31 (?:Jan|January) (?:27|2027)/.test(enBook.bodyText)&&/31(?: de)? enero(?: de)? 2027/i.test(esBook.bodyText)&&!/31\.01\.27/.test(enBook.bodyText),{en:(enBook.bodyText.match(/.{0,90}31 (?:Jan|January) (?:27|2027).{0,130}/)||[])[0]||null,es:(esBook.bodyText.match(/.{0,90}31(?: de)? enero(?: de)? 2027.{0,130}/i)||[])[0]||null});
    pass(report.books,'mobile_clean',!enBook.overflow&&!esBook.overflow&&enBook.outside.length===0&&esBook.outside.length===0&&enBook.collisions.length===0&&esBook.collisions.length===0,{enOutside:enBook.outside,esOutside:esBook.outside,enCollisions:enBook.collisions,esCollisions:esBook.collisions});
    pass(report.books,'images_loaded',enBook.images.every(x=>x.ok)&&esBook.images.every(x=>x.ok),{enBad:enBook.images.filter(x=>!x.ok),esBad:esBook.images.filter(x=>!x.ok)});

    // Sundays: exact schedule, count, links and mobile grid.
    const enSun=await inspect(browser,'/en/sundays/',390,844,true),esSun=await inspect(browser,'/domingos/',390,844,true);
    const dates=['2026-08-09','2026-08-16','2026-08-23','2026-08-30','2026-09-06','2026-09-13','2026-09-20','2026-09-27','2026-10-04','2026-10-11','2026-10-18','2026-10-25','2026-11-01','2026-11-08','2026-11-15','2026-11-22','2026-11-29','2026-12-06','2026-12-13','2026-12-20','2026-12-27','2027-01-03'];
    const expected=Date.now()<Date.parse('2026-08-23T17:00:00Z')?2:3;const active=enSun.sundayTiles.filter(x=>x.href);
    const activeStatuses=[];for(const x of active){const r=await fetch(new URL(x.href,BASE),{redirect:'follow'});activeStatuses.push({n:x.n,status:r.status,url:r.url});}
    report.sundays={expected,countEn:enSun.sundayCount,countEs:esSun.sundayCount,tiles:enSun.sundayTiles.map(x=>({n:x.n,date:x.date,href:x.href,current:x.current})),activeStatuses,gridEn:enSun.sundayGrid,gridEs:esSun.sundayGrid,overflowEn:enSun.overflow,overflowEs:esSun.overflow,outsideEn:enSun.outside,outsideEs:esSun.outside,axeEn:enSun.axe,axeEs:esSun.axe};
    pass(report.sundays,'count_correct',Number(enSun.sundayCount)===expected&&Number(esSun.sundayCount)===expected,{expected,en:enSun.sundayCount,es:esSun.sundayCount});
    pass(report.sundays,'dates_correct',enSun.sundayTiles.length===22&&enSun.sundayTiles.every((x,i)=>x.n===i+1&&x.date===dates[i]),enSun.sundayTiles.map(x=>({n:x.n,date:x.date})));
    pass(report.sundays,'published_open',active.length===expected&&activeStatuses.every(x=>x.status>=200&&x.status<400),activeStatuses);
    pass(report.sundays,'future_inactive',enSun.sundayTiles.every(x=>x.n<=expected?Boolean(x.href):!x.href),enSun.sundayTiles.map(x=>({n:x.n,href:Boolean(x.href)})));
    pass(report.sundays,'mobile_grid',!enSun.overflow&&!esSun.overflow&&enSun.outside.length===0&&esSun.outside.length===0&&enSun.sundayGrid?.right<=390.5&&esSun.sundayGrid?.right<=390.5,{en:enSun.sundayGrid,es:esSun.sundayGrid});

    // Navigation 01–14: all linked numbers and grouping.
    const wanted=Array.from({length:14},(_,i)=>String(i+1).padStart(2,'0'));const ens=new Set(enDesk.numbered.map(x=>x.n)),ess=new Set(esDesk.numbered.map(x=>x.n));
    report.navigation={en:enDesk.numbered,es:esDesk.numbered,enGroups:enDesk.groups,esGroups:esDesk.groups};
    pass(report.navigation,'numbers_01_14',wanted.every(n=>ens.has(n)&&ess.has(n)),{missingEn:wanted.filter(n=>!ens.has(n)),missingEs:wanted.filter(n=>!ess.has(n)),en:enDesk.numbered,es:esDesk.numbered});
    pass(report.navigation,'groups_clear',['Read and understand','Elsewhere','Project'].every(x=>enDesk.groups.includes(x))&&['Leer y entender','Fuera de este sitio','Proyecto'].every(x=>esDesk.groups.includes(x)),{en:enDesk.groups,es:esDesk.groups});

    // Site-wide internal crawl plus representative SEO/accessibility/image/header/footer checks.
    const sitemap=await fetchText(`${BASE}/sitemap.xml`);const locs=[...sitemap.text.matchAll(/<loc>\s*([^<]+)\s*<\/loc>/gi)].map(m=>m[1].trim());
    const key=['/','/en/','/ediciones/libro/','/en/editions/book/','/domingos/','/en/sundays/','/laberinto/','/en/labyrinth/','/sobre-oolita/','/en/about/'];
    const reps=[];const internal=new Set(locs);
    for(const p of key){const d=await inspect(browser,p,390,844,true);reps.push({path:p,status:d.status,title:d.title,description:d.description,canonical:d.canonical,hreflang:d.hreflang,h1:d.h1,headers:d.headers,footers:d.footers,overflow:d.overflow,outside:d.outside,badImages:d.images.filter(i=>!i.ok),missingAlt:d.images.filter(i=>i.alt===null),axe:d.axe,consoleErrors:d.consoleErrors,pageErrors:d.pageErrors});for(const a of d.anchors){try{const u=new URL(a.href);if(u.origin===BASE&&!u.hash)internal.add(u.href);}catch{}}}
    const statuses=[];for(const url of internal){try{const r=await fetch(url,{redirect:'follow'});statuses.push({url,status:r.status,final:r.url});}catch(e){statuses.push({url,status:0,error:String(e).slice(0,200)});}}
    const robots=await fetchText(`${BASE}/robots.txt`);const severe=reps.flatMap(r=>(r.axe||[]).filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>({path:r.path,...v})));
    report.quality={sitemapStatus:sitemap.status,sitemapCount:locs.length,internalCount:statuses.length,broken:statuses.filter(x=>x.status<200||x.status>=400),representative:reps,robotsStatus:robots.status,robotsHasSitemap:/sitemap:/i.test(robots.text),severeAccessibility:severe};
    pass(report.quality,'broken_internal_links',report.quality.broken.length===0,report.quality.broken);
    pass(report.quality,'english_spanish_hreflang',reps.every(r=>r.hreflang.some(x=>x.lang==='es')&&r.hreflang.some(x=>x.lang==='en')),reps.filter(r=>!r.hreflang.some(x=>x.lang==='es')||!r.hreflang.some(x=>x.lang==='en')).map(r=>r.path));
    pass(report.quality,'seo_metadata',reps.every(r=>r.status===200&&r.title&&r.description&&r.canonical&&r.h1===1),reps.filter(r=>r.status!==200||!r.title||!r.description||!r.canonical||r.h1!==1).map(r=>({path:r.path,status:r.status,h1:r.h1,title:Boolean(r.title),description:Boolean(r.description),canonical:Boolean(r.canonical)})));
    pass(report.quality,'mobile_overflow',reps.every(r=>!r.overflow&&r.outside.length===0),reps.filter(r=>r.overflow||r.outside.length).map(r=>({path:r.path,overflow:r.overflow,outside:r.outside})));
    pass(report.quality,'forms_images',reps.every(r=>r.badImages.length===0&&r.missingAlt.length===0),reps.filter(r=>r.badImages.length||r.missingAlt.length).map(r=>({path:r.path,badImages:r.badImages.length,missingAlt:r.missingAlt.length})));
    pass(report.quality,'header_footer_consistency',reps.every(r=>r.headers===1&&r.footers===1),reps.filter(r=>r.headers!==1||r.footers!==1).map(r=>({path:r.path,headers:r.headers,footers:r.footers})));
    pass(report.quality,'javascript_clean',reps.every(r=>r.consoleErrors.length===0&&r.pageErrors.length===0),reps.filter(r=>r.consoleErrors.length||r.pageErrors.length).map(r=>({path:r.path,console:r.consoleErrors,page:r.pageErrors})));
    pass(report.quality,'accessibility_no_serious_critical',severe.length===0,severe);
    pass(report.quality,'robots_sitemap',robots.status===200&&/sitemap:/i.test(robots.text),{status:robots.status});
  }finally{await browser.close();}
}catch(e){report.errors.push(String(e?.stack||e));}
finally{try{if(ACCOUNT&&TOKEN)await d1('DELETE FROM subscribers WHERE email IN (?, ?)',[auditEmail,botEmail]);}catch(e){report.errors.push(`D1 cleanup failed: ${String(e)}`);}}

await fs.mkdir('audit-results',{recursive:true});await fs.writeFile('audit-results/final-production-audit.json',JSON.stringify(report,null,2));
const lines=[`# OOLITA final production audit`,`Generated: ${report.generated_at}`,`Target main: ${TARGET}`,''];
for(const [sec,obj] of Object.entries(report)){if(!obj||typeof obj!=='object'||Array.isArray(obj)||sec==='errors')continue;const items=Object.entries(obj).filter(([,v])=>v&&typeof v==='object'&&'pass'in v);if(!items.length)continue;lines.push(`## ${sec}`);for(const [k,v] of items)lines.push(`${k}: ${v.pass?'PASS':'FAIL'}${v.detail!==null?` — ${typeof v.detail==='string'?v.detail:JSON.stringify(v.detail)}`:''}`);lines.push('');}
lines.push('## Errors',...(report.errors.length?report.errors:['None']));await fs.writeFile('audit-results/final-production-audit.md',lines.join('\n'));
