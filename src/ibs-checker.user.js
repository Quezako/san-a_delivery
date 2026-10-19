// ==UserScript==
// @name         San-A IBS / FODMAP Checker
// @namespace    http://tampermonkey.net/
// @version      0.2.1
// @description  Analyse les produits San-A via une base locale FODMAP, détecte les ingrédients du nom et de la fiche, puis colore les cartes.
// @author       Copilot
// @match        https://netsuper.san-a.co.jp/shop/*
// @updateURL    https://github.com/Quezako/san-a_delivery/raw/refs/heads/master/src/ibs-checker.user.js
// @downloadURL  https://github.com/Quezako/san-a_delivery/raw/refs/heads/master/src/ibs-checker.user.js
// @grant        none
// @require      https://raw.githubusercontent.com/Quezako/san-a_delivery/refs/heads/master/src/fodmap_reference_embed.js
// ==/UserScript==

(() => {
  'use strict';

  const STORAGE_KEY = 'sanA_ibs_db_v1';
  const UNKNOWN_TERMS_KEY = 'sanA_ibs_unknown_terms_v1';
  const REFERENCE_VERSION_KEY = 'sanA_ibs_reference_version';
  const UI_ID = 'sanA-ibs-float-panel';
  const REFERENCE_DATA = (globalThis.SAN_A_FODMAP_REFERENCE && globalThis.SAN_A_FODMAP_REFERENCE.entries) || {};
  const CURRENT_REFERENCE_VERSION = 'v1';

  const RISK_LEVEL_MAP = {
    high: 3,
    moderate: 2,
    low: 1,
    unknown: 0,
  };

  const LEVEL_BG = {
    high: '#ffd6d6',
    moderate: '#fff0b3',
    low: '#d9f7d9',
    unknown: '#f2f2f2',
  };

  function normalizeText(value) {
    return String(value || '')
      .normalize('NFKC')
      .toLowerCase()
      .replace(/[\s　_\-]+/g, '')
      .replace(/[()\[\]{}<>.,!?:;"'’“”]/g, '')
      .trim();
  }

  function readStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (error) {
      console.warn('San-A IBS: impossible de lire le stockage local', error);
      return {};
    }
  }

  function writeStorage(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function readJsonKey(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      console.warn(`San-A IBS: impossible de lire la clé ${key}`, error);
      return fallback;
    }
  }

  function writeJsonKey(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function mergeProduct(itemCode, payload) {
    const db = readStorage();
    db[itemCode] = { ...db[itemCode], ...payload };
    writeStorage(db);
  }

  function getCurrentReferenceVersion() {
    return readJsonKey(REFERENCE_VERSION_KEY, CURRENT_REFERENCE_VERSION);
  }

  function setCurrentReferenceVersion(version) {
    writeJsonKey(REFERENCE_VERSION_KEY, version || CURRENT_REFERENCE_VERSION);
  }

  function getUnknownTerms() {
    return readJsonKey(UNKNOWN_TERMS_KEY, []);
  }

  function saveUnknownTerms(terms) {
    const uniqueTerms = Array.from(new Set((terms || []).map((term) => String(term).trim()).filter(Boolean)));
    writeJsonKey(UNKNOWN_TERMS_KEY, uniqueTerms);
  }

  function extractIngredientCandidates(text) {
    if (!text) return [];

    const lines = String(text)
      .replace(/【作り方】.*$/gi, '')
      .replace(/【.*?】/g, '\n')
      .split(/[\n\r]+/);

    const candidates = [];

    for (const line of lines) {
      const clean = line
        .replace(/[()（）\[\]{}<>.,!?:;"'’“”……]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      if (!clean) continue;

      const firstToken = clean.split(/\s+/)[0];
      if (firstToken && /[\p{Script=Hiragana}\p{Script=Katakana}\p{L}\p{N}]/u.test(firstToken)) {
        candidates.push(firstToken);
      }
    }

    return Array.from(new Set(candidates));
  }

  function collectUnknownTermsFromText(text) {
    const knownAliases = new Set();
    Object.values(REFERENCE_DATA).forEach((entry) => {
      if (!entry || !entry.aliases) return;
      (entry.aliases || []).forEach((alias) => {
        const token = normalizeText(alias);
        if (token) knownAliases.add(token);
      });
    });

    const extracted = extractIngredientCandidates(text || '');
    return extracted.filter((term) => {
      const normalized = normalizeText(term);
      return normalized && !knownAliases.has(normalized);
    });
  }

  function recordUnknownTermsForProduct(itemCode, text) {
    const terms = collectUnknownTermsFromText(text || '');
    if (!terms.length) return [];

    const existing = getUnknownTerms();
    const merged = Array.from(new Set([...(existing || []), ...terms]));
    saveUnknownTerms(merged);

    const productCache = readStorage();
    const current = productCache[itemCode] || {};
    productCache[itemCode] = {
      ...current,
      item_code: itemCode,
      unknown_terms: merged.filter((term) => terms.includes(term)),
      updated_at: new Date().toISOString(),
    };
    writeStorage(productCache);

    return terms;
  }

  function detectPageType() {
    const pathname = location.pathname || '';
    if (pathname.includes('detail.php')) return 'detail';
    if (pathname.includes('list.php')) return 'list';
    if (pathname.includes('storetour_entry.php')) return 'store';
    return 'other';
  }

  function getItemCodeFromUrl(url) {
    if (!url) return null;
    try {
      const parsed = new URL(url, location.href);
      const value = parsed.searchParams.get('item_code') || parsed.searchParams.get('group_code');
      return value ? String(value) : null;
    } catch (error) {
      const match = String(url).match(/(?:item_code|itemCode)=([^&]+)/i);
      return match ? match[1] : null;
    }
  }

  function getProductItemCode() {
    const direct = document.querySelector('meta[name="item_code"]')?.content;
    if (direct) return String(direct);

    const fromUrl = getItemCodeFromUrl(location.href);
    if (fromUrl) return fromUrl;

    const candidateLink = Array.from(document.querySelectorAll('a[href]')).find((link) => {
      const href = link.getAttribute('href') || '';
      return href.includes('item_code=') || href.includes('itemCode=');
    });

    return candidateLink ? getItemCodeFromUrl(candidateLink.getAttribute('href')) : null;
  }

  function getProductName() {
    const selectors = [
      'meta[property="og:title"]',
      'meta[name="title"]',
      'h1',
      '.product-name',
      '.item-name',
      '.product_title',
      '.productName',
      '.title'
    ];

    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (!el) continue;
      const value = el.getAttribute('content') || el.textContent || '';
      if (value.trim()) return value.trim();
    }
    return document.title || '';
  }

  function getRelevantPageText() {
    const pageType = detectPageType();

    if (pageType === 'detail') {
      const detailRoot = document.querySelector('.proditem-main');
      if (detailRoot) {
        const rawText = detailRoot.innerText || detailRoot.textContent || '';

        const productDescriptionMatch = rawText.match(/商品説明[\s\S]*?(?=【作り方】|$)/i);
        if (productDescriptionMatch) {
          return productDescriptionMatch[0].replace(/^商品説明\s*/i, '').trim();
        }

        const productInfoMatch = rawText.match(/(?:材料|原材料|成分)[\s\S]*?(?=【作り方】|$)/i);
        if (productInfoMatch) {
          return productInfoMatch[0].trim();
        }

        return rawText.trim();
      }
    }

    const markers = ['材料', '原材料', '成分', '商品説明', 'ingredients', 'ingredient', 'composition', 'description'];
    const candidateNodes = Array.from(document.querySelectorAll('p, li, div, td, th, span, h2, h3'));
    const fragments = [];
    const seen = new Set();

    for (const node of candidateNodes) {
      const rawText = (node.textContent || '').trim();
      if (!rawText) continue;
      const haystack = rawText.toLowerCase();
      const hasMarker = markers.some((marker) => rawText.includes(marker) || haystack.includes(marker.toLowerCase()));
      if (!hasMarker) continue;
      if (seen.has(rawText)) continue;
      seen.add(rawText);
      fragments.push(rawText);
    }

    const ingredientText = fragments.join('\n');
    if (ingredientText) return ingredientText.split(/【作り方】/i)[0].trim();
    return document.body ? document.body.innerText : '';
  }

  function findReferenceMatches(text) {
    if (!text || !Object.keys(REFERENCE_DATA).length) {
      return [];
    }

    const normalizedText = normalizeText(text);
    const hits = [];

    Object.values(REFERENCE_DATA).forEach((entry) => {
      if (!entry || !entry.aliases) return;

      const aliases = Array.isArray(entry.aliases) ? entry.aliases : [];
      for (const alias of aliases) {
        const normalizedAlias = normalizeText(alias);
        if (!normalizedAlias || !normalizedText.includes(normalizedAlias)) continue;

        hits.push({
          food_id: entry.food_id,
          canonical: entry.canonical,
          fodmap_group: entry.fodmap_group,
          fodmap_level: entry.fodmap_level,
          aliases: entry.aliases,
          match_label: alias,
          confidence: entry.confidence || 'low',
        });
        break;
      }
    });

    return hits.sort((a, b) => (RISK_LEVEL_MAP[b.fodmap_level] || 0) - (RISK_LEVEL_MAP[a.fodmap_level] || 0));
  }

  function getRiskLevelFromMatches(matches) {
    if (!matches.length) return 'unknown';
    return matches.reduce((current, match) => {
      const nextValue = RISK_LEVEL_MAP[match.fodmap_level] || 0;
      const currentValue = RISK_LEVEL_MAP[current] || 0;
      return nextValue > currentValue ? match.fodmap_level : current;
    }, 'unknown');
  }

  function getRiskText(level) {
    if (level === 'high') return 'avoid';
    if (level === 'moderate') return 'watch';
    if (level === 'low') return 'safe';
    return 'unknown';
  }

  function inferCompatibilityFromText(text) {
    const matches = findReferenceMatches(text);
    if (!matches.length) {
      return {
        matches: [],
        fodmap_level: 'unknown',
        risk: 'unknown',
        is_fodmap: false,
        status: 'unknown',
        source: 'reference-match',
      };
    }

    const level = getRiskLevelFromMatches(matches);
    const first = matches[0];

    return {
      matches,
      fodmap_level: level,
      fodmap_group: first.fodmap_group || 'unknown',
      risk: getRiskText(level),
      is_fodmap: level !== 'low' && level !== 'unknown',
      status: level,
      source: 'reference-match',
    };
  }

  function getCardCandidates() {
    return Array.from(document.querySelectorAll('a[href*="item_code="], a[href*="itemCode="], [data-item-code], [data-product-id], .item-card, .product-card, .product-item, .goods-card')).filter((node) => {
      const attr = node.getAttribute('data-item-code') || node.getAttribute('data-product-id');
      if (attr) return true;
      if (node.matches('a[href*="item_code="]') || node.matches('a[href*="itemCode="]')) return true;
      return !!node.querySelector('a[href*="item_code="]') || !!node.querySelector('a[href*="itemCode="]');
    });
  }

  function applyCardColor(card, outcome) {
    if (!card) return;
    const level = outcome?.fodmap_level || 'unknown';
    card.style.backgroundColor = LEVEL_BG[level] || LEVEL_BG.unknown;
    card.style.border = '1px solid rgba(0,0,0,0.08)';
    const label = outcome?.matches?.length ? `${outcome.matches[0].canonical} (${level})` : 'IBS: unknown';
    card.setAttribute('data-sanA-ibs-risk', level);
    card.setAttribute('title', label);
  }

  function analyzeTextForMatches(text) {
    const result = inferCompatibilityFromText(text || '');
    return result;
  }

  function persistAnalysis(itemCode, details) {
    const record = {
      item_code: itemCode,
      name_ja: details.name || '',
      ingredient_hits: details.matches || [],
      fodmap_level: details.fodmap_level || 'unknown',
      risk: details.risk || 'unknown',
      status: details.status || 'unknown',
      updated_at: new Date().toISOString(),
      source: details.source || 'reference-match',
    };

    mergeProduct(itemCode, record);
  }

  function analyzeCurrentProduct() {
    const itemCode = getProductItemCode();
    if (!itemCode) return;

    const name = getProductName();
    const detailText = getRelevantPageText();
    const text = `${name}\n${detailText || ''}`;
    const result = analyzeTextForMatches(text);

    const record = {
      item_code: itemCode,
      name,
      ingredient_text: detailText || '',
      matches: result.matches,
      fodmap_level: result.fodmap_level,
      risk: result.risk,
      status: result.status,
      source: result.source,
      updated_at: new Date().toISOString(),
    };

    persistAnalysis(itemCode, record);
    recordUnknownTermsForProduct(itemCode, detailText || '');

    return { itemCode, result };
  }

  function createFloatingPanel() {
    if (document.getElementById(UI_ID)) return;

    const panel = document.createElement('div');
    panel.id = UI_ID;
    panel.style.position = 'fixed';
    panel.style.bottom = '16px';
    panel.style.right = '16px';
    panel.style.zIndex = '99999';
    panel.style.background = '#fff';
    panel.style.border = '1px solid #ddd';
    panel.style.borderRadius = '10px';
    panel.style.padding = '8px';
    panel.style.boxShadow = '0 4px 18px rgba(0,0,0,0.12)';
    panel.style.fontFamily = 'sans-serif';
    panel.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:6px;">
        <button data-action="export" style="padding:6px 8px; cursor:pointer;">Export JSON</button>
        <button data-action="export-unknowns" style="padding:6px 8px; cursor:pointer;">Exporter inconnus</button>
        <button data-action="scan" style="padding:6px 8px; cursor:pointer;">Re-scan</button>
        <button data-action="reanalyze-cache" style="padding:6px 8px; cursor:pointer;">Re-analyser cache</button>
        <button data-action="stats" style="padding:6px 8px; cursor:pointer;">Stats</button>
        <button data-action="clear" style="padding:6px 8px; cursor:pointer;">Vider base</button>
      </div>
    `;

    panel.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      const action = target.dataset.action;
      if (!action) return;

      if (action === 'export') {
        const data = readStorage();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'san-a-ibs-export.json';
        a.click();
        URL.revokeObjectURL(url);
      }

      if (action === 'export-unknowns') {
        const unknowns = getUnknownTerms();
        const blob = new Blob([JSON.stringify({ reference_version: getCurrentReferenceVersion(), unknown_terms: unknowns }, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'san-a-ibs-unknown-terms.json';
        a.click();
        URL.revokeObjectURL(url);
      }

      if (action === 'scan') {
        analyzeCurrentProduct();
        getCardCandidates().forEach((card) => {
          const itemCode = card.getAttribute('data-item-code') || card.getAttribute('data-product-id') || getItemCodeFromUrl(card.innerHTML || '');
          if (!itemCode) return;
          const text = `${card.textContent || ''}`;
          const outcome = analyzeTextForMatches(text);
          applyCardColor(card, outcome);
        });
      }

      if (action === 'reanalyze-cache') {
        const db = readStorage();
        Object.entries(db).forEach(([itemCode, record]) => {
          if (!record || !record.ingredient_text) return;
          const outcome = inferCompatibilityFromText(record.ingredient_text || '');
          db[itemCode] = {
            ...record,
            matches: outcome.matches,
            fodmap_level: outcome.fodmap_level,
            risk: outcome.risk,
            status: outcome.status,
            source: outcome.source,
            updated_at: new Date().toISOString(),
          };
        });
        writeStorage(db);
        alert(`Cache recalculé : ${Object.keys(db).length} produits.`);
      }

      if (action === 'stats') {
        const data = readStorage();
        const count = Object.keys(data).length;
        const unknowns = getUnknownTerms();
        alert(`Produits enregistrés : ${count}\nIngrédients inconnus : ${unknowns.length}`);
      }

      if (action === 'clear') {
        if (confirm('Vider la base locale IBS/FODMAP ?')) {
          localStorage.removeItem(STORAGE_KEY);
          localStorage.removeItem(UNKNOWN_TERMS_KEY);
          localStorage.removeItem(REFERENCE_VERSION_KEY);
        }
      }
    });

    document.body.appendChild(panel);
  }

  function scanCards() {
    getCardCandidates().forEach((card) => {
      const itemCode = card.getAttribute('data-item-code') || card.getAttribute('data-product-id');
      const hrefCode = itemCode || (() => {
        const link = card.querySelector('a[href*="item_code="]') || card.querySelector('a[href*="itemCode="]');
        return link ? getItemCodeFromUrl(link.getAttribute('href')) : null;
      })();

      if (!hrefCode) return;

      const text = `${card.textContent || ''}`;
      const outcome = analyzeTextForMatches(text);
      applyCardColor(card, outcome);
      const payload = {
        item_code: hrefCode,
        name: card.textContent || '',
        ingredient_text: text,
        matches: outcome.matches,
        fodmap_level: outcome.fodmap_level,
        risk: outcome.risk,
        status: outcome.status,
        source: outcome.source,
        updated_at: new Date().toISOString(),
      };
      persistAnalysis(hrefCode, payload);
      recordUnknownTermsForProduct(hrefCode, text);
    });
  }

  function init() {
    const pageType = detectPageType();
    console.log('San-A IBS: page type =', pageType);
    setCurrentReferenceVersion(CURRENT_REFERENCE_VERSION);

    if (!document.body) return;

    createFloatingPanel();

    if (pageType === 'detail' || pageType === 'other') {
      analyzeCurrentProduct();
    }

    scanCards();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
