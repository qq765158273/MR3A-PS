// Keep the official Playwright CLI client loaded; the browser daemon stays its owner.
const {createRequire} = require('node:module');
const path = require('node:path');
const readline = require('node:readline');

async function main() {
  const cliRequire = createRequire(path.resolve(process.argv[2]));
  const core = path.dirname(cliRequire.resolve('playwright-core/package.json'));
  const {Registry, createClientInfo} = require(path.join(core, 'lib/tools/cli-client/registry.js'));
  const {Session} = require(path.join(core, 'lib/tools/cli-client/session.js'));
  const {minimist} = require(path.join(core, 'lib/tools/cli-client/minimist.js'));
  const info = createClientInfo();
  const registry = await Registry.load();
  const entry = registry.entry(info, process.argv[3]);
  if (!entry) throw new Error('Configured Playwright CLI session is not open');
  const session = new Session(entry);
  // Each request still uses Session.run: official version checks, command parsing,
  // socket transport and daemon serialization. No browser is launched or detached.
  process.stdout.write(JSON.stringify({ready: true}) + '\n');
  for await (const line of readline.createInterface({input: process.stdin, crlfDelay: Infinity})) {
    const request = JSON.parse(line);
    try {
      const args = minimist(request.arguments, {boolean: ['raw', 'json'], string: ['_']});
      const result = await session.run(info, args, {raw: request.raw});
      process.stdout.write(JSON.stringify({id: request.id, returncode: result.isError ? 1 : 0,
                                          stdout: result.text || '', stderr: ''}) + '\n');
    } catch (error) {
      process.stdout.write(JSON.stringify({id: request.id, returncode: 1,
                                          stdout: '', stderr: error.message}) + '\n');
    }
  }
}
main().catch(error => {
  process.stdout.write(JSON.stringify({fatal: error.message}) + '\n');
  process.exitCode = 1;
});
