const fs=require('node:fs');
const q=s=>JSON.stringify(s);
const files={
  Config:'src/ReactorBackend/Config.luau',
  Engine:'src/ReactorBackend/Engine.luau',
  StateBridge:'src/ReactorBackend/StateBridge.luau',
  ControlBinder:'src/ReactorBackend/ControlBinder.luau',
  Bootstrap:'src/ReactorBackend/Runtime.server.luau',
};
const assignments=Object.entries(files).map(([name,file])=>{
  const source=fs.readFileSync(file,'utf8');
  const cls=name==='Bootstrap'?'Script':'ModuleScript';
  return `local n=backend:FindFirstChild(${q(name)}) or Instance.new(${q(cls)}); n.Name=${q(name)}; n.Source=${q(source)}; n.Parent=backend; if n:IsA('BaseScript') then n.Disabled=false end`;
}).join('\n');
const code=`assert(game.PlaceId==83752844701736,'Wrong target place')\nlocal sss=game:GetService('ServerScriptService')\nlocal backend=sss:FindFirstChild('ReactorBackend') or Instance.new('Folder')\nbackend.Name='ReactorBackend'; backend:SetAttribute('Mode','LiveRewrite'); backend:SetAttribute('Version','0.2.0'); backend.Parent=sss\n${assignments}\nfor _,name in ipairs({'BackendRuntime','ShiftService','StateService'}) do local n=backend:FindFirstChild(name); if n and n:IsA('BaseScript') then n.Disabled=true end end\nlocal old=backend:FindFirstChild('Bootstrap'); old.Disabled=false\nreturn 'deployed modules='..tostring(#backend:GetChildren())`;
fs.writeFileSync('_tools/bridge_request.json',JSON.stringify({method:'tools/call',params:{name:'execute_luau',arguments:{studio_id:process.argv[2],datamodel_type:'Edit',code}}}));
