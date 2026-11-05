# Probabilités conditionnelles et formule de Bayes

Ce chapitre introduit les probabilités conditionnelles, la formule des probabilités totales, l'indépendance et la formule de Bayes. Chaque notion est illustrée par un exemple.

## 1. Probabilité conditionnelle

Savoir qu'un événement B est réalisé change la probabilité d'un autre événement A. La probabilité de A sachant B est définie lorsque P(B) est strictement positive.

$$ P(A \mid B) = \frac{P(A \cap B)}{P(B)} $$

Exemple. On lance un dé équilibré. Sachant que le résultat est pair, la probabilité d'obtenir 6 vaut 1/3, car il reste trois issues paires équiprobables.

## 2. Formule des probabilités totales

Si les événements B1, ..., Bn forment une partition de l'univers, la probabilité de A se décompose selon les cas. Chaque cas contribue en proportion de sa propre probabilité.

$$ P(A) = \sum_{i=1}^{n} P(A \mid B_i) P(B_i) $$

Un arbre de probabilités permet d'organiser ce calcul : on multiplie les probabilités le long d'une branche, puis on additionne les branches qui mènent à A.

## 3. Indépendance

Deux événements A et B sont indépendants lorsque la réalisation de l'un ne modifie pas la probabilité de l'autre. De façon équivalente, la probabilité de l'intersection est le produit des probabilités.

$$ P(A \cap B) = P(A) P(B) $$

Attention : des événements incompatibles de probabilités non nulles ne sont jamais indépendants.

## 4. Formule de Bayes

La formule de Bayes permet d'inverser une probabilité conditionnelle. On l'utilise lorsque P(A sachant B) est connue mais que l'on cherche P(B sachant A).

$$ P(B \mid A) = \frac{P(A \mid B) P(B)}{P(A)} $$

P(B) est appelée probabilité a priori et P(B sachant A) probabilité a posteriori. Le dénominateur se calcule en général avec la formule des probabilités totales.
