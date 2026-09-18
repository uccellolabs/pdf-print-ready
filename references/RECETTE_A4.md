# La recette CSS et JS d'un document A4

> **La partie technique du skill, et elle a une seule source : ce fichier.** Le `SKILL.md` porte
> la conduite (quand invoquer, le workflow, la checklist avant remise) ; ici vivent les règles CSS,
> les composants et les pièges, qui n'ont aucune raison de varier d'un usage à l'autre.
>
> **Pourquoi la séparation.** Ce skill est repris dans des dépôts qui l'adaptent : ils réécrivent
> la conduite pour leurs propres étapes et leurs propres contrôles, et recopiaient la technique au
> passage. Résultat, deux textes de la même recette qui divergent, sans que personne sache lequel
> fait foi. La conduite a le droit d'être adaptée, la technique non : elle se synchronise depuis
> ici.
>
> **Ce qui est ici se lit avant de générer**, pas après avoir constaté un débordement.

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

/* Une page paysage, pour un tableau large. Les dimensions s'echangent, rien
   d'autre ne change : la zone de contenu, le pied et la numerotation restent
   les memes, et la mesure les voit pareil.

   **Ne jamais obtenir un paysage en faisant tourner une page portrait**
   (`transform: rotate`). La rotation ment a la mesure : le navigateur calcule
   le debordement sur la boite avant rotation, donc une page qui deborde rend
   « aucun debordement ». Un devis est parti quatre fois chez un client avec
   une page debordant de 15 px, sur un gabarit paysage improvise. */
.page.paysage {
  width: 297mm;
  height: 210mm;
  min-height: 210mm;
  max-height: 210mm;
}

@page paysage { size: A4 landscape; }
.page.paysage { page: paysage; }

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

### Séparateur entre deux sous-sections d'une même page (OBLIGATOIRE si tu fusionnes)

```css
/* À DÉFINIR si tu utilises <div class="divider"></div>. Piège vécu : classe utilisée mais jamais stylée → séparateur invisible, sous-sections collées. */
.divider { height: 0; border-top: 1px solid var(--border); margin: 19px 0; }
```

### Composants visuels (graphiques) : privilégier un visuel scannable à un paragraphe

Règle : un graphique vaut mieux qu'un tableau dense, qui vaut mieux qu'un paragraphe. Toutes les valeurs restent sourcées/catégorisées.

**Filet d'accent "takeaway"** (conclusion légère, à préférer au gros callout partout) :
```css
.takeaway { border-left: 3px solid var(--primary); padding: 2px 0 2px 14px; margin: 10px 0; }
.takeaway .k { font-family: '{{header_font}}',sans-serif; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--primary); font-weight: 600; }
.takeaway p { font-size: 12.5px; line-height: 1.5; margin: 3px 0 0; }
```

**Entonnoir** (TAM/SAM/SOM, ou conversion) en SVG + légende. Trapèzes décroissants, nombres au centre, légende à droite avec badges de catégorie :
```html
<div class="funnel-wrap">
  <svg viewBox="0 0 280 270" role="img" aria-label="Entonnoir">
    <polygon points="6,8 274,8 216,92 64,92" fill="#93C5FD"/>
    <polygon points="70,104 210,104 178,188 102,188" fill="#3B82F6"/>
    <polygon points="108,200 172,200 156,262 124,262" fill="#1E3A8A"/>
    <text x="140" y="52" text-anchor="middle" font-weight="700" font-size="26" fill="#1E3A8A">~2 350</text>
    <!-- niveaux 2 et 3 : texte blanc -->
  </svg>
  <div class="funnel-legend">
    <div class="leg-row"><span class="leg-dot" style="background:#93C5FD"></span><div><div class="lt">Marché total <span class="badge ok">Vérifié</span></div><div class="ld">…</div></div></div>
    <!-- … -->
  </div>
</div>
```
```css
.funnel-wrap { display: flex; align-items: center; gap: 24px; margin: 14px 0; }
.funnel-wrap svg { flex: 0 0 280px; }
.funnel-legend { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.leg-row { display: flex; gap: 12px; align-items: flex-start; }
.leg-dot { flex: 0 0 12px; width: 12px; height: 12px; border-radius: 3px; margin-top: 3px; }
.leg-row .lt { font-family: '{{header_font}}',sans-serif; font-weight: 600; font-size: 12.5px; }
.leg-row .ld { font-size: 11px; color: var(--muted); line-height: 1.45; margin-top: 2px; }
```

**Carte 2×2 de positionnement** (deux axes, la case gagnante en vert) :
```css
.pmap { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0 4px; }
.pmap .q { border: 1px solid var(--border); border-radius: 8px; padding: 11px 13px; min-height: 74px; }
.pmap .q .qh { font-family: '{{header_font}}',sans-serif; font-weight: 600; font-size: 11px; margin-bottom: 3px; }
.pmap .q p { font-size: 10.5px; color: var(--muted); line-height: 1.4; margin: 0; }
.pmap .q.win { background: #ECFDF5; border-color: #A7F3D0; } .pmap .q.win .qh { color: #047857; }
.pmap .q.warn { background: #FFFBEB; border-color: #FDE68A; } .pmap .q.warn .qh { color: #B45309; }
.axis-x { text-align: center; font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-top: 4px; }
```

**Frise temporelle** (amorçage + portes de décision ; `.gate` = jalon de décision en orange) :
```css
.timeline { display: flex; margin: 16px 0; }
.tl-step { flex: 1; position: relative; padding: 0 8px; text-align: center; }
.tl-step::before { content: ""; position: absolute; top: 7px; left: 0; right: 0; height: 2px; background: var(--border); }
.tl-step:first-child::before { left: 50%; } .tl-step:last-child::before { right: 50%; }
.tl-dot { position: relative; width: 14px; height: 14px; border-radius: 50%; background: var(--primary); margin: 0 auto 8px; border: 2px solid #fff; box-shadow: 0 0 0 1.5px var(--primary); }
.tl-step.gate .tl-dot { background: var(--warning); box-shadow: 0 0 0 1.5px var(--warning); }
.tl-week { font-family: '{{header_font}}',sans-serif; font-weight: 600; font-size: 10px; color: var(--primary); }
.tl-lab { font-size: 9.5px; color: var(--muted); line-height: 1.35; margin-top: 2px; }
```

**Cartes de prix** (3 niveaux, la recommandée encadrée) :
```css
.pcards { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin: 12px 0; }
.pcard { border: 1px solid var(--border); border-radius: 10px; padding: 13px; display: flex; flex-direction: column; }
.pcard.reco { border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary); position: relative; }
.pcard .pc-tag { position: absolute; top: -9px; left: 13px; background: var(--primary); color: #fff; font-size: 8px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 999px; }
.pcard .pc-price { font-family: '{{header_font}}',sans-serif; font-weight: 700; font-size: 21px; margin: 4px 0 8px; }
.pcard ul { margin: 0 0 0 15px; } .pcard li { font-size: 9.5px; line-height: 1.4; }
```

**Barres de score** (notes /N) et **barres de scénarios** :
```css
.sbar .sb-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.sbar .sb-lab { flex: 0 0 120px; font-size: 10.5px; }
.sbar .sb-track { flex: 1; height: 9px; background: var(--bg-alt); border: 1px solid var(--border); border-radius: 999px; overflow: hidden; }
.sbar .sb-fill { height: 100%; background: linear-gradient(90deg,var(--primary),var(--secondary)); }
.sbar .sb-val { flex: 0 0 42px; text-align: right; font-family: '{{header_font}}',sans-serif; font-weight: 600; font-size: 10.5px; color: var(--primary); }
.bars { display: flex; align-items: flex-end; gap: 18px; height: 130px; margin: 14px 0 6px; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.bar-fill { width: 60%; border-radius: 6px 6px 0 0; background: linear-gradient(180deg,var(--secondary),var(--primary)); }
.bar-cap { font-family: '{{header_font}}',sans-serif; font-weight: 700; font-size: 13px; margin-bottom: 4px; color: var(--primary); }
.bar-lab { font-size: 9.5px; color: var(--muted); margin-top: 6px; text-align: center; line-height: 1.3; }
```

**Badges de catégorie** (à appliquer à chaque chiffre, cf. DELIVERABLE_STANDARD B1) :
```css
.badge { display: inline-block; font-size: 8.5px; font-weight: 600; padding: 1px 6px; border-radius: 999px; }
.badge.ok { background: #ECFDF5; color: #047857; }   /* Vérifié (source indépendante) */
.badge.est { background: #FFF7ED; color: #B45309; }  /* Estimé / source à pondérer */
.badge.tbc { background: #EFF6FF; color: #1D4ED8; }  /* À confirmer terrain */
.badge.cap { background: #F1F5F9; color: #475569; }  /* Capacité (choix de charge, PAS une donnée de marché) */
```

---

---

## Remplir les pages : fusionner deux sous-sections (au lieu de demi-pages vides)

Quand une section ne remplit qu'environ la moitié d'une page, regrouper deux sous-sections courtes sur une seule `.page` (séparées par `.divider`) plutôt que de laisser du blanc.

- Une page fusionnée = un en-tête, un pied, deux sous-sections (chacune avec son eyebrow + titre), un `.divider` entre.
- **Chrome cohérent (D2)** : l'en-tête (haut) et le pied (bas) doivent porter le **même libellé combiné** (ex. « Cartographie & positionnement »), jamais l'en-tête de A et le pied de B.
- Ne fusionner que des paires dont le remplissage cumulé reste **≤ ~90 %** (laisser une marge ; `overflow:hidden` tronque sinon).
- Mesurer le remplissage réel : `lastChild.getBoundingClientRect().bottom - content.top` rapporté à `content.clientHeight` (le conteneur flex remplit, le vide est SOUS le contenu).

---

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

9. **NE PAS utiliser une classe CSS sans la définir**. Piège vécu : `<div class="divider">` employé 8 fois mais `.divider` jamais stylée → hauteur nulle, sous-sections collées. Vérifier que chaque classe du corps a une règle dans le `<style>`.

10. **NE PAS laisser un en-tête et un pied incohérents sur une page fusionnée**. Si deux sous-sections partagent une page, le libellé du haut et du bas doivent coïncider (libellé combiné). Sinon le lecteur voit « Cartographie » en haut et « Positionnement » en bas sur la même page.

11. **NE PAS descendre sous 9,5px**. Texte principal ~13px, secondaire ~11px, jamais moins de 9,5px (y compris tableaux de sources). Densifier l'espacement (marges) avant de rapetisser la police.

12. **NE PAS juger le débordement à l'oeil**. Le mesurer page par page (DOM) : `content.scrollHeight - content.clientHeight > 2` OU bas du dernier enfant vs hauteur disponible. Le rendu écran trompe (overflow:auto), seul le print tronque. C'est ce que fait `scripts/rendre_pdf.py --audit`.

14. **NE PAS croire un rapport « aucun débordement » sur une mise en page en colonnes.** Le contrôle de page mesure `.page`, et le contrôle de troncature ne regarde que les conteneurs dont l'`overflow` calculé vaut `hidden`, `auto` ou `scroll`. Une carte en `overflow: visible` dans une grille échappe aux deux : son contenu ne fait pas déborder la page, il sort par le bas et **la bande suivante le repeint avec son fond**. Rien n'est signalé, et le contenu a pourtant disparu du PDF. Piège vécu le 10/09/2026 sur un mémo A4 paysage à trois colonnes : un bloc entier manquait au rendu pendant que l'audit affichait « 97 %, aucun débordement ». Le contrôle qui l'attrape ne regarde pas l'`overflow` : il compare le rectangle de chaque élément à la **bordure** du plus proche ancêtre qui se voit (un fond, une bordure, ou un `overflow` qui coupe). C'est le verdict `HORS CADRE`. Corollaire de méthode : ajouter du contenu dans une colonne déjà pleine se vérifie, ne se suppose pas.

13. **NE PAS réutiliser tel quel le CSS d'une page web responsive**. Une page A4 fait 794 px de large, et c'est cette largeur que Chrome donne aux media queries à l'impression. Un `@media (max-width: 900px)` prévu pour le mobile se déclenche donc sur chaque page : les grilles à deux colonnes s'empilent, tout déborde. Piège vécu le 10/09/2026 : quatre pages sur quatre en débordement, jusqu'à forcer `grid-template-columns` avec `!important` dans une surcouche A4. Écrire le CSS A4 sans media query de largeur, ou les neutraliser.

14. **NE PAS mettre un SVG à demi-largeur sans recalculer la taille de son texte**. Un texte à 12 px dans un `viewBox` de 560 rendu sur 330 px s'imprime à 7 px. La taille effective vaut `font-size × (largeur rendue / largeur du viewBox)`. L'audit la calcule ; la règle des 9,5 px s'applique à cette taille-là. Solution : un graphique par ligne en pleine largeur avec un `viewBox` proche de la largeur rendue, ou des textes plus grands dans le `viewBox`.

15. **NE PAS laisser une classe utilitaire écraser la police d'un tableau**. Piège vécu : `.small { font-size: 13px }` posé sur les références d'un tableau réglé à 10,5 px les a fait passer sur deux lignes. Dans une surcouche print, vérifier les classes de taille héritées de la version web.

16. **NE PAS empiler des colonnes `white-space: nowrap` dans un tableau large**. Onze colonnes dont huit en nowrap laissent 130 px aux deux colonnes de texte, qui se replient sur cinq lignes. Fixer les largeurs (`table-layout: fixed` + `<colgroup>`), laisser les en-têtes passer sur deux lignes, remplacer les notes longues par un repère court.

17. **Dans un schéma, un texte ne chevauche jamais rien et ne dépasse jamais une bordure.** Ni un autre texte, ni le cadre du SVG, ni la boîte qui le porte. Un libellé plus large que sa boîte, une légende coupée au bord droit, deux colonnes de texte qui se rejoignent : autant de défauts que la mesure de remplissage ne voit pas. Règle de construction : compter la largeur du texte (environ 0,5 em par caractère en sans, 0,6 em en mono) et dimensionner la boîte dessus, jamais l'inverse ; un texte trop long se coupe en deux lignes ou se raccourcit, il ne rétrécit pas. L'audit (`rendre_pdf.py`) signale ces trois cas par page, verdict `SCHEMA`, code de retour 1.

---
