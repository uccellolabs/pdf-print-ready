---
name: pdf-print-ready
description: Scaffold un HTML print-ready pour générer un PDF A4 propre. Pages figées 297mm avec overflow contrôlé, structure flexbox content+footer (zéro vide forcé), numérotation auto via JS (plus jamais en dur), pré-checks anti-erreurs (em-dash, identité légale sourcée, créneaux calendrier vérifiés, chiffres marché sourcés ou retirés). À utiliser pour tout livrable destiné PDF imprimable : note d'intention, proposition commerciale, pitch deck, lead magnet, contrat, brief partenaire, mémo officiel, étude de cas, compte-rendu de RDV formel.
metadata:
  trigger: générer un PDF, imprimer en PDF, livrable PDF, document imprimable, note d'intention, contrat, brief partenaire, mémo officiel, lead magnet PDF, proposition commerciale PDF, pitch deck PDF, étude de cas PDF
  license: MIT
  author: Uccello Labs (https://uccellolabs.com)
---

# pdf-print-ready

## Rôle

Tu génères le squelette HTML+CSS+JS d'un document A4 print-ready, prêt à être imprimé en PDF via Chrome (⌘P, sans marges). Pas de bricolage CSS chaotique, pas d'espaces blancs forcés, pas de coupures malheureuses, pas de numérotation manuelle. Recette éprouvée terrain.

Tu **ne rédiges pas le contenu** du livrable. Tu produis le contenant et tu intègres le contenu fourni par l'utilisateur, par un fichier source markdown, ou par un autre skill qui te délègue la mise en forme print.

## Quand t'invoquer

- L'utilisateur a un contenu structuré (markdown, plan de sections, brief) et veut un livrable A4 imprimable.
- Un workflow ou un autre skill a besoin de produire un HTML destiné PDF (note d'intention, contrat, lead magnet, etc.).
- L'utilisateur dit : "génère un PDF", "fais-moi un livrable imprimable", "fais-en un format A4", "transforme ça en PDF".

## Quand NE PAS t'invoquer

- Le livrable cible est un site web responsive (utiliser un skill web dédié).
- Le livrable est un email, un post social, un script verbatim (pas de besoin print).
- L'utilisateur veut juste un markdown propre (rester en .md).

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

## Workflow

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

### Étape 4 : calibration du contenu

Chaque page doit remplir ~80-95% de la hauteur A4. Si une section dépasse, splitter en 2 pages. Si une section fait moins de 60%, soit accepter un blanc sobre en bas, soit consolider avec la section suivante.

**Test de débordement** : avec `overflow: hidden` sur `.page`, le contenu qui dépasse est tronqué visuellement à l'écran. Si tronqué → splitter ou compacter, pas bricoler le CSS.

### Étape 5 : pre-livraison

1. Vérifier que le HTML s'ouvre dans Chrome sans erreur console.
2. Tester ⌘P et vérifier le rendu PDF : pas d'em-dash, numérotation correcte, pas de coupures malheureuses, palette respectée.
3. Logguer l'action dans le journal de session du projet si l'utilisateur en a un.

---

## Recette CSS+JS (à embarquer dans tout HTML généré)

### CSS de base

```css
:root {
  --primary: {{primary_color}};
  --secondary: {{secondary_color}};
  --text: {{text_color}};
  --muted: {{muted_color}};
  --bg: {{bg_color}};
  --bg-alt: {{bg_alt_color}};
  --border: #E5E7EB;
  --success: #10B981;
  --warning: #F59E0B;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--bg-alt); }
body {
  font-family: '{{body_font}}', -apple-system, sans-serif;
  color: var(--text);
  line-height: 1.55;
  font-size: 12.5px;
}
h1, h2, h3, h4 {
  font-family: '{{header_font}}', sans-serif;
  font-weight: 600;
  letter-spacing: -0.01em;
  break-after: avoid;
  page-break-after: avoid;
}

/* RÈGLE D'OR : la page A4 est FIGÉE à 297mm, pas extensible */
.page {
  width: 210mm;
  height: 297mm;
  min-height: 297mm;
  max-height: 297mm;
  padding: 20mm 20mm 14mm;
  background: var(--bg);
  margin: 12px auto;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
  page-break-after: always;
  break-after: page;
}

.page-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.page-footer {
  flex: 0 0 auto;
  margin-top: auto;
  padding-top: 3mm;
  min-height: 6mm;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
}

.page-num {
  font-size: 9.5px;
  color: var(--muted);
  letter-spacing: 0.05em;
  line-height: 1;
}

.page-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 9.5px;
  color: var(--muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 10mm;
  min-height: 5mm;
}

.brand-mark { font-weight: 600; color: var(--primary); }

/* TABLES propres */
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px 0; }
table th, table td { padding: 6px 9px; font-size: 11px; }
table th {
  background: var(--bg-alt);
  text-align: left;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}
table td {
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  line-height: 1.5;
}
table tr:last-child td { border-bottom: none; }
table thead { display: table-header-group; }     /* se répète si table coupée */
table tr { break-inside: avoid; page-break-inside: avoid; }
table { break-inside: auto; page-break-inside: auto; }

/* Anti-orphelins */
p, li { orphans: 3; widows: 3; }
p.lead, .section-eyebrow + h2.section-title {
  break-after: avoid;
  page-break-after: avoid;
}

/* Blocs critiques indivisibles */
.callout, .sig-card, .toc, .lexique, .keep-together {
  page-break-inside: avoid;
  break-inside: avoid;
}

@media screen {
  .page:not(.cover) { overflow: auto; }   /* à l'écran, scroll si debug */
}

@media print {
  html, body {
    margin: 0;
    padding: 0;
    background: #fff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  @page {
    size: 210mm 297mm;
    margin: 0;
  }
  .page {
    width: 210mm;
    height: 297mm;
    margin: 0 auto;
    box-shadow: none;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
  }
}
```

### Script JS de numérotation automatique

À coller juste avant `</body>`. Ne JAMAIS écrire un numéro de page en dur dans le HTML.

```html
<script>
(function () {
  function pad(n) { return String(n).padStart(2, '0'); }
  function numberSheets() {
    var sheets = document.querySelectorAll('.page');
    var total = sheets.length;
    sheets.forEach(function (sheet, index) {
      var el = sheet.querySelector('[data-sheet-num]');
      if (el) el.textContent = pad(index + 1) + ' / ' + pad(total);
    });
    document.querySelectorAll('[data-total-pages]').forEach(function (el) {
      el.textContent = String(total);
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', numberSheets);
  } else {
    numberSheets();
  }
  window.addEventListener('beforeprint', numberSheets);
})();
</script>
```

**Avantages** :
- Ajouter / supprimer / déplacer une page : zéro update manuel.
- Pad à 2 chiffres ("01 / 13" plutôt que "1 / 13"), typographique.
- `beforeprint` recalcule juste avant le PDF.
- `<span data-total-pages></span>` ailleurs dans le doc référence le total dynamiquement.

---

## Composants utiles (à embarquer si nécessaire)

### Couverture avec dégradé

```html
<section class="page cover">
  <div class="page-header">
    <span class="brand-mark">{{brand_mark}}</span>
    <span>{{cover_meta}}</span>
  </div>
  <div class="page-content">
    <div class="cover-eyebrow">{{eyebrow}}</div>
    <h1 class="cover-title">{{title}}</h1>
    <p class="cover-sub">{{subtitle}}</p>
    <!-- Optionnel : blocs de présentation des parties, statut, métadonnées -->
  </div>
  <footer class="page-footer">
    <div class="page-num" data-sheet-num></div>
  </footer>
</section>
```

```css
.cover {
  background: linear-gradient(135deg, #0F172A 0%, var(--primary) 100%);
  color: #fff;
  padding: 28mm 22mm 16mm 22mm;
  break-inside: avoid;
  page-break-inside: avoid;
}
.cover .page-num { color: rgba(255,255,255,0.65); }
.cover .brand-mark { color: var(--secondary); }
.cover-eyebrow { font-size: 11.5px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--secondary); margin-bottom: 12mm; }
.cover-title { font-size: 38px; line-height: 1.1; font-weight: 700; margin-bottom: 6mm; }
.cover-sub { font-size: 17px; color: rgba(255,255,255,0.85); margin-bottom: 14mm; line-height: 1.4; }
@media print {
  .page.cover {
    background: linear-gradient(135deg, #0F172A 0%, {{primary_color}} 100%) !important;
  }
}
```

### Lexique pédagogique "Pour mieux comprendre"

```html
<div class="lexique">
  <p class="term"><strong>Terme</strong> : définition courte et claire.</p>
  <p class="term"><strong>Autre terme</strong> <em>(traduction ou contexte)</em> : définition.</p>
</div>
```

```css
.lexique {
  background: #F0F9FF;
  border-left: 3px solid var(--secondary);
  border-radius: 0 4px 4px 0;
  padding: 10px 13px;
  margin: 10px 0;
  page-break-inside: avoid;
  break-inside: avoid;
}
.lexique::before {
  content: 'POUR MIEUX COMPRENDRE';
  display: block;
  font-size: 9.5px;
  color: var(--secondary);
  letter-spacing: 0.12em;
  font-weight: 600;
  margin-bottom: 6px;
  font-family: '{{header_font}}', sans-serif;
}
.lexique .term { font-size: 11px; line-height: 1.5; color: var(--text); margin-bottom: 5px; }
.lexique .term strong { color: var(--primary); font-weight: 600; }
.lexique .term em { font-style: italic; color: var(--muted); font-weight: 400; }
```

### Callout d'information

```html
<div class="callout">
  <p><strong>Note importante.</strong> Contenu sobre, marqué visuellement.</p>
</div>
<div class="callout warn">
  <p><strong>Attention.</strong> Variante avec accent warning.</p>
</div>
```

```css
.callout {
  border-left: 3px solid var(--primary);
  padding: 10px 13px;
  background: var(--bg-alt);
  margin: 10px 0;
  border-radius: 0 4px 4px 0;
}
.callout p { margin-bottom: 0; font-size: 12px; line-height: 1.55; }
.callout strong { color: var(--primary); }
.callout.warn { border-left-color: var(--warning); }
.callout.warn strong { color: var(--warning); }
```

### Page de signature

```html
<section class="page">
  <div class="page-header"><span class="brand-mark">{{brand_mark}}</span><span>{{header_subtitle}}</span></div>
  <div class="page-content">
    <div class="section-eyebrow">Signatures</div>
    <h2 class="section-title">Engagement à poursuivre la négociation.</h2>
    <div class="signature-block">
      <div class="sig-card">
        <div class="sig-eyebrow">Partie A</div>
        <div class="sig-company">{{partie_a_nom}}</div>
        <div class="sig-meta">{{partie_a_meta}}</div>
        <div class="sig-people">
          <div class="sig-person">
            <div class="sig-name">{{partie_a_signataire}}</div>
            <div class="sig-role">{{partie_a_qualite}}</div>
            <div class="sig-line"></div>
            <div class="sig-line-label">Signature et date</div>
          </div>
        </div>
      </div>
      <!-- Partie B idem -->
    </div>
  </div>
  <footer class="page-footer">
    <div class="page-num" data-sheet-num></div>
  </footer>
</section>
```

```css
.signature-block { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
.sig-card { background: var(--bg-alt); border: 1px solid var(--border); border-radius: 8px; padding: 20px; min-height: 200px; display: flex; flex-direction: column; }
.sig-eyebrow { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--primary); font-weight: 600; margin-bottom: 8px; }
.sig-company { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: var(--text); }
.sig-meta { font-size: 11px; color: var(--muted); line-height: 1.6; margin-bottom: 12px; }
.sig-people { margin-top: auto; padding-top: 14px; border-top: 1px dashed var(--border); }
.sig-person { margin-bottom: 12px; }
.sig-person:last-child { margin-bottom: 0; }
.sig-name { font-size: 12.5px; font-weight: 600; color: var(--text); }
.sig-role { font-size: 10.5px; color: var(--muted); margin-bottom: 22px; }
.sig-line { border-bottom: 1px solid var(--text); height: 0; margin-top: 4px; }
.sig-line-label { font-size: 9.5px; color: var(--muted); margin-top: 2px; letter-spacing: 0.05em; }
```

### Sommaire (TOC)

```html
<div class="toc">
  <div class="toc-item"><span class="toc-num">01</span><span class="toc-name">Section 1</span><span class="toc-page">p. 2</span></div>
  <!-- ... -->
</div>
```

```css
.toc { background: var(--bg-alt); border-radius: 6px; padding: 14px 16px; margin: 12px 0; }
.toc-item { display: flex; justify-content: space-between; padding: 5px 0; font-size: 12px; border-bottom: 1px dashed var(--border); }
.toc-item:last-child { border-bottom: none; }
.toc-num { color: var(--primary); font-weight: 600; font-family: '{{header_font}}', sans-serif; margin-right: 10px; min-width: 22px; }
.toc-name { flex: 1; }
.toc-page { color: var(--muted); font-size: 11px; }
```

---

## Pièges à éviter (anti-patterns documentés)

1. **NE PAS utiliser `min-height: 297mm` seul sur `.page`**. Toujours combiner `height + min-height + max-height: 297mm` + `overflow: hidden`. Sinon Chrome remplit silencieusement et la numérotation explose.

2. **NE PAS positionner `.page-num` en `position: absolute`**. Ça crée des vides blancs entre le contenu et le footer. Toujours `flex` + `margin-top: auto` sur `.page-footer`.

3. **NE PAS écrire les numéros de page en dur** ("02 / 10"). Toujours `data-sheet-num` + script JS. Ajouter une page = 0 update manuel.

4. **NE PAS abuser de `page-break-inside: avoid`**. Si un bloc est trop long pour tenir sur une page, l'`avoid` créera un grand espace blanc au-dessus pour pousser le bloc sur la page suivante. Réservé aux blocs vraiment courts (callout, lexique, sig-card, lignes de table).

5. **NE PAS oublier `-webkit-print-color-adjust: exact`** dans `@media print`. Sinon Chrome décolore les fonds (le dégradé de la cover saute).

6. **NE PAS inventer un chiffre marché, un créneau horaire, une qualité légale**. Toujours sourcer (SIRENE pour l'identité, Calendar pour les créneaux, étude ou pilote pour les chiffres) ou retirer.

7. **NE PAS utiliser l'em-dash (—)**. Remplacer par `:`, `,`, parenthèses, ou point.

8. **NE PAS saturer chaque page à 100%**. Viser 80-95%. Un peu d'air en bas est acceptable. Saturer = risque de débordement avec `overflow: hidden` qui tronquera le contenu.

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
- [ ] Chaque page calibrée 80-95% de la hauteur A4

---

## Comment générer le PDF final

Après génération du HTML, l'utilisateur ouvre le fichier dans Chrome puis :

1. ⌘P (Cmd+P) pour ouvrir la boîte d'impression
2. Destination : "Enregistrer au format PDF"
3. Mise en page : Portrait
4. Pages : Tout
5. Mise à l'échelle : Par défaut (100%)
6. **Marges : Aucune** (critique, sinon le padding se cumule)
7. **Cocher "Graphiques d'arrière-plan"** (sinon les dégradés et fonds colorés sautent)
8. Enregistrer

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

## Output attendu

Un fichier HTML autonome (`<projet>/livrables/<NOM>.html`) avec :
- CSS embarqué (pas de dépendance externe sauf Google Fonts)
- Script JS embarqué (numérotation auto)
- Contenu structuré en pages calibrées
- Tests visuels passés (preview Chrome + impression PDF test)

Logguer dans le journal de session du projet (si applicable) :
```
[DATE] /pdf-print-ready : généré <NOM>.html, N pages, destination <interne|externe nominatif|externe public>, pre-flight checks ✅
```

---

## Sources et références

- API SIRENE (Annuaire des Entreprises, gratuite, sans clé) : `https://recherche-entreprises.api.gouv.fr`
- Pas de tiret cadratin en français : usage typographique préférer `:`, `,`, parenthèses, ou point
- Pattern CSS validé terrain le 22/05/2026 sur un livrable commercial réel

---

## À propos

`pdf-print-ready` est un skill open source maintenu par [Uccello Labs](https://uccellolabs.com), éditeur d'**Uccello Hub** (plateforme IA d'entreprise souveraine) et concepteur de l'équipe IA **Uccello Crew**.

**Contributions bienvenues** : fork, PR, signalement de bugs ou de cas d'usage non couverts.

**Découvrir l'équipe IA complète Uccello Crew** (25 skills pour vendre plus, mieux, plus cher) : [uccellolabs.com](https://uccellolabs.com).

Licence : MIT.
