---
name: pdf-print-ready
description: Scaffold un HTML print-ready pour générer un PDF A4 propre. Pages figées 297mm avec overflow contrôlé, structure flexbox content+footer (zéro vide forcé), numérotation auto via JS (plus jamais en dur), pré-checks anti-erreurs (em-dash, identité légale sourcée, créneaux calendrier vérifiés, chiffres marché sourcés ou retirés), et un script `scripts/rendre_pdf.py` qui mesure le débordement de chaque page dans le DOM, imprime le PDF en headless et rend un aperçu par page. À utiliser pour tout livrable destiné PDF imprimable : note d'intention, proposition commerciale, pitch deck, lead magnet, contrat, brief partenaire, mémo officiel, étude de cas, compte-rendu de RDV formel.
metadata:
  trigger: générer un PDF, imprimer en PDF, livrable PDF, document imprimable, note d'intention, contrat, brief partenaire, mémo officiel, lead magnet PDF, proposition commerciale PDF, pitch deck PDF, étude de cas PDF
  license: MIT
  author: Uccello Labs (https://uccellolabs.com)
---

# pdf-print-ready

---

## Rôle

Tu génères le squelette HTML+CSS+JS d'un document A4 print-ready, prêt à être imprimé en PDF via Chrome (⌘P, sans marges). Pas de bricolage CSS chaotique, pas d'espaces blancs forcés, pas de coupures malheureuses, pas de numérotation manuelle. Recette éprouvée terrain.

Tu **ne rédiges pas le contenu** du livrable. Tu produis le contenant et tu intègres le contenu fourni par l'utilisateur, par un fichier source markdown, ou par un autre skill qui te délègue la mise en forme print.

---

## Quand t'invoquer

- L'utilisateur a un contenu structuré (markdown, plan de sections, brief) et veut un livrable A4 imprimable.
- Un workflow ou un autre skill a besoin de produire un HTML destiné PDF (note d'intention, contrat, lead magnet, etc.).
- L'utilisateur dit : "génère un PDF", "fais-moi un livrable imprimable", "fais-en un format A4", "transforme ça en PDF".

---

## Quand NE PAS t'invoquer

- Le livrable cible est un site web responsive (utiliser un skill web dédié).
- Le livrable est un email, un post social, un script verbatim (pas de besoin print).
- L'utilisateur veut juste un markdown propre (rester en .md).

---

---

## Inputs attendus

1. **Contenu source** : markdown structuré, plan de sections, ou brief verbatim. Si rien n'est fourni, lance une mini-interview (5 questions max) pour récupérer :
   - Titre du livrable
   - Sous-titre / accroche
   - Destinataire(s) : interne, externe nominatif, ou externe public
   - Plan des pages (titres des sections)
   - Mentions légales nécessaires (parties au contrat ? si oui, demander la forme juridique + SIREN ou les chercher via API)

2. **Design system** (lu depuis `PROJECT_CONTEXT.md` du projet actif si disponible, sinon utilise un défaut sobre) :
   - Palette : primaire, secondaire, texte, muted, background
   - Typo : header (par défaut Space Grotesk), body (par défaut Inter)
   - Brand mark : nom à afficher en haut de chaque page

3. **Nombre de pages cibles** : 1 (one-pager), 4-6 (brief court), 8-12 (note d'intention type), 15-20 (lead magnet ou pitch deck long).

---

---

## Workflow

**Un document se fabrique en phases, et chaque phase se ferme avant d'ouvrir la suivante.**
Une phase se ferme par un contrôle, pas par une impression de fini : tant que le contrôle
n'a pas tourné, « c'est terminé » est un sentiment.

| Phase | Ce qu'elle produit | Le contrôle qui la ferme |
|---|---|---|
| Le contenu | Le texte, validé sur le fond | La relecture de l'auteur. Ce skill ne rédige pas |
| **Les schémas** | Chaque SVG, seul | `rendre_pdf.py <schema> --schema` |
| La mise en page | Le HTML paginé | `rendre_pdf.py <document> --audit` |
| L'impression | Le PDF | Les aperçus, ouverts un à un |

**L'ordre n'est pas du confort, il suit les dépendances.** Un schéma repris après la mise en
page fait repasser toute la mise en page : le recadrer change sa hauteur, donc le remplissage
des pages, donc les coupes de texte décidées autour. Ce qui porte le reste se ferme en premier.

### Fermer la phase des schémas

```bash
python3 scripts/rendre_pdf.py mon-schema.svg --schema
python3 scripts/rendre_pdf.py mon-schema.svg --schema --largeur 120   # colonne étroite
```

Le schéma est posé seul sur une page A4, à la largeur réelle qu'il aura dans le document, et
mesuré là. Ce que le contrôle attrape, et qu'aucune relecture visuelle ne donne de façon
fiable :

- **Un trait qui passe sous un mot.** Il ne chevauche aucun texte et ne déborde d'aucune boîte :
  il ne se voit qu'à la lecture, et seulement quand on le cherche. Le tracé est échantillonné
  point par point, pas approximé par sa boîte englobante, qui serait fausse en diagonale.
- **Un texte trop petit à l'impression.** Un SVG réduit à la largeur d'une page imprime son
  texte à `font-size × largeur rendue / largeur du viewBox` : du 15 px devient du 8,9 px. Le
  rapport rend la taille effective **et le facteur à appliquer**, parce que corriger sans le
  facteur revient à tâtonner.
- Un texte qui sort du cadre, qui déborde de sa boîte, ou qui en chevauche un autre.

Le code de sortie vaut 1 tant qu'un défaut reste : la phase n'est pas fermée.

### Étape 0 : détection contexte et inputs

1. Si un `PROJECT_CONTEXT.md` (ou équivalent : brand-guidelines, design-tokens.json) existe dans le répertoire courant ou son arborescence parente, le lire pour récupérer le design system (palette, typo, nom de marque). Sinon utiliser un défaut sobre (palette neutre #1D4ED8 primaire, Space Grotesk + Inter).
2. Confirmer les inputs avec l'utilisateur : contenu source (markdown ou brief), plan des pages, destination du livrable, design system retenu.

### Étape 1 : pre-flight checks (CRITIQUE, avant toute génération)

Si le livrable est destiné à un tiers (externe nominatif ou externe public), exécuter cette checklist BEFORE de générer le HTML :

1. **Identité légale des parties au contrat (si applicable)**. Si le livrable mentionne une société (Partie A, Partie B, signataires), exiger la source SIRENE. Proposer :
   - Lookup automatique via l'API `recherche-entreprises.api.gouv.fr` (gratuit, sans clé, source officielle SIRENE) :
     ```
     curl 'https://recherche-entreprises.api.gouv.fr/search?q=<nom>&per_page=5'
     ```
   - Champs à récupérer : raison sociale exacte, forme juridique (SARL/SAS/EURL...), SIREN, adresse siège, qualité officielle des dirigeants (Président, Gérant, DG...).
   - Si l'API retourne "Président de SAS", traduire en "Président" (titre français usuel, "de SAS" est une description du registre).

2. **Créneaux horaires (si applicable)**. Si le document mentionne un RDV, call, briefing : appeler un MCP Calendar (Google Calendar ou autre) sur la fenêtre concernée AVANT d'écrire un créneau. Vérifier :
   - Le créneau est sur un jour travaillé de l'utilisateur (ne pas inventer "lundi" ou "mercredi" si l'utilisateur ne travaille pas ces jours-là).
   - Aucun conflit avec un événement existant.
   - Pas d'événement "Absent du bureau" qui couvre la plage.
   - Pas de violation du cap horaire sommeil de l'utilisateur s'il en a un.
   - Si MCP Calendar absent : demander à l'utilisateur de confirmer les créneaux de son côté, ne pas inventer.

3. **Chiffres marché / coûts / benchmarks**. Tout chiffre cité doit être :
   - **Vérifié** : URL ou étude citable.
   - **Estimé** : méthode de calcul explicite.
   - **À confirmer terrain** : avec mention explicite "à mesurer en pilote".
   - Sinon : retirer le chiffre ou reformuler en qualitatif ("plusieurs", "des dizaines", "à mesurer"). Aucun chiffre rond inventé (10, 100, 1 000).

4. **Em-dash (tiret cadratin U+2014)**. Scan le contenu source. Si présent, remplacer par `:` (définition), `,` (incise), `(...)` (parenthèse), ou point. Le tiret cadratin n'est pas un usage typographique français.

5. **Confidentialité selon destination**.
   - **Interne** : noms, montants, dates, % autorisés.
   - **Externe nominatif** : nommer uniquement le destinataire. Pas de noms de tiers, pas de montants de deals tiers.
   - **Externe public** : anonymiser tous les tiers, aucun nom, montant, ou date de signature en clair.

### Étape 2 : générer le HTML print-ready

Utiliser le template `references/template.html` comme base. Substituer :
- `{{title}}` : titre du document
- `{{primary_color}}`, `{{secondary_color}}`, `{{text_color}}`, etc. : palette du PROJECT_CONTEXT
- `{{brand_mark}}` : nom de marque en uppercase (ex: "UCCELLO LABS × GREEN4CLOUD")
- `{{header_subtitle}}` : sous-titre du header (ex: "Note d'intention · 22 mai 2026")
- `{{pages}}` : itérer sur chaque page avec sa structure

### Étape 3 : pages individuelles

Chaque page suit la structure :

```html
<section class="page">
  <div class="page-header">
    <span class="brand-mark">{{brand_mark}}</span>
    <span>{{header_subtitle}}</span>
  </div>
  <div class="page-content">
    <!-- Contenu de la page ici -->
  </div>
  <footer class="page-footer">
    <div class="page-num" data-sheet-num></div>
  </footer>
</section>
```

**Règle d'or** : `data-sheet-num` reste vide en HTML. Le script JS le remplit automatiquement à `01 / 13`, `02 / 13`, etc. Plus jamais de numéro en dur.

### Étape 4 : calibration du contenu, mesurée

Chaque page doit remplir ~80-95% de la hauteur A4. Si une section dépasse, splitter en 2 pages. Si une section fait moins de 60%, soit accepter un blanc sobre en bas, soit consolider avec la section suivante.

**Le débordement ne se juge pas à l'œil, il se mesure.** Le script du skill le fait avec Chrome en headless :

```bash
python3 scripts/rendre_pdf.py livrable.html --audit
```

Il rend, page par page, le remplissage, le débordement en hauteur et en largeur, les conteneurs à défilement dont le contenu est coupé (un tableau plus large que sa carte perd ses dernières colonnes sans que la page déborde), les blocs qui sortent de leur cadre sans être coupés par lui (verdict `HORS CADRE`, voir le piège 14), les textes rendus sous 9,5 px (y compris dans les SVG, dont la taille réelle dépend du `viewBox`), et les défauts de schéma : un texte qui chevauche un autre texte, qui sort du cadre du SVG ou qui déborde de sa boîte. Boucle : corriger, relancer, jusqu'à ce que chaque page soit `ok`. Quand une page déborde sans qu'on sache où couper, `--detail` donne la hauteur de chaque bloc :

```bash
python3 scripts/rendre_pdf.py livrable.html --audit --detail
```

Cinq à huit passes sont normales sur un document de dix pages. C'est moins long que de deviner.

### Étape 5 : impression et contrôle visuel

```bash
python3 scripts/rendre_pdf.py livrable.html
```

Une commande : l'audit, le PDF (à côté du HTML, même nom), et un aperçu PNG de chaque page dans `<nom>_pages/`. Le code de retour vaut 1 si une page déborde ou si le PDF compte plus de pages que de sections, ce qui permet de l'enchaîner dans un script.

Puis **ouvrir les aperçus un par un**. La mesure ne voit ni un libellé qui en chevauche un autre, ni une colonne de tableau tronquée par `overflow-x`, ni une légende coupée au bord d'un SVG : seul l'œil les voit, et c'est le seul moment où il est indispensable. Corriger, relancer la commande, et livrer le PDF qu'elle produit.

Enfin, logguer l'action dans le journal de session du projet si l'utilisateur en a un.

---

---

## La recette CSS et JS, et les composants

**Ils sont dans [`references/RECETTE_A4.md`](references/RECETTE_A4.md), et ce fichier est leur
seule source.** Les règles CSS et JS à embarquer dans tout HTML produit, les composants prêts à
poser, la fusion de deux sous-sections pour éviter les demi-pages vides, et les pièges déjà payés.

**À lire avant de générer**, pas après avoir constaté un débordement. **À ne pas recopier ici** :
un dépôt qui adapte ce skill adapte la conduite, jamais la technique, et c'est ce qui permet de la
mettre à jour pour tout le monde d'un seul endroit.

---

## Pre-flight checklist (à valider AVANT de remettre le livrable)

- [ ] `.page` figée à `height/min/max-height: 297mm` + `overflow: hidden`
- [ ] Structure `.page > .page-content + .page-footer` avec flexbox column
- [ ] `.page-footer` calé via `margin-top: auto` (PAS position: absolute)
- [ ] `break-after: avoid` sur tous les `h1-h4` + `p.lead` + `section-eyebrow + h2`
- [ ] `table tr { break-inside: avoid }` + `table thead { display: table-header-group }`
- [ ] `@page { size: 210mm 297mm; margin: 0 }`
- [ ] `-webkit-print-color-adjust: exact` dans `@media print`
- [ ] Numérotation auto via script JS (data-sheet-num), zéro numéro en dur
- [ ] Aucun em-dash (—) dans le contenu
- [ ] Identité légale sourcée SIRENE (si parties au contrat)
- [ ] Créneaux horaires vérifiés calendrier (si RDV mentionnés)
- [ ] Chiffres sourcés ou marqués "à mesurer / à confirmer"
- [ ] Confidentialité respectée selon destination (interne / externe nominatif / externe public)
- [ ] `python3 scripts/rendre_pdf.py livrable.html` rend un code 0 : chaque page `ok` (80-95 %), aucun débordement en hauteur ni en largeur, autant de pages au PDF que de sections
- [ ] Toutes les classes CSS utilisées sont définies (le rapport liste les classes fantômes type `.divider`)
- [ ] Aucune police < 9,5px, taille effective des SVG comprise (le rapport les liste)
- [ ] Aucune media query de largeur ne change la mise en page à 794 px (piège 13)
- [ ] Dans les schémas, aucun texte ne chevauche un autre texte, ne sort du cadre du SVG ni ne déborde de sa boîte (verdict `SCHEMA` absent du rapport)
- [ ] Aucun tableau ni bloc coupé par un `overflow` de conteneur (verdict `TRONQUE` absent du rapport)
- [ ] Aucun bloc ne sort de la bordure du cadre qui le porte (verdict `HORS CADRE` absent du rapport)
- [ ] Les aperçus PNG ont été ouverts un par un : pas de libellé qui chevauche, pas de colonne tronquée
- [ ] Pages fusionnées : en-tête = pied (libellé combiné), `.divider` visible entre sous-sections
- [ ] Sommaire généré depuis le DOM (numéros réels), sous-entrées pour les pages fusionnées
- [ ] Chaque chiffre porte un badge de catégorie (Vérifié / Estimé / À confirmer / Capacité)
- [ ] Graphiques utilisés là où un visuel aide (entonnoir, 2×2, frise, cartes, barres) plutôt qu'un paragraphe

---

---

## Répartir le contenu en pages, au lieu de le couper à l'estime

**`scripts/rendre_pdf.py` mesure, il ne répartit pas.** Il dit ce qui déborde, ce qui est creux et
ce qui est serré : c'est un constat, pas une coupe. Tant que la coupe se fait à la main, elle se
refait **en entier** à chaque retouche du texte.

Mesuré le 16/09/2026 sur deux documents mis en page le même jour : quinze pages remplies de 21 % à
57 % pour la première version, deux recompositions manuelles pour arriver à onze pages correctes,
et le même travail refait de zéro sur le second. Plus deux titres orphelins et un titre « suite »
en double, **que la mesure ne voyait pas** parce que ces pages n'avaient rien d'anormal.

```bash
python3 scripts/repartir_pages.py <doc.html>              # le plan, rien n'est écrit
python3 scripts/repartir_pages.py <doc.html> --appliquer  # écrit <doc>.pagine.html
```

**La convention d'entrée.** Le document porte **une seule page**, et dans sa zone de contenu un
conteneur `data-flux` dont chaque enfant direct est un bloc. Un bloc ne se coupe jamais.

- **`data-titre`** sur un bloc : il ne restera jamais seul en bas de page.
- **`data-ensemble="<clé>"`** sur des blocs voisins : ils partent ensemble.

**Le flux est mesuré dans une vraie page**, donc à la largeur réelle du contenu. Mesurer ailleurs
donnerait des hauteurs fausses.

**Un bloc plus haut qu'une page part seul et se signale, il ne se coupe pas** : le couper voudrait
dire rédiger à la place de l'auteur.

**Et le résultat se remesure après écriture**, jamais le seul calcul : les hauteurs changent quand
les blocs se regroupent, une marge disparaît en haut de page, un titre suivi d'un tableau ne prend
pas la même place qu'un titre suivi d'un paragraphe.

---

## Comment générer le PDF final

### Par le script (recommandé)

```bash
python3 scripts/rendre_pdf.py livrable.html
python3 scripts/rendre_pdf.py livrable.html --pdf sortie.pdf --apercus apercus/ --dpi 80
python3 scripts/rendre_pdf.py livrable.html --json      # pour un autre outil
```

Prérequis : Google Chrome ou Chromium (détecté sur macOS et dans le `PATH`, sinon `--chrome` ou la variable `CHROME`). Les aperçus demandent `pdftoppm` (`brew install poppler`) ; sans lui, le script produit l'audit et le PDF et le dit. Aucune dépendance Python.

Ce que le script fait, dans l'ordre : il copie le HTML à côté de l'original avec un script d'audit injecté (les chemins relatifs restent valables), le charge dans Chrome headless à 794 px de large pour que les media queries soient celles de l'impression, attend les polices, mesure, puis imprime avec `--print-to-pdf` sans en-tête ni pied, compte les pages du PDF et rend chaque page en PNG. La copie temporaire est effacée.

### À la main (si Chrome headless n'est pas disponible)

L'utilisateur ouvre le fichier dans Chrome puis :

1. ⌘P (Cmd+P) pour ouvrir la boîte d'impression
2. Destination : "Enregistrer au format PDF"
3. Mise en page : Portrait
4. Pages : Tout
5. Mise à l'échelle : Par défaut (100%)
6. **Marges : Aucune** (critique, sinon le padding se cumule)
7. **Cocher "Graphiques d'arrière-plan"** (sinon les dégradés et fonds colorés sautent)
8. Enregistrer

---

---

## Exemples de livrables à générer avec ce skill

- **Note d'intention** de partenariat ou de pré-contrat
- **Proposition commerciale** nominative à un prospect identifié
- **Pitch deck** B2B, 10-15 slides exportables en PDF
- **Lead magnet** type guide méthode, 8-20 pages
- **Contrat ferme** ou conditions particulières
- **Brief partenaire** formel (agence, freelance, intégrateur, sous-traitant)
- **Mémo officiel** interne ou externe (CODIR, board, partenaire stratégique)
- **Étude de cas** client publiable
- **Compte-rendu de RDV** formel adressé à un tiers
- **Rapport d'audit** ou de diagnostic

---

---

## Output attendu

Un fichier HTML autonome (`<projet>/livrables/<NOM>.html`) avec :
- CSS embarqué (pas de dépendance externe sauf Google Fonts)
- Script JS embarqué (numérotation auto)
- Contenu structuré en pages calibrées
- Le PDF produit par `scripts/rendre_pdf.py`, avec son rapport à code 0, et les aperçus ouverts

Logguer dans le journal de session du projet (si applicable) :
```
[DATE] /pdf-print-ready : généré <NOM>.html, N pages, destination <interne|externe nominatif|externe public>, pre-flight checks ✅
```

---

---

## Sources et références

- API SIRENE (Annuaire des Entreprises, gratuite, sans clé) : `https://recherche-entreprises.api.gouv.fr`
- Pas de tiret cadratin en français : usage typographique préférer `:`, `,`, parenthèses, ou point
- Pattern CSS validé terrain le 22/05/2026 sur un livrable commercial réel

---

---

## À propos

`pdf-print-ready` est un skill open source maintenu par [Uccello Labs](https://uccellolabs.com), éditeur d'**Uccello Hub** (plateforme IA d'entreprise souveraine) et concepteur de l'équipe IA **Uccello Crew**.

**Contributions bienvenues** : fork, PR, signalement de bugs ou de cas d'usage non couverts.

**Découvrir l'équipe IA complète Uccello Crew** (25 skills pour vendre plus, mieux, plus cher) : [uccellolabs.com](https://uccellolabs.com).

Licence : MIT.

---

---

## Un schéma se pose dès qu'il fait comprendre plus vite, et ça ne se demande pas

C'est une étape de la fabrication, pas une option de confort, et elle ne se déclenche pas sur une
demande du lecteur.

**Le test est unique** : est-ce qu'un lecteur qui ne connaît pas le dossier comprend plus vite avec
l'image qu'avec le paragraphe ? Si oui, le paragraphe reste et le schéma s'ajoute. **Le schéma ne
remplace pas le texte**, il le rend saisissable d'un coup d'œil.

**Cinq formes qui appellent un schéma, presque à coup sûr :**

| Ce que dit le texte | Ce qu'on dessine |
|---|---|
| Plusieurs acteurs qui s'échangent quelque chose | Le flux, avec le goulot mis en évidence |
| Qui voit quoi, qui a le droit de quoi | Les acteurs en colonnes, et la cloison en trait interrompu |
| Une suite d'étapes numérotées | La chaîne, groupée par phase |
| Un seuil, une bascule, une fourchette | L'échelle, avec la zone marquée |
| Un avant et un après, deux options comparées | Les deux colonnes face à face |

**Ce qui n'en appelle pas** : une énumération de faits sans relation entre eux, un chiffre isolé,
une liste d'actions. Un schéma qui ne montre qu'une liste encadrée coûte une demi-page et
n'apprend rien.

**L'ordre ne se négocie pas** (voir le tableau des phases plus haut) : chaque schéma se ferme seul,
à la largeur réelle qu'il aura dans la page, **avant** la mise en page.

```bash
python3 scripts/rendre_pdf.py mon-schema.svg --schema
```

Poser un schéma dans un document déjà paginé fait repasser toute la pagination : sa hauteur change
le remplissage des pages, donc les coupes décidées autour.

**Deux règles de construction, payées sur un document réel :**

1. **Le `viewBox` se cale sur la largeur rendue.** Le contrôle rend le schéma sur 150 mm, soit
   567 px. Un `viewBox` de 640 réduit toute police de 11,4 % : du 10 px devient du 8,9 px, sous le
   seuil. Partir de polices à 11,5 px minimum dans un `viewBox` de 640, ou resserrer le `viewBox`.
2. **La boîte se dimensionne sur le texte, jamais l'inverse.** Compter environ 0,5 em par caractère
   en sans. Un libellé trop long se coupe en deux lignes ou se raccourcit ; il ne rétrécit pas.

**Un schéma se branche sur les variables de charte** (`var(--brand-1)`, `var(--brand-2)`…) et non
sur des couleurs figées, sinon il reste au neutre du gabarit pendant que le reste du document est
charté, et il faudra le reprendre à chaque changement de charte.

**Pourquoi c'est écrit ici et pas espéré.** Un compte rendu est sorti en six pages de prose et de
tableaux, contrôlé, charté, à code 0, **et sans un seul schéma**, alors que trois de ses passages en
appelaient un. Aucun contrôle ne l'a signalé, parce qu'aucun ne cherchait. Il a fallu que le
dirigeant le demande. **Une étape qu'on n'exécute que sur demande n'est pas une étape.**
