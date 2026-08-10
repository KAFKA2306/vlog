import {
  SLOTS,
  encodeReading,
  katakana,
  syncedParameterBits,
  weight,
} from './companion-core.mjs';

const STORAGE_KEY = 'vlog.companion.demo.words.v1';

const $ = (selector) => document.querySelector(selector);
const wordsEl = $('#words');
const speechEl = $('#speech');
const paramsEl = $('#params');
const readingEl = $('#reading');
let words = load();

function load() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
  catch { return {}; }
}
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(words)); }
function parseEntries(text) {
  return text.split(/[\s、，,]+/u).map((value) => value.trim()).filter(Boolean).map((raw) => {
    const slash = raw.indexOf('/');
    if (slash < 0) return { text: raw, reading: raw };
    return { text: raw.slice(0, slash), reading: raw.slice(slash + 1) || raw.slice(0, slash) };
  }).filter((entry) => entry.text && entry.reading);
}
function observe(entries) {
  const now = Date.now() / 1000;
  for (const entry of entries) {
    const current = words[entry.text];
    words[entry.text] = { text: entry.text, reading: entry.reading, count: (current?.count || 0) + 1, lastSeen: now };
  }
  save(); renderWords();
}
function choose() {
  const list = Object.values(words);
  if (!list.length) return null;
  const weights = list.map((word) => weight(word));
  const total = weights.reduce((a, b) => a + b, 0);
  let cursor = Math.random() * total;
  for (let index = 0; index < list.length; index += 1) {
    cursor -= weights[index];
    if (cursor <= 0) return list[index];
  }
  return list.at(-1);
}
function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}
function renderWords() {
  const list = Object.values(words).sort((a, b) => b.count - a.count || a.text.localeCompare(b.text, 'ja'));
  if (!list.length) { wordsEl.innerHTML = '<p class="muted">まだ語を観測していません。</p>'; return; }
  const max = Math.max(...list.map((word) => word.count));
  wordsEl.innerHTML = list.map((word) => `<div class="word"><div><strong>${escapeHtml(word.text)}</strong><div class="muted">${escapeHtml(word.reading)}</div><div class="bar"><i style="width:${Math.max(5, word.count / max * 100)}%"></i></div></div><span class="muted">count</span><span>${word.count}</span></div>`).join('');
}
function renderParams(values = Array(SLOTS).fill(0), mood = 0, speak = false) {
  const entries = values.map((value, index) => [`PetChar${index}`, value]);
  entries.push(['PetMood', mood], ['PetSpeak', speak ? 1 : 0]);
  paramsEl.innerHTML = entries.map(([name, value]) => `<div class="param"><span class="muted">${name}</span><b>${value}</b></div>`).join('');
}
function react() {
  const word = choose();
  if (!word) { speechEl.textContent = 'まだ記憶がない'; return; }
  const values = encodeReading(word.reading);
  speechEl.textContent = word.text;
  renderParams(values, 0, true);
  readingEl.textContent = `読み: ${katakana(word.reading)} / [${values.join(', ')}] → PetSpeak=true → 180ms後にfalse / ${syncedParameterBits()} bit`;
  window.setTimeout(() => renderParams(values, 0, false), 180);
}

$('#learn-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const input = $('#learn-input');
  const entries = parseEntries(input.value);
  if (!entries.length) return;
  observe(entries); input.value = ''; input.focus();
});
$('#seed').addEventListener('click', () => observe(parseEntries('猫/ネコ ラーメン VRChat/ブイアールチャット 猫/ネコ 猫/ネコ 音楽/オンガク')));
$('#clear').addEventListener('click', () => { words = {}; save(); speechEl.textContent = '…'; readingEl.textContent = '反応を抽選すると、読みとAvatar Parameter値を表示します。'; renderWords(); renderParams(); });
$('#speak').addEventListener('click', react);

renderWords(); renderParams();
