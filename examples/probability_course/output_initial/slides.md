# Introduction to Probability
<!-- language: en -->
<!--
Edit this file to correct the slides, then run:
    course2video continue <out-dir> --from md
Format: '## Slide N: Title', then '- ' bullets, '$$ latex $$' followed by a
'> explanation' line for each equation, optional 'Notes:' and 'Source:' lines.
Delete a whole '## Slide' block to drop a slide. Slides are renumbered in order.
-->

## Slide 1: Introduction to Probability
- A first introduction to probability for science and engineering students
- Topics: sample spaces and events, axioms of probability
- Conditional probability, independence and Bayes' theorem
- Discrete random variables, expectation and variance
- Each chapter ends with a short worked example

Notes: Overview of the course structure.
Source: Introduction to Probability

## Slide 2: Random Experiments and Sample Spaces
- Random experiment: outcome cannot be predicted with certainty (e.g. coin toss, bulb lifetime)
- Sample space S: set of all possible outcomes
- One die roll: S = {1, 2, 3, 4, 5, 6}
- Event: a subset of the sample space, e.g. "roll is even" A = {2, 4, 6}
- An event occurs when the outcome belongs to it; empty set is impossible, S is certain

Notes: Emphasize that events are sets of outcomes.
Source: 1. Sample spaces and events

## Slide 3: Combining Events
- Union of A and B: A or B occurs
- Intersection of A and B: both occur
- Complement of A: A does not occur
- Mutually exclusive (disjoint): cannot occur together, intersection is empty
- Example: A = even, B = greater than 3; union {2, 4, 5, 6}, intersection {4, 6}

Notes: Worked example from the die roll.
Source: 1. Sample spaces and events

## Slide 4: Kolmogorov's Axioms
- A probability measure assigns a number P(A) to every event A
- Probabilities are never negative
- The probability of the whole sample space is one
- Probability of a union of mutually exclusive events is the sum of their probabilities

$$ P ( A ) \geq 0 , \ \ P ( S ) = 1 $$
> Every event has non-negative probability, and the certain event has probability one.

$$ P ( A \cup B ) = P ( A ) + P ( B ) \text { if } A \cap B = \emptyset $$
> For disjoint events, the probability that one or the other occurs is the sum of their probabilities.

Notes: These three axioms are the foundation for all later rules.
Source: 2. Axioms of probability

## Slide 5: Consequences of the Axioms
- Complement of A has probability one minus P(A)
- The impossible event has probability zero
- Addition rule for any two events subtracts the intersection, which would be counted twice
- Equally likely outcomes: P(event) = outcomes in event / total outcomes
- Fair die: P(even) = 3/6 = 1/2

$$ P ( A \cup B ) = P ( A ) + P ( B ) - P ( A \cap B ) $$
> General addition rule: add the probabilities and remove the double-counted overlap.

Notes: The addition rule holds for events that are not necessarily disjoint.
Source: 2. Axioms of probability

## Slide 6: Conditional Probability
- Describes how probability of an event changes when another event is known to have occurred
- P(A given B) is defined when P(B) is greater than zero
- Multiplication rule: P(A and B) = P(A given B) times P(B)

$$ P ( A \, | \, B ) = \frac { P ( A \cap B ) } { P ( B ) } $$
> The probability of A given B is the probability of both occurring divided by the probability of B.

$$ P ( A \cap B ) = P ( A \, | \, B ) P ( B ) $$
> Multiplication rule, obtained by rearranging the definition of conditional probability.

Notes: Multiplication rule follows directly from the definition.
Source: 3. Conditional probability and independence

## Slide 7: Total Probability and Independence
- Law of total probability splits P(A) over a partition into disjoint cases B1, ..., Bn
- Independent: knowing one occurred does not change the probability of the other
- Equivalently, P of the intersection is the product of the probabilities
- Independence is not mutual exclusivity: disjoint events with positive probabilities are always dependent

$$ P ( A ) = \sum _ { i = 1 } ^ { n } P ( A \ | \ B _ { i } ) P ( B _ { i } ) $$
> The probability of A is a weighted sum of its conditional probabilities over all cases of a partition.

$$ P ( A \cap B ) = P ( A ) P ( B ) $$
> Condition for A and B to be independent.

Notes: Stress the common confusion between independent and disjoint events.
Source: 3. Conditional probability and independence

## Slide 8: Worked Example: Two Aces
- Draw two cards from a deck without replacement
- P(both aces) = 4/52 times 3/51, about 0.0045
- The second factor is a conditional probability: the first ace has been removed

Notes: Application of the multiplication rule.
Source: 3. Conditional probability and independence

## Slide 9: Bayes' Theorem
- Reverses a conditional probability
- Expresses P(B given A) using P(A given B), which is often easier to know
- P(B) is the prior probability; P(B given A) is the posterior probability
- Denominator P(A) is usually computed with the law of total probability

$$ P ( B \ | \ A ) = \frac { P ( A \ | \ B ) P ( B ) } { P ( A ) } $$
> The posterior probability of B given A equals the likelihood of A given B times the prior of B, divided by P(A).

Notes: Connect the denominator to the law of total probability from the previous section.
Source: 4. Bayes' theorem

## Slide 10: Worked Example: Medical Test
- Disease affects 1% of the population
- Test detects 99% of sick people; 5% false positives among healthy people
- P(sick given positive) = 0.99·0.01 / (0.99·0.01 + 0.05·0.99), about 0.17
- The prior is so small that most positive results are false positives

Notes: A classic illustration of the importance of the prior.
Source: 4. Bayes' theorem

## Slide 11: Random Variables, Mean and Variance
- Random variable: function assigning a number to each outcome
- Discrete: takes a finite or countable number of values
- PMF p(x): probability the variable equals x; non-negative and sums to one
- Expectation: probability-weighted average; variance: spread around the mean

$$ E [ X ] = \sum _ { x } x \, p ( x ) $$
> The mean is the sum of each value weighted by its probability.

$$ Var ( X ) = E [ X ^ { 2 } ] - ( E [ X ] ) ^ { 2 } $$
> The variance is the mean of the square minus the square of the mean.

Notes: Introduce the PMF before expectation.
Source: 5. Discrete random variables

## Slide 12: Linearity and Fair Die Example
- Expectation is linear: E[aX + b] = a E[X] + b for any constants a, b
- Var(aX + b) = a squared times Var(X): adding a constant does not change the spread
- Fair die: E[X] = (1 + 2 + ... + 6) / 6 = 3.5
- E[X squared] = 91/6, so variance = 91/6 - 12.25, about 2.92

$$ E [ a X + b ] = a E [ X ] + b $$
> Scaling and shifting a random variable scales and shifts its mean in the same way.

$$ Var ( a X + b ) = a ^ { 2 } Var ( X ) $$
> Scaling multiplies the variance by the square of the factor; shifting has no effect.

Notes: Worked example closes the chapter.
Source: 5. Discrete random variables
