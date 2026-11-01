# Introduction to Probability

These lecture notes give a first introduction to probability for students in science and engineering. They cover sample spaces and events, the axioms of probability, conditional probability and independence, Bayes' theorem, and discrete random variables with their expectation and variance. Each chapter ends with a short worked example.

## 1. Sample spaces and events

A random experiment is a procedure whose outcome cannot be predicted with certainty, such as tossing a coin or measuring the lifetime of a light bulb. The sample space, written S, is the set of all possible outcomes of the experiment. For one roll of a six-sided die, S = {1, 2, 3, 4, 5, 6}.

An event is a subset of the sample space. The event "the roll is even" is A = {2, 4, 6}. We say that an event occurs when the outcome of the experiment belongs to it. The empty set is the impossible event, and S itself is the certain event.

Events are combined with set operations. The union of A and B is the event that A or B occurs. The intersection of A and B is the event that both occur. The complement of A is the event that A does not occur. Two events are mutually exclusive, or disjoint, when they cannot occur together, which means that their intersection is empty.

Worked example. Roll a die once. Let A be "even" and B be "greater than 3". Then the union of A and B is {2, 4, 5, 6} and the intersection of A and B is {4, 6}.

## 2. Axioms of probability

A probability measure assigns to every event A a number P(A). Kolmogorov's three axioms state that probabilities are never negative, that the probability of the whole sample space is one, and that the probability of a union of mutually exclusive events is the sum of their probabilities.

$$ P(A) \geq 0, \quad P(S) = 1 $$

$$ P(A \cup B) = P(A) + P(B) \text{ if } A \cap B = \emptyset $$

Several rules follow directly from the axioms. The probability of the complement of A is one minus the probability of A. The probability of the impossible event is zero. For any two events, not necessarily disjoint, the addition rule subtracts the intersection, which would otherwise be counted twice.

$$ P(A \cup B) = P(A) + P(B) - P(A \cap B) $$

When all outcomes of a finite sample space are equally likely, the probability of an event is the number of outcomes in the event divided by the total number of outcomes. For a fair die, the probability of an even roll is 3/6 = 1/2.

## 3. Conditional probability and independence

Conditional probability describes how the probability of an event changes when we learn that another event has occurred. The probability of A given B is defined when P(B) is greater than zero.

$$ P(A \mid B) = \frac{P(A \cap B)}{P(B)} $$

Rearranging the definition gives the multiplication rule: the probability that both A and B occur equals P(A given B) times P(B). The law of total probability splits a probability over a partition of the sample space into disjoint cases B1, ..., Bn.

$$ P(A) = \sum_{i=1}^{n} P(A \mid B_i) P(B_i) $$

Two events are independent when knowing that one occurred does not change the probability of the other. Equivalently, the probability of their intersection is the product of their probabilities. Independence is not the same as being mutually exclusive: two disjoint events with positive probabilities are always dependent.

Worked example. Draw two cards from a deck without replacement. The probability that both are aces is 4/52 times 3/51, which is about 0.0045. The second factor is a conditional probability, because the first ace has been removed.

## 4. Bayes' theorem

Bayes' theorem reverses a conditional probability. It expresses P(B given A) using P(A given B), which is often easier to know.

$$ P(B \mid A) = \frac{P(A \mid B) P(B)}{P(A)} $$

In this formula P(B) is called the prior probability and P(B given A) the posterior probability. The denominator P(A) is usually computed with the law of total probability.

Worked example. A disease affects 1 percent of a population. A test detects it in 99 percent of sick people and gives a false positive in 5 percent of healthy people. If a person tests positive, the probability that they are sick is 0.99 times 0.01 divided by (0.99 times 0.01 plus 0.05 times 0.99), which is only about 0.17. The prior is so small that most positive results are false positives.

## 5. Discrete random variables

A random variable is a function that assigns a number to each outcome of an experiment. It is discrete when it takes a finite or countable number of values. Its probability mass function p(x) gives the probability that the variable equals x; these probabilities are non-negative and add up to one.

The expectation, or mean, is the probability-weighted average of the values. The variance measures how far the values spread around the mean.

$$ E[X] = \sum_x x \, p(x) $$

$$ \operatorname{Var}(X) = E[X^2] - (E[X])^2 $$

Expectation is linear: the expectation of aX + b is a times E[X] plus b, for any constants a and b. The variance of aX + b is a squared times the variance of X, so adding a constant does not change the spread.

Worked example. For a fair die, E[X] = (1 + 2 + 3 + 4 + 5 + 6) / 6 = 3.5, and E[X squared] = 91/6, so the variance is 91/6 - 12.25, which is about 2.92.
