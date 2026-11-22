'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const http=require('node:http');
const crypto=require('node:crypto');
const os=require('node:os');
const path=require('node:path');
const fs=require('node:fs');
const {spawn}=require('node:child_process');
const cli=path.resolve(__dirname,'../bin/keel.js');
function run(args,action="status"){return new Promise(resolve=>{const p=spawn(process.execPath,action==='tick'?[cli,'tick',...args]:[cli,'codex',action,...args]);let out='',err='';p.stdout.on('data',b=>out+=b);p.stderr.on('data',b=>err+=b);p.on('close',code=>resolve({code,out,err}));});}
test('managed CLI lifecycle, mailbox scheduling and frame boundaries',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'keel-host-'));const sock=path.join(dir,'host.sock');const requests=[];const requestDetails=[];const peers=[];const blank=new Set(),lost=new Set();let active=true,serial=0,uncertain=false,invalidHost=false,injectNotice=false,unloaded=false,resumeActive=false,resumeFails=false,resumeMismatch=false,readMismatch=false,resumeDelay=false,initNameFails=false;
 const server=http.createServer();server.on('upgrade',(req,s)=>{peers.push(s);s.on('end',()=>{for(const id of blank)lost.add(id);});s.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+crypto.createHash('sha1').update(req.headers['sec-websocket-key']+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64')+'\r\n\r\n');let initialized=false;let buf=Buffer.alloc(0);s.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);while(buf.length>=6){let n=buf[1]&127,off=2;if(n===126){if(buf.length<8)return;n=buf.readUInt16BE(2);off=4;}else if(n===127){if(buf.length<14)return;n=Number(buf.readBigUInt64BE(2));off=10;}if(buf.length<off+4+n)return;const mask=buf.subarray(off,off+4);const data=Buffer.from(buf.subarray(off+4,off+4+n));buf=buf.subarray(off+4+n);for(let i=0;i<data.length;i++)data[i]^=mask[i%4];const x=JSON.parse(data);requests.push(x.method);requestDetails.push(x);if(x.method==='initialized'){initialized=true;continue;}if(!x.id)continue;if(x.method!=='initialize'&&!initialized){s.destroy();return;}if(x.method==='thread/read'&&lost.has(x.params.threadId)){const b=Buffer.from(JSON.stringify({id:x.id,error:{message:'thread not loaded: '+x.params.threadId}}));s.write(Buffer.concat([Buffer.from([129,b.length]),b]));continue;}if(x.method==='thread/name/set'&&!initNameFails)blank.delete(x.params.threadId);if(x.method==='thread/name/set'&&initNameFails){const b=Buffer.from(JSON.stringify({id:x.id,error:{message:'fixture name persistence failure'}}));s.write(Buffer.concat([Buffer.from([129,b.length]),b]));continue;}if(x.method==='thread/resume'){if(resumeFails){const b=Buffer.from(JSON.stringify({id:x.id,error:{message:'fixture resume failure'}}));s.write(Buffer.concat([Buffer.from([129,b.length]),b]));continue;}unloaded=false;if(resumeActive)active=true;}const result=x.method==='initialize'?(invalidHost?{}:{userAgent:'test-host'}):x.method==='turn/start'?{turn:uncertain?{}:{id:'turn-fixture'}}:{thread:{id:x.method==='thread/start'?`fixture-thread-${++serial}`:(x.params.threadId||'fixture-thread'),status:{type:unloaded?'notLoaded':active?'active':'idle'},cwd:(x.method==='thread/read'&&readMismatch)||(x.method==='thread/resume'&&resumeMismatch)?'/wrong-worktree':dir}};if(x.method==='thread/start')blank.add(result.thread.id);const b=Buffer.from(JSON.stringify({id:x.id,result}));const h=b.length<126?Buffer.from([129,b.length]):Buffer.from([129,126,b.length>>8,b.length&255]);const split=Math.floor(b.length/2);const frame=(op,body)=>Buffer.concat([body.length<126?Buffer.from([op,body.length]):Buffer.from([op,126,body.length>>8,body.length&255]),body]);if(injectNotice){const notice=Buffer.from(JSON.stringify({id:x.id,method:'server/notice',params:{}}));s.write(frame(129,notice));}const reply=()=>{if(!s.destroyed)s.write(Buffer.concat([frame(1,b.subarray(0,split)),frame(128,b.subarray(split))]));};if(resumeDelay&&x.method==='thread/resume')setTimeout(reply,5500).unref();else reply();}});});
 await new Promise(r=>server.listen(sock,r));
 try{const x=await run(['--socket',sock,'--thread','fixture-thread','--json']);assert.equal(x.code,0,x.err);assert.equal(JSON.parse(x.out).thread.status.type,'active');assert.deepEqual(requests.filter(x=>x!=='initialized'),['initialize','thread/read']);
 active=false;const {spawnSync}=require('node:child_process');spawnSync('git',['init','-q',dir]);
 const reserved=await run(['--socket',sock,'--repo',dir,'--role','keel','--json'],'start');assert.notEqual(reserved.code,0);assert.equal(serial,0,'reserved role must be rejected before thread/start');
 fs.mkdirSync(path.join(dir,'.git/keel-chat'),{recursive:true});fs.writeFileSync(path.join(dir,'.git/keel-chat/renames.json'),JSON.stringify({'old-role':'new-role'}));const renamed=await run(['--socket',sock,'--repo',dir,'--role','old-role'],'start');assert.notEqual(renamed.code,0);assert.match(renamed.err,/renamed/);assert.equal(serial,0);
 const started=await run(['--socket',sock,'--repo',dir,'--role','test-role','--json'],'start');assert.equal(started.code,0,started.err);
 assert.equal(JSON.parse(started.out).role,'test-role');
 const again=await run(['--socket',sock,'--repo',dir,'--role','test-role'],'start');assert.notEqual(again.code,0);assert.match(again.err,/already|exists/);
 const own=await run(['--repo',dir,'--role','test-role','--json']);assert.equal(own.code,0,own.err);
  assert.deepEqual(requestDetails.find(x=>x.method==='thread/name/set')?.params,{threadId:'fixture-thread-1',name:'test-role'},'successful start must persist its original identity through native naming');
 assert.equal(requests.filter(x=>x==='thread/start').length,1);
 const message=['--repo',dir,'--role','test-role','--record','fixture-record','--text','Run keel chat unread','--json'];
 const sent=await run(message,'deliver');assert.equal(sent.code,0,sent.err);
 const duplicate=await run(message,'deliver');assert.equal(duplicate.code,0,duplicate.err);assert.equal(requests.filter(x=>x==='turn/start').length,1);
 active=true;const waiting=await run(['--repo',dir,'--role','test-role','--note','finish fixture','--json'],'handover');assert.equal(waiting.code,0,waiting.err);assert.equal(JSON.parse(waiting.out).state,'waiting');assert.equal(serial,1);
 active=false;const handed=await run(['--repo',dir,'--role','test-role','--note','finish fixture','--json'],'handover');assert.equal(handed.code,0,handed.err);assert.equal(serial,2);assert.ok(requestDetails.some(x=>x.method==='thread/name/set'&&x.params.threadId==='fixture-thread-2'&&x.params.name==='test-role'),'successor must be persisted before handover succeeds');
 const store=require('../src/core/chat/store');const where=store.requireLocation(dir);
 store.createGroup(where,'owner','team',['test-role']);
 store.writeRecord(where,{group:'team',kind:'message',from:'owner',mentions:['test-role'],text:'addressed fixture'});
 store.writeRecord(where,{group:'team',kind:'message',from:'owner',mentions:['test-role'],no_wake:true,text:'do not wake'});
 const beforeDrain=requests.filter(x=>x==='turn/start').length;
 const drained=await run(['--repo',dir,'--json'],'drain');assert.equal(drained.code,0,drained.err);assert.equal(requests.filter(x=>x==='turn/start').length,beforeDrain+1);
 const drainedAgain=await run(['--repo',dir,'--json'],'drain');assert.equal(drainedAgain.code,0,drainedAgain.err);assert.equal(requests.filter(x=>x==='turn/start').length,beforeDrain+1);
 const beforeTick=requests.filter(x=>x==='turn/start').length;
 store.writeRecord(where,{group:'team',kind:'message',from:'owner',mentions:['test-role'],text:'tick addressed fixture'});
 const ticked=await run(['--repo',dir,'--json'],'tick');assert.equal(ticked.code,0,ticked.err);assert.ok(JSON.parse(ticked.out).codex.some(x=>x.state==='delivered'));assert.equal(requests.filter(x=>x==='turn/start').length,beforeTick+1);
 uncertain=true;const failedMessage=['--repo',dir,'--role','test-role','--record','uncertain-record','--text','read pending','--json'];const failed=await run(failedMessage,'deliver');assert.notEqual(failed.code,0);const retried=await run(failedMessage,'deliver');assert.notEqual(retried.code,0);assert.match(retried.err,/unknown/);assert.equal(requests.filter(x=>x==='turn/start').length,4);
 const lock=path.join(dir,'.git/keel-chat/codex-roles/test-role.json.lock');fs.writeFileSync(lock,'owned by another process');const locked=await run(message,'deliver');assert.notEqual(locked.code,0);assert.equal(fs.readFileSync(lock,'utf8'),'owned by another process');fs.unlinkSync(lock);
 const registry=JSON.parse(fs.readFileSync(path.join(dir,'.git/keel-chat/codex-roles/test-role.json')));assert.equal(registry.history.length,1);assert.equal(registry.history[0].note,'finish fixture');

 uncertain=false;const large=await run(['--repo',dir,'--role','test-role','--record','large-record','--text','x'.repeat(70000),'--json'],'deliver');assert.equal(large.code,0,large.err);
 const raceBefore=requests.filter(x=>x==='turn/start').length;const raceArgs=['--repo',dir,'--role','test-role','--record','concurrent-record','--text','concurrent fixture','--json'];const raced=await Promise.all([run(raceArgs,'deliver'),run(raceArgs,'deliver')]);assert.ok(raced.some(x=>x.code===0));assert.equal(requests.filter(x=>x==='turn/start').length,raceBefore+1);
 // An unloaded owned thread is not an unrelated desktop session.
 const recoveryArgs=record=>['--repo',dir,'--role','test-role','--record',record,'--text','recovery round','--json'];
 const resumes=()=>requests.filter(x=>x==='thread/resume').length;
 const turns=()=>requests.filter(x=>x==='turn/start').length;
 unloaded=true;let rb=resumes(),tb=turns();
 const unloadedDuplicate=await run(recoveryArgs('large-record'),'deliver');assert.equal(unloadedDuplicate.code,0,unloadedDuplicate.err);assert.equal(JSON.parse(unloadedDuplicate.out).state,'already-delivered');assert.equal(resumes(),rb);assert.equal(turns(),tb);
 const recovered=await run(recoveryArgs('recovery-record'),'deliver');assert.equal(recovered.code,0,recovered.err);assert.equal(JSON.parse(recovered.out).state,'delivered');assert.equal(resumes(),rb+1);assert.equal(turns(),tb+1);assert.equal(serial,2);
 const resumeRequest=requestDetails.find(x=>x.method==='thread/resume');assert.deepEqual(resumeRequest.params,{threadId:'fixture-thread-2',serviceName:'keel'});
 unloaded=true;rb=resumes();tb=turns();const recoveredDuplicate=await run(recoveryArgs('recovery-record'),'deliver');assert.equal(recoveredDuplicate.code,0,recoveredDuplicate.err);assert.equal(resumes(),rb);assert.equal(turns(),tb);
 const unknown=await run(recoveryArgs('uncertain-record'),'deliver');assert.notEqual(unknown.code,0);assert.match(unknown.err,/unknown/);assert.equal(resumes(),rb);
 resumeActive=true;const busyRecovery=await run(recoveryArgs('busy-recovery'),'deliver');assert.equal(busyRecovery.code,0,busyRecovery.err);assert.equal(JSON.parse(busyRecovery.out).state,'waiting');assert.equal(turns(),tb);resumeActive=false;active=false;
 unloaded=true;resumeFails=true;const failedRecovery=await run(recoveryArgs('failed-recovery'),'deliver');assert.notEqual(failedRecovery.code,0);assert.match(failedRecovery.err,/fixture resume failure/);assert.equal(turns(),tb);resumeFails=false;
 unloaded=true;resumeMismatch=true;const mismatchRecovery=await run(recoveryArgs('mismatch-recovery'),'deliver');assert.notEqual(mismatchRecovery.code,0);assert.match(mismatchRecovery.err,/identity/);assert.equal(turns(),tb);resumeMismatch=false;
 unloaded=true;readMismatch=true;rb=resumes();const wrongRead=await run(recoveryArgs('wrong-read'),'deliver');assert.notEqual(wrongRead.code,0);assert.equal(resumes(),rb);readMismatch=false;
 unloaded=true;resumeDelay=true;const slowResume=await run(recoveryArgs('cold-recovery'),'deliver');assert.equal(slowResume.code,0,slowResume.err);unloaded=true;const explicitDeadline=await run([...recoveryArgs('short-deadline'),'--timeout','100'],'deliver');assert.notEqual(explicitDeadline.code,0);assert.match(explicitDeadline.err,/thread\/resume timeout/);resumeDelay=false;unloaded=true;rb=resumes();tb=turns();
 const wrongEndpoint=await run([...recoveryArgs('wrong-endpoint'),'--socket',path.join(dir,'other.sock')],'deliver');assert.notEqual(wrongEndpoint.code,0);assert.match(wrongEndpoint.err,/endpoint mismatch/);assert.equal(resumes(),rb);
 const roleFile=path.join(dir,'.git/keel-chat/codex-roles/test-role.json'),savedRole=fs.readFileSync(roleFile);fs.unlinkSync(roleFile);const notOwned=await run(recoveryArgs('not-owned'),'deliver');assert.notEqual(notOwned.code,0);assert.equal(resumes(),rb);fs.writeFileSync(roleFile,savedRole);
 const unloadedHandover=await run(['--repo',dir,'--role','test-role','--note','not an implicit resume'],'handover');assert.notEqual(unloadedHandover.code,0);assert.equal(resumes(),rb);assert.equal(serial,2);unloaded=false;
 injectNotice=true;const notified=await run(['--socket',sock,'--json']);assert.equal(notified.code,0,notified.err);assert.equal(JSON.parse(notified.out).host.userAgent,'test-host');injectNotice=false;
 invalidHost=true;const malformed=await run(['--socket',sock,'--json']);assert.notEqual(malformed.code,0);assert.match(malformed.err,/identity/i);invalidHost=false;
 const bad=await run(['--socket',path.join(dir,'missing'),'--timeout','100']);assert.notEqual(bad.code,0);assert.match(bad.err,/connect|ENOENT/i);
 initNameFails=true;active=false;const beforeFailedHandover=serial;const failedInitHandover=await run(['--repo',dir,'--role','test-role','--note','retain failed successor','--json'],'handover');assert.notEqual(failedInitHandover.code,0);assert.match(failedInitHandover.err,/fixture name persistence failure/);const pendingHandover=JSON.parse(fs.readFileSync(roleFile));assert.equal(pendingHandover.thread,'fixture-thread-2');assert.equal(pendingHandover.handover.thread,`fixture-thread-${beforeFailedHandover+1}`);const retryHandover=await run(['--repo',dir,'--role','test-role','--note','retry must not replace'],'handover');assert.notEqual(retryHandover.code,0);assert.equal(serial,beforeFailedHandover+1);
 fs.unlinkSync(roleFile);const beforeFailedStart=serial;const failedInitStart=await run(['--socket',sock,'--repo',dir,'--role','test-role','--json'],'start');assert.notEqual(failedInitStart.code,0);assert.match(failedInitStart.err,/fixture name persistence failure/);const pendingStart=JSON.parse(fs.readFileSync(roleFile));assert.equal(pendingStart.state,'creation-pending');assert.equal(pendingStart.thread,`fixture-thread-${beforeFailedStart+1}`);const retryStart=await run(['--socket',sock,'--repo',dir,'--role','test-role'],'start');assert.notEqual(retryStart.code,0);assert.equal(serial,beforeFailedStart+1);
 initNameFails=false;fs.unlinkSync(roleFile);readMismatch=true;const badIdentityStart=await run(['--socket',sock,'--repo',dir,'--role','test-role'],'start');assert.notEqual(badIdentityStart.code,0);assert.match(badIdentityStart.err,/identity/);
 }finally{peers.forEach(s=>s.destroy());await new Promise(r=>server.close(r));fs.rmSync(dir,{recursive:true,force:true});}
});
test('silent endpoint fails before the deadline',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'keel-silent-')),sock=path.join(dir,'host.sock');const server=http.createServer();const peers=[];server.on('connection',s=>peers.push(s));await new Promise(r=>server.listen(sock,r));
 try{const before=Date.now();const x=await run(['--socket',sock,'--timeout','100']);assert.notEqual(x.code,0);assert.match(x.err,/timeout/);assert.ok(Date.now()-before<3000);}finally{peers.forEach(s=>s.destroy());await new Promise(r=>server.close(r));fs.rmSync(dir,{recursive:true,force:true});}
});

test('native patch guard checks every source and move destination', () => {
  const {spawnSync} = require('node:child_process');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'keel-native-guard-'));
  const hook = path.resolve(__dirname, '../plugins/keel/scripts/pretooluse-guard.js');
  try {
    fs.mkdirSync(path.join(dir, 'keel'));
    fs.mkdirSync(path.join(dir, 'openspec/changes/fixture'), {recursive: true});
    fs.writeFileSync(path.join(dir, 'openspec/changes/fixture/tasks.md'), '- [ ] 1.1 fixture\n');
    fs.writeFileSync(path.join(dir, 'keel/guard.json'), JSON.stringify({schema:'keel-write-guard/v1',change:'fixture',task:'1.1',touch:['allowed.txt'],authority:[{path:'openspec/changes/fixture/tasks.md',sha256:'0'.repeat(64)}]}));
    const check = patch => {
      const r = spawnSync(process.execPath, [hook], {cwd:dir,encoding:'utf8',input:JSON.stringify({cwd:dir,tool_name:'apply_patch',tool_input:{command:patch}})});
      assert.equal(r.status,0,r.stderr);
      return r.stdout ? JSON.parse(r.stdout).hookSpecificOutput : null;
    };
    assert.equal(check('*** Begin Patch\n*** Add File: forbidden.txt\n+bad\n*** End Patch').permissionDecision,'deny');
    assert.equal(check('*** Begin Patch\n*** Update File: allowed.txt\n*** Move to: forbidden.txt\n@@\n-old\n+new\n*** End Patch').permissionDecision,'deny');
    assert.equal(check('*** Begin Patch\n*** Add File: allowed.txt\n+ok\n*** End Patch'),null);
    const config=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../plugins/keel/hooks/codex.json')));
    assert.ok(config.hooks.PreToolUse.some(group=>new RegExp(group.matcher).test('Bash')));
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('public capability and help distinguish managed host from native enforcement', () => {
  const {spawnSync}=require('node:child_process');
  const result=spawnSync(process.execPath,[cli,'capabilities','--target','codex','--json'],{encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const capabilities=JSON.parse(result.stdout);
  assert.equal(capabilities.host.managedRoles.level,'manual');
  assert.match(capabilities.host.managedRoles.evidence,/explicit.*endpoint/);
  assert.equal(capabilities.guard.enforcement.level,'manual');
  assert.equal(capabilities.compaction.postCompactReinjection.level,'manual');
  const help=spawnSync(process.execPath,[cli,'--help'],{encoding:'utf8'});
  assert.match(help.stdout,/keel codex status\|start\|deliver\|handover\|drain/);
});

test('tick renders managed host failures without starting a replacement', async () => {
  const {spawnSync}=require('node:child_process');
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'keel-codex-tick-'));
  try {
    spawnSync('git',['init','-q',dir]);
    const store=require('../src/core/chat/store'),where=store.requireLocation(dir);
    fs.mkdirSync(path.join(where.root,'codex-roles'),{recursive:true});
    fs.writeFileSync(path.join(where.root,'codex-roles/bad-role.json'),JSON.stringify({state:'creation-pending',role:'bad-role'}));
    const result=await run(['--repo',dir],'tick');
    assert.equal(result.code,0,result.err);
    assert.match(result.out,/Codex bad-role.*unverified/);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

// A native protocol boundary fixture; the public CLI and store run unchanged.
async function reviewerHost() {
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'keel-reviewer-'));
 require('node:child_process').spawnSync('git',['init','-q',dir]);
 const sock=path.join(dir,'host.sock'),requests=[],threads=new Map(),peers=[],turnReviewers=[];
 let serial=0,rejectPersistence=false,mismatch=false,dropStartReply=false;
 const server=http.createServer();
 server.on('upgrade',(req,s)=>{
  peers.push(s);s.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+crypto.createHash('sha1').update(req.headers['sec-websocket-key']+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64')+'\r\n\r\n');
  let buf=Buffer.alloc(0), experimentalApi=false;s.on('end',()=>{for(const t of threads.values()){t.loaded=false;t.reviewer=t.savedReviewer;}});
  s.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);while(buf.length>=6){let n=buf[1]&127,off=2;if(n===126){if(buf.length<8)return;n=buf.readUInt16BE(2);off=4;}else if(n===127){if(buf.length<14)return;n=Number(buf.readBigUInt64BE(2));off=10;}if(buf.length<off+4+n)return;const mask=buf.subarray(off,off+4),data=Buffer.from(buf.subarray(off+4,off+4+n));buf=buf.subarray(off+4+n);for(let i=0;i<data.length;i++)data[i]^=mask[i%4];const x=JSON.parse(data);requests.push(x);if(!x.id)continue;
   let result={},error;const p=x.params||{};let t=threads.get(p.threadId);
   const reply=()=>({thread:{id:t.id,cwd:t.cwd||dir,status:{type:t.status||(t.loaded?'idle':'notLoaded')}},approvalsReviewer:mismatch?'user':t.reviewer,approvalPolicy:'on-request',sandbox:{type:'workspaceWrite',networkAccess:false,writableRoots:[]}});
   if(x.method==='initialize'){experimentalApi=p.capabilities?.experimentalApi===true;result={userAgent:'native-reviewer-fixture'};}
   else if(x.method==='thread/start'){t={id:'reviewer-'+ ++serial,reviewer:p.approvalsReviewer||'user',savedReviewer:'user',loaded:true};threads.set(t.id,t);result=reply();}
   else if(x.method==='thread/name/set'){}
   else if(x.method==='thread/settings/update'){if(rejectPersistence)error={message:'native reviewer persistence rejected'};else t.savedReviewer=t.reviewer=p.approvalsReviewer;}
   else if(x.method==='thread/read')result=reply();
   else if(x.method==='thread/resume'){if(p.runtimeWorkspaceRoots!==undefined&&!experimentalApi)error={message:'thread/resume.runtimeWorkspaceRoots requires experimentalApi capability'};else if(t.resumeError)error={message:t.resumeError};else {t.loaded=true;t.cwd=p.cwd||t.cwd;t.reviewer=p.approvalsReviewer||t.savedReviewer;result=reply();if(t.wrongResumeCwd)result.thread.cwd='/wrong-resumed-cwd';}}
   else if(x.method==='turn/start'){t.reviewer=p.approvalsReviewer||t.reviewer;turnReviewers.push(t.reviewer);t.savedReviewer=t.reviewer;result={turn:{id:'reviewer-turn-'+turnReviewers.length}};}
   else error={message:'unsupported fixture RPC '+x.method};
   if(dropStartReply&&x.method==='thread/start')continue;
   const body=Buffer.from(JSON.stringify({id:x.id,...error?{error}:{result}}));const h=body.length<126?Buffer.from([129,body.length]):Buffer.from([129,126,body.length>>8,body.length&255]);s.write(Buffer.concat([h,body]));
  }});
 });
 await new Promise(r=>server.listen(sock,r));
 return {dir,sock,requests,threads,turnReviewers,dropStartReply:()=>{dropStartReply=true;},rejectPersistence:()=>{rejectPersistence=true;},mismatch:()=>{mismatch=true;},args:(reviewer='auto_review')=>['--socket',sock,'--repo',dir,'--role','reviewer-worker','--approvals-reviewer',reviewer,'--json'],close:async()=>{peers.forEach(p=>p.destroy());await new Promise(r=>server.close(r));fs.rmSync(dir,{recursive:true,force:true});}};
}

test('explicit thread reviewer persists before managed success without a model turn',async()=>{
 const h=await reviewerHost();try{
  const r=await run(h.args(),'start');assert.equal(r.code,0,r.err);
  const entry=JSON.parse(r.out);assert.equal(entry.approvalsReviewer,'auto_review');
  assert.equal(h.threads.get(entry.thread).savedReviewer,'auto_review');
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
  const init=h.requests.find(x=>x.method==='initialize');assert.equal(init.params.capabilities.experimentalApi,true);
  assert.ok(h.requests.findIndex(x=>x.method==='thread/settings/update')>h.requests.findIndex(x=>x.method==='thread/start'));
 }finally{await h.close();}
});


test('explicit thread reviewer controls cold delivery after native policy drift',async()=>{
 const h=await reviewerHost();try{
  const r=await run(h.args(),'start');assert.equal(r.code,0,r.err);
  const id=JSON.parse(r.out).thread;h.threads.get(id).savedReviewer='user';h.threads.get(id).loaded=false;
  const delivered=await run(['--repo',h.dir,'--role','reviewer-worker','--record','reviewer-delivery','--text','explicit policy work','--json'],'deliver');
  assert.equal(delivered.code,0,delivered.err);assert.deepEqual(h.turnReviewers,['auto_review']);
  assert.equal(h.requests.filter(x=>x.method==='thread/start').length,1,'cold delivery retains original id');
 }finally{await h.close();}
});

test('explicit thread reviewer persists on handover successor',async()=>{
 const h=await reviewerHost();try{
  const r=await run(h.args(),'start');assert.equal(r.code,0,r.err);
  const original=JSON.parse(r.out).thread;h.threads.get(original).loaded=true;
  const handed=await run(['--repo',h.dir,'--role','reviewer-worker','--note','retained authority','--json'],'handover');
  assert.equal(handed.code,0,handed.err);const next=JSON.parse(handed.out).thread;
  assert.notEqual(next,original);assert.equal(h.threads.get(next).savedReviewer,'auto_review');
  const role=JSON.parse(fs.readFileSync(path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json')));
  assert.equal(role.approvalsReviewer,'auto_review');assert.equal(role.history[0].thread,original);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
 }finally{await h.close();}
});

test('explicit thread reviewer rejects native policy mismatch without losing id',async()=>{
 const h=await reviewerHost();try{
  h.mismatch();const r=await run(h.args(),'start');assert.notEqual(r.code,0,'policy mismatch must not report managed success');
  assert.match(r.err,/reviewer mismatch/);
  const role=JSON.parse(fs.readFileSync(path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json')));
  assert.equal(role.state,'creation-pending');assert.equal(role.thread,'reviewer-1');
  const retry=await run(h.args(),'start');assert.notEqual(retry.code,0);
  assert.equal(h.requests.filter(x=>x.method==='thread/start').length,1);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
 }finally{await h.close();}
});

test('explicit user reviewer and invalid start flags leave native boundaries intact',async()=>{
 const h=await reviewerHost();try{
  for(const [action,args,message]of [['start',h.args('never'),/must be user or auto_review/],['status',h.args(),/only accepted by start/],['deliver',h.args(),/only accepted by start/]]){
   const r=await run(args,action);assert.notEqual(r.code,0);assert.match(r.err,message);
  }
  assert.equal(h.requests.length,0,'invalid flag/action must reach no native RPC');
  const r=await run(h.args('user'),'start');assert.equal(r.code,0,r.err);
  assert.equal(h.threads.get(JSON.parse(r.out).thread).savedReviewer,'user');
  assert.equal(h.requests.find(x=>x.method==='thread/start').params.sandbox,'workspace-write');
  assert.equal(h.requests.find(x=>x.method==='thread/start').params.approvalPolicy,'on-request');
 }finally{await h.close();}
});

test('explicit thread reviewer persistence failure retains pending creation identity',async()=>{
 const h=await reviewerHost();try{
  h.rejectPersistence();const r=await run(h.args(),'start');assert.notEqual(r.code,0);assert.match(r.err,/native reviewer persistence rejected/);
  const role=JSON.parse(fs.readFileSync(path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json')));
  assert.equal(role.state,'creation-pending');assert.equal(role.thread,'reviewer-1');
  assert.equal((await run(h.args(),'start')).code,1);assert.equal(h.threads.size,1);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
 }finally{await h.close();}
});

test('explicit thread reviewer successor persistence failure keeps old and pending ids',async()=>{
 const h=await reviewerHost();try{
  const r=await run(h.args(),'start');assert.equal(r.code,0,r.err);const original=JSON.parse(r.out).thread;
  h.threads.get(original).loaded=true;h.rejectPersistence();
  const args=['--repo',h.dir,'--role','reviewer-worker','--note','keep pending successor','--json'];
  const handed=await run(args,'handover');assert.notEqual(handed.code,0);assert.match(handed.err,/native reviewer persistence rejected/);
  const role=JSON.parse(fs.readFileSync(path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json')));
  assert.equal(role.thread,original);assert.equal(role.handover.thread,'reviewer-2');assert.equal(role.approvalsReviewer,'auto_review');
  h.threads.get(original).loaded=true;assert.notEqual((await run(args,'handover')).code,0);
  assert.equal(h.threads.size,2);assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
 }finally{await h.close();}
});

test('explicit thread reviewer mismatch on resume starts no delivery',async()=>{
 const h=await reviewerHost();try{
  const r=await run(h.args(),'start');assert.equal(r.code,0,r.err);h.mismatch();
  const delivered=await run(['--repo',h.dir,'--role','reviewer-worker','--record','not-started','--text','policy mismatch','--json'],'deliver');
  assert.notEqual(delivered.code,0);assert.match(delivered.err,/reviewer mismatch/);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);assert.equal(h.threads.size,1);
 }finally{await h.close();}
});


test('explicit thread reviewer remains declared when creation response is unknown',async()=>{
 const h=await reviewerHost();try{
  h.dropStartReply();const r=await run([...h.args(),'--timeout','300'],'start');assert.notEqual(r.code,0);assert.match(r.err,/thread\/start timeout/);
  const role=JSON.parse(fs.readFileSync(path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json')));
  assert.equal(role.state,'creation-pending');assert.equal(role.approvalsReviewer,'auto_review');assert.equal(role.thread,undefined);
  assert.notEqual((await run(h.args(),'start')).code,0);assert.equal(h.threads.size,1);
 }finally{await h.close();}
});


test('recover restores original owned cwd without rewriting role claims or starting work',async()=>{
 const h=await reviewerHost();try{
  const started=await run(h.args(),'start');assert.equal(started.code,0,started.err);const id=JSON.parse(started.out).thread;
  const delivered=await run(['--repo',h.dir,'--role','reviewer-worker','--record','prior-claim','--text','prior work','--json'],'deliver');assert.equal(delivered.code,0,delivered.err);
  const file=path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json'),before=fs.readFileSync(file);
  h.threads.get(id).cwd='/drifted-cwd';h.threads.get(id).loaded=false;
  const turnCount=h.requests.filter(x=>x.method==='turn/start').length;
  const result=await run(['--repo',h.dir,'--role','reviewer-worker','--json'],'recover');assert.equal(result.code,0,result.err);
  assert.equal(JSON.parse(result.out).state,'recovered');assert.equal(JSON.parse(result.out).thread,id);
  const resume=h.requests.filter(x=>x.method==='thread/resume').at(-1);
  assert.equal(resume.params.cwd,h.dir);assert.deepEqual(resume.params.runtimeWorkspaceRoots,[h.dir]);assert.equal(resume.params.threadId,id);
  assert.equal(resume.params.approvalsReviewer,'auto_review');assert.deepEqual(fs.readFileSync(file),before);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,turnCount);assert.equal(h.requests.filter(x=>x.method==='thread/start').length,1);
 }finally{await h.close();}
});

test('legacy recover negotiates workspace roots support without adding a reviewer or changing claims',async()=>{
 const h=await reviewerHost();
 try {
  const args=['--repo',h.dir,'--role','reviewer-worker','--json'];
  const started=await run([...args,'--socket',h.sock],'start');
  assert.equal(started.code,0,started.err);
  const id=JSON.parse(started.out).thread;
  const delivered=await run([...args,'--record','prior-claim','--text','prior work'],'deliver');
  assert.equal(delivered.code,0,delivered.err);
  const file=path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json');
  const before=fs.readFileSync(file);
  const record=JSON.parse(before);
  assert.equal(Object.hasOwn(record,'approvalsReviewer'),false);
  assert.equal(Object.hasOwn(record,'nativePolicy'),false);
  h.threads.get(id).cwd='/drifted-cwd';
  h.threads.get(id).loaded=false;
  const previous=h.requests.length;

  const result=await run(args,'recover');
  assert.equal(result.code,0,result.err);
  assert.equal(JSON.parse(result.out).thread,id);
  const recoveryRequests=h.requests.slice(previous);
  const resume=recoveryRequests.find(request=>request.method==='thread/resume');
  assert.equal(resume.params.cwd,h.dir);
  assert.deepEqual(resume.params.runtimeWorkspaceRoots,[h.dir]);
  assert.equal(Object.hasOwn(resume.params,'approvalsReviewer'),false);
  assert.deepEqual(fs.readFileSync(file),before);
  assert.equal(recoveryRequests.some(request=>['thread/start','turn/start'].includes(request.method)),false);
 } finally {await h.close();}
});

test('recover refuses unsafe native and role boundaries without changing records',async()=>{
 const h=await reviewerHost();try{
  const started=await run(h.args(),'start');assert.equal(started.code,0,started.err);const id=JSON.parse(started.out).thread,t=h.threads.get(id);
  const file=path.join(h.dir,'.git/keel-chat/codex-roles/reviewer-worker.json'),before=fs.readFileSync(file);
  const args=['--repo',h.dir,'--role','reviewer-worker','--json'];
  t.cwd='/drifted-cwd';t.status='active';let count=h.requests.filter(x=>x.method==='thread/resume').length;
  const busy=await run(args,'recover');assert.equal(busy.code,0,busy.err);assert.equal(JSON.parse(busy.out).state,'waiting');assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,count);
  t.status='idle';t.id='foreign-thread';const wrongId=await run(args,'recover');assert.notEqual(wrongId.code,0);assert.match(wrongId.err,/identity/);assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,count);t.id=id;
  t.status='unknown';const unknown=await run(args,'recover');assert.notEqual(unknown.code,0);assert.match(unknown.err,/state/);assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,count);
  t.status='idle';t.resumeError='already has an active writer';const writer=await run(args,'recover');assert.notEqual(writer.code,0);assert.match(writer.err,/active writer/);delete t.resumeError;
  t.wrongResumeCwd=true;const mismatch=await run(args,'recover');assert.notEqual(mismatch.code,0);assert.match(mismatch.err,/identity/);delete t.wrongResumeCwd;
  h.mismatch();const policy=await run(args,'recover');assert.notEqual(policy.code,0);assert.match(policy.err,/reviewer mismatch/);
  count=h.requests.length;const endpoint=await run([...args,'--socket',path.join(h.dir,'wrong.sock')],'recover');assert.notEqual(endpoint.code,0);assert.match(endpoint.err,/endpoint mismatch/);assert.equal(h.requests.length,count);
  const unowned=await run(['--repo',h.dir,'--role','unowned','--json'],'recover');assert.notEqual(unowned.code,0);assert.equal(h.requests.length,count);
  const noRole=await run(['--repo',h.dir,'--json'],'recover');assert.notEqual(noRole.code,0);assert.equal(h.requests.length,count);
  assert.deepEqual(fs.readFileSync(file),before);assert.equal(h.requests.filter(x=>x.method==='thread/start').length,1);assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
 }finally{await h.close();}
});
