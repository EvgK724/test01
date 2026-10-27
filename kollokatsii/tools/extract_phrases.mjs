// Собирает все английские фразы приложения из index.html в phrases.json
// (по ним tools/make_audio.py делает записи голосом Microsoft Ryan).
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(root, 'index.html'), 'utf8');
const block = html.match(/\/\*DATA-START\*\/([\s\S]*?)\/\*DATA-END\*\//);
if (!block) throw new Error('В index.html не найден блок /*DATA-START*/ … /*DATA-END*/');

const phrases = Array.from(vm.runInNewContext(block[1] + '\n;allPhrases();'));
writeFileSync(join(root, 'phrases.json'), JSON.stringify({ voice: 'en-GB-RyanNeural', phrases }, null, 2) + '\n');
console.log(`${phrases.length} phrases -> phrases.json`);
