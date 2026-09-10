# pdf-print-ready

> Skill Claude open source pour générer un HTML A4 print-ready propre, sans bricolage CSS.

Ce skill scaffold un HTML qui s'imprime en PDF impeccable via Chrome (⌘P, marges "Aucune"). Il intègre :

- Pages A4 figées à 297mm avec `overflow: hidden` (pas de débordement silencieux).
- Structure flexbox content + footer (zéro espace blanc forcé).
- Numérotation automatique via script JS (ajoute/retire une page, zéro update manuel).
- Anti-orphelins (`break-after: avoid` sur titres, leads, eyebrows).
- Tables avec lignes indivisibles et thead répété si coupure.
- Pre-flight checks anti-erreurs : em-dash français, identité légale sourcée SIRENE, créneaux calendrier vérifiés, chiffres marché sourcés ou retirés.
- Un script, `scripts/rendre_pdf.py`, qui mesure le remplissage et le débordement de chaque page dans le DOM (Chrome headless), imprime le PDF et rend un aperçu PNG par page. Une commande, un code de retour.

## Pour qui

- Freelances et consultants qui rédigent des livrables formels (notes d'intention, propositions, mémos).
- Agences qui produisent des PDF clients à la chaîne.
- Juristes, RH, comptables, formateurs qui éditent des documents structurés.
- Toute personne qui en a marre des PDF moches générés depuis HTML.

## Installation

### Claude Code

```bash
mkdir -p ~/.claude/skills/pdf-print-ready/references ~/.claude/skills/pdf-print-ready/scripts
curl -sL https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main/SKILL.md \
  -o ~/.claude/skills/pdf-print-ready/SKILL.md
curl -sL https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main/references/template.html \
  -o ~/.claude/skills/pdf-print-ready/references/template.html
curl -sL https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main/scripts/rendre_pdf.py \
  -o ~/.claude/skills/pdf-print-ready/scripts/rendre_pdf.py
```

Ou en une ligne, pour Claude Code et Cursor : `curl -sL https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main/install.sh | bash`.

Le script demande Google Chrome ou Chromium, et `pdftoppm` pour les aperçus (`brew install poppler`). Pas de dépendance Python.

### Cursor

```bash
mkdir -p ~/.cursor/skills/pdf-print-ready
curl -sL https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main/SKILL.md \
  -o ~/.cursor/skills/pdf-print-ready/SKILL.md
```

### Vérification

```bash
ls ~/.claude/skills/pdf-print-ready/SKILL.md   # Claude Code
ls ~/.cursor/skills/pdf-print-ready/SKILL.md   # Cursor
```

## Utilisation

Dans Claude Code :

```
/pdf-print-ready
```

Ou en délégation depuis un autre skill ou workflow :

```
"Génère un PDF de cette note d'intention en utilisant pdf-print-ready"
"Transforme ce markdown en PDF imprimable"
"Fais-en un livrable A4 propre"
```

Le skill lance une mini-interview (5 questions max) si le contenu n'est pas déjà structuré, génère le HTML autonome, puis mesure et imprime :

```bash
python3 ~/.claude/skills/pdf-print-ready/scripts/rendre_pdf.py livrable.html --audit    # pendant le calage
python3 ~/.claude/skills/pdf-print-ready/scripts/rendre_pdf.py livrable.html            # audit + PDF + aperçus
```

Le rapport dit, page par page, le remplissage (cible 80 à 95 %), le débordement en hauteur et en largeur, les textes rendus sous 9,5 px, SVG compris, et les textes de schéma qui chevauchent, sortent du cadre ou débordent d'une boîte. Pour le document : pages du PDF contre sections, tirets cadratins, classes sans règle CSS, polices non chargées.

## Exemple de rendu

Voir le mini guide [`examples/mini-guide-print-ready.html`](examples/mini-guide-print-ready.html) : **6 pages A4, généré par le skill lui-même comme méta-preuve**. Ouvre-le dans Chrome, fais ⌘P (marges "Aucune", graphiques d'arrière-plan cochés), tu obtiens le PDF de référence.

Le mini guide explique les 5 règles d'or du pattern :
1. Page A4 figée à 297mm (pas extensible)
2. Structure flexbox content + footer
3. Numérotation automatique via script JS
4. Anti-orphelins de titre
5. Tables avec lignes indivisibles et thead répété

## Pourquoi ce skill existe

Génerer un PDF propre depuis du HTML est étonnamment difficile. Les pièges classiques :

- `min-height: 297mm` qui laisse Chrome ajouter des pages silencieusement → numérotation cassée
- `.page-num` en `position: absolute` qui flotte sans contenu autour → espaces blancs énormes
- `page-break-inside: avoid` mal placé qui force des sauts brutaux avec gros vides
- Numéros de page en dur ("02 / 10") qui sautent à la moindre modif
- Em-dash (—) typographiquement faux en français
- Chiffres marché inventés non sourcés
- Créneaux RDV donnés sans vérifier le calendrier

Ce skill encapsule la recette qui évite tous ces pièges. Elle a été validée sur un livrable commercial réel (note d'intention de partenariat, 10 pages, envoyée à 3 dirigeants d'une SAS française) avant publication.

## Auteur et licence

Maintenu par [Uccello Labs](https://uccellolabs.com), éditeur d'**Uccello Hub** (plateforme IA d'entreprise) et concepteur de l'équipe IA **Uccello Crew** (25 skills pour vendre plus, mieux, plus cher).

Licence : MIT.

## Contribuer

Les PR sont bienvenues. Cas d'usage non couverts, bugs, suggestions : ouvrir une issue ou contacter `hello@uccellolabs.com`.

## Découvrir Uccello Crew

`pdf-print-ready` est un skill complémentaire à l'équipe IA Uccello Crew. Si tu veux les 25 skills commerciaux qui vont avec (idea-finder, persona, pricing, cold-call, discovery-call, VSL, proposal, brand…) :

→ [uccellolabs.com](https://uccellolabs.com)
