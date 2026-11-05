# Introduction to Probability
<!-- language: en -->
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

## Slide 1: Sample Space
- Random experiment outcomes unknown
- Sample space S = set of all possible outcomes
- Example: die roll S = {1,2,3,4,5,6}

Say: Why it matters: defining the universe of outcomes lets us assign probabilities rigorously.
Say: Intuition: think of S as the list of every result you could possibly see when you run the experiment.
Say: Example: for a single six-sided die, the sample space is S = {1,2,3,4,5,6}. This captures all six equally possible faces.
Source: 1. Sample spaces and events

## Slide 2: Events and Set Operations
- Event = subset of S
- Union A∪B, Intersection A∩B, Complement Aᶜ
- Disjoint events have empty intersection

Say: Why it matters: events are the objects we assign probabilities to, and set operations let us combine them.
Say: Intuition: an event is simply a collection of outcomes you care about, like "even roll".
Say: Example: A = {2,4,6} (even), B = {4,5,6} (greater than 3). Union A∪B = {2,4,5,6}, Intersection A∩B = {4,6}. This matches the worked example in the notes.
Say: Common mistake: forgetting that the union counts outcomes appearing in both sets unless you subtract the intersection.
Source: 1. Sample spaces and events

## Slide 3: Kolmogorov Axioms
- P(A) ≥ 0
- P(S) = 1
- If A∩B=∅ then P(A∪B)=P(A)+P(B)

$$ P ( A ) \geq 0 , \; P ( S ) = 1 $$
> Probabilities are never negative and the whole sample space has probability one.

$$ P ( A \cup B ) = P ( A ) + P ( B ) \text{ if } A \cap B = \emptyset $$
> For disjoint events the probability of their union is the sum of their individual probabilities.

Say: Why it matters: these axioms are the foundation from which all probability rules are derived.
Say: Intuition: think of probability as a weight assigned to sets of outcomes; the whole space must weigh to one and weights cannot be negative.
Say: Connection: from these axioms we can derive formulas for complements and general unions.
Source: 2. Axioms of probability

## Slide 4: Addition Rule and Uniform Example
- P(A∪B)=P(A)+P(B)-P(A∩B)
- Uniform case: P(event)=#outcomes/total
- Even roll probability = 3/6 = 1/2

$$ P ( A \cup B ) = P ( A ) + P ( B ) - P ( A \cap B ) $$
> For any two events we subtract the overlap to avoid double‑counting.

Say: Why it matters: most real problems involve events that are not disjoint, so we need the full addition rule.
Say: Intuition: start with the sum of probabilities, then remove the part counted twice.
Say: Example: for a fair die, event "even" has 3 favorable outcomes out of 6, giving P(even)=3/6=1/2. This uses the uniform probability formula.
Say: Common mistake: forgetting to subtract P(A∩B) leads to probabilities larger than 1.
Source: 2. Axioms of probability

## Slide 5: Conditional probability and independence
- P(A|B)=P(A∩B)/P(B)
- Multiplication rule: P(A∩B)=P(A|B)P(B)
- Independence: P(A∩B)=P(A)P(B)

$$ P ( A \mid B ) = \frac { P ( A \cap B ) } { P ( B ) } $$
> The probability of A given B is the joint probability divided by the probability of B.

$$ P ( A \cap B ) = P ( A \mid B ) P ( B ) $$
> Rearranged form, showing how to compute a joint probability from a conditional.

Say: Conditional probability tells us how our belief about A changes once we know B happened.
Say: Independence means learning B does not affect the chance of A, so the joint factorises.
Say: Example: drawing two cards without replacement. P(both aces)=4/52 × 3/51≈0.0045; the second factor is P(second ace|first ace).
Say: A common mistake is to treat dependent events as independent and multiply marginal probabilities.
Source: 3. Conditional probability and independence

## Slide 6: Bayes' theorem
- P(B|A)=P(A|B)P(B)/P(A)
- Prior = P(B), Posterior = P(B|A)
- Denominator via total probability

$$ P ( B \mid A ) = \frac { P ( A \mid B ) P ( B ) } { P ( A ) } $$
> Bayes' theorem expresses the reverse conditional probability in terms of the forward one.

Say: Bayes' theorem lets us update our belief about B after observing A.
Say: The prior P(B) reflects the initial chance of B, while the posterior P(B|A) is the updated chance.
Say: Example: disease prevalence 1%, test sensitivity 99%, false positive 5%. Posterior ≈0.17, showing most positives are false.
Say: Beware: forgetting to compute P(A) correctly; usually need the law of total probability.
Source: 4. Bayes' theorem

## Slide 7: Discrete random variables: expectation & variance
- E[X]=Σ x p(x)
- Var(X)=E[X²]−(E[X])²
- Linearity: E[aX+b]=aE[X]+b

$$ E [ X ] = \sum _ { x } x \, p ( x ) $$
> The mean is the weighted average of all possible values.

$$ V a r ( X ) = E [ X ^ { 2 } ] - ( E [ X ] ) ^ { 2 } $$
> Variance measures the average squared deviation from the mean.

Say: A discrete random variable maps outcomes to numbers; its pmf gives probabilities for each value.
Say: Expectation is linear, making calculations with sums of variables easy.
Say: Example: fair die. E[X]=3.5, E[X²]=91/6, variance≈2.92.
Say: A subtle point: adding a constant shifts the mean but does not change variance.
Source: 5. Discrete random variables
