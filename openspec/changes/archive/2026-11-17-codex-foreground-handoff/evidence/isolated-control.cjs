const fs=require('fs'),cp=require('child_process'),crypto=require('crypto'),path=require('path');
const stateFile='/tmp/keel541-isolated-state.json',action=process.argv[2];
const stat=pid=>{try{return fs.readFileSync('/proc/'+pid+'/stat','utf8').split(') ')[1].split(' ')[19]}catch{return null}};
const hash=p=>{try{return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')}catch{return null}};
const originals=()=>({app:{pid:914946,start:stat(914946)},backend:{pid:1933800,start:stat(1933800)},configHash:hash('/home/tlm/.codex/config.toml'),registries:['kaiwu-chief','kaiwu-flow','kaiwu-pm-iecc'].map(n=>({role:n,sha256:hash('/home/tlm/my-github/kaiwu-ip/.git/keel-chat/codex-roles/'+n+'.json')}))});
if(action==='launch'){
 let s=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile)):null;
 if(s&&(stat(s.pid)||s.launches>=2||Date.now()>Date.parse(s.deadline)))throw Error('Existing experiment running, exhausted, or expired');
 if(!s){const root=fs.mkdtempSync('/tmp/keel541-isolated-');s={attempt:path.basename(root),root,profile:path.join(root,'profile'),home:path.join(root,'codex-home'),startedAt:new Date().toISOString(),deadline:new Date(Date.now()+1800000).toISOString(),launches:0,before:originals()};fs.mkdirSync(s.profile);fs.mkdirSync(s.home);}
 const now=originals();if(!now.app.start||!now.backend.start||now.app.start!==s.before.app.start||now.backend.start!==s.before.backend.start)throw Error('Original identity changed');
 const env={...process.env,CODEX_ELECTRON_USER_DATA_PATH:s.profile,CODEX_HOME:s.home,CODEX_APP_SERVER_WS_URL:'ws+unix://localhost/home/tlm/.codex/app-server-control/app-server-control.sock:/rpc'};
 const log=fs.openSync(path.join(s.root,'app-'+(s.launches+1)+'.log'),'a',0o600);const child=cp.spawn('/usr/lib/chatgpt/ChatGPT',['--user-data-dir='+s.profile,'--remote-debugging-address=127.0.0.1','--remote-debugging-port=0'],{env,detached:true,stdio:['ignore',log,log]});fs.closeSync(log);child.unref();s.pid=child.pid;s.launches++;fs.writeFileSync(stateFile,JSON.stringify(s,null,2));console.log(JSON.stringify(s,null,2));
}else if(action==='state'){
 const s=JSON.parse(fs.readFileSync(stateFile));console.log(JSON.stringify({...s,currentStart:stat(s.pid),after:originals(),devTools:fs.existsSync(path.join(s.profile,'DevToolsActivePort'))?fs.readFileSync(path.join(s.profile,'DevToolsActivePort'),'utf8'):null},null,2));
}else if(action==='quit'){
 const s=JSON.parse(fs.readFileSync(stateFile));if(!stat(s.pid))throw Error('Isolated App already absent');
 const lines=cp.execFileSync('busctl',['--user','--no-pager','--no-legend','list'],{encoding:'utf8'}).split('\n');const names=lines.map(l=>l.trim().split(/\s+/)).filter(a=>a[1]===String(s.pid)&&a[0].startsWith(':')).map(a=>a[0]);let matches=[];
 for(const bus of names){try{const j=JSON.parse(cp.execFileSync('busctl',['--user','--json=short','--timeout=3s','--','call',bus,'/org/chromium/DbusMenu','com.canonical.dbusmenu','GetLayout','iias','0','-1','4','label','enabled','visible','type'],{encoding:'utf8',stdio:['ignore','pipe','ignore']}));const entries=j.data[1][2].map(v=>v.data);const quit=entries.filter(([id,p])=>p.label?.data==='Quit'&&p.enabled?.data!==false&&p.visible?.data!==false);if(quit.length===1)matches.push({bus,id:quit[0][0]});}catch{}}
 if(matches.length!==1)throw Error('No unique isolated native menu; preserve state, do not force');
 const m=matches[0];cp.execFileSync('busctl',['--user','--timeout=5s','call',m.bus,'/org/chromium/DbusMenu','com.canonical.dbusmenu','Event','isvu',String(m.id),'clicked','i','0','0']);s.quitRequestedAt=new Date().toISOString();s.quitMenuOwner=m.bus;fs.writeFileSync(stateFile,JSON.stringify(s,null,2));console.log('Normal Quit requested only for isolated pid '+s.pid);
}else throw Error('launch|state|quit');
