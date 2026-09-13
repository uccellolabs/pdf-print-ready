#!/usr/bin/env python3
"""
rendre_pdf.py : mesurer, imprimer et prévisualiser un HTML print-ready, en une commande.

Le skill pdf-print-ready pose une règle : le débordement ne se juge pas à l'œil, il se
mesure page par page dans le DOM. Ce script fait cette mesure avec Chrome en mode
headless, puis imprime le PDF et rend chaque page en image pour un contrôle visuel.

    python3 scripts/rendre_pdf.py livrable.html              # audit + PDF + aperçus
    python3 scripts/rendre_pdf.py livrable.html --audit      # audit seul, à relancer pendant le calage
    python3 scripts/rendre_pdf.py livrable.html --detail     # audit + hauteur de chaque bloc, pour décider où couper
    python3 scripts/rendre_pdf.py livrable.html --pdf sortie.pdf --apercus dossier/ --dpi 80
    python3 scripts/rendre_pdf.py livrable.html --json       # sortie machine

Ce que l'audit mesure, par page :
  - le remplissage (bas du dernier bloc rapporté à la hauteur disponible), cible 80 à 95 %
  - le débordement en hauteur et en largeur (scrollHeight/scrollWidth contre client)
  - les textes rendus sous 9,5 px, y compris dans les SVG mis à l'échelle par leur viewBox
  - dans les schémas SVG : un texte qui chevauche un autre texte, qui sort du cadre du SVG,
    ou qui déborde d'une boîte (rect) qu'il traverse
  - les conteneurs à défilement (overflow auto, scroll, hidden) dont le contenu est coupé :
    un tableau plus large que sa carte perd ses dernières colonnes sans que la page déborde
  - le contenu qui sort de son cadre sans être coupé par lui : un bloc plus haut que la carte
    qui le porte déborde par-dessus la bande suivante, laquelle le repeint avec son fond. Rien
    ne dépasse de la page, rien n'est signalé comme tronqué, et le contenu a pourtant disparu.
    Le cadre est ici tout ancêtre qui se voit : un fond, une bordure, ou un overflow qui coupe.
    La limite mesurée est le trait de bordure, pas la boîte de contenu : mordre sur le
    rembourrage est une marge choisie, sortir du trait ne l'est pas
Et pour le document :
  - le nombre de pages du PDF contre le nombre de sections .page (une différence = une page qui déborde)
  - les tirets cadratins (U+2014), proscrits en français
  - les classes employées sans aucune règle CSS (piège de la classe fantôme)
  - les polices déclarées mais non chargées
  - les numéros de page restés vides

Code de retour : 0 si tout passe, 1 si au moins une page déborde, si un bloc sort de son cadre,
si un schéma a un défaut,
ou si le PDF a plus de pages que de sections, 2 si un outil manque (Chrome).

Prérequis : Google Chrome (ou Chromium). Aperçus : pdftoppm (poppler), sinon ils sont sautés.
Aucune dépendance Python hors bibliothèque standard.
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SEUIL_POLICE = 9.5
CIBLE_MIN, CIBLE_MAX = 60, 95

# ---------------------------------------------------------------------------
# Script d'audit injecté dans une copie du HTML. Il écrit son rapport en base64
# dans un <pre>, que --dump-dom nous rend.
# ---------------------------------------------------------------------------
AUDIT_JS = r"""
<script>
(function(){
  var SEUIL = %(seuil)s;
  function run(){
    var out = {pages: [], doc: {}};
    var pages = document.querySelectorAll('.page');
    out.doc.sections = pages.length;
    out.doc.numeros_vides = Array.prototype.filter.call(document.querySelectorAll('[data-sheet-num]'), function(e){ return !e.textContent.trim(); }).length;

    // polices déclarées mais non chargées
    var familles = {}, erreurs = [];
    try { document.fonts.forEach(function(f){ var fam = f.family.replace(/^["']|["']$/g, ''); familles[fam] = familles[fam] || false; if (f.status === 'loaded') familles[fam] = true; if (f.status === 'error') erreurs.push(fam + ' ' + f.weight); }); } catch(e){}
    out.doc.polices_non_chargees = Object.keys(familles).filter(function(k){ return !familles[k]; }).concat(erreurs.map(function(e){ return e + ' (erreur)'; })).slice(0, 8);

    // classes sans règle CSS
    var selecteurs = [];
    try {
      Array.prototype.forEach.call(document.styleSheets, function(ss){
        var rules; try { rules = ss.cssRules; } catch(e) { return; }
        if (!rules) return;
        (function collecte(rs){ Array.prototype.forEach.call(rs, function(r){ if (r.selectorText) selecteurs.push(r.selectorText); if (r.cssRules) collecte(r.cssRules); }); })(rules);
      });
    } catch(e){}
    var texteSel = selecteurs.join('\n');
    var classes = {};
    Array.prototype.forEach.call(document.body.querySelectorAll('[class]'), function(el){
      if (el.closest('#__audit_pages')) return;
      var cl = (typeof el.className === 'string') ? el.className : (el.getAttribute('class') || '');
      cl.split(/\s+/).forEach(function(c){ if (c) classes[c] = (classes[c] || 0) + 1; });
    });
    var fantomes = [];
    Object.keys(classes).forEach(function(c){
      var re = new RegExp('\\.' + c.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') + '(?![\\w-])');
      if (!re.test(texteSel)) fantomes.push(c + ' (' + classes[c] + ')');
    });
    out.doc.classes_fantomes = fantomes;

    function label(page){
      var h = page.querySelector('.page-header'); var f = page.querySelector('.page-footer');
      var src = (h && h.textContent.trim()) ? h : f; if (!src) return '';
      var parts = src.children.length ? Array.prototype.map.call(src.children, function(c){ return c.textContent.trim(); }).filter(Boolean) : [src.textContent.trim()];
      return parts.join(' | ').replace(/\s+/g, ' ').slice(0, 70);
    }

    // taille effective des textes, y compris SVG mis à l'échelle
    function petitsTextes(page){
      var petits = [], min = Infinity;
      var svgScale = new Map();
      Array.prototype.forEach.call(page.querySelectorAll('svg'), function(svg){
        var vb = svg.getAttribute('viewBox'); if (!vb) return;
        var parts = vb.split(/[\s,]+/).map(parseFloat); if (parts.length < 4 || !parts[2]) return;
        var w = svg.getBoundingClientRect().width; if (!w) return;
        svgScale.set(svg, w / parts[2]);
      });
      Array.prototype.forEach.call(page.querySelectorAll('*'), function(el){
        if (el.closest('#__audit_pages')) return;
        var texte = false;
        for (var i = 0; i < el.childNodes.length; i++) { var n = el.childNodes[i]; if (n.nodeType === 3 && n.textContent.trim()) { texte = true; break; } }
        if (!texte) return;
        var r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
        var fs = parseFloat(getComputedStyle(el).fontSize); if (!fs) return;
        var svg = el.closest && el.closest('svg');
        if (svg && svgScale.has(svg)) fs = fs * svgScale.get(svg);
        if (fs < min) min = fs;
        if (fs < SEUIL) {
          var extrait = el.textContent.trim().replace(/\s+/g, ' ').slice(0, 40);
          petits.push({taille: Math.round(fs * 10) / 10, texte: extrait, svg: !!svg});
        }
      });
      return {min: min === Infinity ? null : Math.round(min * 10) / 10, petits: petits};
    }

    // schémas : un texte ne chevauche jamais un autre texte, ne sort jamais du cadre du SVG,
    // ne déborde jamais d'une boîte (rect) qu'il traverse
    function defautsSchemas(page){
      var defauts = [];
      var TOL = 0.75;
      function inter(a, b){ return Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)); }
      function dedans(a, b){ return a.left >= b.left - TOL && a.right <= b.right + TOL && a.top >= b.top - TOL && a.bottom <= b.bottom + TOL; }
      function extrait(t){ return t.textContent.trim().replace(/\s+/g, ' ').slice(0, 32); }
      Array.prototype.forEach.call(page.querySelectorAll('svg'), function(svg){
        var cadre = svg.getBoundingClientRect(); if (!cadre.width) return;
        var textes = Array.prototype.filter.call(svg.querySelectorAll('text'), function(t){ var r = t.getBoundingClientRect(); return r.width > 0 && r.height > 0 && t.textContent.trim(); });
        var rects = Array.prototype.filter.call(svg.querySelectorAll('rect'), function(r){ var b = r.getBoundingClientRect(); return b.width > 4 && b.height > 4 && !r.closest('defs') && !r.closest('clipPath') && !r.closest('pattern'); });
        // un trait qui passe sous un mot ne chevauche aucun texte et ne déborde
        // d'aucune boîte : il ne se voit qu'à la lecture. On échantillonne le
        // tracé plutôt que sa boîte englobante, qui serait fausse en diagonale.
        var traits = Array.prototype.filter.call(svg.querySelectorAll('line, path, polyline'), function(l){
          if (l.closest('defs') || l.closest('marker') || l.closest('clipPath')) return false;
          return typeof l.getTotalLength === 'function' && l.getTotalLength() > 4;
        });
        var ctm = svg.getScreenCTM();
        var points = [];
        if (ctm) traits.forEach(function(l){
          var L = l.getTotalLength(), n = Math.min(120, Math.max(12, Math.round(L / 3)));
          for (var k = 0; k <= n; k++) {
            var q = l.getPointAtLength(L * k / n);
            var pt = svg.createSVGPoint(); pt.x = q.x; pt.y = q.y;
            var e = pt.matrixTransform(ctm);
            points.push({x: e.x, y: e.y, el: l});
          }
        });

        textes.forEach(function(t, i){
          var a = t.getBoundingClientRect();
          if (!dedans(a, cadre)) defauts.push({type: 'hors cadre', texte: extrait(t)});
          // 1,5 px de tolérance : un trait qui frôle une lettre ne gêne pas.
          var M = 1.5;
          for (var k = 0; k < points.length; k++) {
            var q = points[k];
            if (q.x > a.left + M && q.x < a.right - M && q.y > a.top + M && q.y < a.bottom - M) {
              defauts.push({type: 'traverse', texte: extrait(t)});
              break;
            }
          }
          for (var j = i + 1; j < textes.length; j++) {
            var b = textes[j].getBoundingClientRect();
            var dx = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            var dy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            // deux lignes qui se suivent partagent un peu de leur boîte (jambages) : on exige un vrai recouvrement vertical
            if (dx > TOL && dy > 0.25 * Math.min(a.height, b.height))
              defauts.push({type: 'chevauche', texte: extrait(t), autre: extrait(textes[j])});
          }
          rects.forEach(function(r){
            var b = r.getBoundingClientRect();
            var x = inter(a, b);
            if (x > 0 && !dedans(a, b)) {
              var recouvrement = x / (a.width * a.height);
              // un texte posé à cheval sur un bord : plus d'un dixième dedans, pas tout dedans
              if (recouvrement > 0.1) defauts.push({type: 'déborde d\'une boîte', texte: extrait(t), autre: Math.round(b.width) + 'x' + Math.round(b.height) + ' px'});
            }
          });
        });
      });
      return defauts;
    }

    // un conteneur à défilement (overflow auto/scroll/hidden) masque ce qui déborde : la page ne le voit pas,
    // le lecteur du PDF non plus, la colonne est juste coupée
    function tronques(page){
      var res = [];
      Array.prototype.forEach.call(page.querySelectorAll('*'), function(el){
        if (el.closest('#__audit_pages') || el.classList.contains('page-content') || el === page) return;
        var cs = getComputedStyle(el);
        var ox = cs.overflowX, oy = cs.overflowY;
        if (!/(auto|scroll|hidden)/.test(ox) && !/(auto|scroll|hidden)/.test(oy)) return;
        var dx = el.scrollWidth - el.clientWidth, dy = el.scrollHeight - el.clientHeight;
        if (dx > 2 || dy > 2) {
          var nom = el.className && typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/)[0] : el.tagName.toLowerCase();
          var titre = el.querySelector && el.querySelector('th, h3, h2, caption'); titre = titre ? titre.textContent.trim().replace(/\s+/g, ' ').slice(0, 30) : '';
          res.push({conteneur: nom, largeur: Math.max(0, Math.round(dx)), hauteur: Math.max(0, Math.round(dy)), repere: titre});
        }
      });
      return res;
    }

    function estCadre(el){
      var cs = getComputedStyle(el);
      if (/(auto|scroll|hidden)/.test(cs.overflowY) || /(auto|scroll|hidden)/.test(cs.overflowX)) return true;
      var bg = cs.backgroundColor;
      if (bg && bg !== 'transparent' && !/^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0\s*\)$/.test(bg)) return true;
      var cotes = ['Top', 'Right', 'Bottom', 'Left'];
      for (var i = 0; i < 4; i++){
        var w = parseFloat(cs['border' + cotes[i] + 'Width']) || 0;
        var c = cs['border' + cotes[i] + 'Color'] || '';
        if (w > 0 && !/^rgba\([^)]*,\s*0\s*\)$/.test(c)) return true;
      }
      return false;
    }

    // Un bloc plus haut que la carte qui le porte ne fait pas déborder la page : il passe
    // par-dessus la bande suivante, qui le recouvre. Aucun autre contrôle ne le voit.
    function horsCadre(page){
      var fautifs = [], res = [];
      Array.prototype.forEach.call(page.querySelectorAll('*'), function(el){
        if (el.closest('#__audit_pages')) return;
        var a = el.getBoundingClientRect();
        if (!a.width && !a.height) return;
        var cadre = null, n = el.parentElement;
        while (n && n !== page.parentElement){ if (n === page || estCadre(n)) { cadre = n; break; } n = n.parentElement; }
        if (!cadre) return;
        // la limite est la bordure, pas la boîte de contenu : mordre sur le rembourrage
        // est une marge de manoeuvre choisie par la mise en page, sortir du trait ne l'est pas
        var cs = getComputedStyle(cadre), b = cadre.getBoundingClientRect();
        var basLimite = b.bottom - (parseFloat(cs.borderBottomWidth) || 0);
        var droiteLimite = b.right - (parseFloat(cs.borderRightWidth) || 0);
        var db = a.bottom - basLimite, dd = a.right - droiteLimite;
        if (db > 2 || dd > 2) fautifs.push({el: el, cadre: cadre, bas: db, droite: dd});
      });
      // ne garder que le plus extérieur : sinon un bloc fautif remonte avec tous ses enfants
      var lot = fautifs.map(function(f){ return f.el; });
      fautifs.forEach(function(f){
        if (lot.indexOf(f.el.parentElement) !== -1) return;
        function nom(e){ return (e.className && typeof e.className === 'string' && e.className.trim()) ? '.' + e.className.trim().split(/\s+/)[0] : e.tagName.toLowerCase(); }
        res.push({
          element: nom(f.el), cadre: nom(f.cadre),
          bas: Math.max(0, Math.round(f.bas)), droite: Math.max(0, Math.round(f.droite)),
          repere: (f.el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 34)
        });
      });
      return res;
    }

    function blocs(node, profondeur){
      var res = [];
      Array.prototype.forEach.call(node.children, function(k){
        var h = Math.round(k.getBoundingClientRect().height); if (h < 20) return;
        var nom = (k.className && typeof k.className === 'string' && k.className.trim()) ? '.' + k.className.trim().split(/\s+/).slice(0, 2).join('.') : k.tagName.toLowerCase();
        var titre = k.querySelector && k.querySelector('h1,h2,h3'); titre = titre ? titre.textContent.trim().replace(/\s+/g, ' ').slice(0, 50) : '';
        var b = {nom: nom, hauteur: h, titre: titre};
        if (profondeur < 1) b.enfants = blocs(k, profondeur + 1);
        res.push(b);
      });
      return res;
    }

    pages.forEach(function(page, i){
      var c = page.querySelector('.page-content') || page;
      var kids = Array.prototype.filter.call(c.children, function(k){ return k.getBoundingClientRect().height > 0; });
      var last = kids[kids.length - 1];
      var top = c.getBoundingClientRect().top;
      var bas = last ? last.getBoundingClientRect().bottom : top;
      var avail = c.clientHeight;
      var p = {
        index: i + 1,
        libelle: label(page),
        disponible: Math.round(avail),
        remplissage: avail ? Math.round((bas - top) / avail * 100) : null,
        deborde_hauteur: Math.round(c.scrollHeight - c.clientHeight),
        deborde_largeur: Math.round(c.scrollWidth - c.clientWidth),
        a_page_content: c !== page,
        couverture: page.classList.contains('cover')
      };
      var pt = petitsTextes(page); p.police_min = pt.min; p.petits_textes = pt.petits.slice(0, 6); p.nb_petits_textes = pt.petits.length;
      var ds = defautsSchemas(page); p.defauts_schemas = ds.slice(0, 8); p.nb_defauts_schemas = ds.length;
      var tr = tronques(page); p.tronques = tr.slice(0, 6); p.nb_tronques = tr.length;
      var hc = horsCadre(page); p.hors_cadre = hc.slice(0, 6); p.nb_hors_cadre = hc.length;
      if (%(detail)s) p.blocs = blocs(c, 0);
      out.pages.push(p);
    });
    var pre = document.createElement('pre'); pre.id = '__audit_pages';
    pre.textContent = btoa(unescape(encodeURIComponent(JSON.stringify(out))));
    document.body.appendChild(pre);
  }
  function go(){ (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(function(){ setTimeout(run, 50); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
</script>
"""


# Une phase se ferme par son propre contrôle. Celle des schémas n'en avait pas :
# il fallait intégrer le schéma dans le document pour le mesurer, donc le
# découvrir faux après avoir bâti la mise en page dessus. Ce gabarit donne au
# schéma une page à sa vraie largeur d'impression, et rien d'autre.
GABARIT_SCHEMA = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>contrôle de schéma</title>
<style>
 @page{size:210mm 297mm;margin:0}
 *{box-sizing:border-box;margin:0;padding:0}
 body{font-family:Arial,Helvetica,sans-serif;background:#fff;color:#333}
 .page{width:210mm;height:297mm;padding:20mm %(marge)smm;display:flex;flex-direction:column;overflow:hidden}
 .page-content{flex:1 1 auto;min-height:0;overflow:hidden}
 .page-content svg{width:100%%;height:auto;max-height:%(hauteur)smm}
 .page-footer{flex:0 0 auto;margin-top:auto;min-height:6mm}
</style></head><body>
<section class="page"><div class="page-content">
%(schema)s
</div><footer class="page-footer"></footer></section>
</body></html>"""


def page_de_schema(fragment, largeur_mm, hauteur_mm):
    """Le fragment (un SVG, ou un HTML qui en contient) posé seul sur une page A4."""
    return GABARIT_SCHEMA % {
        "marge": round((210 - largeur_mm) / 2.0, 2),
        "hauteur": hauteur_mm,
        "schema": fragment,
    }


def conseil_de_taille(pages, largeur_mm):
    """Ce qu'il faudrait écrire dans le viewBox pour tenir le seuil de lisibilité.

    Un SVG réduit à la largeur d'une page imprime son texte à
    `font-size × largeur rendue / largeur du viewBox`. Le rapport rend donc la
    taille effective et le facteur, parce que corriger sans le facteur revient à
    tâtonner.
    """
    p = pages[0] if pages else {}
    mini = p.get("police_min")

    if not mini or mini >= SEUIL_POLICE:
        return None

    return ("Textes trop petits à l'impression : %.1f px pour un seuil de %.1f. "
            "Multiplier les font-size du schéma par %.2f, ou resserrer le viewBox "
            "d'autant." % (mini, SEUIL_POLICE, SEUIL_POLICE / mini))


def trouver_chrome(explicite=None):
    candidats = []
    if explicite:
        candidats.append(explicite)
    if os.environ.get("CHROME"):
        candidats.append(os.environ["CHROME"])
    candidats += [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for nom in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        chemin = shutil.which(nom)
        if chemin:
            candidats.append(chemin)
    for c in candidats:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def chrome(chrome_bin, args, timeout=120):
    base = [chrome_bin, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--hide-scrollbars", "--window-size=794,1123"]
    return subprocess.run(base + args, capture_output=True, text=True, timeout=timeout)


def auditer(chrome_bin, html_path, detail=False, budget_ms=8000):
    """Injecte le script d'audit dans une copie temporaire, à côté du fichier pour garder les chemins relatifs."""
    source = open(html_path, encoding="utf-8").read()
    js = AUDIT_JS % {"seuil": SEUIL_POLICE, "detail": "true" if detail else "false"}
    if "</body>" in source:
        copie = source.replace("</body>", js + "</body>", 1)
    else:
        copie = source + js
    dossier = os.path.dirname(os.path.abspath(html_path))
    fd, tmp = tempfile.mkstemp(prefix=".__audit_", suffix=".html", dir=dossier)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(copie)
        res = chrome(chrome_bin, [f"--virtual-time-budget={budget_ms}", "--dump-dom", "file://" + tmp])
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    m = re.search(r'<pre id="__audit_pages">([A-Za-z0-9+/=\s]+)</pre>', res.stdout)
    if not m:
        raise RuntimeError("l'audit n'a rien rendu : Chrome n'a pas exécuté la page (stderr : %s)" % res.stderr.strip()[-300:])
    data = json.loads(base64.b64decode(re.sub(r"\s+", "", m.group(1))).decode("utf-8"))
    data["doc"]["tirets_cadratins"] = source.count("—")
    return data


def imprimer(chrome_bin, html_path, pdf_path, budget_ms=10000):
    pdf_path = os.path.abspath(pdf_path)
    res = chrome(chrome_bin, [f"--virtual-time-budget={budget_ms}", "--no-pdf-header-footer",
                              f"--print-to-pdf={pdf_path}", "file://" + os.path.abspath(html_path)], timeout=180)
    if not os.path.isfile(pdf_path):
        raise RuntimeError("le PDF n'a pas été écrit (stderr : %s)" % res.stderr.strip()[-300:])
    return pdf_path


def pages_pdf(pdf_path):
    data = open(pdf_path, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def apercus(pdf_path, dossier, dpi):
    outil = shutil.which("pdftoppm")
    if not outil:
        return None, "pdftoppm absent : `brew install poppler` pour obtenir les aperçus PNG"
    os.makedirs(dossier, exist_ok=True)
    prefixe = os.path.join(dossier, "page")
    subprocess.run([outil, "-r", str(dpi), "-png", pdf_path, prefixe], check=True, capture_output=True)
    fichiers = sorted(f for f in os.listdir(dossier) if f.startswith("page") and f.endswith(".png"))
    return [os.path.join(dossier, f) for f in fichiers], None


def verdict(p):
    if p["deborde_hauteur"] > 2 or p["deborde_largeur"] > 2:
        return "DEBORDE"
    if p.get("nb_tronques"):
        return "TRONQUE"
    if p.get("nb_hors_cadre"):
        return "HORS CADRE"
    if p.get("nb_defauts_schemas"):
        return "SCHEMA"
    if p.get("couverture"):
        return "couv."
    if p["remplissage"] is not None and p["remplissage"] > CIBLE_MAX:
        return "serré"
    if p["remplissage"] is not None and p["remplissage"] < CIBLE_MIN:
        return "creux"
    return "ok"


def rapport(audit, pdf_path=None, nb_pdf=None, images=None, note_apercus=None, detail=False):
    lignes = []
    w = lignes.append
    w("AUDIT DES PAGES")
    w("  cible : remplissage entre %d et %d %%, aucun débordement, rien de coupé, rien hors cadre, aucun texte sous %s px, aucun texte de schéma qui chevauche ou déborde" % (CIBLE_MIN, CIBLE_MAX, str(SEUIL_POLICE).replace(".", ",")))
    w("")
    for p in audit["pages"]:
        v = verdict(p)
        marque = {"DEBORDE": "!!", "SCHEMA": "!!", "TRONQUE": "!!", "HORS CADRE": "!!", "serré": " !", "creux": " ~", "ok": "  ", "couv.": "  "}[v]
        extra = []
        if p["deborde_hauteur"] > 2:
            extra.append("déborde de %d px en hauteur" % p["deborde_hauteur"])
        if p["deborde_largeur"] > 2:
            extra.append("déborde de %d px en largeur" % p["deborde_largeur"])
        if p["nb_petits_textes"]:
            extra.append("%d texte(s) sous %s px, min %s px" % (p["nb_petits_textes"], SEUIL_POLICE, p["police_min"]))
        if p.get("nb_defauts_schemas"):
            extra.append("%d défaut(s) de schéma : un texte chevauche, sort du cadre ou déborde d'une boîte" % p["nb_defauts_schemas"])
        if p.get("nb_tronques"):
            extra.append("%d conteneur(s) à défilement dont le contenu est coupé (tableau trop large, colonne masquée)" % p["nb_tronques"])
        if p.get("nb_hors_cadre"):
            extra.append("%d bloc(s) qui sortent de leur cadre sans être coupés par lui : recouverts par ce qui suit" % p["nb_hors_cadre"])
        if not p["a_page_content"]:
            extra.append("pas de .page-content, mesure sur .page")
        w("%s page %02d  %3s %%  %-8s %s" % (marque, p["index"], p["remplissage"] if p["remplissage"] is not None else "?", v, p["libelle"][:60]))
        for e in extra:
            w("           - " + e)
        for t in p["petits_textes"][:3]:
            w("             « %s » %s px%s" % (t["texte"], t["taille"], " (svg, mis à l'échelle)" if t["svg"] else ""))
        for t in p.get("tronques", [])[:4]:
            w("             %s%s : coupé de %d px en largeur, %d px en hauteur" % (t["conteneur"], (" (" + t["repere"] + ")") if t["repere"] else "", t["largeur"], t["hauteur"]))
        for h in p.get("hors_cadre", [])[:4]:
            sens = []
            if h["bas"]: sens.append("%d px sous le bas" % h["bas"])
            if h["droite"]: sens.append("%d px après le bord droit" % h["droite"])
            w("             %s sort de %s : %s%s" % (h["element"], h["cadre"], ", ".join(sens), (" · « %s »" % h["repere"]) if h["repere"] else ""))
        for d in p.get("defauts_schemas", [])[:6]:
            w("             %s : « %s »%s" % (d["type"], d["texte"], (" et « %s »" % d["autre"]) if d.get("autre") else ""))
        if detail and p.get("blocs"):
            for b in p["blocs"]:
                w("           %5d px  %s %s" % (b["hauteur"], b["nom"], ("· " + b["titre"]) if b["titre"] else ""))
                for e in b.get("enfants", []):
                    w("           %5d px     %s %s" % (e["hauteur"], e["nom"], ("· " + e["titre"]) if e["titre"] else ""))
    w("")
    d = audit["doc"]
    w("DOCUMENT")
    w("  sections .page : %d" % d["sections"])
    if nb_pdf is not None:
        etat = "ok" if nb_pdf == d["sections"] else "!! le PDF a %d page(s), une section déborde ou une page est vide" % nb_pdf
        w("  pages du PDF   : %d  %s" % (nb_pdf, etat))
    w("  tirets cadratins (U+2014) : %d%s" % (d["tirets_cadratins"], "" if not d["tirets_cadratins"] else "  !! à remplacer par : , ( ) ou un point"))
    w("  numéros de page vides : %d%s" % (d["numeros_vides"], "" if not d["numeros_vides"] else "  !! le script de numérotation n'a pas tourné"))
    if d["polices_non_chargees"]:
        w("  polices non chargées : " + ", ".join(d["polices_non_chargees"]) + "  (réseau ? le rendu utilise la police de repli)")
    else:
        w("  polices : toutes chargées")
    if d["classes_fantomes"]:
        w("  classes sans règle CSS (%d) : %s" % (len(d["classes_fantomes"]), ", ".join(d["classes_fantomes"][:12]) + (" …" if len(d["classes_fantomes"]) > 12 else "")))
        w("    (des crochets JS peuvent être légitimes ; une classe de mise en forme absente est le piège n° 9)")
    else:
        w("  classes : toutes définies")
    if pdf_path:
        w("")
        w("PDF      : " + pdf_path)
    if images:
        w("APERÇUS  : %d image(s) dans %s" % (len(images), os.path.dirname(images[0])))
        w("           ouvre-les une à une : la mesure ne voit ni un libellé qui chevauche, ni une colonne tronquée")
    if note_apercus:
        w("APERÇUS  : " + note_apercus)
    return "\n".join(lignes)


def controler_schema(chrome_bin, chemin, largeur_mm, hauteur_mm):
    """Rend (audit, page_html_temporaire) pour un schéma seul."""
    fragment = open(chemin, encoding="utf-8").read()

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(page_de_schema(fragment, largeur_mm, hauteur_mm))
        page = fh.name

    try:
        return auditer(chrome_bin, page), page
    finally:
        pass


def rapport_schema(audit, chemin, largeur_mm):
    """Ce que le contrôle d'un schéma doit dire, et rien d'autre."""
    pages = audit.get("pages") or []
    p = pages[0] if pages else {}
    lignes = ["CONTRÔLE DU SCHÉMA : %s" % os.path.basename(chemin),
              "  rendu sur une largeur de %g mm, celle d'une page A4 reliée" % largeur_mm,
              ""]

    defauts = p.get("defauts_schemas") or []

    if defauts:
        lignes.append("  %d défaut(s) de tracé :" % p.get("nb_defauts_schemas", len(defauts)))
        for d in defauts:
            if d.get("type") == "chevauche":
                lignes.append("    chevauche : « %s » et « %s »" % (d.get("texte"), d.get("autre")))
            elif d.get("type") == "hors cadre":
                lignes.append("    hors cadre : « %s »" % d.get("texte"))
            elif d.get("type") == "traverse":
                lignes.append("    un trait passe sous : « %s »" % d.get("texte"))
            else:
                lignes.append("    déborde d'une boîte : « %s » et « %s »"
                              % (d.get("texte"), d.get("boite", "")))
    else:
        lignes.append("  tracé : aucun texte qui chevauche, sort du cadre ou déborde d'une boîte")

    conseil = conseil_de_taille(pages, largeur_mm)

    if conseil:
        lignes += ["", "  " + conseil]
        for t in (p.get("petits_textes") or [])[:5]:
            lignes.append("    %s px  « %s »" % (t.get("taille"), t.get("texte")))
    else:
        lignes.append("  lisibilité : aucun texte sous %.1f px à l'impression" % SEUIL_POLICE)

    if p.get("deborde_h") or p.get("deborde_l"):
        lignes += ["", "  le schéma ne tient pas dans la page d'essai : réduire sa hauteur,"
                       "  ou le passer en paysage"]

    lignes += ["", "  Un schéma se ferme avant d'être posé dans un document : une reprise",
               "  après coup fait repasser toute la mise en page bâtie dessus."]
    return "\n".join(lignes)


def main():
    ap = argparse.ArgumentParser(description="Mesure, imprime et prévisualise un HTML print-ready.")
    ap.add_argument("html", help="le fichier HTML paginé (.page > .page-content + .page-footer)")
    ap.add_argument("--audit", action="store_true", help="audit seul, sans PDF ni aperçus")
    ap.add_argument("--detail", action="store_true", help="ajoute la hauteur de chaque bloc par page")
    ap.add_argument("--pdf", help="chemin du PDF (défaut : à côté du HTML, même nom)")
    ap.add_argument("--apercus", help="dossier des aperçus PNG (défaut : <nom>_pages/ à côté du HTML)")
    ap.add_argument("--sans-apercus", action="store_true", help="ne pas rendre les aperçus")
    ap.add_argument("--dpi", type=int, default=70, help="résolution des aperçus (défaut 70, lisible et léger)")
    ap.add_argument("--chrome", help="chemin de Chrome ou Chromium (sinon $CHROME, puis détection)")
    ap.add_argument("--json", action="store_true", help="sortie JSON au lieu du rapport")
    ap.add_argument("--schema", action="store_true",
                    help="contrôle un schéma seul (fichier .svg ou fragment HTML), avant de le poser dans un document")
    ap.add_argument("--largeur", type=float, default=150.0,
                    help="largeur de rendu du schéma en mm pour --schema (défaut 150, une A4 avec marge de reliure)")
    ap.add_argument("--hauteur", type=float, default=150.0,
                    help="hauteur maximale du schéma en mm pour --schema (défaut 150)")
    a = ap.parse_args()

    if not os.path.isfile(a.html):
        print("fichier introuvable : " + a.html, file=sys.stderr)
        return 2
    chrome_bin = trouver_chrome(a.chrome)

    if a.schema:
        audit, page = controler_schema(chrome_bin, a.html, a.largeur, a.hauteur)
        pages = audit.get("pages") or []
        p = pages[0] if pages else {}
        os.unlink(page)

        if a.json:
            print(json.dumps(audit, ensure_ascii=False, indent=1))
        else:
            print(rapport_schema(audit, a.html, a.largeur))

        mauvais = bool(p.get("nb_defauts_schemas")) or (
            p.get("police_min") is not None and p.get("police_min") < SEUIL_POLICE)
        return 1 if mauvais else 0
    if not chrome_bin:
        print("Chrome ou Chromium introuvable. Indique-le avec --chrome ou la variable CHROME.", file=sys.stderr)
        return 2

    try:
        audit = auditer(chrome_bin, a.html, detail=a.detail)
    except Exception as e:  # noqa: BLE001
        print("audit impossible : %s" % e, file=sys.stderr)
        return 2

    pdf_path = nb_pdf = images = note = None
    if not a.audit:
        base = os.path.splitext(os.path.abspath(a.html))[0]
        pdf_path = a.pdf or base + ".pdf"
        try:
            imprimer(chrome_bin, a.html, pdf_path)
            nb_pdf = pages_pdf(pdf_path)
        except Exception as e:  # noqa: BLE001
            print("impression impossible : %s" % e, file=sys.stderr)
            return 2
        if not a.sans_apercus:
            dossier = a.apercus or base + "_pages"
            try:
                images, note = apercus(pdf_path, dossier, a.dpi)
            except subprocess.CalledProcessError as e:
                note = "pdftoppm a échoué : %s" % e

    deborde = any(verdict(p) in ("DEBORDE", "SCHEMA", "TRONQUE", "HORS CADRE") for p in audit["pages"]) or (nb_pdf is not None and nb_pdf != audit["doc"]["sections"])
    if a.json:
        audit["pdf"] = {"chemin": pdf_path, "pages": nb_pdf, "apercus": images, "note": note}
        audit["verdicts"] = {p["index"]: verdict(p) for p in audit["pages"]}
        print(json.dumps(audit, ensure_ascii=False, indent=1))
    else:
        print(rapport(audit, pdf_path, nb_pdf, images, note, detail=a.detail))
    return 1 if deborde else 0


if __name__ == "__main__":
    sys.exit(main())
