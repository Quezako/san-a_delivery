# Conception du userscript IBS / FODMAP pour San-A

## 1. Contexte

Le besoin est de repérer rapidement si un produit San-A est potentiellement compatible avec un régime IBS ou pauvre en FODMAP, en analysant :
- le nom du produit ;
- éventuellement la fiche détaillée du produit ;
- les données déjà collectées dans le navigateur.

Le site San-A est accessible via plusieurs pages de navigation, dont :
- liste de catégorie ;
- fiche détaillée du produit ;
- magasin sélectionné.

Le script doit permettre une analyse rapide sans dépendre d'un backend externe ni du cache du navigateur.

## 2. Objectif fonctionnel

Le userscript doit :
- détecter automatiquement le type de page ;
- extraire `item_code` et nom du produit ;
- si disponible, lire les informations détaillées de la fiche ;
- comparer avec une base locale de données IBS/FODMAP ;
- colorer la carte produit selon la compatibilité ;
- permettre un export JSON des résultats.

## 3. Données à traiter

### 3.1. Product ID

Le point d'ancrage principal est `item_code`.

Exemple :
- `item_code = 0000000000222`

Cela permet de faire un index unique pour chaque produit et de conserver les données localement dans le navigateur.

### 3.2. Données métier

Pour chaque produit, on stocke :
- `is_fodmap` : booléen
- `fodmap_type` : type de FODMAP (`fructose`, `fructan`, `polyol`, `lactose`, `galacto-oligosaccharides`, etc.)
- `fodmap_quantity` : `low`, `moderate`, `high`, `unknown`
- `source` : manière de collecte (`manual`, `detail-page`, `name-analysis`, `import`)
- `confidence` : `high`, `medium`, `low`
- `updated_at` : horodatage

## 4. Base locale de compatibilité

### 4.1. Stockage navigateur

Le stockage devra être durable dans le navigateur et ne pas dépendre du cache.

Options recommandées :
- `localStorage` pour simplicité et rapidité ;
- `IndexedDB` si on prévoit un volume plus important.

Pour une première version, `localStorage` est suffisant :

```js
const STORAGE_KEY = 'sanA_ibs_db_v1';
```

Le JSON obtenu peut ressembler à :

```json
{
  "0000000000222": {
    "is_fodmap": true,
    "fodmap_type": "fructan",
    "fodmap_quantity": "moderate",
    "source": "manual"
  }
}
```

### 4.2. Rôle de la base locale

La base locale permet :
- de mémoriser les produits déjà analysés ;
- de réutiliser les résultats d'une session à l'autre ;
- de pousser la donnée à export / import ;
- de tenir un historique propre aux données IBS/FODMAP.

## 5. Détection des pages

### 5.1. Pages supportées

- `list.php` : liste des produits d'une catégorie
- `detail.php` : fiche détaillée du produit
- `storetour_entry.php` : page de sélection du magasin

Exemple de magasin ciblé :
- `https://netsuper.san-a.co.jp/shop/storetour_entry.php?shop_code=SNA_006`

### 5.2. Détection du contexte

Le script doit déterminer le contexte pour appliquer les bons extracteurs :

```js
const pageType = location.pathname.includes('detail.php') ? 'detail'
  : location.pathname.includes('list.php') ? 'list'
  : 'other';
```

## 6. Extraction des informations

### 6.1. Sur les listes

Les éléments de liste peuvent être des cartes de produits avec :
- nom du produit ;
- image ;
- prix ;
- lien vers fiche détaillée ;
- `item_code` ou un identifiant accessible dans le `href`.

Règle : extraire le `item_code` dès que possible depuis le `href`, le dataset ou un attribut HTML.

### 6.2. Sur les fiches détaillées

La fiche contient généralement :
- nom du produit ;
- code article ;
- attributs nutritionnels ;
- description ;
- points de vente.

Le système doit dans un premier temps chercher dans le HTML :
- `item_code`
- `group_code`
- `name`
- `title`
- `meta[name=description]`
- balises de détails produites par le site.

## 7. Logique de compatibilité IBS/FODMAP

### 7.1. Analyse du nom

Le nom du produit permet souvent d'identifier des familles de produits :
- orange
- pomme
- poire
- ail
- oignon
- blé
- lait
- fromage
- soja
- pois chiche
- etc.

L'algorithme peut utiliser :
- normalisation lowercase ;
- trimming ;
- suppression des accents ;
- tokeniser les mots-clés.

### 7.2. Analyse de la fiche détaillée

Si la fiche contient des descriptions ou attributs nutritionnels, le parser doit extraire :
- ingrédients ;
- informations nutritionnelles ;
- catégorie / type de produit ;
- mots-clés utiles.

### 7.3. Règle d'évaluation

Exemple de logique simple :

```js
function scoreProduct(product) {
  const tokens = extractTokens(product.name + ' ' + product.detailText);

  if (tokens.includes('oignon') || tokens.includes('ail')) return 'high';
  if (tokens.includes('pomme') || tokens.includes('poire')) return 'moderate';
  if (tokens.includes('lait') || tokens.includes('fromage')) return 'moderate';
  return 'unknown';
}
```

Ensuite :
- `high` => `is_fodmap = true`, `fodmap_type = 'fructan'` ou autre
- `moderate` => `is_fodmap = true`, `fodmap_quantity = 'moderate'`
- `unknown` => `is_fodmap = false`/`null` selon l'état de la donnée

## 8. Couleur de fond sur la carte produit

### 8.1. Règles proposées

- vert : compatibilité forte / faible FODMAP
- orange : attention, modéré
- rouge : à éviter pour IBS
- gris : non évalué

### 8.2. Exemple

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
- ajouter un attribut ou une classe visuelle ;
- éventuellement afficher un badge `IBS` ou `FODMAP`.

## 9. Menu flottant d'export

### 9.1. But du menu

Le menu doit permettre rapidement :
- exporter les données locales de compatibilité ;
- importer un JSON ;
- vider la base locale ;
- vérifier le nombre d'entrées stockées.

### 9.2. Positionnement

- `position: fixed`
- `bottom: 16px; right: 16px;`
- petite icône flottante à gauche du bouton principal

### 9.3. Actions minimales

- bouton `Export JSON`
- bouton `Import JSON`
- bouton `Clear local storage`
- bouton `Stats`

## 10. Persistance et sécurité

- Les données sont stockées dans le navigateur, pas chez un tiers.
- Les données doivent rester portables via export JSON.
- Le script ne doit pas envoyer de données sensibles à un serveur externe.
- Le stockage local doit être découpé par clé afin de garder les données lisibles.

## 11. Étapes de conception détaillées

### Étape 1 — Reproduire le contexte réel

- ouvrir la page de liste ;
- ouvrir la page de fiche ;
- vérifier la page de magasin ;
- noter les sélecteurs HTML utiles.

### Étape 2 — Détecter les données productives

- vérifier comment San-A encode le `item_code` ;
- trouver le lien produit ;
- tester la récupération depuis `document.body.innerHTML` et DOM.

### Étape 3 — Créer le module de stockage

- définir la clé `sanA_ibs_db_v1` ;
- définir `readStorage()`, `writeStorage()`, `mergeProduct()`.

### Étape 4 — Construire le moteur de classification

- normaliser le nom ;
- extraire les mots-clés IBS/FODMAP ;
- associer les mots-clés à un type ;
- produire un score de compatibilité.

### Étape 5 — Branchements visuels

- repérer le conteneur de carte ;
- ajouter un fond couleur ;
- ou ajouter une badge ;
- ou ajouter un tooltip explicatif.

### Étape 6 — Ajouter le menu utilisateur

- petite icône ;
- panneau de commandes ;
- export JSON.

### Étape 7 — Validation sur un magasin réel

- tester sur `SNA_006` ;
- vérifier les éléments connus ;
- corriger le match sur les produits à forte valeur FODMAP ;
- enrichir la base locale de manuellement validé.

## 12. Plan d'implémentation

### Phase 1 — lecteur de page
- extraction `item_code`
- extraction `name`
- détection de type de page

### Phase 2 — stockage local
- JSON localStorage
- clé par `item_code`
- export / import / nettoyage

### Phase 3 — moteur de scoring
- analyse du nom
- analyse de la fiche détaillée
- calcul de niveau

### Phase 4 — rendu visuel
- fond de carte
- badge d'état
- panneau flottant

### Phase 5 — validation
- tests sur un magasin cible
- revue des faux positifs / faux négatifs
- enrichissement de la base

## 13. Problèmes connus et points de vigilance

- Le site peut charger le contenu dynamique ou via JS.
- Les informations nutritionnelles ne sont pas forcément présentes dans la page listée.
- La sélection du magasin est obligatoire pour accéder aux pages détaillées.
- Les valeurs FODMAP doivent rester humaines et auditables.

## 14. Conclusion

La solution la plus robuste consiste à combiner :
- extraction de données depuis les pages San-A ;
- base locale dans le navigateur ;
- logique de score IBS/FODMAP simple et lisible ;
- rendu visuel immédiat sur les cartes produits ;
- export JSON pour traitement hors navigateur.

Cette approche est légère, portable, et bien adaptée à un usage personnel de tri et d'analyse de produits.
