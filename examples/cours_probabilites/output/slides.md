# Probabilités conditionnelles et formule de Bayes
<!-- language: fr -->
<!--
Edit this file to correct the slides, then run:
    course2video continue <out-dir> --from md
Format: '## Slide N: Title', then '- ' bullets, '$$ latex $$' followed by a
'> explanation' line for each equation, optional 'Notes:' and 'Source:' lines.
'Say:' lines are talking points: what the lecturer explains out loud (not shown on the slide).
'Kind:' is theory, exercise or solution; 'From:' names the source document and problem.
'Figure:' shows a source figure on the slide (ids in figures/figures.json); delete the line to remove it.
Delete a whole '## Slide' block to drop a slide. Slides are renumbered in order.
-->

## Slide 1: Probabilité conditionnelle
- Définition avec P(B) > 0
- Formule : P(A|B) = P(A∩B)/P(B)
- Exemple du dé pair

$$ P(A \mid B) = \frac{P(A \cap B)}{P(B)} $$
> La probabilité de A sachant B est le rapport de l'intersection sur la probabilité de B.

Say: Cette notion montre comment l'information sur B modifie notre évaluation de A.
Say: Intuition : on ne considère que les cas où B est vrai, alors on renormalise.
Say: Example: lancer un dé équilibré, sachant que le résultat est pair, les issues possibles sont {2,4,6}; la probabilité d'obtenir 6 est donc 1/3.
Say: Il faut toujours vérifier que P(B) soit strictement positif avant d’appliquer la formule.
Source: 1. Probabilité conditionnelle

## Slide 2: Formule des probabilités totales
- B1…Bn forment une partition
- P(A) = Σ P(A|Bi) P(Bi)
- Arbre de probabilités

$$ P(A) = \sum_{i=1}^{n} P(A \mid B_i) P(B_i) $$
> La probabilité de A est la somme des probabilités conditionnelles sur chaque cas Bi pondérées par P(Bi).

Say: Cette formule permet de décomposer une probabilité complexe en cas simples.
Say: Intuition : on regarde chaque scénario possible Bi et on combine les contributions.
Say: Un arbre de probabilités aide à visualiser le calcul : on multiplie le long d'une branche puis on additionne les branches menant à A.
Say: Attention à bien choisir des événements B_i qui forment une partition de l'univers.
Source: 2. Formule des probabilités totales

## Slide 3: Indépendance
- A et B indépendants ⇔ P(A∩B)=P(A)P(B)
- Pas d'effet de l'un sur l'autre
- Incompatibles ≠ indépendants

$$ P(A \cap B) = P(A) P(B) $$
> Si A et B sont indépendants, la probabilité de les voir se réaliser ensemble est le produit de leurs probabilités séparées.

Say: L'indépendance signifie que connaître B n'influence pas la probabilité de A.
Say: Souvent confondu avec incompatibilité : deux événements incompatibles (mutuellement exclusifs) ont P(A∩B)=0 mais ne sont pas indépendants si leurs probabilités sont non nulles.
Say: Un moyen de vérifier l'indépendance est de comparer P(A|B) avec P(A).
Source: 3. Indépendance

## Slide 4: Formule de Bayes
- Inversion de probabilité conditionnelle
- P(B|A)=P(A|B)P(B)/P(A)
- Utilise souvent les probabilités totales

$$ P(B \mid A) = \frac{P(A \mid B) P(B)}{P(A)} $$
> La probabilité a posteriori de B sachant A s'obtient en combinant la vraisemblance P(A|B) et la probabilité a priori P(B), normalisée par P(A).

Say: Bayes permet de mettre à jour nos croyances sur B après l'observation de A.
Say: Le terme P(B) est la probabilité a priori, P(B|A) la probabilité a posteriori.
Say: P(A) se calcule généralement avec la formule des probabilités totales, en sommant sur tous les B_i possibles.
Say: Erreur fréquente : oublier de normaliser correctement, ce qui conduit à une probabilité >1.
Source: 4. Formule de Bayes

## Slide 5: Exercice 1 – Le dé
- Lancer un dé équilibré à six faces
- Condition : résultat ≥ 4
- Question : probabilité d’obtenir un nombre pair

Say: On veut la probabilité d'un événement sous condition d'un autre événement.
Say: Le problème porte sur la probabilité conditionnelle, pas sur une probabilité simple.
Say: Il faut identifier clairement les issues compatibles avec la condition « ≥ 4 ».
Say: Le défi est de ne pas confondre le nombre total d'issues du dé avec celles admises par la condition.
Source: Exercice corrigé 1: Le dé
Kind: exercise
From: TD 3, Exercice 1

## Slide 6: Solution – Probabilité conditionnelle
- A : résultat ≥ 4 = {4,5,6}
- B : nombre pair = {2,4,6}
- A∩B = {4,6}
- P(B|A)= (2/6)/(3/6)=2/3

$$ P(B|A)=\frac{P(A\cap B)}{P(A)} $$
> La probabilité conditionnelle de B sachant A est le rapport de l'intersection sur la probabilité de A.

Say: On calcule d'abord P(A) = 3/6 = 1/2 car trois faces satisfont ≥ 4.
Say: L'intersection A∩B contient les nombres pairs 4 et 6, donc P(A∩B)=2/6.
Say: En appliquant la formule, on obtient (2/6)/(3/6) = 2/3.
Say: Vérifier : parmi les trois issues possibles sous la condition, deux sont paires, donc 2/3.
Source: Exercice corrigé 1: Le dé
Kind: solution
From: TD 3, Exercice 1

## Slide 7: Test de dépistage
- Prévalence de la maladie : 2 %
- Sensibilité du test : 95 % des malades détectés
- Faux positif : 10 % des sains testés positifs
- Une personne est testée positive, quel est P(M|T) ?

Say: L'énoncé veut la probabilité d'être malade sachant qu'on a un test positif.
Say: Il faut combiner la rareté de la maladie avec les performances du test.
Say: C'est un problème classique de probabilité conditionnelle.
Source: Exercice corrigé 2: Test de dépistage
Kind: exercise
From: TD 3, Exercice 2

## Slide 8: Solution – Bayes
- Calcul de P(T) par la formule des probabilités totales
- Application de la formule de Bayes
- Résultat : environ 0,16

$$ P(T)=0.95 \times 0.02 + 0.10 \times 0.98 $$
> Probabilité d'obtenir un test positif, qu'on soit malade ou sain.

$$ P(M\mid T)=\frac{0.95 \times 0.02}{P(T)}=\frac{0.019}{0.117} $$
> Formule de Bayes pour la probabilité d'être malade sachant le test positif.

Say: On multiplie la sensibilité par la prévalence, puis le taux de faux positif par la proportion saine.
Say: P(T) vaut 0,019 + 0,098 = 0,117, soit la probabilité totale d'un test positif.
Say: Ensuite on divise la partie « malade et test positif » par P(T) pour obtenir P(M|T).
Say: Le quotient donne environ 0,16, c'est‑à‑dire 16 % des positifs sont réellement malades.
Source: Exercice corrigé 2: Test de dépistage
Kind: solution
From: TD 3, Exercice 2

## Slide 9: Exercice 3 – Deux urnes
- U1 : 3 rouges, 2 vertes
- U2 : 1 rouge, 4 vertes
- Choix d'une urne au hasard
- Quel est P(boule rouge) ?

Say: On doit calculer la probabilité totale d'obtenir une boule rouge.
Say: Le problème combine deux étapes aléatoires : choisir l'urne, puis la boule.
Say: Il faut faire attention à ne pas confondre les proportions de chaque urne.
Source: Exercice corrigé 3: Deux urnes
Kind: exercise
From: TD 3, Exercice 3

## Slide 10: Solution – Probabilité totale
- P(urne choisie) = 1/2 pour chaque urne
- P(R|U1) = 3/5, P(R|U2) = 1/5
- P(R) = 1/2·3/5 + 1/2·1/5 = 2/5

$$ P(R)=\frac{1}{2}\times\frac{3}{5}+\frac{1}{2}\times\frac{1}{5} $$
> Probabilité totale : somme des produits probabilité d'urne et probabilité rouge conditionnée.

$$ P(R)=\frac{2}{5} $$
> Résultat final de la probabilité d'obtenir une boule rouge.

Say: Chaque urne étant équi‑probable, on multiplie la probabilité de choisir l'urne par la probabilité d'une rouge dans celle‑ci.
Say: On calcule d'abord les proportions : 3/5 dans U1, 1/5 dans U2.
Say: On applique la formule des probabilités totales et on simplifie les fractions.
Say: Vérifier : la somme des contributions donne bien 2/5, soit 0,4.
Source: Exercice corrigé 3: Deux urnes
Kind: solution
From: TD 3, Exercice 3
