# Vector Spaces: A Short Introduction
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

## Slide 1: Vectors in Rⁿ
- Vector u = (u₁,…,u_n)
- Componentwise addition
- Scalar multiplication of each component
- Zero vector has all components 0

$$ \mathbf u + \mathbf v = (u_1+v_1,\dots,u_n+v_n) $$
> Add two vectors by adding each corresponding component.

$$ a\,\mathbf u = (a u_1,\dots,a u_n) $$
> Multiply a vector by a scalar a by scaling every component.

Say: These operations are the foundation for all later linear‑algebra concepts.
Say: Geometrically, in R² and R³ vectors can be visualized as arrows starting at the origin.
Say: Example: (1,2,3) + (4,0,-1) = (5,2,2) and 2·(1,2,3) = (2,4,6).
Say: A common mistake is to try to add vectors of different dimensions; the dimensions must match.
Say: We will now see how these simple operations fit into the abstract definition of a vector space.
Source: 1. Vectors in R^n

## Slide 2: Definition of a Vector Space
- Set V with addition & scalar multiplication
- Axioms: commutative, associative, zero, inverses
- Distributive laws for scalar multiplication
- Examples: ℝⁿ, polynomials, matrices

$$ a(\mathbf u+\mathbf v)=a\mathbf u + a\mathbf v $$
> Scalar multiplication distributes over vector addition.

Say: The axioms guarantee that any theorem proved from them applies to all listed examples.
Say: Intuitively, the axioms say that vectors behave like arrows that can be moved and stretched consistently.
Say: Example: In the space of 2×2 matrices, adding matrices and multiplying by scalars follows the same rules as for ordinary vectors.
Say: A subtle point: the zero vector must be the same for both operations; some students forget to check this when verifying a new vector space.
Say: Next we will examine special subsets of a vector space that are themselves vector spaces.
Source: 2. Definition of a vector space

## Slide 3: Subspaces
- Subset W⊆V that is a vector space with same operations
- Three checks: contains zero, closed under addition, closed under scalar multiplication
- Line y=2x in ℝ² is a subspace
- Line y=2x+1 is not

Say: Subspaces let us focus on smaller, manageable parts of a vector space while preserving all structure.
Say: The three‑condition test is sufficient because the other axioms are inherited from V.
Say: Example: The set W={ (t,2t) | t∈ℝ } satisfies the three conditions, so it is a subspace of ℝ².
Say: Common mistake: forgetting to verify that the zero vector belongs to W; the line y=2x+1 fails this test.
Say: Understanding subspaces prepares us for concepts like span and basis.
Source: 3. Subspaces

## Slide 4: Linear Combinations and Span
- Linear combination: Σ a_i v_i
- Span = all linear combinations of a set
- Span is always a subspace
- Two non‑parallel vectors in ℝ³ span a plane

$$ a_1\mathbf v_1 + a_2\mathbf v_2 + \dots + a_k\mathbf v_k $$
> A vector built by scaling each v_i with a scalar a_i and adding the results.

Say: The span captures everything we can reach using the given vectors and scalar multiples.
Say: Intuition: think of the span as the “reach” of the vectors when you can stretch and add them.
Say: Example: Vectors (1,0,0) and (0,1,0) in ℝ³ span the xy‑plane because any (x,y,0) can be written as x·(1,0,0)+y·(0,1,0).
Say: A subtle point: the span of a single non‑zero vector is a line, not the whole space.
Say: Later we will see how choosing independent vectors from a span leads to a basis.
Source: 4. Linear combinations and span

## Slide 5: Linear Independence and Basis
- Independent ⇔ only trivial coefficients give zero
- Dependent ⇔ some vector is a combination of others
- Basis = independent set that spans V
- All bases have same size = dimension

Say: Independence tells us that no vector in the set is redundant.
Say: Intuitively, a basis is a minimal set of directions that can build every vector in the space.
Say: Example: In ℝ², {(1,0),(0,1)} is independent and spans ℝ², so it is a basis; its size 2 is the dimension.
Say: A common error is to assume any spanning set is a basis; independence must also be checked.
Say: The standard basis of ℝⁿ consists of the n vectors with a single 1 and the rest 0, confirming that dim ℝⁿ = n.
Source: 5. Linear independence and basis

## Slide 6: Exercise: Linear Dependence in ℝ²
- Vectors (1,2) and (3,6)
- Check independence
- Result: linearly dependent

Say: We test whether a non‑trivial combination gives the zero vector.
Say: Example: 3·(1,2) - (3,6) = (0,0); coefficients (3, -1) are not both zero, so the vectors are dependent.
Say: Because they are multiples of each other, they span only a line, not the whole plane.
Say: A subtle point: two vectors in ℝ² are independent precisely when they are not scalar multiples.
Say: This exercise illustrates the definitions of dependence and span from the previous slides.
Source: 6. Exercise and solution
