# Post LinkedIn, partage skill pdf-print-ready

**Cible** : profil LinkedIn personnel Jonathan Sardo.
**Angle** : pédagogique. Révéler que Claude peut générer des PDF magnifiques, expliquer la technique (HTML → impression PDF), signaler les pièges, partager le skill qui les évite.
**Objectif** : générer des commentaires "skill" qui ouvrent des conversations en DM (qualification puis partage du lien GitHub).

---

## Verbatim final, prêt à publier

On peut générer des PDF magnifiques avec Claude.

La plupart des gens ne le savent pas. Et je te partage le skill open source qui le fait gratuitement 👇

La technique de base est simple.

Tu demandes à Claude de générer une page HTML qui correspond à ton document.

Tu l'ouvres dans Chrome.

⌘P, "Enregistrer en PDF", marges "Aucune". Et voilà, ton livrable est prêt à envoyer à un client, un partenaire, un investisseur.

Sauf que.

Si tu t'arrêtes là, tu vas tomber sur quatre pièges classiques :

- Des espaces blancs énormes au milieu des pages.

- Des titres seuls en bas, leur contenu à la page suivante.

- Des numéros de page en dur qui pètent à chaque modif.

- Des dégradés qui sautent à l'impression.

(CSS print n'est pas du CSS standard. C'est un sous-système avec ses règles à part : breaks, orphans, widows, table-header-group, page-break-inside. La plupart des LLM les ignorent par défaut.)

J'ai isolé 5 règles d'or et un script de 18 lignes qui font le boulot à tous les coups.

Et j'ai packagé tout ça en skill Claude open source, licence MIT.

Compatible Claude Code et Cursor.

Tu l'installes en une commande. Tu lances /pdf-print-ready. Tu décris ton livrable. Tu obtiens un HTML qui s'imprime parfaitement en PDF.

Pas de bricolage.

Pas de coupures bizarres.

Pas de numérotation à entretenir.

Méta-preuve : le mini guide d'utilisation est lui-même généré par le skill.

---

Tu veux le skill ?

Commente "skill" en dessous et je te l'envoie en DM.

---

## Variantes d'accroche (si tu veux tester)

**Variante A (celle ci-dessus, recommandée)**
> On peut générer des PDF magnifiques avec Claude.
> La plupart des gens ne le savent pas. Et je te partage le skill open source qui le fait gratuitement 👇

**Variante B (question rhétorique, inversion sujet-verbe)**
> Sais-tu qu'on peut générer des PDF impeccables avec Claude, sans logiciel d'édition ?
> La technique tient en une page HTML. Et 4 pièges à éviter. Je te partage le skill 👇

**Variante C (autorité, plus directe)**
> Claude peut générer des PDF magnifiques. Si tu connais la recette CSS print.
> 5 règles, 1 script de 18 lignes. Packagé en skill open source, sous le post 👇

---

## Notes de production

- **Heure de publication suggérée** : mardi ou jeudi matin (9h-11h Europe/Paris), créneaux engagement LinkedIn B2B FR optimaux.
- **Format LinkedIn** : long post natif (pas de lien dans le post, sinon l'algo pénalise). Le lien GitHub se partage en DM après commentaire.
- **Réponse aux commentaires "skill"** : NE PAS envoyer le lien directement en DM. Qualifier d'abord (memory `feedback_dm_qualif_asynchrone.md`). Verbatim de réponse type :
  > "Salut [prénom], merci pour ton intérêt sur le skill. Avant que je t'envoie le repo, dis-moi rapidement : tu utilises Claude Code ou Cursor au quotidien, et c'est pour quel type de livrable principalement (propositions clients, contrats, lead magnets, autre) ? Ça m'aide à savoir si j'ai d'autres ressources qui pourraient t'aider en complément."

  Bascule vers un call seulement si le pain est confirmé et qu'il y a un signal d'achat clair sur Crew / Hub.

- **Pas de hashtags** (memory `feedback_linkedin_no_hashtags`).
- **Pas d'em-dash** (vérifié).
- **Pas de tarif visible** (TOFU pur, lead magnet gratuit).
- **Confidentialité** : aucune mention de prospect ou client, conformément à règle 24 destination externe public.
- **Pas de mention Crew dans le post** : graine plantée en DM lors de la qualification post-commentaire.

## Garde-fous appliqués

- ✅ Open loop dès la 1ère ligne ("la plupart des gens ne le savent pas")
- ✅ Posture pédagogique, pas storytelling lacrymal (cohérent BRAND_VOICE.md)
- ✅ Tension narrative maintenue par le pain quantifié (4 pièges concrets)
- ✅ Révélation explicite (5 règles + script de 18 lignes + skill)
- ✅ CTA clair "commente skill, je te l'envoie en DM"
- ✅ Style Jonathan : phrases isolées, doubles sauts de ligne, inversion possible sur variantes, ancrages courts
- ✅ Pas de promesse "ferme tes deals pendant que tu dors" (AI-augmentation pas AI-automation)
- ✅ Pas de claim "souverain" (skill universel, pas spécifique au positionnement Hub)
- ✅ Posture expert qui éduque + challenger qui prend position (cohérent BRAND_VOICE.md section 1)
