// Gov's pm2 config. `pm2 start ecosystem.config.cjs` reproduces the
// process; `pm2 delete` is no longer unrecoverable.
const fs = require('fs');
const path = '/home/bosly_accord/bosly-gov/.env';
const env = {};
if (fs.existsSync(path)) {
  for (const line of fs.readFileSync(path, 'utf8').split('\n')) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const i = t.indexOf('=');
    if (i < 0) continue;
    env[t.slice(0, i).trim()] = t.slice(i + 1).trim().replace(/^["']|["']$/g, '');
  }
}
module.exports = { apps: [{
  name: 'bosly-gov',
  script: '/home/bosly_accord/bosly-gov/server.py',
  interpreter: 'python3',
  cwd: '/home/bosly_accord/bosly-gov',
  env,
}]};
