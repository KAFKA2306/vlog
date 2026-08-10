export const KANA = 'アイウエオカキクケコガギグゲゴサシスセソザジズゼゾタチツテトダヂヅデドナニヌネノハヒフヘホバビブベボパピプペポマミムメモヤユヨラリルレロワヲンァィゥェォャュョッーヴ';
export const SLOTS = 8;
export const WEIGHT_ALPHA = 0.5;
export const WEIGHT_BETA = 0.8;
export const DECAY_PER_DAY = 0.035;

const kanaToInt = new Map([...KANA].map((char, index) => [char, index + 1]));

export function katakana(text) {
  return [...text].map((char) => {
    const code = char.codePointAt(0);
    return code >= 0x3041 && code <= 0x3096 ? String.fromCodePoint(code + 0x60) : char;
  }).join('');
}

export function encodeReading(reading, slots = SLOTS) {
  const values = [...katakana(reading)].slice(0, slots).map((char) => kanaToInt.get(char) || 0);
  while (values.length < slots) values.push(0);
  return values;
}

export function weight(word, now = Date.now() / 1000) {
  const ageDays = Math.max(0, now - word.lastSeen) / 86400;
  return Math.pow(word.count + WEIGHT_ALPHA, WEIGHT_BETA) * Math.exp(-DECAY_PER_DAY * ageDays);
}

export function syncedParameterBits(slots = SLOTS) {
  return slots * 8 + 8 + 1;
}
