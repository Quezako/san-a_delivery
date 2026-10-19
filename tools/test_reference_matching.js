const path = require('path');
const reference = require(path.join(__dirname, '..', 'src', 'fodmap_reference_embed.js'));

const entries = reference.entries || reference;

function normalizeText(value) {
  return String(value || '')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s　_\-]+/g, '')
    .replace(/[()\[\]{}<>.,!?:;"'’“”]/g, '')
    .trim();
}

function findMatchesInText(text) {
  const normalizedText = normalizeText(text);
  const hits = [];

  Object.values(entries).forEach((entry) => {
    for (const alias of entry.aliases || []) {
      const normalizedAlias = normalizeText(alias);
      if (!normalizedAlias || !normalizedText.includes(normalizedAlias)) continue;
      hits.push({
        food_id: entry.food_id,
        fodmap_level: entry.fodmap_level,
        canonical: entry.canonical,
      });
      break;
    }
  });

  return hits;
}

function scoreFromMatches(matches) {
  const value = {
    high: 3,
    moderate: 2,
    low: 1,
    unknown: 0,
  };

  return matches.reduce((best, match) => {
    return value[match.fodmap_level] > value[best] ? match.fodmap_level : best;
  }, 'unknown');
}

const garlicHit = findMatchesInText('にんにくとリンゴの組み合わせ');
const appleHit = findMatchesInText('りんごと牛乳');

if (!garlicHit.some((it) => it.food_id === 'garlic')) {
  throw new Error('garlic alias match failed');
}

if (!appleHit.some((it) => it.food_id === 'apple')) {
  throw new Error('apple alias match failed');
}

const mixed = findMatchesInText('にんにく、りんご、牛乳');
if (scoreFromMatches(mixed) !== 'high') {
  throw new Error(`score mismatch: ${scoreFromMatches(mixed)}`);
}

console.log('reference matcher smoke test: ok');
console.log('mixed matches:', mixed.map((it) => `${it.food_id}:${it.fodmap_level}`).join(', '));
