# Base de référence FODMAP locale

Ce dossier contient les données de référence utilisées pour identifier les aliments et ingrédients susceptibles d'être problématiques pour un profil IBS / FODMAP.

## Structure

- `foods_table.json` : table des aliments et des alias de recherche.
- `fodmap_rules.json` : table de règles FODMAP (groupe et niveau de risque).
- `fodmap_reference.json` : version fusionnée et prête à être consommée par le userscript.
- `source_manifest.json` : sources utilisées, liens, notes et provenance des données.

## Principe de conception

La base est volontairement séparée en deux niveaux :

1. `foods_table` : les aliments, leurs libellés et leurs variantes linguistiques.
2. `fodmap_rules` : les informations de risque FODMAP et la justification de classification.

Ensuite, la sortie `fodmap_reference.json` fusionne ces deux tables pour fournir un référentiel unique, lisible et exploitable par le userscript.

## Sources documentées

Les références principales sont :

- Monash University FODMAP app : https://www.monashfodmap.com/
- Darius Kazemi corpora / food names : https://github.com/dariusk/corpora/tree/master/data/foods
- Listes culinaires et ingrédients courants dans les supermarchés japonais : base de référence locale, maintenue manuellement dans le dépôt.

## Génération

Pour recréer les fichiers de données :

```bash
python tools/generate_fodmap_reference.py
```

## Limite

Cette base est une aide de décision, pas un diagnostic médical. Elle sert surtout à guider le matching dans le userscript et à conserver une trace des sources / versions.
