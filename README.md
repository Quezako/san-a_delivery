# San-A IBS / FODMAP Checker

Userscript de suivi de compatibilité IBS/FODMAP pour le site San-A Netsuper.

## Objectif

Le but est d'aider à analyser rapidement les produits San-A selon leur nom, leur fiche détaillée, leurs ingrédients et leur profil nutritionnel, puis d'afficher une couleur de fond sur la carte produit selon leur compatibilité avec un profil IBS.

Le script doit notamment traiter les cas suivants :
- liste de produits par catégorie ;
- fiche produit détaillée ;
- magasin sélectionné ;
- stockage local dans le navigateur sans dépendre du cache ;
- référence de base FODMAP adaptée au contexte japonais.

## 1. Installation du userscript

1. Ouvrir Tampermonkey (ou tout autre gestionnaire de userscripts compatible).
2. Importer le fichier `src/ibs-checker.user.js` localement, ou utiliser l’URL de mise à jour suivante :
   - `https://github.com/Quezako/san-a_delivery/raw/refs/heads/master/src/ibs-checker.user.js`
3. Vérifier que l’URL correspond à la zone San-A NetSuper : `https://netsuper.san-a.co.jp/shop/*`.
4. Charger une page de liste ou de détail pour vérifier que le panneau flottant apparaît bien.
5. Le script embarque désormais la version locale de la base FODMAP et les outils de maintenance associés.

## 2. Exploitation

### 2.1 Analyse normale

Une fois installé :

```bash
cd "d:/01-Drive/50-Dev/san-a_delivery"
python tools/generate_fodmap_reference.py
```

Puis :
- ouvrir une page San-A ;
- laisser le userscript analyser la fiche ou les cartes ;
- utiliser le menu flottant pour exporter JSON ou vérifier les stats.

### 2.2 Export des ingrédients inconnus

Lorsque le script détecte des ingrédients absents de la base locale, il peut exporter un fichier JSON :

- `san-a-ibs-unknown-terms.json`

Format attendu :

```json
{
  "reference_version": "v1",
  "unknown_terms": [
    "ごぼう",
    "サラダ油",
    "白いりごま",
    "ポン酢",
    "砂糖"
  ]
}
```

Ce fichier est la matière première pour l’enrichissement de la base de référence.

### 2.3 Enrichissement de la base via Python

Le flux de maintenance est le suivant :

```bash
cd "d:/01-Drive/50-Dev/san-a_delivery"
python tools/merge_unknown_terms.py --input san-a-ibs-unknown-terms.json --output data/unknown_terms_report.json
```

Ce script ne sert pas seulement à produire un rapport. Il va :
- comparer les termes inconnus avec la référence locale ;
- identifier les termes déjà connus et les termes manquants ;
- interroger un service de traduction externe (LibreTranslate) pour obtenir les formes anglaises et françaises des ingrédients japonais inconnus ;
- construire des entrées structurées à partir des traductions récupérées ;
- fusionner ces entrées dans `data/fodmap_reference.json` ;
- régénérer le fichier embarqué `src/fodmap_reference_embed.js` utilisé par le userscript.

Le rapport JSON produit contient aussi un historique exploitable :
- `already_known`
- `missing_terms`
- `known_count`
- `missing_count`
- `merged_terms`
- `translations`

C’est le point d’entrée du cycle de maintenance de la base.

### 2.4 Regénération canonique de la base locale

La génération complète de la référence reste la commande canonique :

```bash
cd "d:/01-Drive/50-Dev/san-a_delivery"
python tools/generate_fodmap_reference.py
```

Cette étape reconstruit complètement :
- `data/fodmap_reference.json`
- `data/foods_table.json`
- `data/fodmap_rules.json`
- `src/fodmap_reference_embed.js`

En pratique, le workflow recommandé est donc :
1. exporter les inconnus depuis le userscript ;
2. lancer `merge_unknown_terms.py` pour demander des traductions via LibreTranslate et fusionner les nouveaux termes ;
3. relire le rapport JSON et valider les résultats de traduction ;
4. relancer `generate_fodmap_reference.py` pour reconstruire la référence complète depuis les tables sources ;
5. recharger le userscript / recalculer le cache produit.

### 2.5 Recalcul du cache produit

Après une mise à jour de la base, il faut reprocesser les produits déjà vus sans refaire un scan manuel de tout le site :

- bouton `Re-analyser cache` dans le panneau flottant du userscript.

Le script recalcule :
- `fodmap_level`
- `matches`
- `risk`
- `status`
- à partir du texte d’ingrédients déjà stocké dans le cache local.

## URLs de référence

- Liste de produits : https://netsuper.san-a.co.jp/shop/list.php?category_code=102
- Fiche détaillée : https://netsuper.san-a.co.jp/shop/detail.php?group_code=100221&item_code=0000000000222
- Magasin cible : https://netsuper.san-a.co.jp/shop/storetour_entry.php?shop_code=SNA_006

## Conclusion de conception

Pour un volume de plusieurs centaines, voire milliers de produits, le meilleur stockage local est IndexedDB.

Pourquoi IndexedDB est préférable à localStorage :
- stockage beaucoup plus volumineux ;
- lecture/écriture plus adaptées aux objets structurés ;
- meilleure tolérance pour des bases de référence et des caches produits ;
- plus stable pour des données multi-entrées et des export/import JSON.

La logique recommandée est la suivante :
- un magasin de référence FODMAP, pré-généré et embarqué dans le projet : `data/fodmap_reference.json` ;
- un magasin de cache produit pour les données produit de San-A : `products` dans IndexedDB ;
- un magasin de résultats analysés : `product_analysis` dans IndexedDB ;
- un export JSON pour sauvegarde manuelle et transfert.

## Périmètre fonctionnel

- Détection automatique de la page actuelle (liste, fiche détaillée, magasin).
- Extraction de l'identifiant produit `item_code` et du nom produit en japonais.
- Analyse du nom produit et, si disponible, de la fiche détaillée.
- Extraction des ingrédients et des mots-clés susceptibles de poser problème (FODMAP).
- Traduction ou normalisation des ingrédients en anglais / français pour l'affichage utilisateur.
- Calcul d'un niveau de compatibilité selon un profil IBS.
- Affichage de couleur sur la carte produit :
  - vert = compatible / faible FODMAP ;
  - orange = attention / modéré ;
  - rouge = pour éviter / fort FODMAP ;
  - gris = inconnu / non évalué.
- Stockage local persistant via IndexedDB.
- Export des données IBS/FODMAP au format JSON.
- Menu flottant en bas à droite pour importer, exporter, nettoyer et consulter les statistiques.

## Modèle de données

### 1. Base de référence FODMAP

La base référence est une base de connaissances sur les aliments et ingrédients communs au Japon. Elle est pré-générée et embarquée dans le dépôt.

Exemple de structure :

```json
{
  "apple": {
    "canonical": "apple",
    "labels_ja": ["リンゴ", "りんご", "アップル"],
    "labels_fr": ["pomme"],
    "labels_en": ["apple"],
    "fodmap_group": "fructose",
    "fodmap_level": "high",
    "notes": "Fruit souvent haut en fructose et fréquemment problématique pour IBS."
  },
  "garlic": {
    "canonical": "garlic",
    "labels_ja": ["にんにく", "ニンニク", " garlic "],
    "labels_fr": ["ail"],
    "labels_en": ["garlic"],
    "fodmap_group": "fructan",
    "fodmap_level": "high",
    "notes": "Très fréquent dans les plats asiatiques."
  }
}
```

### 2. Résultat produit stocké localement

Le stockage local est indexé par `item_code`, avec un niveau produit + ingrédients trouvés.

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
    "confidence": "medium",
    "updated_at": "2026-10-19T00:00:00Z",
    "source": "detail-page"
  }
}
```

### 3. Format de référence recommandé

Le bon compromis est :
- `data/fodmap_reference.json` ou version compressée JSONG/CSV pour la base locale embarquée ;
- IndexedDB pour les produits et analyses actives du navigateur ;
- export JSON pour sauvegarde et rechargement.

Cela permet de garder la base de référence stable, lisible, et facile à enrichir sans dépendre du cache navigateur.

## Architecture proposée

### 1. Script userscript

Le script surveille la page chargée et branche les actions suivantes :
- détection du contexte (`list`, `detail`, `store`);
- extraction des informations produit ;
- lecture de la base référence FODMAP ;
- lecture/écriture dans IndexedDB ;
- affichage visuel sur la carte produit ;
- export JSON pour sauvegarde locale.

### 2. Base de référence FODMAP locale

La base de référence doit être un fichier de données embarqué dans le dépôt, généré ou enrichi à partir d'une liste de produits alimentaires japonais communs.

Le fichier doit contenir :
- `canonical_name`
- `labels_ja`
- `labels_en`
- `labels_fr`
- `fodmap_group`
- `fodmap_level`
- `is_fodmap`
- `notes`
- `source`

### 3. Base locale du navigateur

L'UI ne doit pas dépendre des valeurs en mémoire de session. Les données persistant dans le navigateur sont gérées par IndexedDB avec les stores :
- `products`
- `reference`
- `analysis`
- `manual_edits`

### 4. Règles de catégorisation

Exemple de logique :
- faible FODMAP => compatible / vert
- modéré => orange / à surveiller
- fort => rouge / éviter
- inconnu => gris

## Affichage des ingrédients problématiques

Un produit en japonais doit pouvoir afficher aussi les ingrédients qui comptent :
- en japonais : `にんにく`, `りんご`, `ネギ`, `大根`, etc.
- en anglais : `garlic`, `apple`, `onion`, `asparagus`
- en français : `ail`, `pomme`, `oignon`, `asperge`

Le but est de rendre le signal compréhensible même si l'utilisateur connaît mieux une langue que l'autre.

## Data strategy recommandée

### Option A — fichier de données embarqué dans le script

Avantages :
- facile à distribuer ;
- aucun besoin de backend ;
- très simple pour un userscript autonome.

Inconvénients :
- fichier lourd si la base grossit ;
- moins pratique à éditer et valider ;
- plus difficile à maintenir en plusieurs langues.

### Option B — mini base JSON/CSV pré-générée dans le dépôt

Avantages :
- très lisible ;
- facile à versionner ;
- facile à enrichir et à comparer ;
- beaucoup plus propre pour un projet de recherche et de collecte.

Recommandation :
- créer un fichier JSON ou CSV source de référence dans `data/` ;
- le charger dans le userscript lors de l'init ;
- l'utiliser comme base pour le matching clé par clé.

### Option C — IndexedDB + base locale de référence dans le navigateur

Avantages :
- très bon pour le stockage persistant et les milliers d'entrées ;
- permet la personnalisation utilisateur ;
- bien adapté à la collecte locale et à l'export.

Recommandation finale :
- base de référence pré-générée dans le dépôt ;
- base produit + analyse dans IndexedDB ;
- export/import JSON pour sauvegarde.

## Workflow d'exploitation et de maintenance

Le cycle de vie attendu du projet est le suivant :

1. Le userscript analyse un produit et extrait les ingrédients du bloc principal (`.proditem-main` ou équivalent).
2. Les termes trouvés sont comparés à la base locale embarquée.
3. Si un ingrédient n'est pas connu, il est ajouté à une liste d'`unknown_terms` locale.
4. L'utilisateur exporte cette liste au format JSON/CSV pour l'enrichissement manuel ou semi-automatique.
5. Un script Python prend cette liste, la compare avec les sources externes (Monash, corpus Japon / anglais / français, listes de supermarché), puis enrichit la base de référence.
6. Le fichier de référence est régénéré (`fodmap_reference_embed.js` ou JSON embarqué).
7. Le cache produit existant est recalculé en batch pour mettre à jour les anciens résultats sans refaire le scan manuel de toute la page.

### Schéma fonctionnel

```text
produits analysés
  -> ingrédients extraits
  -> inconnus détectés
  -> export JSON des ingrédients inconnus
  -> enrichissement via script Python + sources externes
  -> nouvelle base locale FODMAP
  -> recalcul du cache produit existant
  -> produits mis à jour avec nouveau niveau de risque
```

### Données locales utiles

Le stockage local du navigateur doit contenir au minimum :

- `reference_version` : version actuelle de la base FODMAP ;
- `products` : cache des produits déjà vus, avec texte des ingrédients et résultat d'analyse ;
- `unknown_terms` : termes non reconnus, à enrichir ;
- `manual_overrides` : corrections utilisateur si une décision doit être forcée.

### Action recommandée dans le panneau flottant

Ajouter des actions de maintenance comme :

- `Exporter les inconnus` ;
- `Importer une base enrichie` ;
- `Re-analyser le cache local` ;
- `Recharger la version de référence` ;
- `Vider les résultats locaux` ;
- `Afficher les statistiques`.

Cette séparation est importante : la base de référence est l'"atlas de connaissance", tandis que le cache produit est le "snapshot de produits déjà analysés". Quand la base change, on reprocessse seulement le cache, ce qui est beaucoup plus propre que de relancer un scan sur l'ensemble des pages.

## UI proposée

- Icône flottante dans le coin bas droit.
- Menu contextuel ou panneau latéral.
- Actions :
  - exporter JSON des produits ;
  - exporter les ingrédients inconnus ;
  - importer une base enrichie ;
  - re-analyser le cache local ;
  - effacer la base locale ;
  - afficher le nombre d'éléments connus ;
  - afficher produits à risque / neutres / inconnus.

## Déploiement

1. Installer un gestionnaire de userscript tel que Tampermonkey.
2. Ouvrir le fichier `src/ibs-checker.user.js` dans le navigateur.
3. Vérifier que le script s'exécute sur les pages San-A NetSuper.
4. Sélectionner le magasin cible : `SNA_006`.
5. Naviguer sur les pages liste / détail pour alimenter la base locale.
6. Exporter la base JSON régulièrement pour archiver les résultats.

## Fichiers du projet

- `README.md` : documentation générale
- `docs/conception-userscript-ibs.md` : étapes de conception détaillées
- `data/README.md` : note sur la structure de la base de référence
- `data/foods_table.json` : table des aliments / alias / catégories
- `data/fodmap_rules.json` : table de règles FODMAP
- `data/fodmap_reference.json` : sortie fusionnée prête à l'usage
- `tools/generate_fodmap_reference.py` : script de génération de la base locale
- `src/ibs-checker.user.js` : squelette du userscript
- `.gitignore` : exclusions Git standard

## Génération de la base

La base de référence locale est maintenant générée par un script Python dédié :

```bash
python tools/generate_fodmap_reference.py
```

Le schéma choisi sépare deux tables sources :
- `foods_table` pour les aliments, catégories et alias ;
- `fodmap_rules` pour les niveaux de risque et le groupe FODMAP ;
- puis `fodmap_reference` pour la version fusionnée utilisée par le userscript.

## Étapes de développement

1. Identifier les structures HTML des pages San-A.
2. Construire un extracteur d'`item_code` et de nom produit.
3. Créer le gestionnaire IndexedDB.
4. Définir les tables / stores : `reference`, `products`, `analysis`.
5. Construire la base de référence FODMAP japonaise commune.
6. Définir les règles de matching sur nom + ingrédients + détails.
7. Implémenter le rendu visuel sur les cartes.
8. Ajouter le panneau d'export/import.
9. Valider sur un magasin réel et corriger les faux positifs / négatifs.

## Limites

- Les pages ne sont pas accessibles sans magasin sélectionné.
- Certaines fiches peuvent omettre des ingrédients ou des informations détaillées.
- La base FODMAP doit rester une aide de décision, pas un diagnostic médical.
- Le script est conçu pour un usage personnel et un enrichissement manuel local.

## Licence

À définir selon le contexte du projet et l'usage final.
