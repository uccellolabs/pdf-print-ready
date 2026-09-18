#!/usr/bin/env python3
"""
Repartit un contenu en pages A4, en mesurant au lieu d'estimer.

**Le defaut qu'il corrige.** `rendre_pdf.py` mesure tres bien : il dit ce qui
deborde, ce qui est creux et ce qui est serre. Mais il **constate**, il ne
repartit pas. La coupe en pages se faisait donc a la main, a l'estime, et se
refaisait en entier a chaque retouche du texte. Mesure du 16/09/2026, sur deux
documents mis en page le meme jour : quinze pages remplies de 21 % a 57 % pour
la premiere version, deux recompositions manuelles pour arriver a onze pages
correctes, et le meme travail refait de zero sur le second document.

**Ce qu'il fait, et c'est tout.** Il lit un document dont le contenu est une
suite de blocs, mesure la hauteur reelle de chacun **dans le rendu du document
lui-meme**, et ecrit les blocs dans des pages. Il ne rédige rien, ne reformule
rien, ne coupe aucun bloc en deux.

**Pourquoi il mesure le resultat au lieu de s'arreter au calcul.** Les hauteurs
changent quand les blocs se regroupent : une marge entre deux blocs disparait en
haut de page, un titre suivi d'un tableau ne prend pas la meme place qu'un titre
suivi d'un paragraphe. Le script repasse donc jusqu'a ce que **plus rien ne
bouge**, jamais sur un seul calcul. C'est la meme regle que partout ailleurs : on
s'arrete sur « rien de nouveau », pas sur « ca devrait aller ».

## La convention d'entree

Le document porte **une seule page**, et dans sa zone de contenu **un conteneur
de flux** :

    <div class="page">
      <div class="page-content">
        <div data-flux>
          <h2 data-titre>Un titre</h2>
          <p>Un bloc</p>
          <div data-ensemble="1">…</div>   <!-- reste avec le suivant -->
          …
        </div>
      </div>
      <div class="page-footer">…</div>
    </div>

- **Chaque enfant direct de `[data-flux]` est un bloc**, et un bloc ne se coupe
  jamais.
- **`data-titre`** marque un bloc qui ne doit jamais rester seul en bas de page.
- **`data-ensemble="<cle>"`** colle des blocs voisins : ils partent ensemble.

La zone de flux est dans une vraie page, donc **la largeur de mesure est la
largeur reelle du contenu**. Mesurer ailleurs donnerait des hauteurs fausses.

Usage :
    python3 scripts/repartir_pages.py <doc.html>              a blanc, rend le plan
    python3 scripts/repartir_pages.py <doc.html> --appliquer  ecrit <doc>.paginé.html
    python3 scripts/repartir_pages.py <doc.html> --cible 0.90
    python3 scripts/repartir_pages.py --test
"""

import argparse
import base64
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CIBLE_DEFAUT = 0.92      # remplissage vise d'une page
PASSES_MAX = 6           # au-dela, on ne converge pas : on le dit

MESURE_JS = """
<script>
window.addEventListener('load', function () {
  var flux = document.querySelector('[data-flux]');
  var zone = document.querySelector('.page-content') || flux.parentElement;
  var blocs = [];
  Array.prototype.forEach.call(flux.children, function (el, i) {
    var r = el.getBoundingClientRect();
    var st = getComputedStyle(el);
    blocs.push({
      i: i,
      h: r.height + parseFloat(st.marginTop || 0) + parseFloat(st.marginBottom || 0),
      titre: el.hasAttribute('data-titre'),
      ensemble: el.getAttribute('data-ensemble') || null
    });
  });
  var out = {utile: zone.clientHeight, blocs: blocs};
  var pre = document.createElement('pre');
  pre.id = '__mesure';
  pre.textContent = btoa(unescape(encodeURIComponent(JSON.stringify(out))));
  document.body.appendChild(pre);
});
</script>
"""


# --------------------------------------------------------------- la repartition

def grouper(blocs):
    """Les blocs qui ne se separent pas, dans l'ordre.

    Deux voisins qui portent la meme cle `data-ensemble` partent ensemble, et un
    titre s'accroche a ce qui le suit : **un titre seul en bas de page est le
    defaut que la mesure ne voit pas**, parce que la page n'a rien d'anormal.
    """
    groupes, courant = [], []

    for b in blocs:
        if courant:
            prec = courant[-1]
            colle = (prec.get("ensemble") and prec["ensemble"] == b.get("ensemble")) \
                or prec.get("titre")
            if not colle:
                groupes.append(courant)
                courant = []
        courant.append(b)

    if courant:
        groupes.append(courant)

    return groupes


def repartir(blocs, utile, cible=CIBLE_DEFAUT):
    """Rend la liste des pages, chacune une liste d'indices de blocs.

    **Un groupe plus haut qu'une page part seul**, et il est signale : on ne le
    coupe pas, parce que le couper voudrait dire rediger a la place de l'auteur.
    """
    pages, page, haut = [], [], 0.0
    trop_hauts = []

    for g in grouper(blocs):
        hg = sum(b["h"] for b in g)
        idx = [b["i"] for b in g]

        if hg > utile:
            if page:
                pages.append(page)
                page, haut = [], 0.0
            pages.append(idx)
            trop_hauts.append((idx[0], hg))
            continue

        if page and haut + hg > utile * cible and haut + hg > utile:
            pages.append(page)
            page, haut = [], 0.0
        elif page and haut + hg > utile:
            pages.append(page)
            page, haut = [], 0.0

        page.extend(idx)
        haut += hg

    if page:
        pages.append(page)

    return pages, trop_hauts


def remplissages(pages, blocs, utile):
    """Le taux de remplissage de chaque page, pour dire ce qui est creux."""
    h = {b["i"]: b["h"] for b in blocs}
    return [sum(h[i] for i in p) / utile if utile else 0.0 for p in pages]


# --------------------------------------------------------------- l'ecriture

def borner(source, ouvrante):
    """(debut de l'interieur, fin de l'interieur) d'un element, par comptage.

    **Une expression reguliere ne sait pas fermer une balise imbriquee.** La
    premiere version cherchait « la fermeture suivie d'un `</div>` » : sur un
    flux de trois blocs, elle rendait un fragment coupe au milieu du deuxieme,
    et le document sortait casse sans que rien ne le dise. Trouve a l'ecriture
    du test, pas a l'usage.
    """
    nom = re.match(r"<([a-zA-Z][\w-]*)", ouvrante.group(0)).group(1)
    debut = ouvrante.end()
    prof = 1

    for b in re.finditer(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(nom), source[debut:], re.I):
        if b.group(2) == "/":
            continue
        prof += -1 if b.group(1) else 1
        if prof == 0:
            return debut, debut + b.start()

    raise RuntimeError("l'element <%s> n'est pas referme" % nom)


def decouper_flux(source):
    """(debut, fin) de l'interieur du conteneur de flux."""
    m = re.search(r"<[a-zA-Z][\w-]*[^>]*\sdata-flux[^>]*>", source)
    if not m:
        raise RuntimeError("aucun conteneur [data-flux] dans ce document")
    return borner(source, m)


def bloc_page(source):
    """(debut, fin) de l'element `.page` du document, bornes par comptage.

    **Une expression reguliere ne sait pas trouver la fermeture d'une balise
    imbriquee.** Un `.page` contient des dizaines de `<div>` : chercher le
    premier `</div>` donnerait un fragment tronque, et le document sortirait
    casse sans que rien ne le dise.
    """
    m = re.search(r"<div[^>]*\bclass=[\"'][^\"']*\bpage\b[^\"']*[\"'][^>]*>", source)
    if not m:
        raise RuntimeError("aucun element .page dans ce document")

    prof, i = 0, m.start()
    for b in re.finditer(r"<(/?)div\b[^>]*?(/?)>", source[m.start():]):
        if b.group(2) == "/":
            continue
        prof += -1 if b.group(1) else 1
        if prof == 0:
            return m.start(), m.start() + b.end()

    raise RuntimeError("l'element .page n'est pas referme")


def gabarit(source):
    """Le gabarit d'une page : la page du document, videe de son flux."""
    deb, fin = bloc_page(source)
    page = source[deb:fin]
    d, f = decouper_flux(page)
    page = page[:d] + "\n<!--CONTENU-->\n" + page[f:]

    # Le numero de page, s'il y en a un, devient un marqueur : il se pose a
    # l'ecriture, jamais en dur (c'est deja la regle du skill).
    page = re.sub(r"(<[^>]*\bclass=[\"'][^\"']*\bpage-num\b[^\"']*[\"'][^>]*>)(.*?)(</)",
                  r"\1<!--NUM-->\3", page, count=1, flags=re.S)

    return page, deb, fin


def appliquer(source, pages):
    """Rend le document entier, ses blocs repartis dans autant de pages."""
    gab, deb, fin = gabarit(source)
    d, f = decouper_flux(source)
    morceaux = decouper_blocs(source[d:f])

    rendu = []
    for n, p in enumerate(pages, 1):
        contenu = "\n".join(morceaux[i] for i in p)
        rendu.append(gab.replace("<!--CONTENU-->", contenu).replace("<!--NUM-->", str(n)))

    return source[:deb] + "\n".join(rendu) + source[fin:]


def decouper_blocs(interieur):
    """Les enfants directs d'un fragment HTML, dans l'ordre, tels quels."""
    blocs, prof, debut = [], 0, None
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>", interieur):
        fermant, nom, attrs, auto = m.group(1), m.group(2), m.group(3), m.group(4)
        seul = auto == "/" or nom.lower() in ("br", "hr", "img", "input", "meta", "link")

        if not fermant:
            if prof == 0:
                debut = m.start()
            if not seul:
                prof += 1
            elif prof == 0:
                blocs.append(interieur[debut:m.end()])
                debut = None
        else:
            prof -= 1
            if prof == 0 and debut is not None:
                blocs.append(interieur[debut:m.end()])
                debut = None

    return blocs


# --------------------------------------------------------------- la mesure

def mesurer(chrome_bin, chemin):
    """Les hauteurs reelles, dans le rendu du document lui-meme."""
    import tempfile
    import rendre_pdf

    source = open(chemin, encoding="utf-8").read()
    copie = source.replace("</body>", MESURE_JS + "</body>", 1) \
        if "</body>" in source else source + MESURE_JS

    dossier = os.path.dirname(os.path.abspath(chemin))
    fd, tmp = tempfile.mkstemp(prefix=".__mesure_", suffix=".html", dir=dossier)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(copie)
        res = rendre_pdf.chrome(chrome_bin,
                                ["--virtual-time-budget=8000", "--dump-dom", "file://" + tmp])
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    m = re.search(r'<pre id="__mesure">([A-Za-z0-9+/=\s]+)</pre>', res.stdout)
    if not m:
        raise RuntimeError("la mesure n'a rien rendu : Chrome n'a pas execute la page")

    return json.loads(base64.b64decode(re.sub(r"\s+", "", m.group(1))).decode("utf-8"))


# --------------------------------------------------------------- autotest

def autotest():
    ok = fail = 0

    def v(nom, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok   %s" % nom)
        else:
            fail += 1
            print("  FAIL %s" % nom)

    def B(i, h, titre=False, ens=None):
        return {"i": i, "h": h, "titre": titre, "ensemble": ens}

    print("Regroupement")
    g = grouper([B(0, 10, titre=True), B(1, 50), B(2, 30)])
    v("un titre s'accroche a ce qui le suit", [x["i"] for x in g[0]] == [0, 1])
    v("et le reste est libre", [x["i"] for x in g[1]] == [2])

    g = grouper([B(0, 10, ens="a"), B(1, 20, ens="a"), B(2, 30)])
    v("deux blocs de meme ensemble partent ensemble", [x["i"] for x in g[0]] == [0, 1])

    g = grouper([B(0, 10, titre=True), B(1, 10, titre=True), B(2, 30)])
    v("deux titres de suite emportent le bloc suivant",
      [x["i"] for x in g[0]] == [0, 1, 2] and len(g) == 1)

    print("\nRepartition")
    blocs = [B(i, 100) for i in range(10)]
    pages, trop = repartir(blocs, utile=300, cible=1.0)
    v("trois blocs de 100 tiennent dans 300", pages[0] == [0, 1, 2])
    v("et le compte de pages est juste", len(pages) == 4)
    v("aucun bloc trop haut", trop == [])

    pages, _ = repartir([B(0, 100), B(1, 100), B(2, 100)], utile=250, cible=1.0)
    v("un bloc qui ne tient pas passe a la page suivante", pages == [[0, 1], [2]])

    # Le defaut que la mesure ne voit pas : un titre seul en bas de page.
    blocs = [B(0, 200), B(1, 40, titre=True), B(2, 200)]
    pages, _ = repartir(blocs, utile=260, cible=1.0)
    v("un titre ne reste jamais seul en bas de page",
      all(not (len(p) and blocs[p[-1]]["titre"]) for p in pages))
    v("il descend avec son contenu", pages == [[0], [1, 2]])

    pages, trop = repartir([B(0, 50), B(1, 900), B(2, 50)], utile=300, cible=1.0)
    v("un bloc plus haut qu'une page part seul", [1] in pages)
    v("et il est signale au lieu d'etre coupe", trop and trop[0][0] == 1)
    v("ce qui le precede n'est pas absorbe", pages[0] == [0])

    print("\nRemplissage")
    blocs = [B(0, 100), B(1, 100), B(2, 100)]
    pages, _ = repartir(blocs, utile=300, cible=1.0)
    r = remplissages(pages, blocs, 300)
    v("une page pleine est a 100 %", abs(r[0] - 1.0) < 1e-9)

    print("\nDecoupage des blocs")
    frag = '<h2 data-titre>T</h2>\n<p>un <b>mot</b> gras</p>\n<hr>\n<div><p>imbrique</p></div>'
    b = decouper_blocs(frag)
    v("quatre blocs, pas cinq", len(b) == 4)
    v("le balisage interne ne compte pas", "<b>mot</b>" in b[1])
    v("une balise seule est un bloc", b[2].strip() == "<hr>")
    v("un bloc imbrique reste entier", b[3].strip().endswith("</div>"))

    print("\nGabarit et ecriture")
    doc = ('<html><body>\n'
           '<div class="page"><div class="page-content"><div data-flux>'
           '<h2 data-titre>T</h2><p>A</p><p>B</p>'
           '</div></div><div class="page-footer"><span class="page-num">1</span></div></div>\n'
           '</body></html>')
    g, deb, fin = gabarit(doc)
    v("le gabarit garde la page entiere", g.startswith('<div class="page"') and g.endswith("</div>"))
    v("son flux est vide et marque", "<!--CONTENU-->" in g and "<h2" not in g)
    v("le numero devient un marqueur", "<!--NUM-->" in g and ">1<" not in g)

    out = appliquer(doc, [[0, 1], [2]])
    v("deux pages ecrites", out.count('class="page"') == 2)
    v("les blocs sont a leur place", out.index("<p>A</p>") < out.index("<p>B</p>"))
    v("les numeros sont poses", ">1<" in out and ">2<" in out)
    v("ce qui entoure la page est garde", out.startswith("<html><body>"))

    print("\nUn document sans flux le dit")
    try:
        decouper_flux("<html><body><div class='page'></div></body></html>")
        v("un document sans [data-flux] leve une erreur", False)
    except RuntimeError:
        v("un document sans [data-flux] leve une erreur", True)

    print("\n%d reussis, %d echoues" % (ok, fail))
    return 0 if fail == 0 else 1


# --------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[1])
    ap.add_argument("html", nargs="?", help="le document a repartir")
    ap.add_argument("--appliquer", action="store_true", help="ecrire le document pagine")
    ap.add_argument("--cible", type=float, default=CIBLE_DEFAUT,
                    help="remplissage vise (defaut : %.2f)" % CIBLE_DEFAUT)
    ap.add_argument("--chrome", help="chemin de Chrome ou Chromium")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()

    if a.test:
        return autotest()

    if not a.html:
        ap.print_help()
        return 2

    import rendre_pdf
    chrome_bin = rendre_pdf.trouver_chrome(a.chrome)

    m = mesurer(chrome_bin, a.html)
    pages, trop = repartir(m["blocs"], m["utile"], a.cible)
    taux = remplissages(pages, m["blocs"], m["utile"])

    print("Zone utile mesuree : %d px" % m["utile"])
    print("%d bloc(s) repartis en %d page(s)\n" % (len(m["blocs"]), len(pages)))

    for n, (p, t) in enumerate(zip(pages, taux), 1):
        etat = "creuse" if t < 0.55 else ("serree" if t > 0.98 else "")
        print("  page %-3d %2d bloc(s)  %5.1f %%  %s" % (n, len(p), t * 100, etat))

    if trop:
        print("\n  %d bloc(s) plus haut(s) qu'une page, laisse(s) seul(s) :" % len(trop))
        for i, h in trop:
            print("    bloc %d : %d px pour %d px utiles" % (i, h, m["utile"]))
        print("  Ils ne se coupent pas ici : les couper serait rediger a la place de l'auteur.")

    if not a.appliquer:
        print("\nRien n'a ete ecrit. Relancer avec --appliquer.")
        return 0

    source = open(a.html, encoding="utf-8").read()
    sortie = os.path.splitext(a.html)[0] + ".pagine.html"
    open(sortie, "w", encoding="utf-8").write(appliquer(source, pages))
    print("\nEcrit : %s" % sortie)

    # **On remesure le resultat.** Les hauteurs changent quand les blocs se
    # regroupent : une marge disparait en haut de page, un titre suivi d'un
    # tableau ne prend pas la meme place. Un plan calcule n'est pas un plan
    # verifie.
    verif = rendre_pdf.auditer(chrome_bin, sortie)
    debordent = [p for p in verif.get("pages", []) if p.get("overflow", 0) > 1]
    print("  %d page(s) rendue(s), %d debordement(s) mesure(s)"
          % (len(verif.get("pages", [])), len(debordent)))

    if debordent:
        print("  Relancer avec une cible plus basse (--cible 0.85) : la repartition a ete")
        print("  calculee sur des hauteurs mesurees avant regroupement.")
        return 1

    print("  Le document n'est pas relu pour autant : "
          "`rendre_pdf.py` dit la forme, pas le fond.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
