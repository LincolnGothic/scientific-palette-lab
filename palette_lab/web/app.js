'use strict';
const $ = (q, root=document) => root.querySelector(q);
const $$ = (q, root=document) => [...root.querySelectorAll(q)];
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validHex = value => /^#[0-9a-f]{6}$/i.test(value);
const safeUrl = value => { try { const u=new URL(value); return u.protocol==='https:' ? escape(u.href) : ''; } catch { return ''; } };
const option = (v, text, selected) => `<option value="${escape(v)}" ${String(v)===String(selected)?'selected':''}>${escape(text)}</option>`;
const fmt = n => Number(n).toLocaleString();
const percent = n => `${(100*n).toFixed(1)}%`;
let state=null, view='atlas', kind='data', dataset='real', renderVersion=0, selectedPanel='', activeResults=[], jobTimer=null;
const drafts = new Map();
const filters = {journal:'',year:'',count:'',palette_type:'',threshold:8,include_manuscripts:false};
const recOptions = {count:4,palette_type:'categorical',background:'#FFFFFF',locked:'',cvd_filter:false,include_references:true};
const pageInfo = {
  atlas:['THE RESEARCH PALETTE ATLAS','Color, with context.','Discover how color is used in scientific figures, with a source behind every palette.','Palette atlas'],
  recommend:['FROM EVIDENCE TO YOUR NEXT FIGURE','Find your next palette.','Choose the encoding, set your constraints, and preview colors in context.','Recommendations'],
  review:['HUMAN REVIEW · TRUSTWORTHY COUNTS','Make every color count.','Confirm the panel, its intended colors, and article eligibility before analysis.','Review queue'],
  collect:['BUILD YOUR RESEARCH CORPUS','Start with the source.','Collect a bounded sample of open-access papers from the three flagship journals.','Collect articles'],
  methods:['TRANSPARENT BY DESIGN','Know what is counted.','Inspect the scope, extraction assumptions, and ranking definitions.','Methods & sources']
};
async function api(path, body) {
  let response;
  try {response=await fetch(path, body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
  catch {throw new Error('The local application is unavailable. Restart it with bash run.sh, then reload this page.');}
  const result=await response.json();
  if(!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}
function toast(message, error=false) {
  const el=$('#toast');el.textContent=message;el.hidden=false;el.classList.toggle('error',error);
  clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.hidden=true,7000);
}
function query(values) { return new URLSearchParams(Object.entries(values).filter(([,v])=>v!=='' && v!==null && v!==undefined)).toString(); }
async function refresh() {
  state=await api(`/api/state?dataset=${dataset}`);
  $('#queueBadge').textContent=state.overview.pending;
  $('#demoBanner').hidden=dataset!=='demo';
  $('#datasetNote').textContent=dataset==='demo'?'Illustrative examples only. No journal findings.':'Only reviewed, eligible panels enter the rankings.';
  if(state.jobs.some(j=>j.status==='running') && !jobTimer) jobTimer=setInterval(pollJobs,2000);
}
async function pollJobs() {
  try {
    const next=await api(`/api/state?dataset=${dataset}`);state=next;$('#queueBadge').textContent=state.overview.pending;
    if(view==='collect') updateJobs();
    if(!state.jobs.some(j=>j.status==='running')) {clearInterval(jobTimer);jobTimer=null;toast('Collection finished. Inspect the report and review the imported panels.');if(view==='collect') render();}
  } catch(error) {clearInterval(jobTimer);jobTimer=null;toast(error.message,true);}
}
function empty(title, description, actions='') {
  return `<div class="empty"><div class="empty-mark"><i></i><i></i><i></i></div><h2>${escape(title)}</h2><p>${escape(description)}</p><div class="actions">${actions}</div></div>`;
}
function summary(data) {
  const o=state.overview;
  return `<div class="summary-grid">${[
    ['Collected papers',o.papers,'Candidates in this dataset'],
    ['Reviewed panels',o.reviewed,`${o.pending} awaiting visual review`],
    ['Analyzed papers',data.analyzed_papers,'Eligible papers in current filters'],
    ['Palette families',data.families.length,kind==='data'?'Data encodings grouped separately':'Colors grouped by diagram role']
  ].map(([label,n,sub])=>`<div class="summary-card"><div class="label">${label}</div><div class="number">${fmt(n)}</div><div class="sub">${escape(sub)}</div></div>`).join('')}</div>`;
}
function filterBar() {
  const years=[...new Set(state.panels.map(p=>p.year))].sort((a,b)=>b-a);
  const types=kind==='data'?[['categorical','Categorical'],['sequential','Sequential'],['diverging','Diverging']]:[['roles','Role-based']];
  return `<div class="filters"><div class="field"><label for="filterJournal">Journal</label><select id="filterJournal" data-filter="journal">${option('','All journals',filters.journal)}${state.journals.map(j=>option(j,j,filters.journal)).join('')}</select></div>
    <div class="field"><label for="filterYear">Publication year</label><select id="filterYear" data-filter="year">${option('','All years',filters.year)}${years.map(y=>option(y,y,filters.year)).join('')}</select></div>
    <div class="field"><label for="filterCount">Colors</label><select id="filterCount" data-filter="count">${option('','All counts',filters.count)}${Array.from({length:8},(_,i)=>i+1).map(n=>option(n,`${n} colors`,filters.count)).join('')}</select></div>
    <div class="field"><label for="filterType">Encoding</label><select id="filterType" data-filter="palette_type">${option('','All encodings',filters.palette_type)}${types.map(([v,t])=>option(v,t,filters.palette_type)).join('')}</select></div>
    <div class="field"><label for="filterThreshold">Similarity · ΔE76</label><input id="filterThreshold" data-filter="threshold" type="number" min="0" max="25" step="1" value="${filters.threshold}" title="0 = exact colors. Higher values merge more visually similar palettes."></div>
    <label class="check" title="Accepted manuscripts can differ from published figures and are excluded by default."><input type="checkbox" data-filter="include_manuscripts" ${filters.include_manuscripts?'checked':''}> Include accepted manuscripts</label>
    <div class="export-actions"><a class="button small" href="/api/export.csv?${query({...filters,kind,dataset})}">↓ CSV</a><a class="button small" href="/api/export.json?${query({...filters,kind,dataset})}">↓ JSON</a></div></div>`;
}
function textColor(hex) {
  const channels=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722 > .3 ? '#17243A' : '#FFFFFF';
}
function preview(colors, flow=false, ptype='categorical', background='#FFFFFF') {
  const values=colors.map(c=>c.hex).filter(validHex);
  if(!values.length) return '';
  if(flow) {
    const fills=colors.filter(c=>['fill','decision','group'].includes(c.role));
    const drawFills=fills.length?fills:colors;
    const connector=colors.find(c=>c.role==='connector')?.hex||'#64748B';
    return `<svg viewBox="0 0 300 100" aria-label="Flowchart role preview" role="img"><rect width="300" height="100" fill="${background}"/>${[0,1,2].map((i)=>{const c=drawFills[i%drawFills.length];const x=5+i*101;return `${i<2?`<path d="M${x+78} 49h22m-5-4 5 4-5 4" stroke="${connector}" fill="none" stroke-width="1.5"/>`:''}${c.role==='decision'?`<path d="M${x+39} 17l39 32-39 32-39-32z" fill="${c.hex}" stroke="${connector}"/>`:`<rect x="${x}" y="26" width="78" height="47" rx="7" fill="${c.hex}" stroke="${connector}"/>`}<text x="${x+39}" y="52" text-anchor="middle" font-size="9" fill="${textColor(c.hex)}">${c.role==='decision'?'Decision':`Process ${i+1}`}</text>`}).join('')}<text x="150" y="96" text-anchor="middle" font-size="7" fill="#8490A1">ROLE-BASED DIAGRAM · ADAPTIVE LABEL TEXT</text></svg>`;
  }
  if(ptype!=='categorical') {
    return `<svg viewBox="0 0 300 100" aria-label="Ordered color ramp preview" role="img"><rect width="300" height="100" fill="${background}"/>${values.map((c,i)=>`<rect x="${10+i*280/values.length}" y="25" width="${280/values.length+.3}" height="42" fill="${c}"/>`).join('')}<text x="10" y="82" font-size="8" fill="#8490A1">Low</text><text x="280" y="82" font-size="8" fill="#8490A1">High</text></svg>`;
  }
  const widths=230/values.length;
  return `<svg viewBox="0 0 300 100" aria-label="Categorical bar chart preview" role="img"><rect width="300" height="100" fill="${background}"/><path d="M24 8v76h258" stroke="#9BA8B7" stroke-width=".8" fill="none"/>${[24,44,64].map(y=>`<path d="M25 ${y}h257" stroke="#D8E0EC" stroke-width=".5"/>`).join('')}${values.map((c,i)=>{const h=25+(i*17)%48;return `<rect x="${35+i*widths}" y="${84-h}" width="${widths*.64}" height="${h}" fill="${c}" rx="1"/>`;}).join('')}<text x="153" y="98" text-anchor="middle" font-size="7" fill="#8490A1">SAMPLE VALUES · PALETTE PREVIEW ONLY</text></svg>`;
}
function paletteCard(row, index, recommending=false) {
  const reference=row.origin==='reference';
  const simulated=$('#simulationMode')?.value||'normal';
  const shown=simulated!=='normal' && row.metrics?.simulations?.[simulated] ? row.colors.map((c,i)=>({...c,hex:row.metrics.simulations[simulated].colors[i]})) : row.colors;
  const title=row.name||`Palette family ${row.id.slice(0,6)}`;
  return `<article class="palette-card"><div class="palette-top"><span class="rank">${recommending?'RECOMMENDATION':'RANK'} ${String(index+1).padStart(2,'0')}</span><span class="palette-tag ${reference?'reference':'observed'}">${reference?'REFERENCE':dataset==='demo'?'SYNTHETIC':'OBSERVED'}</span></div>
    <div class="swatch-strip">${shown.map(c=>`<span style="background:${c.hex}" title="${escape(c.hex)} · ${escape(c.role)}"></span>`).join('')}</div>
    <div class="palette-info"><h3 class="palette-name">${escape(title)}</h3><div class="palette-meta">${row.count||new Set(row.colors.map(c=>c.hex)).size} colors · ${escape(row.palette_type|| (kind==='flowchart'?'roles':recOptions.palette_type))}${row.exact_variants?` · ${row.exact_variants} exact variant${row.exact_variants===1?'':'s'}`:''}</div></div>
    <div class="mini-preview">${preview(shown,kind==='flowchart',row.palette_type||recOptions.palette_type,recommending?recOptions.background:'#FFFFFF')}</div>
    <div class="hex-list">${row.colors.map(c=>`<code title="${escape(c.role)}">${c.hex}</code>`).join('')}</div>
    ${row.warnings?.length?`<div class="warning-list">${row.warnings.map(escape).join('<br>')}</div>`:''}
    <div class="palette-bottom"><div class="prevalence">${reference?'Reference':percent(row.prevalence)}<small>${reference?'Not included in usage statistics':`${row.paper_count}/${row.paper_denominator} papers · ${row.panel_count} panels`}</small></div><div class="copy-group"><button class="button small" data-action="copy" data-index="${index}" title="Copy HEX colors">Copy</button><button class="button small" data-action="code" data-index="${index}" title="Download plotting code">Code</button></div></div>
    ${reference?`<div class="sources"><span class="reference-note">${row.reference_url?`<a href="${safeUrl(row.reference_url)}" target="_blank" rel="noopener">Reference source ↗</a>`:'Illustrative palette, not mined from a publication.'}</span></div>`:`<details class="sources"><summary>Inspect ${row.sources.length} source panel${row.sources.length===1?'':'s'}</summary>${row.sources.slice(0,30).map(s=>`<p><b>${escape(s.journal)} · ${s.year}</b> · ${escape(s.label)} · ${escape(s.version_type||'')}<br>${escape(s.title)}<br>${safeUrl(s.url)?`<a href="${safeUrl(s.url)}" target="_blank" rel="noopener">Source paper ↗</a> · `:''}<button class="icon-button" data-action="source-review" data-panel="${s.panel_id}">Review panel</button></p>`).join('')}</details>`}
  </article>`;
}
async function renderAtlas(version) {
  const data=await api(`/api/statistics?${query({...filters,kind,dataset})}`);
  if(version!==renderVersion) return;
  activeResults=data.families;
  $('#content').innerHTML=summary(data)+filterBar()+`<div class="section-heading"><div><h2>${kind==='data'?'Data-chart palettes':'Flowchart palettes'}</h2><p>Ranked by paper-level prevalence within each encoding and color count</p></div><span class="count-badge">${data.families.length} families</span></div>`+
    (data.families.length?`<div class="palette-grid">${data.families.map((r,i)=>paletteCard(r,i)).join('')}</div>`:empty('Your palette atlas starts here.',state.overview.pending?'Imported panels are waiting for review. Confirm their colors and article eligibility to build the rankings.':'Collect open-access figures, review their palettes, and discover the most common combinations in your corpus.',`<button class="button primary" data-view="${state.overview.pending?'review':'collect'}">${state.overview.pending?'Review imported panels':'Collect your first articles'}</button><button class="button" data-action="demo">Try synthetic examples</button>`))+
    `<p class="caption-note">${escape(data.denominator)} ${escape(data.warning)} Palette families use a ${data.threshold} ΔE76 similarity threshold; set 0 for exact matching. Percentages across different color counts have different denominators.</p>`+
    (data.individual_colors.length?`<div class="section-heading"><div><h2>Individual colors</h2><p>Exact HEX values, counted once per paper and panel</p></div></div><div class="individual-colors">${data.individual_colors.slice(0,18).map(c=>`<div class="color-chip"><i style="background:${c.hex}"></i><span class="mono">${c.hex}</span><small>${c.papers} papers</small></div>`).join('')}</div>`:'');
}
async function renderRecommendations(version) {
  const options={...recOptions,kind,dataset,journal:filters.journal,year:filters.year,threshold:filters.threshold,include_manuscripts:filters.include_manuscripts};
  const data=await api(`/api/recommend?${query(options)}`);
  if(version!==renderVersion) return;
  activeResults=data.recommendations;
  $('#content').innerHTML=`<div class="notice">${kind==='flowchart'?'Flowchart palettes count unique colors across node fills, decisions, borders, labels, and connectors. The preview uses diagram roles and adapts label text for readability.':'Categorical palettes distinguish groups. Sequential and diverging palettes preserve the reviewed order of colors.'} Reference palettes are labeled separately from observed publication palettes.</div>
    <div class="card recommend-settings"><div class="field"><label for="recCount">Number of colors</label><select id="recCount" data-rec="count">${[3,4,5,6,7,8].map(n=>option(n,`${n} colors`,recOptions.count)).join('')}</select></div>
    ${kind==='data'?`<div class="field"><label for="recType">Data encoding</label><select id="recType" data-rec="palette_type">${['categorical','sequential','diverging'].map(t=>option(t,t[0].toUpperCase()+t.slice(1),recOptions.palette_type)).join('')}</select></div>`:''}
    <div class="field"><label for="recBackground">Background</label><input id="recBackground" data-rec="background" type="color" value="${recOptions.background}"></div>
    <div class="field"><label for="recLocked">Required color · exact HEX</label><input id="recLocked" data-rec="locked" placeholder="#0072B2" value="${escape(recOptions.locked)}" maxlength="7"></div>
    <label class="check"><input type="checkbox" data-rec="cvd_filter" ${recOptions.cvd_filter?'checked':''}> Filter simulated color collisions</label>
    <label class="check"><input type="checkbox" data-rec="include_references" ${recOptions.include_references?'checked':''}> Include reference palettes</label>
    <div class="field"><label for="simulationMode">Preview vision</label><select id="simulationMode"><option value="normal">Normal vision</option><option value="protanopia">Protanopia approximation</option><option value="deuteranopia">Deuteranopia approximation</option><option value="tritanopia">Tritanopia approximation</option></select></div></div>
    <div class="section-heading"><div><h2>${data.recommendations.length} palette${data.recommendations.length===1?'':'s'} for your figure</h2><p>Popularity and readability are separate considerations</p></div><span class="count-badge">${kind==='flowchart'?'DIAGRAM ROLES':recOptions.palette_type.toUpperCase()}</span></div>
    <div id="recommendGrid" class="palette-grid">${data.recommendations.map((r,i)=>paletteCard(r,i,true)).join('')}</div>
    ${!data.recommendations.length?empty('No palettes match these constraints.','Review more panels, enable reference palettes, or relax the required color or simulated-separation filter.'):''}
    <p class="caption-note">${escape(data.method)} Score: 55% observed prevalence, 30% simulated separation for categories/fills, 15% background contrast. Reference palettes have no observed prevalence and receive a small ranking penalty. Simulations are approximations; inspect your actual figure. Use line styles or markers alongside color.</p>`;
}
function currentPanel() {return state.panels.find(p=>p.id===selectedPanel);}
function draftFor(p) {
  if(!drafts.has(p.id) || drafts.get(p.id).revision!==p.revision) drafts.set(p.id,{revision:p.revision,kind:p.kind,palette_type:p.palette_type,colors:structuredClone(p.colors),notes:p.notes,eligibility:p.eligibility,confirmed_experimental:p.eligibility==='included'});
  return drafts.get(p.id);
}
function colorRows(d) {
  const roles=['unassigned','fill','border','text','connector','decision','group'];
  return d.colors.map((c,i)=>`<div class="color-row" data-color-row="${i}"><input aria-label="Color ${i+1} picker" type="color" data-color="${i}" data-color-field="picker" value="${c.hex}"><input aria-label="Color ${i+1} HEX" class="hex" maxlength="7" data-color="${i}" data-color-field="hex" value="${c.hex}">${d.kind==='flowchart'?`<select aria-label="Color ${i+1} role" data-color="${i}" data-color-field="role">${roles.map(r=>option(r,r,c.role)).join('')}</select>`:'<span class="small-label">Data color</span>'}<button class="icon-button" data-action="color-up" data-index="${i}" aria-label="Move color ${i+1} up">↑</button><button class="icon-button" data-action="color-remove" data-index="${i}" aria-label="Remove color ${i+1}">×</button></div>`).join('');
}
function updateColorEditor() {const p=currentPanel();if(p){const d=draftFor(p);$('#colorEditor').innerHTML=colorRows(d);$('#colorCount').textContent=`${new Set(d.colors.map(c=>c.hex)).size} unique colors`;}}
function renderReview() {
  if(!state.panels.length) {$('#content').innerHTML=empty('No figures to review yet.','Collect a small pilot or import a figure image to begin.',`<button class="button primary" data-view="collect">Collect articles</button>`);return;}
  if(!currentPanel()) selectedPanel=state.panels.find(p=>!p.reviewed)?.id||state.panels[0].id;
  const p=currentPanel(),d=draftFor(p),position=state.panels.findIndex(x=>x.id===p.id);
  $('#content').innerHTML=`<div class="review-nav"><button class="button small" data-action="review-prev" ${position===0?'disabled':''}>← Previous</button><select id="panelSelect" aria-label="Panel to review">${state.panels.map(x=>option(x.id,`${x.reviewed?'✓':'○'} ${x.journal} ${x.year} · ${x.label} · ${x.title.slice(0,60)}`,p.id)).join('')}</select><button class="button small" data-action="review-next" ${position===state.panels.length-1?'disabled':''}>Next →</button><span class="count-badge">${position+1} / ${state.panels.length}</span></div>
    <div class="review-layout"><section class="card"><div class="section-heading"><h2>${escape(p.label)}</h2><span class="source-pill">${p.reviewed?'REVIEWED':'AWAITING REVIEW'}</span></div><div class="review-source">${escape(p.journal)} · ${p.year} · ${escape(p.license||'License not recorded')} · <b>${escape(p.version_type)}</b><br>${escape(p.title)} ${safeUrl(p.source_url)?`<a href="${safeUrl(p.source_url)}" target="_blank" rel="noopener">Source ↗</a>`:''}</div>
    ${p.version_type==='accepted-manuscript'?'<div class="notice warning">Accepted manuscript, not final published figures. Excluded from standard rankings unless you explicitly enable accepted manuscripts in the atlas filters.</div>':''}
    <div class="image-frame"><canvas id="regionCanvas" aria-label="Figure image: drag a rectangle to choose an extraction region"></canvas></div><p class="help">Drag over a legend or data-mark region to extract its colors. The blue outline is the current panel; the orange outline is the extraction region.</p>
    <div class="review-controls"><label class="small-label" for="regionBox">Region · pixels</label><input class="region" id="regionBox" value="${escape(JSON.stringify(p.extraction_bbox||p.bbox))}"><button class="button small" data-action="reset-region">Full panel</button></div>
    <div class="review-controls"><label class="check"><input id="includeNeutrals" type="checkbox"> Include black / gray</label><button class="button primary small" data-action="extract">Extract colors</button><button class="button small" data-action="suggest-split">Suggest panel split</button></div>
    <div id="splitControls" hidden><p class="help">Inspect these full-image coordinates. Replace with your own non-overlapping boxes if needed. Splitting replaces the current panel and resets its review status.</p><textarea id="splitBoxes" rows="4" style="width:100%"></textarea><button class="button small" data-action="split">Apply panel regions</button></div>
    <details class="panel-caption"><summary>Figure caption</summary>${escape(p.caption)}</details></section>
    <section class="card"><h2>Review the palette</h2><p>Confirm the encoding and remove colors that belong to annotations or other panels.</p>
    <div class="notice">${escape(p.suggestion.reason)}${p.suggestion.kind!=='unknown'?` Suggested: ${escape(p.suggestion.kind)}.`:''}</div>
    <div class="form-grid"><div class="field"><label for="reviewKind">Figure category</label><select id="reviewKind" data-draft="kind">${[['unknown','Select category'],['data','Data chart'],['flowchart','Flowchart'],['other','Other / exclude panel']].map(([v,t])=>option(v,t,d.kind)).join('')}</select></div>
    <div class="field"><label for="reviewType">Palette encoding</label><select id="reviewType" data-draft="palette_type">${(d.kind==='flowchart'?['roles']:d.kind==='data'?['unknown','categorical','sequential','diverging']:['unknown']).map(t=>option(t,t[0].toUpperCase()+t.slice(1),d.palette_type)).join('')}</select></div></div>
    <div class="section-heading"><span class="small-label" id="colorCount">${new Set(d.colors.map(c=>c.hex)).size} unique colors</span><button class="button small" data-action="color-add">＋ Add color</button></div><div id="colorEditor" class="color-editor">${colorRows(d)}</div>
    <p class="help">For ordered ramps, move colors into low-to-high order. For diagrams, assign every color a role; the same HEX may have multiple role entries.</p>
    ${p.extraction.flags?.length?`<div class="notice warning">${p.extraction.flags.map(escape).join('<br>')}</div>`:''}
    <div class="review-footer"><div class="field"><label for="paperEligibility">Article eligibility · applies to all panels in this paper</label><select id="paperEligibility" data-draft="eligibility">${[['pending','Not yet confirmed'],['included','Include in the study'],['excluded','Exclude from the study']].map(([v,t])=>option(v,t,d.eligibility)).join('')}</select></div>
    <label class="check"><input type="checkbox" data-draft="confirmed_experimental" ${d.confirmed_experimental?'checked':''}> ${dataset==='demo'?'This is a synthetic demonstration, kept outside publication results.':'I checked that this is original experimental research and that this panel belongs in the main-figure study.'}</label>
    <div class="field"><label for="reviewNotes">Review notes</label><textarea id="reviewNotes" data-draft="notes" placeholder="Uncertain shades, transparency, excluded annotations…">${escape(d.notes)}</textarea></div><button class="button primary" data-action="approve">Save reviewed panel →</button></div></section></div>`;
  initCanvas(p);
}
function initCanvas(p) {
  const canvas=$('#regionCanvas'),context=canvas.getContext('2d'),image=new Image();
  let selection=p.extraction_bbox||p.bbox, start=null, ratio=1;
  function draw() {context.clearRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);for(const [box,color] of [[p.bbox,'#315FCE'],[selection,'#D98B34']]) {context.strokeStyle=color;context.lineWidth=2;context.strokeRect(box[0]*ratio,box[1]*ratio,(box[2]-box[0])*ratio,(box[3]-box[1])*ratio);}}
  image.onload=()=>{ratio=Math.min(1,1000/image.width);canvas.width=Math.round(image.width*ratio);canvas.height=Math.round(image.height*ratio);draw();};
  image.src='/'+p.asset_path;
  function point(event) {const rect=canvas.getBoundingClientRect();return [Math.max(0,Math.min(p.width,Math.round((event.clientX-rect.left)/rect.width*p.width))),Math.max(0,Math.min(p.height,Math.round((event.clientY-rect.top)/rect.height*p.height)))];}
  canvas.addEventListener('pointerdown',event=>{start=point(event);canvas.setPointerCapture(event.pointerId);});
  canvas.addEventListener('pointermove',event=>{if(!start)return;const end=point(event);selection=[Math.min(start[0],end[0]),Math.min(start[1],end[1]),Math.max(start[0],end[0]),Math.max(start[1],end[1])];draw();});
  canvas.addEventListener('pointerup',()=>{if(start){if(selection[2]>selection[0]&&selection[3]>selection[1]) $('#regionBox').value=JSON.stringify(selection);start=null;}});
  canvas.addEventListener('pointercancel',()=>{start=null;});
  $('#regionBox').addEventListener('change',()=>{try{const v=JSON.parse($('#regionBox').value);if(v.length===4){selection=v;draw();}}catch{toast('Enter four region coordinates in a JSON array.',true);}});
}
function renderCollect() {
  const jobs=state.jobs;
  $('#content').innerHTML=`<div class="notice">Discovery uses Europe PMC. Main figure assets come from the official PMC S3 service. Availability differs by journal and field; this collector does not claim complete publisher coverage.</div>
    <div class="two-col"><section class="card"><h2>Collect open-access research</h2><p>Begin with a small pilot. Imported figures remain unreviewed and experimental eligibility remains pending.</p><form id="collectForm"><div class="form-grid"><div class="field"><label for="startYear">Start year</label><input id="startYear" name="start_year" type="number" min="1900" max="2100" value="2021" required></div><div class="field"><label for="endYear">End year</label><input id="endYear" name="end_year" type="number" min="1900" max="2100" value="2025" required></div><div class="field wide"><label for="collectionLimit">Maximum records scanned per journal</label><input id="collectionLimit" name="limit" type="number" min="1" max="10000" value="5" required><p class="help">This is a scan limit, not a guaranteed number of eligible papers. Date-descending pilots are not representative samples.</p></div></div><div class="small-label">Journals</div><div class="checks">${state.journals.map(j=>`<label class="check"><input type="checkbox" name="journal" value="${j}" checked>${j}</label>`).join('')}</div><div class="field" style="margin-bottom:15px"><label for="collectPmcids">Specific PMCIDs · optional</label><input id="collectPmcids" name="pmcids" placeholder="PMC12456302, PMC…"><p class="help">Explicit identifiers are still checked against journal, dates, and open-access scope.</p></div><label class="check" style="margin-bottom:17px"><input type="checkbox" name="include_manuscripts"> Also retrieve licensed accepted manuscripts</label><p class="help">Manuscripts are tagged and excluded from final-version rankings by default. Published figures may differ.</p><button class="button primary" type="submit" ${jobs.some(j=>j.status==='running')?'disabled':''}>↓ Start collection</button></form><div id="jobStatus"></div></section>
    <section class="card"><h2>Import a figure image</h2><p>Use a figure you already have. Enter its publication metadata so its palette remains traceable.</p><form id="importForm"><div class="form-grid"><div class="field"><label for="importJournal">Journal</label><select name="journal" id="importJournal">${state.journals.map(j=>option(j,j,'Nature')).join('')}</select></div><div class="field"><label for="importYear">Publication year</label><input name="year" id="importYear" type="number" min="1900" max="2100" value="2025" required></div><div class="field wide"><label for="importTitle">Paper title</label><input name="title" id="importTitle" required></div><div class="field"><label for="importDoi">DOI · optional</label><input name="doi" id="importDoi" placeholder="10.…"></div><div class="field"><label for="importLicense">License / reuse note</label><input name="license" id="importLicense" placeholder="CC BY 4.0"></div><div class="field wide"><label for="importCaption">Figure caption · optional</label><textarea name="caption" id="importCaption" rows="2"></textarea></div><div class="field wide"><label for="importImage">PNG, JPEG, or TIFF · up to 16 MB</label><input name="file" id="importImage" type="file" accept="image/png,image/jpeg,image/tiff" required></div></div><button class="button" type="submit">＋ Import to review queue</button></form></section></div>
    <div class="collection-log card"><h2>Collection history</h2><p>Query scope, scan counts, retrieval gaps, and errors are saved with each run.</p>${state.overview.runs.length?state.overview.runs.map(r=>`<details><summary>${escape(r.created_at.slice(0,19).replace('T',' '))} UTC · ${r.config.start_year}–${r.config.end_year} · ${r.config.limit_per_journal} records / journal</summary><table class="coverage-table"><thead><tr><th>Journal</th><th>Available OA records</th><th>Scanned</th><th>Papers with figures</th><th>New figures</th><th>Skipped</th></tr></thead><tbody>${Object.entries(r.report.journals).map(([j,c])=>`<tr><td>${j}</td><td>${c.available_oa_records??'Unavailable'}</td><td>${c.scanned}</td><td>${c.papers_with_figures}</td><td>${c.new_figures}</td><td>${c.skipped}</td></tr>`).join('')}</tbody></table>${r.report.errors.length?`<pre class="job-box" style="white-space:pre-wrap">${escape(JSON.stringify(r.report.errors,null,2))}</pre>`:''}</details>`).join(''):'<p>No collection runs yet.</p>'}</div>`;
  updateJobs();
}
function updateJobs() {
  if(!$('#jobStatus')) return;
  $('#jobStatus').innerHTML=state.jobs.map(j=>`<div class="job-box"><span class="small-label">${escape(j.status.replaceAll('_',' ').toUpperCase())}</span><p>${escape(j.message)}</p>${j.report?.errors.length?`<details><summary>${j.report.errors.length} reported issues</summary><pre>${escape(JSON.stringify(j.report.errors,null,2))}</pre></details>`:''}</div>`).join('');
}
function renderMethods() {
  $('#content').innerHTML=`<div class="method-grid"><section class="card"><h2>Study scope</h2><p>Only the flagship <b>Nature, Science, and Cell</b> journals, identified by print/electronic ISSN. Default publication window: 2021–2025. Main figures only; supplementary and extended-data figures are excluded when identified in JATS.</p><p>Metadata identifies research-article candidates. A human must confirm original experimental eligibility. Repository discovery covers an accessible OA subset, with potential field and access bias.</p></section>
    <section class="card"><h2>Two distinct visual languages</h2><p><b>Data charts:</b> categorical colors, ordered sequential ramps, or ordered diverging ramps. Backgrounds, labels, and axes are excluded unless they encode data.</p><p><b>Flowcharts:</b> node fills, decisions, borders, text, connectors, and grouping colors. Matching preserves reviewed color roles. Preview label text may be adapted for contrast.</p></section>
    <section class="card"><h2>Extraction and human review</h2><ol><li>Retrieve original figure assets with captions and source identifiers.</li><li>Propose whitespace panel boundaries; inspect and edit them.</li><li>Select a chart or legend region. Recover a weighted RGB histogram and merge nearby colors in CIELAB.</li><li>Correct colors, gradient order, and diagram roles. Add meaningful black/gray when needed.</li><li>Approve classification and article eligibility.</li></ol><p>This version uses raster estimates and caption keyword suggestions. It does not have a trained visual classifier, OCR legend segmentation, or vector/PDF extraction. Image pixels cannot always recover original HEX values.</p></section>
    <section class="card"><h2>Popularity and grouping</h2><p>Primary prevalence: papers using a palette family ÷ included papers with at least one reviewed panel of the same figure kind, palette encoding, and color count, within the selected filters. Panels from a paper do not multiply its paper-level vote.</p><p>Families use complete-link grouping and minimum bottleneck ΔE76 matching. Every palette in a family must be within the threshold of every other palette. The displayed representative is an actual observed palette. Ordered ramps retain order; flowcharts retain roles. Set ΔE76 to 0 for exact matching.</p><p>Different color counts have different denominators. Multiple families in one paper can make prevalence totals exceed 100%.</p></section>
    <section class="card"><h2>Recommendation baseline</h2><p>Retrieve observed palettes containing 3–8 unique colors. Rank using prevalence, simulated color separation, and background contrast. Optional named reference palettes are never counted as observed journal usage.</p><p>Protanopia, deuteranopia, and tritanopia previews use full-dichromacy matrices from the Machado et al. simulation approach. They are approximations, not a guarantee of accessibility. Small marks, background contrast, and redundant markers still require inspection.</p><p>The corpus is not yet sufficient for claims of a trained recommender. A future learned model should be evaluated with paper-level train/test separation.</p></section>
    <section class="card"><h2>Sources and reproducibility</h2><ul><li><a href="https://europepmc.org/RestfulWebService" target="_blank" rel="noopener">Europe PMC search API</a></li><li><a href="https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/" target="_blank" rel="noopener">Current PMC S3 dataset documentation</a></li><li><a href="https://pmc-oa-opendata.s3.amazonaws.com/README.txt" target="_blank" rel="noopener">PMC S3 structure and version metadata</a></li><li><a href="https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html" target="_blank" rel="noopener">Machado et al. color vision simulation</a></li><li><a href="https://www.nature.com/articles/s41467-020-19160-7" target="_blank" rel="noopener">The misuse of colour in science communication</a></li></ul><p>Local SQLite records preserve article metadata, source URLs, license, image SHA-256, version, extraction parameters, and review snapshots. CSV and JSON exports preserve the selected scope and grouping threshold. The app is not endorsed by the journals or NLM.</p></section></div>`;
}
async function render() {
  const version=++renderVersion;
  const [eyebrow,title,description,name]=pageInfo[view];
  $('#pageEyebrow').textContent=eyebrow;$('#pageTitle').textContent=title;$('#pageDescription').textContent=description;$('#breadcrumb').textContent=name;
  $$('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.view===view));
  $$('[data-kind]').forEach(el=>el.classList.toggle('active',el.dataset.kind===kind));
  $('.workspace-tools').hidden=['collect','methods'].includes(view);
  $('#kindNote').textContent=kind==='data'?'Colors encode categories or numeric values.':'Colors communicate diagram roles and hierarchy.';
  $('#content').innerHTML='<div class="loading">Loading your workspace…</div>';
  try {if(view==='atlas') await renderAtlas(version);else if(view==='recommend') await renderRecommendations(version);else if(view==='review') renderReview();else if(view==='collect') renderCollect();else renderMethods();}
  catch(error) {if(version===renderVersion) $('#content').innerHTML=`<div class="error-block">${escape(error.message)}</div>`;}
}
async function downloadCode(row) {
  let content,filename;
  const values=row.colors.map(c=>c.hex);
  if(kind==='flowchart') {content=JSON.stringify({kind:'flowchart',origin:row.origin||'observed',colors:row.colors,notes:'Colors map to diagram roles. Verify text/fill contrast in the final figure.'},null,2);filename='flowchart-palette.json';}
  else {
    const ptype=row.palette_type||recOptions.palette_type;
    const literal=JSON.stringify(values);
    content=`# Scientific Palette Lab · ${row.origin||'observed'} palette\n# ${dataset==='demo'?'SYNTHETIC DEMO: not a journal finding':row.origin==='reference'?'Reference colors, not observed journal frequency':`Source family: ${row.id}`}\ncolors = ${literal}\n\n`;
    if(ptype==='categorical') content+='import matplotlib.pyplot as plt\nfrom cycler import cycler\nplt.rcParams["axes.prop_cycle"] = cycler(color=colors)\n# Keep group-to-color assignments consistent across figures.\n';
    else content+='from matplotlib.colors import LinearSegmentedColormap\ncmap = LinearSegmentedColormap.from_list("reviewed_palette", colors)\n# Verify value mapping and the midpoint for diverging data.\n';
    filename='chart-palette.py';
  }
  const url=URL.createObjectURL(new Blob([content],{type:'text/plain'}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');if(!button || button.disabled) return;
  if(button.dataset.view) {try{view=button.dataset.view;await refresh();await render();}catch(error){toast(error.message,true);}return;}
  if(button.dataset.kind) {kind=button.dataset.kind;filters.palette_type='';await render();return;}
  const action=button.dataset.action;if(!action) return;
  button.disabled=true;
  try {
    const p=currentPanel();
    if(action==='demo') {await api('/api/demo',{});dataset='demo';$('#dataset').value=dataset;await refresh();view='atlas';await render();}
    else if(action==='copy') {const row=activeResults[Number(button.dataset.index)];await navigator.clipboard.writeText(row.colors.map(c=>c.hex).join(', '));toast('HEX colors copied.');}
    else if(action==='code') await downloadCode(activeResults[Number(button.dataset.index)]);
    else if(action==='source-review') {selectedPanel=button.dataset.panel;view='review';await render();}
    else if(action==='review-prev'||action==='review-next') {const i=state.panels.findIndex(x=>x.id===selectedPanel);selectedPanel=state.panels[i+(action==='review-next'?1:-1)].id;renderReview();}
    else if(action==='color-add') {draftFor(p).colors.push({hex:'#0072B2',role:'unassigned',weight:0});updateColorEditor();}
    else if(action==='color-remove') {draftFor(p).colors.splice(Number(button.dataset.index),1);updateColorEditor();}
    else if(action==='color-up') {const d=draftFor(p),i=Number(button.dataset.index);if(i>0)[d.colors[i-1],d.colors[i]]=[d.colors[i],d.colors[i-1]];updateColorEditor();}
    else if(action==='reset-region') {$('#regionBox').value=JSON.stringify(p.bbox);$('#regionBox').dispatchEvent(new Event('change'));}
    else if(action==='extract') {const bbox=JSON.parse($('#regionBox').value);await api('/api/extract',{panel_id:p.id,bbox,include_neutrals:$('#includeNeutrals').checked,threshold:filters.threshold||8});drafts.delete(p.id);await refresh();renderReview();toast('Color estimates ready. Confirm them before saving.');}
    else if(action==='suggest-split') {const result=await api('/api/suggest-panels',{panel_id:p.id});$('#splitBoxes').value=JSON.stringify(result.boxes,null,2);$('#splitControls').hidden=false;toast(result.warning);}
    else if(action==='split') {const result=await api('/api/split',{panel_id:p.id,boxes:JSON.parse($('#splitBoxes').value)});drafts.delete(p.id);selectedPanel=result.panel_ids[0];await refresh();renderReview();toast('Panel regions saved. Review each region separately.');}
    else if(action==='approve') {const d=draftFor(p);await api('/api/review',{panel_id:p.id,...d});drafts.delete(p.id);await refresh();selectedPanel=state.panels.find(x=>!x.reviewed)?.id||p.id;renderReview();toast('Review saved. Only included, eligible panels enter the rankings.');}
  } catch(error) {toast(error.message,true);} finally {if(button.isConnected)button.disabled=false;}
});
document.addEventListener('change',async event=>{
  const target=event.target;
  try {
    if(target.id==='dataset') {dataset=target.value;selectedPanel='';await refresh();await render();}
    else if(target.dataset.filter) {filters[target.dataset.filter]=target.type==='checkbox'?target.checked:target.value;await render();}
    else if(target.dataset.rec) {const k=target.dataset.rec,v=target.type==='checkbox'?target.checked:target.value;if(['locked','background'].includes(k) && v && !validHex(v))throw new Error('Enter a six-digit HEX color.');recOptions[k]=v;await render();}
    else if(target.id==='simulationMode') {$('#recommendGrid').innerHTML=activeResults.map((r,i)=>paletteCard(r,i,true)).join('');}
    else if(target.id==='panelSelect') {selectedPanel=target.value;renderReview();}
    else if(target.dataset.draft) {const d=draftFor(currentPanel()),k=target.dataset.draft;d[k]=target.type==='checkbox'?target.checked:target.value;if(k==='kind'){d.palette_type=d.kind==='flowchart'?'roles':d.kind==='data'?'categorical':'unknown';renderReview();}}
    else if(target.dataset.color!==undefined) {const i=Number(target.dataset.color),field=target.dataset.colorField,d=draftFor(currentPanel());if(field==='role')d.colors[i].role=target.value;else{if(!validHex(target.value))throw new Error('Enter a six-digit HEX color.');d.colors[i].hex=target.value.toUpperCase();updateColorEditor();}}
  } catch(error) {toast(error.message,true);}
});
document.addEventListener('input',event=>{const target=event.target;if(target.dataset.draft && target.type!=='checkbox' && target.tagName!=='SELECT')draftFor(currentPanel())[target.dataset.draft]=target.value;});
document.addEventListener('submit',async event=>{
  event.preventDefault();const form=event.target,submit=$('button[type=submit]',form);if(submit)submit.disabled=true;
  try {
    const fd=new FormData(form);
    if(form.id==='collectForm') {await api('/api/collect',{start_year:Number(fd.get('start_year')),end_year:Number(fd.get('end_year')),limit:Number(fd.get('limit')),journals:fd.getAll('journal'),pmcids:String(fd.get('pmcids')||'').trim().split(/[\s,]+/).filter(Boolean),include_manuscripts:fd.get('include_manuscripts')==='on'});dataset='real';$('#dataset').value='real';await refresh();renderCollect();toast('Collection started. Progress and retrieval issues will appear here.');}
    else if(form.id==='importForm') {const file=fd.get('file');if(file.size>16_000_000)throw new Error('Choose an image under 16 MB.');const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});const values=Object.fromEntries([...fd.entries()].filter(([k])=>k!=='file'));await api('/api/import',{...values,image:data});dataset='real';$('#dataset').value='real';await refresh();selectedPanel=state.panels.find(p=>!p.reviewed)?.id||'';view='review';await render();toast('Image imported. Check the source metadata and palette.');}
  } catch(error) {toast(error.message,true);} finally {if(submit?.isConnected)submit.disabled=false;}
});
(async()=>{try{await refresh();await render();}catch(error){$('#content').innerHTML=`<div class="error-block">${escape(error.message)}</div>`;}})();
