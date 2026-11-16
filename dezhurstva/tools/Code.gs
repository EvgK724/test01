/* NOT DEPLOYED. Advanced Sheets API + readonly/external_request scopes required.
 * Names are self-declarations, not authenticated identities. No POST handler.
 */
const CONFIG = Object.freeze({
  sheetId: 'REPLACE_WITH_OWNER_APPROVED_PRIVATE_SHEET_ID',
  range: "'Form responses 1'!A1:B10001",
  scheduleUrl: 'https://raw.githubusercontent.com/EvgK724/test01/main/dezhurstva/data/schedule.json',
  // Explicit reviewed mappings ONLY: {month:{version,digest,notBefore,seed:[...]}}.
  // Empty deliberately: no implicit adoption of legacy confirmed arrays.
  legacy: {'2026-12': {version:1,digest:'d6c6cc87b4e3050466b0cef00caae7d2d8ab2497947c2d10c430145af028000f',notBefore:'2026-11-16T08:31:19Z',sourceCommit:'209c810e4408aba5b9484265f17ccd1304060514',seed:['klepikov'],acceptLegacy:false}},
  maxRows: 10000
});
function canonical(x) {
  if (Array.isArray(x)) return '[' + x.map(canonical).join(',') + ']';
  if (x && typeof x === 'object') return '{' + Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',') + '}';
  return JSON.stringify(x);
}
function sha(x) { return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,canonical(x),Utilities.Charset.UTF_8).map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join(''); }
function revision(month, data) {
  const copy=JSON.parse(JSON.stringify(month));
  delete copy.status; delete copy.final_at; delete copy.finalization; delete copy.confirm;
  copy.confirm={version:month.confirm.version,published:month.confirm.published,need:month.confirm.need};
  const doctors={};for(const who of month.confirm.need){if(!data.doctors[who])throw Error('doctor');doctors[who]=data.doctors[who];}
  return sha({month:copy,tz:data.tz,doctors});
}
function reduce(rows, monthKey, m, digest, now, legacy) {
  const need=m.confirm.need, latest={}, blocked=new Set(), seenIds={};
  if (!Array.isArray(need)||!need.length||new Set(need).size!==need.length) throw Error('roster');
  if (!Number.isInteger(m.confirm.version)||m.confirm.version<1||m.version!==m.confirm.version) throw Error('version');
  if (!Array.isArray(rows)||rows.length===0||rows.length>CONFIG.maxRows||rows[0][0]!=='Timestamp'||rows[0][1]!=='Пожелания') throw Error('source');
  const published=Date.parse(m.confirm.published); if(!Number.isFinite(published))throw Error('published');
  const mapping=legacy && legacy.version===m.confirm.version && legacy.digest===digest && /^[a-f0-9]{40}$/.test(legacy.sourceCommit||'') && legacy.notBefore===m.confirm.published && Number.isFinite(Date.parse(legacy.notBefore)) ? legacy : null;
  if(mapping) for(const who of mapping.seed||[]) {if(!need.includes(who))throw Error('seed');latest[who]={at:Date.parse(mapping.notBefore),votes:new Set([true])};}
  for(const row of rows.slice(1).sort((a,b)=>Date.parse(a[0])-Date.parse(b[0]))) {
    if(!row.length||!row[1])continue;
    const raw=String(row[1]);if(!raw.includes('#DEZH'))continue;
    const terminal=raw.match(/(?:^|\n)#DEZH ([^\r\n]+)\s*$/);
    if(!terminal)throw Error('missing terminal payload');
    let a;try{a=JSON.parse(terminal[1]);}catch{throw Error('malformed payload');}
    if(a.kind!=='ack')continue;
    if(a.m!==monthKey||a.ver!==m.confirm.version)continue;
    if(!need.includes(a.who))throw Error('unknown doctor');
    if(a.v!==1)throw Error('payload version');
    if(a.receiptId!==undefined){if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(a.receiptId))throw Error('receipt'); const sig=canonical([a.who,a.m,a.ver,a.digest,a.ok]);if(seenIds[a.receiptId]){if(seenIds[a.receiptId]!==sig)throw Error('duplicate receipt');continue;}seenIds[a.receiptId]=sig;}
    let at;
    // Read UNFORMATTED_VALUE dates: Sheets epoch serial, timezone handled by sheet metadata.
    // Adapter supplies normalized UTC receipt ISO instead; raw strings/serial are rejected here.
    at=Date.parse(row[0]);
    if(typeof row[0]!=='string'||!/^\d{4}-\d\d-\d\dT.*(?:Z|[+-]\d\d:\d\d)$/.test(row[0])||!Number.isFinite(at)||at>now) {blocked.add(a.who);continue;}
    const invalid=at<published||typeof a.ok!=='boolean'||(a.digest!==digest && !(mapping && mapping.acceptLegacy===true && !a.digest && at>=Date.parse(mapping.notBefore)));
    if(invalid){
      if(!latest[a.who]||at>latest[a.who].at)latest[a.who]={at,votes:new Set(),invalid:true};
      else if(at===latest[a.who].at)latest[a.who].invalid=true;
      continue;
    }
    if(!latest[a.who]||at>latest[a.who].at) latest[a.who]={at,votes:new Set([a.ok]),receiptId:a.receiptId};
    else if(at===latest[a.who].at) {latest[a.who].votes.add(a.ok);if(latest[a.who].receiptId!==a.receiptId)latest[a.who].invalid=true;}
  }
  let yes=0,no=0,ambiguous=blocked.size;const receiptIds=[];
  for(const who of need){if(blocked.has(who)||!latest[who])continue;const votes=latest[who].votes;if(latest[who].invalid||votes.size!==1)ambiguous++;else {if(votes.has(true)){yes++;}else no++;if(latest[who].receiptId)receiptIds.push(latest[who].receiptId);}}
  return {receiptIds:receiptIds.sort(),required:need.length,agreed:yes,disagreed:no,ambiguous,waiting:need.length-yes-no-ambiguous,allAgreed:yes===need.length&&no===0&&ambiguous===0};
}
function doGet(e) {
  let out={ok:false,error:'UNAVAILABLE'};
  try {
    const q=e.parameter||{};
    if(!/^20\d\d-(0[1-9]|1[0-2])$/.test(q.month||'')||!/^[-a-zA-Z0-9]{16,80}$/.test(q.nonce||''))throw Error('query');
    const response=UrlFetchApp.fetch(CONFIG.scheduleUrl,{followRedirects:false,muteHttpExceptions:true});
    if(response.getResponseCode()!==200)throw Error('schedule');
    const data=JSON.parse(response.getContentText()),m=data.months[q.month];
    if(!m||!['preliminary','final'].includes(m.status))throw Error('month');
    const digest=revision(m,data), now=Date.now();
    if(m.confirm.digest!==undefined&&m.confirm.digest!==digest)throw Error('republish version');
    const sheet=Sheets.Spreadsheets.get(CONFIG.sheetId,{fields:'properties(timeZone),sheets(properties(title,gridProperties(rowCount)))'});
    if(sheet.properties.timeZone!=='Asia/Yekaterinburg')throw Error('timezone');
    const tab=sheet.sheets.find(s=>s.properties.title==='Form responses 1');
    if(!tab||tab.properties.gridProperties.rowCount>CONFIG.maxRows)throw Error('sheet bound');
    const result=Sheets.Spreadsheets.Values.get(CONFIG.sheetId,CONFIG.range,{valueRenderOption:'UNFORMATTED_VALUE',dateTimeRenderOption:'SERIAL_NUMBER'});
    const rows=result.values||[];
    // Google Sheets serial is local wall time, here fixed UTC+5 (Yekaterinburg).
    const normalized=rows.map((r,i)=>i&&typeof r[0]==='number'?[new Date(Math.round((r[0]-25569)*86400000)-18000000).toISOString(),r[1]]:r);
    const state=reduce(normalized,q.month,m,digest,now,CONFIG.legacy[q.month]);
    out={ok:true,schema:1,identity:'self-declared',month:q.month,version:m.confirm.version,digest,rosterHash:sha(m.confirm.need),checkedAt:new Date(now).toISOString(),nonce:q.nonce,sourceComplete:true,...state};
  } catch (_) { /* No raw exception, rows, addresses or names returned/logged. */ }
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}
if(typeof module!=='undefined')module.exports={canonical,revision,reduce,CONFIG};
