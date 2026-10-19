# San-A IBS / FODMAP Checker

Userscript de suivi de compatibilité IBS/FODMAP pour le site San-A Netsuper.

## Objectif

Le but est d'aider à analyser rapidement les produits San-A selon leur nom, leur fiche détaillée et leurs propriétés nutritionnelles, puis d'afficher une couleur de fond sur la carte produit selon leur compatibilité avec un profil IBS.

Le script cible des cas comme :
- liste de produits par catégorie ;
- fiche produit détaillée ;
- sélection d'un magasin ;
- stockage local du navigateur pour éviter de dépendre du cache.

## URLs de référence

- Liste de produits : https://netsuper.san-a.co.jp/shop/list.php?category_code=102
- Fiche détaillée : https://netsuper.san-a.co.jp/shop/detail.php?group_code=100221&item_code=0000000000222
- Magasin cible : https://netsuper.san-a.co.jp/shop/storetour_entry.php?shop_code=SNA_006

## Périmètre fonctionnel

- Détection automatique de la page actuelle (liste ou fiche détaillée).
- Extraction de l'identifiant produit `item_code` et du nom produit.
- Analyse du nom produit et, si disponible, de la fiche détaillée.
- Calcul d'un niveau de compatibilité selon un profil IBS.
- Affichage de couleur de fond sur la carte produit :
  - vert = compatible / faible FODMAP ;
  - orange = attention / modéré ;
  - rouge = pour éviter / fort FODMAP ;
  - gris = inconnu / non évalué.
- Stockage des données par `item_code` dans le navigateur via `localStorage` ou `IndexedDB`.
- Export des données IBS/FODMAP en JSON.
- Menu flottant en bas à droite pour importer, exporter et nettoyer les données.

## Modèle de données

Le stockage local doit être indexé par `item_code`.

Exemple de structure :

```json
{
  "0000000000222": {
    "item_code": "0000000000222",
    "name": "Tomate cerise",
    "is_fodmap": true,
    "fodmap_type": "fructose",
    "fodmap_quantity": "moderate",
    "confidence": "manual",
    "updated_at": "2026-10-19T00:00:00Z",
    "source": "manual-review"
  }
}
```

Autre format plus compact, selon l'usage :

```json
{
  "0000000000222": {
    "is_fodmap": true,
    "fodmap_type": "fructan",
    "fodmap_quantity": "high",
    "source": "detail-page"
  }
}
```

## Architecture proposée

### 1. Script userscript

Le script surveille la page chargée et branche les actions suivantes :
- détection du contexte (`list`, `detail`, `store`);
- extraction des informations produit;
- lecture/écriture dans le stockage navigateur;
- affichage visuel sur la carte produit;
- export JSON pour sauvegarde ou analyse locale.

### 2. Base locale de compatibilité IBS

La base locale peut être gérée comme une table JSON simple ou une base SQLite dans le navigateur si on choisit une implémentation plus avancée.

Les champs recommandés :
- `item_code`
- `name`
- `is_fodmap`
- `fodmap_type`
- `fodmap_quantity`
- `source`
- `confidence`
- `updated_at`

### 3. Règles de catégorisation

Exemple de logique approximative :
- faible FODMAP => compatible / vert
- modéré => orange / à surveiller
- fort => rouge / éviter
- inconnue => gris

## UI proposée

- Icône flottante en bas à droite.
- Menu contextuel ou panneau latéral.
- Actions :
  - exporter JSON ;
  - importer JSON ;
  - effacer la base locale ;
  - afficher le nombre d'éléments connus ;
  - afficher les produits IBS / non IBS.

## Déploiement

1. Installer un gestionnaire de userscript comme Tampermonkey.
2. Ouvrir le fichier `src/ibs-checker.user.js` dans le navigateur.
3. Vérifier que le script s'exécute sur les pages San-A NetSuper.
4. Sélectionner le magasin ciblé : `SNA_006`.
5. Naviguer sur les listes et fiches détaillées pour générer la base locale.

## Fichiers du projet

- `README.md` : documentation générale
- `docs/conception-userscript-ibs.md` : étapes de conception détaillées
- `src/ibs-checker.user.js` : squelette du userscript
- `.gitignore` : exclusions Git standard

## Étapes de développement

1. Identifier les structures HTML des pages San-A.
2. Construire un extracteur d'`item_code` et de nom.
3. Créer le stockage navigateur local.
4. Définir les règles de compatibilité IBS/FODMAP.
5. Implémenter le rendu visuel sur les cartes.
6. Ajouter le panneau d'export/import.
7. Valider sur un magasin réel et corriger les cas edge.

## Limites

- Les pages ne sont pas accessibles sans magasin sélectionné.
- Certaines fiches peuvent omettre des informations sur les FODMAP.
- Le script est conçu pour un usage personnel et un enrichissement manuel local.

## Licence

À définir selon le contexte du projet et l'usage final.
