'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const http=require('node:http');
const {spawn,spawnSync}=require('node:child_process');
const cli=path.resolve(__dirname,'../bin/keel.js');
function run(action,args){return new Promise(resolve=>{const p=spawn(process.execPath,[cli,'codex',action,...args],{env:{...process.env,KEEL_CHAT_ROLE:'',KEEL_MAIL_ROLE:''}});let out='',err='';p.stdout.on('data',b=>out+=b);p.stderr.on('data',b=>err+=b);p.on('close',code=>resolve({code,out,err}));});}
async function fixture(){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'keel-onboard-test-'));
 assert.equal(spawnSync('git',['init','-q',dir]).status,0);
 const root=path.join(dir,'.git/keel-chat');fs.mkdirSync(root,{recursive:true});
 const role='review',thread='original-review';fs.writeFileSync(path.join(root,'roles.json'),JSON.stringify({[dir]:role}));
 const record=path.join(root,'codex-roles',role+'.json');
 const native={id:thread,cwd:dir,status:'idle',turns:[{id:'previous-turn',status:'completed',items:[{id:'previous-answer',type:'agentMessage',text:'original result'}]}],policy:{approvalPolicy:'on-request',approvalsReviewer:'user',sandbox:{type:'readOnly',networkAccess:false},runtimeWorkspaceRoots:[dir]},loaded:'source'};
 const requests=[],peers=[],servers=[],controls={};
 async function host(name){
  const sock=path.join(dir,name+'.sock'),server=http.createServer();servers.push(server);
  server.on('upgrade',(req,s)=>{peers.push(s);
   s.on('error',error=>{if(error.code!=='ECONNRESET')throw error;});
   s.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+crypto.createHash('sha1').update(req.headers['sec-websocket-key']+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64')+'\r\n\r\n');let buf=Buffer.alloc(0);
   s.on('data',chunk=>{buf=Buffer.concat([buf,chunk]);while(buf.length>=6){let len=buf[1]&127,offset=2;if(len===126){if(buf.length<8)return;len=buf.readUInt16BE(2);offset=4;}else if(len===127){if(buf.length<14)return;len=Number(buf.readBigUInt64BE(2));offset=10;}if(buf.length<offset+4+len)return;const mask=buf.subarray(offset,offset+4),body=Buffer.from(buf.subarray(offset+4,offset+4+len));buf=buf.subarray(offset+4+len);for(let i=0;i<body.length;i++)body[i]^=mask[i%4];const x=JSON.parse(body);requests.push({host:name,...x});if(!x.id)continue;
    const p=x.params||{};let result={},error;
    const metadata=()=>({id:(controls.wrongId||(name==='target'&&controls.targetWrongId))?'wrong-id':native.id,cwd:(controls.wrongCwd||(name==='target'&&controls.targetWrongCwd))?'/wrong-cwd':native.cwd,status:{type:native.loaded===name?native.status:'notLoaded'},turns:p.includeTurns?native.turns:[]});
    if(x.method==='initialize')result={userAgent:'native-onboarding-boundary'};
    else if(controls.beforeReply)controls.beforeReply(x,name);
    if(x.method==='thread/read')result={thread:metadata()};
    else if(x.method==='thread/resume'){
     if(native.loaded&&native.loaded!==name)error='original has an active writer';
     else {native.loaded=name;result={thread:metadata(),...structuredClone(native.policy)};if(controls.badPolicy||(name==='target'&&controls.targetBadPolicy))result.sandbox={type:'workspaceWrite'};}
    }else if(x.method==='thread/turns/list'){
     const start=Number(p.cursor||0);
     result={data:native.turns.slice(start,start+1),nextCursor:start+1<native.turns.length?String(start+1):null};
     if(name==='target'&&controls.missingHistory)result={data:[],nextCursor:null};
     if(name==='target'&&controls.oldHistoryView&&start===1){
      result.data=structuredClone(result.data);
      delete result.data[0].environmentId;
     }
    }
    else if(x.method==='thread/queue/list')result={data:controls.queued?[{id:'queued-input'}]:[],nextCursor:null};
    else if(x.method==='thread/goal/get')result={goal:controls.goal?{objective:'original goal'}:null};
    else if(x.method==='thread/backgroundTerminals/list')result={data:controls.terminal?[{id:'running-tool'}]:[],nextCursor:null};
    else if(x.method==='thread/unsubscribe'){if(!controls.retainWriter)native.loaded=null;result={status:'unsubscribed'};}
    else if(x.method==='turn/start'){native.turns.push({id:'delivered-'+native.turns.length,status:'completed',items:[{id:'new-answer',type:'agentMessage',text:p.input[0].text}]});result={turn:native.turns.at(-1)};}
    else if(x.method!=='initialize')error='unsupported RPC '+x.method;
    if(controls.dropAcquire&&name==='target'&&x.method==='thread/resume'){s.destroy();continue;}
    const b=Buffer.from(JSON.stringify({id:x.id,...error?{error:{message:error}}:{result}}));const h=b.length<126?Buffer.from([129,b.length]):Buffer.from([129,126,b.length>>8,b.length&255]);s.write(Buffer.concat([h,b]));
   }});
  });
  await new Promise(r=>server.listen(sock,r));return sock;
 }
 const source=await host('source'),target=await host('target');
 return {dir,root,role,thread,record,native,requests,controls,source,target,
  args:['--repo',dir,'--role',role,'--thread',thread,'--socket',source,'--authority','https://example.com/owner/approved-thread'],
  savePlan(result){assert.equal(result.code,0,result.err);const file=path.join(dir,'plan-'+crypto.randomBytes(4).toString('hex')+'.json');fs.writeFileSync(file,result.out);return file;},
  close:async()=>{peers.forEach(p=>p.destroy());await Promise.all(servers.map(s=>new Promise(r=>s.close(r))));fs.rmSync(dir,{recursive:true,force:true});}};
}

test('register original readonly frontend and deliver with unchanged policy',async()=>{
 const h=await fixture();try{
  const before=structuredClone(h.native.turns);
  const plan=h.savePlan(await run('inspect-registration',h.args));
  const r=await run('register',['--plan',plan,'--json']);assert.equal(r.code,0,r.err);
  const entry=JSON.parse(fs.readFileSync(h.record));assert.equal(entry.thread,h.thread);assert.deepEqual(entry.nativePolicy,h.native.policy);
  assert.deepEqual(h.native.turns,before);assert.equal(h.requests.filter(x=>['thread/start','thread/settings/update','turn/start'].includes(x.method)).length,0);
  h.native.loaded=null;
  const args=['--repo',h.dir,'--role',h.role,'--record','coordination-1','--text','Read the assigned review; no edits.','--json'];
  const delivered=await run('deliver',args);assert.equal(delivered.code,0,delivered.err);assert.equal(JSON.parse(delivered.out).state,'delivered');
  const duplicate=await run('deliver',args);assert.equal(duplicate.code,0,duplicate.err);assert.equal(JSON.parse(duplicate.out).state,'already-delivered');
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,1);assert.deepEqual(h.native.policy,entry.nativePolicy);
  const resumed=h.requests.filter(x=>x.method==='thread/resume');assert.ok(resumed.every(x=>Object.keys(x.params).every(key=>key==='threadId'||(key==='excludeTurns'&&x.params.excludeTurns===true))),'no permission overrides while inspecting or delivering registered frontend');
 }finally{await h.close();}
});

test('registration preserves active work and registered recovery preserves original runtime roots',async()=>{
 const h=await fixture();try{
  h.native.status='active';h.native.policy.runtimeWorkspaceRoots=[];
  const plan=h.savePlan(await run('inspect-registration',h.args));
  assert.equal((await run('register',['--plan',plan])).code,0);
  assert.equal(h.native.status,'active');
  const waiting=await run('deliver',['--repo',h.dir,'--role',h.role,'--record','while-busy','--text','do not interrupt','--json']);
  assert.equal(waiting.code,0,waiting.err);assert.equal(JSON.parse(waiting.out).state,'waiting');assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);
  h.native.status='idle';h.native.loaded=null;
  const recovered=await run('recover',['--repo',h.dir,'--role',h.role,'--json']);assert.equal(recovered.code,0,recovered.err);
  const request=h.requests.filter(x=>x.method==='thread/resume').at(-1);assert.deepEqual(request.params.runtimeWorkspaceRoots,[],'registered recovery must not replace the observed runtime roots');
  const handover=await run('handover',['--repo',h.dir,'--role',h.role,'--note','do not create second review']);assert.notEqual(handover.code,0);assert.match(handover.err,/successor authorization/);assert.equal(h.requests.filter(x=>x.method==='thread/start').length,0);
 }finally{await h.close();}
});

test('registration rejects unapproved, conflicting, stale and concurrent identities',async()=>{
 const h=await fixture();try{
  for(const args of [h.args.filter((_,i)=>i<h.args.length-2),h.args.map(x=>x===h.role?'keel':x)]){
   const r=await run('inspect-registration',args);assert.notEqual(r.code,0);assert.ok(!fs.existsSync(h.record));
  }
  const plan=h.savePlan(await run('inspect-registration',h.args));
  const originalPlan=fs.readFileSync(plan);let p=JSON.parse(originalPlan);p.thread='not-authorized';fs.writeFileSync(plan,JSON.stringify(p));
  assert.match((await run('register',['--plan',plan])).err,/tampered/);fs.writeFileSync(plan,originalPlan);
  fs.mkdirSync(path.dirname(h.record),{recursive:true});const other=path.join(path.dirname(h.record),'other.json');
  for(const record of [{thread:h.thread},{state:'creation-pending',handover:{thread:h.thread}},{history:[{thread:h.thread}]}]){
   fs.writeFileSync(other,JSON.stringify(record));assert.match((await run('register',['--plan',plan])).err,/another managed role/);assert.ok(!fs.existsSync(h.record));
  }
  fs.writeFileSync(other,'{broken');assert.notEqual((await run('register',['--plan',plan])).code,0);fs.unlinkSync(other);
  const bindings=path.join(h.root,'roles.json'),savedBindings=fs.readFileSync(bindings);
  for(const value of [{[h.dir]:'different'}, {[h.dir]:h.role,'/another-worktree':h.role}]){
   fs.writeFileSync(bindings,JSON.stringify(value));assert.notEqual((await run('register',['--plan',plan])).code,0);assert.ok(!fs.existsSync(h.record));
  }
  fs.writeFileSync(bindings,savedBindings);
  h.controls.badPolicy=true;assert.match((await run('register',['--plan',plan])).err,/policy mismatch/);h.controls.badPolicy=false;
  h.controls.wrongId=true;assert.match((await run('register',['--plan',plan])).err,/identity/);h.controls.wrongId=false;
  h.controls.wrongCwd=true;assert.match((await run('register',['--plan',plan])).err,/worktree/);h.controls.wrongCwd=false;
  const lock=path.join(path.dirname(h.record),'.registration.lock');fs.writeFileSync(lock,'');
  const blocked=await run('register',['--plan',plan]);assert.notEqual(blocked.code,0);assert.ok(fs.existsSync(lock));
  const blockedStart=await run('start',['--repo',h.dir,'--role',h.role,'--socket',h.source]);assert.notEqual(blockedStart.code,0);fs.unlinkSync(lock);
  const successes=await Promise.all([run('register',['--plan',plan]),run('register',['--plan',plan])]);assert.equal(successes.filter(r=>r.code===0).length,1);
  assert.equal(h.requests.filter(x=>['thread/start','turn/start','thread/settings/update'].includes(x.method)).length,0);
 }finally{await h.close();}
});

test('registered policy drift and uncertain claim never start work',async()=>{
 const h=await fixture();try{
  const plan=h.savePlan(await run('inspect-registration',h.args));assert.equal((await run('register',['--plan',plan])).code,0);
  const args=['--repo',h.dir,'--role',h.role,'--record','unknown','--text','must not replay','--json'];
  const entry=JSON.parse(fs.readFileSync(h.record));entry.deliveries={[crypto.createHash('sha256').update('unknown').digest('hex')]:{state:'pending',record:'unknown'}};fs.writeFileSync(h.record,JSON.stringify(entry));
  let count=h.requests.filter(x=>x.method==='thread/resume').length;
  assert.match((await run('deliver',args)).err,/outcome unknown/);assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,count);
  h.controls.badPolicy=true;
  const drift=await run('deliver',args.map(x=>x==='unknown'?'new-record':x));assert.notEqual(drift.code,0);assert.match(drift.err,/policy mismatch/);
  assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);assert.deepEqual(JSON.parse(fs.readFileSync(h.record)).deliveries,entry.deliveries);
 }finally{await h.close();}
});

async function managed(h){const plan=h.savePlan(await run('inspect-registration',h.args));const r=await run('register',['--plan',plan]);assert.equal(r.code,0,r.err);const entry=JSON.parse(fs.readFileSync(h.record));entry.history=[{thread:'older-owned-thread',note:'original handover'}];entry.custom={preserved:true};entry.deliveries={[crypto.createHash('sha256').update('uncertain').digest('hex')]:{record:'uncertain',state:'pending'},[crypto.createHash('sha256').update('already').digest('hex')]:{record:'already',state:'delivered',turn:'previous-turn'}};fs.writeFileSync(h.record,JSON.stringify(entry));return entry;}
function migrationArgs(h){return ['--repo',h.dir,'--role',h.role,'--to-socket',h.target,'--authority','https://example.com/owner/approved-migration'];}
test('target cold preflight detects second-page metadata loss before planning or release',async()=>{
 const h=await fixture();try{
  await managed(h);
  h.native.turns.push({id:'next-turn',status:'completed',environmentId:'native-env',items:[]});
  const original=fs.readFileSync(h.record);
  h.controls.oldHistoryView=true;
  const failedInspect=await run('inspect-migration',migrationArgs(h));
  assert.notEqual(failedInspect.code,0);
  assert.match(failedInspect.err,/target original persistent history mismatch/);
  assert.equal(failedInspect.out,'');
  h.controls.oldHistoryView=false;
  const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));
  const journal=path.join(h.root,'codex-transitions',JSON.parse(fs.readFileSync(plan)).id+'.json');
  for(const [flag,error] of [
   ['oldHistoryView',/target original persistent history mismatch/],
   ['targetWrongId',/identity/],
   ['targetWrongCwd',/worktree/],
  ]){
   h.controls[flag]=true;
   const failed=await run('migrate',['--plan',plan]);
   assert.notEqual(failed.code,0,flag);
   assert.match(failed.err,error);
   assert.doesNotMatch(failed.err,/outcome unknown/);
   assert.ok(!fs.existsSync(journal));
   h.controls[flag]=false;
  }
  assert.ok(h.requests.some(x=>x.host==='target'&&x.method==='thread/turns/list'&&x.params.cursor==='1'&&x.params.itemsView==='full'));
  assert.ok(!h.requests.some(x=>x.method==='thread/unsubscribe'||(x.host==='target'&&x.method==='thread/resume')));
  assert.deepEqual(fs.readFileSync(h.record),original);
 }finally{await h.close();}
});
test('source unload is observed before the single target acquisition',async()=>{
 const h=await fixture();try{
  await managed(h);
  const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));
  let releaseIssued=false, readsAfterRelease=0;
  h.controls.retainWriter=true;
  h.controls.beforeReply=(request,host)=>{
   if(host!=='source')return;
   if(request.method==='thread/unsubscribe')releaseIssued=true;
   if(releaseIssued&&request.method==='thread/read'&&++readsAfterRelease===2)h.native.loaded=null;
  };
  const migrated=await run('migrate',['--plan',plan]);
  assert.equal(migrated.code,0,migrated.err);
  const afterRelease=h.requests.slice(h.requests.findIndex(x=>x.method==='thread/unsubscribe')+1);
  const acquired=afterRelease.findIndex(x=>x.host==='target'&&x.method==='thread/resume');
  assert.equal(afterRelease.filter(x=>x.host==='target'&&x.method==='thread/resume').length,1);
  assert.equal(afterRelease.slice(0,acquired).filter(x=>x.host==='source'&&x.method==='thread/read').length,2);
  assert.equal(h.native.loaded,'target');
 }finally{await h.close();}
});
test('source unload timeout never tries target acquisition and writer races still refuse',async()=>{
 for(const race of [false,true]){
  const h=await fixture();try{
   await managed(h);
   const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));
   const original=fs.readFileSync(h.record);
   h.controls.retainWriter=!race;
   if(race)h.controls.beforeReply=(request,host)=>{
    if(host==='target'&&request.method==='thread/resume')h.native.loaded='source';
   };
   const failed=await run('migrate',['--plan',plan,'--timeout','600']);
   assert.notEqual(failed.code,0);
   assert.match(failed.err,race?/native writer|active writer/:/source unload timed out/);
   assert.match(failed.err,/outcome unknown/);
   const status=JSON.parse((await run('migration-status',['--plan',plan])).out);
   assert.equal(status.state,'unknown');
   assert.equal(status.phase,race?'acquiring':'releasing');
   assert.deepEqual(fs.readFileSync(h.record),original);
   assert.match((await run('migrate',['--plan',plan])).err,/explicitly reconcile/);
   assert.equal(h.requests.filter(x=>x.method==='thread/unsubscribe').length,1);
   assert.equal(h.requests.filter(x=>x.host==='target'&&x.method==='thread/resume').length,race?1:0);
  }finally{await h.close();}
 }
});
test('migrate original native endpoint preserving full history and all claims',async()=>{
 const h=await fixture();try{
  const entry=await managed(h);h.native.turns.push({id:'previous-two',status:'completed',items:[{id:'result-two',type:'agentMessage',text:'retain paginated second result'}]});
  const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));const p=JSON.parse(fs.readFileSync(plan));assert.equal(p.historyCount,2);
  const r=await run('migrate',['--plan',plan,'--json']);assert.equal(r.code,0,r.err);assert.equal(JSON.parse(r.out).state,'migrated');
  const after=JSON.parse(fs.readFileSync(h.record));const {socket,endpointMigrations,...preserved}=after;const {socket:oldSocket,...original}=entry;assert.deepEqual(preserved,original);assert.equal(socket,h.target);assert.equal(endpointMigrations[0].plan,p.id);
  const release=h.requests.findIndex(x=>x.method==='thread/unsubscribe');const target=h.requests.findIndex(x=>x.host==='target'&&x.method==='thread/resume');assert.ok(release>=0&&target>release);
  assert.equal(h.native.loaded,'target');assert.equal(h.requests.filter(x=>['thread/start','turn/start','thread/settings/update'].includes(x.method)).length,0);
  const args=['--repo',h.dir,'--role',h.role,'--record','already','--text','do not repeat','--json'];const duplicate=await run('deliver',args);assert.equal(duplicate.code,0,duplicate.err);assert.equal(JSON.parse(duplicate.out).turn,'previous-turn');
  assert.match((await run('deliver',args.map(x=>x==='already'?'uncertain':x))).err,/outcome unknown/);
 }finally{await h.close();}
});

test('uncertain final journal commit reconciles without rewriting registry or repeating handoff',async()=>{
 const h=await fixture();try{
  await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));const p=JSON.parse(fs.readFileSync(plan));
  assert.equal((await run('migrate',['--plan',plan])).code,0);
  const journal=path.join(h.root,'codex-transitions',p.id+'.json'),entry=JSON.parse(fs.readFileSync(journal));
  // Public persisted boundary: process died after the atomic registry commit
  // and before its final journal write reached disk.
  entry.state='unknown';entry.phase='verified';fs.writeFileSync(journal,JSON.stringify(entry));
  const before=fs.readFileSync(h.record),releaseCount=h.requests.filter(x=>x.method==='thread/unsubscribe').length;
  const reconciled=await run('migrate',['--plan',plan,'--reconcile','--json']);assert.equal(reconciled.code,0,reconciled.err);
  assert.deepEqual(fs.readFileSync(h.record),before);assert.equal(h.requests.filter(x=>x.method==='thread/unsubscribe').length,releaseCount);
  assert.equal(JSON.parse(fs.readFileSync(journal)).state,'committed');
 }finally{await h.close();}
});

test('migration refuses active work and input without consuming or creating intent',async()=>{
 const h=await fixture();try{
  await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h))),id=JSON.parse(fs.readFileSync(plan)).id;
  const before=fs.readFileSync(h.record);
  for(const flag of ['queued','goal','terminal']){
   h.controls[flag]=true;const failed=await run('migrate',['--plan',plan]);assert.notEqual(failed.code,0,flag);h.controls[flag]=false;
   assert.deepEqual(fs.readFileSync(h.record),before);assert.ok(!fs.existsSync(path.join(h.root,'codex-transitions',id+'.json')));
  }
  h.native.status='active';let failed=await run('migrate',['--plan',plan]);assert.match(failed.err,/active work/);h.native.status='idle';
  h.native.turns.push({id:'running',status:'inProgress',items:[]});failed=await run('migrate',['--plan',plan]);assert.match(failed.err,/active work/);h.native.turns.pop();
  assert.equal(h.requests.filter(x=>x.method==='thread/unsubscribe').length,0);assert.equal(h.requests.filter(x=>['turn/start','thread/start'].includes(x.method)).length,0);
 }finally{await h.close();}
});

test('migration detects stale source and concurrent registry or role binding without overwrite',async()=>{
 const h=await fixture();try{
  await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h))),original=fs.readFileSync(h.record);
  let changed=JSON.parse(original);changed.custom={external:'changed'};fs.writeFileSync(h.record,JSON.stringify(changed));
  assert.match((await run('migrate',['--plan',plan])).err,/registry changed/);assert.deepEqual(JSON.parse(fs.readFileSync(h.record)).custom,changed.custom);fs.writeFileSync(h.record,original);
  h.native.turns.push({id:'new-source-result',status:'completed',items:[]});assert.match((await run('migrate',['--plan',plan])).err,/history changed/);h.native.turns.pop();
  const roleFile=path.join(h.root,'roles.json'),saved=fs.readFileSync(roleFile);
  h.controls.beforeReply=(request,host)=>{if(host==='source'&&request.method==='thread/goal/get')fs.writeFileSync(roleFile,JSON.stringify({[h.dir]:'other-role'}));};
  assert.match((await run('migrate',['--plan',plan])).err,/exact role/);fs.writeFileSync(roleFile,saved);
  h.controls.beforeReply=(request,host)=>{if(host==='target'&&request.method==='thread/resume')fs.writeFileSync(h.record,JSON.stringify({...JSON.parse(original),custom:{external:'during-acquire'}}));};
  assert.match((await run('migrate',['--plan',plan])).err,/registry changed/);assert.deepEqual(JSON.parse(fs.readFileSync(h.record)).custom,{external:'during-acquire'});
 }finally{await h.close();}
});

test('migration failure journals preserve writer, identity, history and policy boundaries',async()=>{
 for(const flag of ['retainWriter','missingHistory','targetBadPolicy','targetWrongId','targetWrongCwd']){
  const h=await fixture();try{
   await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h))),p=JSON.parse(fs.readFileSync(plan)),original=fs.readFileSync(h.record);
   h.controls.beforeReply=x=>{if(x.method==='thread/unsubscribe')h.controls[flag]=true;};
   const failed=await run('migrate',['--plan',plan,'--timeout','600']);assert.notEqual(failed.code,0,flag);assert.match(failed.err,/outcome unknown/);
   assert.deepEqual(fs.readFileSync(h.record),original);assert.equal(JSON.parse(fs.readFileSync(path.join(h.root,'codex-transitions',p.id+'.json'))).state,'unknown');
   const releaseCount=h.requests.filter(x=>x.method==='thread/unsubscribe').length,resumeCount=h.requests.filter(x=>x.method==='thread/resume').length;
   assert.match((await run('migrate',['--plan',plan])).err,/explicitly reconcile/);
   const status=await run('migration-status',['--plan',plan]);assert.equal(status.code,0,status.err);assert.equal(JSON.parse(status.out).state,'unknown');
   assert.equal(h.requests.filter(x=>x.method==='thread/unsubscribe').length,releaseCount);assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,resumeCount);
   assert.equal(h.requests.filter(x=>['thread/start','turn/start','thread/settings/update'].includes(x.method)).length,0);
  }finally{await h.close();}
 }
});

test('unknown acquisition requires explicit loaded-target reconciliation and preserves new native work',async()=>{
 const h=await fixture();try{
  await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h))),before=JSON.parse(fs.readFileSync(h.record));
  h.controls.dropAcquire=true;assert.match((await run('migrate',['--plan',plan])).err,/outcome unknown/);h.controls.dropAcquire=false;
  const count=h.requests.filter(x=>x.method==='thread/resume').length,releaseCount=h.requests.filter(x=>x.method==='thread/unsubscribe').length;
  h.native.loaded=null;assert.match((await run('migrate',['--plan',plan,'--reconcile'])).err,/not already loaded/);assert.equal(h.requests.filter(x=>x.method==='thread/resume').length,count);
  h.native.loaded='target';h.native.status='active';h.native.turns.push({id:'native-work-after-uncertain-acquire',status:'inProgress',items:[{id:'preserved-active-tool',type:'commandExecution'}]});
  const reconciled=await run('migrate',['--plan',plan,'--reconcile']);assert.equal(reconciled.code,0,reconciled.err);
  assert.equal(h.native.status,'active');assert.equal(h.native.turns.at(-1).items[0].id,'preserved-active-tool');assert.equal(h.requests.filter(x=>x.method==='thread/unsubscribe').length,releaseCount);
  const after=JSON.parse(fs.readFileSync(h.record));assert.deepEqual(after.deliveries,before.deliveries);
  const repeated=await run('migrate',['--plan',plan]);assert.equal(repeated.code,0,repeated.err);assert.equal(JSON.parse(repeated.out).state,'already-migrated');
 }finally{await h.close();}
});

test('equivalent built-in native profile representation migrates without relaxing effective policy',async()=>{
 const h=await fixture();try{
  h.native.policy.activePermissionProfile=null;await managed(h);
  const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));
  h.controls.beforeReply=(x,host)=>{if(host==='target'&&x.method==='thread/resume')h.native.policy.activePermissionProfile={id:':read-only',extends:null};};
  const r=await run('migrate',['--plan',plan]);assert.equal(r.code,0,r.err);
  const after=JSON.parse(fs.readFileSync(h.record));assert.equal(after.socket,h.target);assert.equal(after.nativePolicy.sandbox.type,'readOnly');assert.equal(after.nativePolicy.approvalPolicy,'on-request');
 }finally{await h.close();}
});

test('registered effective approval, roots and custom profiles remain exact',async()=>{
 for(const change of [{approvalPolicy:'never'},{runtimeWorkspaceRoots:['/unapproved-root']},{activePermissionProfile:{id:'custom-review',extends:null}}]){
  const h=await fixture();try{
   await managed(h);const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));
   h.controls.beforeReply=(x,host)=>{if(host==='target'&&x.method==='thread/resume')Object.assign(h.native.policy,change);};
   const before=fs.readFileSync(h.record),r=await run('migrate',['--plan',plan]);assert.notEqual(r.code,0);assert.match(r.err,/policy mismatch/);assert.deepEqual(fs.readFileSync(h.record),before);
  }finally{await h.close();}
 }
});

test('migrated legacy default role enforces its audited native policy on subsequent work',async()=>{
 const h=await fixture();try{
  await managed(h);h.native.policy.sandbox={type:'workspaceWrite',writableRoots:[],networkAccess:false};
  const entry=JSON.parse(fs.readFileSync(h.record));delete entry.registration;delete entry.nativePolicy;fs.writeFileSync(h.record,JSON.stringify(entry));
  const plan=h.savePlan(await run('inspect-migration',migrationArgs(h)));assert.equal((await run('migrate',['--plan',plan])).code,0);
  const before=fs.readFileSync(h.record);h.native.policy.approvalPolicy='never';
  const delivered=await run('deliver',['--repo',h.dir,'--role',h.role,'--record','policy-must-hold','--text','must not run under changed policy']);
  assert.notEqual(delivered.code,0);assert.match(delivered.err,/policy mismatch/);assert.equal(h.requests.filter(x=>x.method==='turn/start').length,0);assert.deepEqual(fs.readFileSync(h.record),before);
  const recovered=await run('recover',['--repo',h.dir,'--role',h.role]);assert.notEqual(recovered.code,0);assert.match(recovered.err,/policy mismatch/);
  h.native.policy.approvalPolicy='on-request';const recoveredOk=await run('recover',['--repo',h.dir,'--role',h.role,'--json']);assert.equal(recoveredOk.code,0,recoveredOk.err);assert.deepEqual(fs.readFileSync(h.record),before);
 }finally{await h.close();}
});
