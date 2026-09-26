// Use the installed official MCP bridge; never cache a Studio instance id.
// Each invocation has a deadline so an unresponsive playtest cannot hang overnight.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const readline = require('node:readline');
const path = require('node:path');
const exe = process.env.LOCALAPPDATA + '/Roblox/Versions/version-c792f79abddd41bd/StudioMCP.exe';
const requestFile = process.argv[2];
const outputFile = process.argv[3];
const child = spawn(exe, [], {windowsHide: true, stdio: ['pipe', 'pipe', 'pipe']});
let nextId = 0;
const pending = new Map();
const timer = setTimeout(() => { console.error('Studio bridge deadline exceeded'); child.kill(); process.exit(2); }, 90000);
child.stderr.on('data', d => process.stderr.write(d));
child.on('error', err => { console.error(err.message); process.exit(2); });
readline.createInterface({input: child.stdout}).on('line', line => {
  try { const message = JSON.parse(line); const entry = pending.get(message.id);
    if (entry) { pending.delete(message.id); message.error ? entry.reject(new Error(JSON.stringify(message.error))) : entry.resolve(message.result); }
  } catch (err) { console.error('Bridge output:', line.slice(0, 300)); }
});
function call(method, params) {
  const id = ++nextId;
  return new Promise((resolve, reject) => { pending.set(id, {resolve, reject}); child.stdin.write(JSON.stringify({jsonrpc:'2.0', id, method, params}) + '\n'); });
}
(async () => {
  await call('initialize', {protocolVersion:'2024-11-05', capabilities:{}, clientInfo:{name:'reactor-rewrite-local', version:'1.0'}});
  child.stdin.write(JSON.stringify({jsonrpc:'2.0', method:'notifications/initialized'}) + '\n');
  const request = requestFile ? JSON.parse(fs.readFileSync(requestFile, 'utf8').replace(/^\uFEFF/, '')) : {method:'tools/list', params:{}};
  const results = [];
  for (const item of (Array.isArray(request) ? request : [request])) {
    const result = await call(item.method, item.params || {});
    results.push(result);
    if (result.isError) break;
  }
  const text = JSON.stringify(Array.isArray(request) ? results : results[0], null, 2);
  if (outputFile) { fs.writeFileSync(outputFile, text + '\n'); console.log('Saved bridge result:', path.resolve(outputFile)); }
  else console.log(text);
})().catch(err => {console.error(err); process.exitCode = 1;}).finally(() => {clearTimeout(timer); child.kill();});
