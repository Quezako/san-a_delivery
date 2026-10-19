// ==UserScript==
// @name         San-A IBS / FODMAP Checker
// @namespace    http://tampermonkey.net/
// @version      0.1.0
// @description  Analyse les produits San-A et affiche leur compatibilité IBS/FODMAP.
// @author       YourName
// @match        https://netsuper.san-a.co.jp/shop/*
// @grant        none
// ==/UserScript==

(() => {
  'use strict';

  const STORAGE_KEY = 'sanA_ibs_db_v1';
  const UI_ID = 'sanA-ibs-float-panel';

  function getProductItemCode() {
    // TODO: extract item_code from URL, DOM or dataset
    return null;
  }

  function getProductName() {
    // TODO: extract name from page
    return '';
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

  function mergeProduct(itemCode, payload) {
    const db = readStorage();
    db[itemCode] = { ...db[itemCode], ...payload };
    writeStorage(db);
  }

  function detectPageType() {
    const pathname = location.pathname || '';
    if (pathname.includes('detail.php')) return 'detail';
    if (pathname.includes('list.php')) return 'list';
    if (pathname.includes('storetour_entry.php')) return 'store';
    return 'other';
  }

  function inferCompatibilityFromText(text) {
    const normalized = (text || '').toLowerCase();

    if (/(oignon|ail|poire|pomme|blé|pain|lait|fromage|soja)/i.test(normalized)) {
      return {
        is_fodmap: true,
        fodmap_type: 'fructan',
        fodmap_quantity: 'moderate'
      };
    }

    return {
      is_fodmap: false,
      fodmap_type: null,
      fodmap_quantity: 'unknown'
    };
  }

  function applyCardColor(card, itemCode) {
    // TODO: read from local storage and apply background color to the product card
    if (!card) return;
    card.style.backgroundColor = '#f2f2f2';
  }

  function createFloatingPanel() {
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

      if (action === 'stats') {
        const data = readStorage();
        const count = Object.keys(data).length;
        alert(`Produits enregistrés : ${count}`);
      }

      if (action === 'clear') {
        if (confirm('Vider la base locale IBS/FODMAP ?')) {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
    });

    document.body.appendChild(panel);
  }

  function init() {
    const pageType = detectPageType();
    console.log('San-A IBS: page type =', pageType);

    if (!document.body) return;

    createFloatingPanel();

    const itemCode = getProductItemCode();
    if (itemCode) {
      const name = getProductName();
      const payload = inferCompatibilityFromText(`${name} ${document.body.innerText}`);
      mergeProduct(itemCode, {
        item_code: itemCode,
        name,
        ...payload,
        updated_at: new Date().toISOString(),
        source: 'name-analysis'
      });
    }

    document.querySelectorAll('[data-product-id], .item-card, .product-card, li').forEach((card) => {
      const code = card.getAttribute('data-product-id') || card.getAttribute('data-item-code');
      if (code) applyCardColor(card, code);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
