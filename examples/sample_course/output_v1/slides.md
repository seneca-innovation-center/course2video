# Vector Spaces: A Short Introduction
<!-- language: en -->
<!--
Edit this file to correct the slides, then run:
    course2video continue <out-dir> --from md
Format: '## Slide N: Title', then '- ' bullets, '$$ latex $$' followed by a
'> explanation' line for each equation, optional 'Notes:' and 'Source:' lines.
Delete a whole '## Slide' block to drop a slide. Slides are renumbered in order.
-->

## Slide 1: Vector Spaces: Overview
- Introduction to vector spaces for a first course in linear algebra
- Topics: vectors in R^n, vector space axioms, subspaces
- Also: span, linear independence and bases
- Closes with a short exercise and its solution

Notes: Roadmap of the notes.
Source: Vector Spaces: A Short Introduction

## Slide 2: Vectors in R^n
- A vector in R^n is an ordered list of n real numbers: u = (u1, ..., un)
- Addition is done component by component
- Scalar multiplication multiplies every component by a real number
- The zero vector has every component equal to zero
- Vectors in R^2 and R^3 can be drawn as arrows from the origin

$$ \mathbf{u} + \mathbf{v} = (u_1 + v_1, \dots, u_n + v_n) $$
> Two vectors are added by adding their corresponding components.

$$ a\mathbf{u} = (a u_1, \dots, a u_n) \quad (2) $$
> Multiplying a vector by a scalar a multiplies each of its components by a.

Notes: The source equations were typeset irregularly; shown here in cleaned form.
Source: 1. Vectors in R^n

## Slide 3: Vector Space Axioms
- A real vector space is a set V with addition and scalar multiplication satisfying axioms
- Addition is commutative and associative
- There is a zero vector; every vector has an additive inverse
- Scalar multiplication distributes over vector addition and over scalar addition

$$ a(u + v) = a\,u + a\,v \quad (3) $$
> Scaling a sum of vectors gives the same result as summing the scaled vectors.

Notes: Emphasize the distributive laws as part of the axioms.
Source: 2. Definition of a vector space

## Slide 4: Examples and Why Axioms Matter
- R^n is a vector space
- Polynomials of degree at most n form a vector space
- All m by n matrices form a vector space
- Any theorem proved from the axioms holds in all these examples at once

Notes: Stress the economy of the axiomatic approach.
Source: 2. Definition of a vector space

## Slide 5: Subspaces
- W ⊆ V is a subspace if it is a vector space with the same operations
- Check: W contains the zero vector
- Check: W is closed under addition and under scalar multiplication
- Example: the line y = 2x in R^2 is a subspace
- Non-example: y = 2x + 1 does not contain the zero vector

Notes: Three-condition test is enough in practice.
Source: 3. Subspaces

## Slide 6: Linear Combinations and Span
- A linear combination of v1, ..., vk uses scalar coefficients
- The span of a set is the set of all its linear combinations
- The span is always a subspace
- In R^3, the span of two non-multiple vectors is a plane through the origin

$$ a_1 v_1 + a_2 v_2 + \dots + a_k v_k \quad (4) $$
> A general linear combination: each vector is scaled by a coefficient and the results are added.

Notes: Connect span back to subspaces.
Source: 4. Linear combinations and span

## Slide 7: Linear Independence
- v1, ..., vk are linearly independent if zero is only obtained with all coefficients zero
- Otherwise they are linearly dependent
- If dependent, at least one vector is a combination of the others

Notes: Independence means no redundancy among the vectors.
Source: 5. Linear independence and basis

## Slide 8: Basis and Dimension
- A basis of V is a linearly independent set that spans V
- Every basis of the same space has the same number of elements
- This number is called the dimension
- The standard basis of R^n has n vectors, so dim R^n = n

Notes: Dimension is well defined because all bases have equal size.
Source: 5. Linear independence and basis

## Slide 9: Exercise: Are (1, 2) and (3, 6) Independent?
- The second vector is three times the first
- So 3(1, 2) - (3, 6) = (0, 0) with coefficients not all zero
- Hence the vectors are linearly dependent
- They span only a line, not the whole plane

$$ 3(1, 2) - (3, 6) = (0, 0) $$
> A nontrivial linear combination equals the zero vector, proving linear dependence.

Notes: Let students attempt before revealing the solution.
Source: 6. Exercise and solution
