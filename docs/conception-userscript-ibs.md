# Conception du userscript IBS / FODMAP pour San-A

## 1. Contexte

Le besoin est de repérer rapidement si un produit San-A est potentiellement compatible avec un régime IBS ou pauvre en FODMAP, en analysant :
- le nom du produit en japonais ;
- la fiche détaillée du produit ;
- les ingrédients et libellés contenus dans la page ;
- une base de référence FODMAP commune et adaptée au Japon ;
- les données déjà collectées dans le navigateur.

Le site San-A est accessible via plusieurs pages de navigation, dont :
- liste de catégorie ;
- fiche détaillée du produit ;
- magasin sélectionné.

Le script doit permettre une analyse rapide sans dépendre d'un backend externe ni du cache navigateur.

## 2. Objectif fonctionnel

Le userscript doit :
- détecter automatiquement le type de page ;
- extraire `item_code`, le nom produit et, si possible, les ingrédients ;
- valider l'information à partir d'une base de référence FODMAP locale ;
- afficher les composants problématiques avec traduction en anglais / français ;
- colorer la carte produit selon la compatibilité ;
- permettre un export JSON des résultats.

## 3. Données à traiter

### 3.1. Identifiant produit

Le point d'ancrage principal est `item_code`.

Exemple :
- `item_code = 0000000000222`

Cela permet d'indexer uniquements les produits et de tenir un cache local fiable.

### 3.2. Données métier du produit

Pour chaque produit, on stocke :
- `item_code`
- `name_ja`
- `ingredient_hits[]`
- `status` : `low`, `moderate`, `high`, `unknown`
- `risk` : `safe`, `watch`, `avoid`, `unknown`
- `fodmap_group` : `fructose`, `fructan`, `lactose`, `polyol`, `gos`, `unknown`
- `fodmap_level` : `low`, `moderate`, `high`, `unknown`
- `source` : `manual`, `detail-page`, `name-analysis`, `reference-match`, `import`
- `confidence` : `high`, `medium`, `low`
- `updated_at` : horodatage

### 3.3. Données de référence FODMAP

La base de référence contient les aliments et ingrédients les plus courants au Japon :
- fruits : pomme, poire, mangue, pastèque, etc.
- légumes : oignon, ail, poireau, asperge, etc.
- produits laitiers : lait, crème, yaourt, fromage
- céréales et féculents : blé, orge, seigle, etc.
- produits de base du quotidien : miso, soja, edamame, etc.

Il faut aussi inclure les appellations japonaises et leurs traductions en anglais / français.

## 4. Stockage local recommandé

### 4.1. Pourquoi IndexedDB

Pour des centaines, voire des milliers de produits, `localStorage` devient limité et peu adapté.

Le meilleur choix pour un tel projet est :
- IndexedDB pour les données persistantes ;
- JSON exportable pour sauvegarde et transfert ;
- `localStorage` uniquement pour quelques flags de configuration légères.

### 4.2. Structure recommandée

Stores proposés :
- `reference` : base FODMAP, pré-générée et embarquée ;
- `products` : cache produits San-A lus dans le navigateur ;
- `analysis` : résultats IBS/FODMAP par `item_code` ;
- `manual` : corrections utilisateur / validation manuelle.

### 4.3. Exemple de stockage produit

```json
{
  "0000000000222": {
    "item_code": "0000000000222",
    "name_ja": "おやつごぼう",
    "ingredient_hits": [
      {
        "ingredient": "garlic",
        "label_ja": "にんにく",
        "label_en": "garlic",
        "label_fr": "ail",
        "fodmap_group": "fructan",
        "fodmap_level": "high"
      }
    ],
    "status": "high",
    "risk": "avoid",
    "updated_at": "2026-10-19T00:00:00Z"
  }
}
```

## 5. Base de référence FODMAP au Japon

### 5.1. Principe

La base locale doit être une liste exhaustive des aliments et ingrédients connus comme potentiellement problématiques pour les IBS / FODMAP.

Elle doit être adaptée au contexte japonais et contenir :
- noms japonais usuels ;
- variantes de translittération ;
- noms anglais / français ;
- type FODMAP principal ;
- niveau d'impact probable ;
- remarques de contexte (par exemple, "écrit en sauce, souvent plus élevé" etc.).

### 5.2. Exemple de structure de référence

```json
{
  "apple": {
    "canonical": "apple",
    "labels_ja": ["リンゴ", "りんご", "アップル"],
    "labels_en": ["apple"],
    "labels_fr": ["pomme"],
    "fodmap_group": "fructose",
    "fodmap_level": "high",
    "source": "reference-base"
  },
  "garlic": {
    "canonical": "garlic",
    "labels_ja": ["にんにく", "ニンニク"],
    "labels_en": ["garlic"],
    "labels_fr": ["ail"],
    "fodmap_group": "fructan",
    "fodmap_level": "high",
    "source": "reference-base"
  }
}
```

### 5.3. Plan de construction

1. Lister les aliments les plus courants au Japon en supermarché.
2. Ajouter les variantes japonaises communes (Kana, kanji, translitération).
3. Associer chaque aliment à un groupe FODMAP.
4. Ajouter les formes de préparation et les ingrédients communs : sauces, épices, condiments, garnitures.
5. Produire un fichier JSON/CSV embarqué dans le dépôt.

## 6. Détection des pages

### 6.1. Pages supportées

- `list.php` : liste des produits d'une catégorie
- `detail.php` : fiche détaillée du produit
- `storetour_entry.php` : page de sélection du magasin

Exemple de magasin ciblé :
- `https://netsuper.san-a.co.jp/shop/storetour_entry.php?shop_code=SNA_006`

### 6.2. Détection du contexte

Le script doit déterminer le contexte pour appliquer les bons extracteurs :

```js
const pageType = location.pathname.includes('detail.php') ? 'detail'
  : location.pathname.includes('list.php') ? 'list'
  : 'other';
```

## 7. Extraction des informations

### 7.1. Sur les listes

Les éléments de liste peuvent contenir :
- nom du produit ;
- image ;
- prix ;
- lien vers fiche détaillée ;
- `item_code` ou un identifiant accessible dans l'URL.

Règle : extraire `item_code` depuis le `href`, le dataset ou un attribut HTML.

### 7.2. Sur les fiches détaillées

La fiche contient généralement :
- nom du produit ;
- code article ;
- description ;
- ingrédients ;
- information nutritionnelle ;
- points de vente.

Le système doit chercher dans le HTML :
- `item_code`
- `group_code`
- `name`
- `title`
- `meta[name=description]`
- balises d'ingrédients / nutrition / détails

## 8. Logique de compatibilité IBS/FODMAP

### 8.1. Analyse du nom et des ingrédients

Le nom du produit est souvent insuffisant. Il faut donc combiner :
- le nom produit ;
- les éléments visibles dans la page ;
- les ingrédients si présents ;
- la base de référence FODMAP locale.

### 8.2. Moteur de matching

Le matching doit fonctionner sur des séquences comme :
- `りんご`, `リンゴ`, `apple`, `pomme`
- `にんにく`, `ニンニク`, `garlic`, `ail`
- `ネギ`, `onion`, `oignon`
- `大根`, `daikon`, `radis`

Et utiliser des alias pour éviter de rater les variantes de langue.

### 8.3. Règle d'évaluation

Exemple :

```js
function scoreProduct(product) {
  const matches = findMatchingIngredients(product.nameJa, product.ingredients, referenceDb);

  if (matches.some(m => m.fodmap_level === 'high')) return 'high';
  if (matches.some(m => m.fodmap_level === 'moderate')) return 'moderate';
  if (matches.length === 0) return 'unknown';
  return 'low';
}
```

## 9. Couleur de fond sur la carte produit

### 9.1. Règles proposées

- vert : compatible / faible FODMAP
- orange : modéré / attention
- rouge : fort / à éviter
- gris : inconnu

### 9.2. Exemple

```js
const palette = {
  low: '#d9f7d9',
  moderate: '#fff0b3',
  high: '#ffd6d6',
  unknown: '#f2f2f2'
};
```

Le composant devra :
- trouver le conteneur de carte produit ;
- ajouter un style visuel ;
- éventuellement afficher un badge de risque ;
- afficher les ingrédients problématiques au survol ou via panneau d'info.

## 10. Affichage des ingrédients problématiques en anglais / français

Le site est en japonais, donc il faut afficher les informations de façon bilingue ou multilingue :
- `にんにく / garlic / ail`
- `りんご / apple / pomme`
- `ネギ / onion / oignon`

Cela aide à repérer très vite la cause du risque FODMAP, même si le produit affiche uniquement le nom japonais.

## 11. Menu flottant d'export

### 11.1. But du menu

Le menu doit permettre rapidement :
- exporter les données locales de compatibilité ;
- importer un JSON ;
- vider la base locale ;
- vérifier le nombre d'entrées stockées ;
- afficher les éléments à risque.

### 11.2. Positionnement

- `position: fixed`
- `bottom: 16px; right: 16px;`
- petite icône flottante, puis menu au clic

### 11.3. Actions minimales

- bouton `Export JSON`
- bouton `Import JSON`
- bouton `Clear local DB`
- bouton `Stats`

## 12. Stratégie de stockage et de génération

### 12.1. Stockage produit local

Le stockage des produits analysés doit être séparé de la base de référence. La base de référence est une donnée “dictionnaire”, tandis que les produits analysés sont des résultats d'un cas réel.

### 12.2. Base embarquée pré-générée

Le meilleur format pour embarquer la base de référence dans le projet est :
- fichier JSON modifiable ;
- éventuellement version CSV pour traitement externe ;
- éventuellement un JSON compact et minifié pour charge rapide.

Recommandation :
- `data/fodmap_reference.json` comme source de vérité ;
- `IndexedDB` pour les données runtime du navigateur.

### 12.3. Pourquoi ne pas tout mettre directement dans le userscript

Placer toute la base directement dans le script présente des inconvénients :
- fichier beaucoup trop dense ;
- difficile à modifier sans recharger l'extension ;
- moins lisible et moins maintenable ;
- plus difficile à exporter.

La bonne séparation est :
- script logique + parsing ;
- fichier de base FODMAP séparé ;
- stockage navigateur runtime persistant.

## 13. Étapes de conception détaillées

### Étape 1 — Reproduire le contexte réel

- ouvrir la page de liste ;
- ouvrir la page de fiche ;
- vérifier la page de magasin ;
- noter les sélecteurs HTML utiles.

### Étape 2 — Détecter les données productives

- vérifier comment San-A encode le `item_code` ;
- trouver le lien produit ;
- tester la récupération depuis DOM et HTML.

### Étape 3 — Construire le référentiel FODMAP japonais

- lister les aliments courants au Japon ;
- inclure les noms japonais, anglais et français ;
- classer par groupe FODMAP ;
- générer le fichier JSON.

### Étape 4 — Créer le module de stockage

- initialiser IndexedDB ;
- définir stores `reference`, `products`, `analysis` ;
- définir `readDb()`, `writeDb()`, `mergeProduct()`.

### Étape 5 — Construire le moteur de classification

- normaliser le nom ;
- extraire les ingrédients ;
- extraire les mots-clés ;
- faire le match avec la base locale ;
- produire un score de compatibilité.

### Étape 6 — Branchements visuels

- repérer le conteneur de carte ;
- ajouter le fond coloré ;
- ou ajouter un badge ;
- ou ajouter un tooltip explicatif.

### Étape 7 — Ajouter le menu utilisateur

- petite icône ;
- panneau de commandes ;
- export JSON ;
- import JSON.

### Étape 8 — Validation sur un magasin réel

- tester sur `SNA_006` ;
- vérifier les résultats sur les aliments connus ;
- corriger les faux positifs / négatifs ;
- enrichir la base locale.

## 14. Plan d'implémentation

### Phase 1 — lecteur de page
- extraction `item_code`
- extraction `name_ja`
- détection de type de page

### Phase 2 — base FODMAP et référentiel
- création du fichier de référence `data/fodmap_reference.json`
- organisation par ingredient / appareil de nommage
- alias japonais, français et anglais

### Phase 3 — stockage local
- IndexedDB / stores
- export / import / nettoyage

### Phase 4 — moteur de scoring
- analyse du nom
- analyse des ingrédients
- analyse de la fiche détaillée
- calcul du niveau de risque

### Phase 5 — rendu visuel
- fond de carte
- badge d'état
- affichage des ingrédients problématiques

### Phase 6 — validation
- tests sur un magasin cible
- revue des faux positifs / faux négatifs
- enrichissement de la base de référence

## 15. Problèmes connus et points de vigilance

- Le site peut charger le contenu dynamique ou via JS.
- Les informations nutritionnelles ne sont pas forcément présentes dans les pages listées.
- La sélection du magasin est obligatoire pour accéder aux pages détaillées.
- Les données FODMAP sont semi-subjectives et doivent rester humaines, auditables et documentées.
- Le projet ne remplace pas un avis médical professionnel.

## 16. Conclusion

La solution la plus robuste consiste à combiner :
- une base de référence FODMAP japonaise pré-générée ;
- un stockage persistant navigateur avec IndexedDB ;
- des alias de produits en Japonais / Anglais / Français ;
- un matching produit + ingrédients + détails ;
- un rendu visuel immédiat sur les cartes ;
- un export JSON pour archiver les référentiels personnels.

Cette architecture donne un bon équilibre entre lisibilité, volume, persistance et extensibilité, tout en restant compatible avec un usage personnel et local.
