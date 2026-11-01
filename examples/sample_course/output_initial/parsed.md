## Vector Spaces: A Short Introduction

These notes introduce vector spaces for a first course in linear algebra. They cover vectors in R^n, the vector space axioms, subspaces, span, linear independence and bases. A short exercise with its solution closes the section.

## 1. Vectors in R^n

A vector in R^n is an ordered list of n real numbers, written u = (u1, ..., un). Two vectors are added component by component, and a vector is multiplied by a real number (a scalar) by multiplying every component.

$$\mathbf u \, + \, \mathbf v \, = \, ( \mathbf u { 1 } \, + \, \mathbf v { 1 } \, , \ \dots , \ \mathbf u { n } \, + \, \mathbf v { n } )$$

$$a ( u ) = ( a ( u 1 , \dots , a ( u n ) ) \quad ( 2 )$$

The zero vector has every component equal to zero. Geometrically, vectors in R^2 and R^3 can be drawn as arrows from the origin.

## 2. Definition of a vector space

A vector space over the real numbers is a set V with an addition and a scalar multiplication that satisfy a list of axioms. Addition must be commutative and associative, there must be a zero vector, and every vector must have an additive inverse. Scalar multiplication must distribute over vector addition and over scalar addition.

$$a ( u + v ) \, = \, a \, u \, + \, a \, v \quad ( 3 )$$

Examples of vector spaces are R^n, the set of all polynomials of degree at most n, and the set of all m by n matrices. The axioms matter because every theorem proved from them holds in all of these examples at once.

## 3. Subspaces

A subset W of a vector space V is a subspace if it is itself a vector space with the same operations. In practice it is enough to check three conditions: W contains the zero vector, W is closed under addition, and W is closed under scalar multiplication.

For example, the line through the origin in R^2 defined by y = 2x is a subspace. The line y = 2x + 1 is not a subspace, because it does not contain the zero vector.

## 4. Linear combinations and span

A linear combination of vectors v1, ..., vk is any vector of the form below, where the coefficients are scalars.

$$\ a 1 \ v 1 \ + \ a 2 \ v 2 \ + \ \dots \ + \ a k \ v k \quad ( 4 )$$

The span of a set of vectors is the set of all their linear combinations. The span is always a subspace. In R^3, the span of two vectors that are not multiples of each other is a plane through the origin.

## 5. Linear independence and basis

Vectors v1, ..., vk are linearly independent if the only way to write the zero vector as a linear combination of them is with all coefficients equal to zero. Otherwise they are linearly dependent, and at least one of them is a combination of the others.

A basis of V is a linearly independent set that spans V. Every basis of the same vector space has the same number of elements, called the dimension. The standard basis of R^n has n vectors, so the dimension of R^n is n.

## 6. Exercise and solution

Exercise. Are the vectors (1, 2) and (3, 6) linearly independent in R^2? Solution. The second vector is three times the first, so 3(1, 2) - (3, 6) = (0, 0) is a combination equal to zero with coefficients that are not all zero. The vectors are therefore linearly

dependent, and they span only a line, not the whole plane.