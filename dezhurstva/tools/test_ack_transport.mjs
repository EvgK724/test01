// No real Google traffic. Exercises exact frontend functions in a sandbox.
import fs from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const source = fs.readFileSync(fileURLToPath(new URL('./template.html', import.meta.url)), 'utf8');
const functions = source.slice(source.indexOf('function ackKey('), source.indexOf('function pendingAcks(')) +
  source.slice(source.indexOf('function statusPills('), source.indexOf('function monthGen(')) +
  source.slice(source.indexOf('function finalAckNotices('), source.indexOf('function newReceiptId(')) +
  source.slice(source.indexOf('function newReceiptId('), source.indexOf('function badge()'));
function harness() {
  const data = new Map(), requests = []; let nonce = 0;
  const ctx = {
    state:{me:'alpha'}, D:{months:{'2026-12':{status:'preliminary',version:1,title:'Synthetic',
      confirm:{need:['alpha','beta'],confirmed:[],digest:'a'.repeat(64),receiptIds:[]}}}},
    C:{form:{action:'https://example.invalid/form',entry:'entry.synthetic'}},
    store:{get:k=>data.get(k),set:(k,v)=>data.set(k,v)},
    ackNote:{},ackNo:{},ackEditing:{},ackBusy:new Set(),URLSearchParams,Date,JSON,Uint8Array,
    crypto:{getRandomValues:b=>{b.fill(++nonce);return b;}},AbortController,setTimeout,clearTimeout,
    nameOf:x=>x,toast(){},render(){},badge(){},copy(){},MK:['2026-12'],esc:x=>String(x).replaceAll('<','&lt;'),
    fetch:(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}))
  };
  vm.createContext(ctx);vm.runInContext(functions,ctx);
  return {ctx,data,requests,month:ctx.D.months['2026-12']};
}
function payload(request){return JSON.parse(request.options.body.get('entry.synthetic').split('#DEZH ')[1]);}
async function resolve(h,p){h.requests.at(-1).resolve({type:'opaque',status:0});await p;}
test('pending saved before await, captured identity survives navigation',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true),key=h.ctx.ackKey('2026-12','alpha');
  assert.equal(h.data.has(key),true);h.ctx.state.me='beta';await resolve(h,p);
  assert.equal(h.data.has(h.ctx.ackKey('2026-12','beta')),false);
  assert.equal(payload(h.requests[0]).who,'alpha');
});
test('opaque response is pending, never a received agreement',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  assert.equal(h.ctx.ackState('2026-12').done,false);assert.equal(h.ctx.ackState('2026-12').pending,true);
});
test('only exact anonymous receipt acknowledges this submission',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  h.month.confirm.receiptIds=['unrelated'];assert.equal(h.ctx.ackState('2026-12').done,false);
  h.month.confirm.receiptIds=[payload(h.requests[0]).receiptId];assert.equal(h.ctx.ackState('2026-12').done,true);
});
test('old public agreement never hides a newer local pending refusal',async()=>{
  const h=harness();h.month.confirm.confirmed=['alpha'];h.ctx.ackNote[h.ctx.ackKey('2026-12')]='Synthetic reason';
  const p=h.ctx.sendAck('2026-12',false);await resolve(h,p);
  assert.equal(h.ctx.ackState('2026-12').ok,false);assert.equal(h.ctx.ackState('2026-12').pending,true);
});
test('parallel double click makes one POST only',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await h.ctx.sendAck('2026-12',true);
  assert.equal(h.requests.length,1);await resolve(h,p);
});
test('retry uses identical receipt ID and client timestamp',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  const q=h.ctx.sendAck('2026-12',true,true);await resolve(h,q);
  assert.deepEqual(payload(h.requests[0]),payload(h.requests[1]));
});
test('new answer, even same choice, has a new receipt ID',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  const q=h.ctx.sendAck('2026-12',true);await resolve(h,q);
  assert.notEqual(payload(h.requests[0]).receiptId,payload(h.requests[1]).receiptId);
});
test('network failure retains unknown delivery and permits retry',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);h.requests[0].reject(Error('offline'));await p;
  assert.equal(h.ctx.ackState('2026-12').transport,'uncertain');assert.equal(h.ctx.ackState('2026-12').done,false);
  assert.equal(h.ctx.ackBusy.size,0);
});
test('wrong identity, final status or absent digest cannot submit',async()=>{
  for(const change of [h=>h.ctx.state.me='outsider',h=>h.month.status='final',h=>delete h.month.confirm.digest]){
    const h=harness();change(h);await h.ctx.sendAck('2026-12',true);assert.equal(h.requests.length,0);
  }
});
test('new revision does not inherit a local response',async()=>{
  const h=harness(),p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  h.month.confirm.digest='b'.repeat(64);assert.equal(h.ctx.ackState('2026-12').pending,undefined);
});
test('negative reply requires note belonging to selected doctor',async()=>{
  const h=harness();h.ctx.ackNote[h.ctx.ackKey('2026-12','beta')]='Different person';
  await h.ctx.sendAck('2026-12',false);assert.equal(h.requests.length,0);
});
test('received pending note remains local; public data needs no who/choice map',async()=>{
  const h=harness();h.ctx.ackNote[h.ctx.ackKey('2026-12')]='Private synthetic note';
  const p=h.ctx.sendAck('2026-12',false);await resolve(h,p);
  h.month.confirm.receiptIds=[payload(h.requests[0]).receiptId];
  assert.equal(h.ctx.ackState('2026-12').done,true);assert.equal(h.ctx.ackState('2026-12').ok,false);
  assert.equal(JSON.stringify(h.month).includes('Private synthetic note'),false);
});
test('count-only snapshot does not identify a selected doctor as agreed',()=>{
  const h=harness();h.month.confirm.confirmed=['alpha'];h.month.confirm.agreedCount=1;
  assert.equal(h.ctx.ackState('2026-12').done,false);
  h.month.confirm.confirmed=[];assert.equal(h.ctx.agreedCount(h.month.confirm),1);
  assert.match(h.ctx.statusPills('2026-12'),/согласий 1 из 2/);
});
test('no per-doctor receipt map is needed to acknowledge this local submission',async()=>{
  const h=harness();h.month.confirm.agreedCount=1;h.month.confirm.confirmed=[];
  const p=h.ctx.sendAck('2026-12',true);await resolve(h,p);
  h.month.confirm.receiptIds=[payload(h.requests[0]).receiptId];
  assert.equal(h.ctx.ackState('2026-12').done,true);
  assert.equal(h.ctx.ackState('2026-12').ok,true);
});
test('finalizing clears receipts but does not hide this device negative response',async()=>{
  const h=harness();h.ctx.ackNote[h.ctx.ackKey('2026-12')]='Private objection';
  const p=h.ctx.sendAck('2026-12',false);await resolve(h,p);
  h.month.status='final';h.month.confirm.receiptIds=[];h.month.confirm.confirmed=['alpha','beta'];
  const notice=h.ctx.finalAckNotices();
  assert.match(notice,/На этом устройстве сохранён ответ «Не согласен»/);
  assert.doesNotMatch(notice,/Private objection|получено|учтено|alpha/);
});
test('another selected doctor cannot see the local final objection',async()=>{
  const h=harness();h.ctx.ackNote[h.ctx.ackKey('2026-12')]='Private objection';
  const p=h.ctx.sendAck('2026-12',false);await resolve(h,p);
  h.month.status='final';h.ctx.state.me='beta';assert.equal(h.ctx.finalAckNotices(),'');
});
