// Serialize requests without passing Luau through shell or escape-decoding layers.
const fs = require('node:fs');
const [tool, studio, file, mode = 'Edit'] = process.argv.slice(2);
let args = {studio_id: studio};
if (tool === 'execute_luau') args = {...args, datamodel_type:mode, code:fs.readFileSync(file, 'utf8')};
else if (file) args = {...args, ...JSON.parse(file)};
fs.writeFileSync('_tools/bridge_request.json', JSON.stringify({method:'tools/call', params:{name:tool, arguments:args}}));
