# Teaching style: what the slides show and what the narration says

## The problem in the first versions

The narration read the slide out loud and added linking sentences. The cause was
structural: the script step only saw the slide text, so it could not say more than the
slide. Real lecturers work the other way round. The slide carries a few key points, and the
lecture is in what they **say**: the motivation, the intuition, a worked example, the
common mistake.

## What we looked at

**A recorded MIT lecture on the same topic.** MIT OCW 6.041SC (Fall 2013), Lecture 2,
*Conditioning and Bayes' Rule*, John Tsitsiklis: both the slides and the transcript are
published.

| | Words |
|---|---|
| On the lecture slides (3 PDF pages) | 434 |
| Spoken (transcript) | 7,074 |
| **Spoken words per slide word** | **≈ 16** |

What the lecturer does while a slide is shown (quotes from the transcript):

| Move | Example |
|---|---|
| Motivation / story | "Now besides silly problems, conditional probabilities show up in real and interesting situations … So here's the story." |
| Concrete numbers, worked live | "So it's 0.05 times 0.99. And the answer, in case you care, it's 0.0495." |
| Question to the audience | "Can we derive ordinary probabilities starting from the conditional ones? Yeah, we certainly can." |
| Interpretation | "This piece of the picture is a self-contained probability model." |
| Generalising after the example | "More generally, whenever you have a uniform distribution …" |

**Research on multimedia learning.** Mayer's *redundancy principle*: learners do worse when
on-screen text duplicates the narration (Mayer, Heiser & Lonn 2001). On-screen text should
be short and highlight the key point, not repeat the speech; slightly different wording beats
identical wording (Yue, Bjork & Bjork 2013).

**MOOC engagement.** Guo, Kim & Rubin (2014), 6.9 million edX viewing sessions: shorter
videos, informal explanation (talking head, Khan-style tablet drawing) are more engaging than
polished recordings of classroom lectures.

## What the pipeline does now

| Step | Before | Now |
|---|---|---|
| Slide | title + up to 6 sentence-bullets | title + 2-4 **keyword** bullets (≤ 12 words, checked and retried) + formulas |
| What the lecturer explains | not represented | **`talking_points`** per slide (3-6): why it matters, intuition, an "Example:" with the source's numbers, the common mistake, the link to the next idea. Generated from the **source document**, shown as `Say:` lines in `slides.md`, **reviewed by the lecturer** with the slide |
| Narration | rephrased bullets, ~120 words/slide | a short lecture per slide, ~220 words: question or story → intuition → example worked step by step → question to the viewer → one-sentence summary. Must not read the bullets out |
| Worked problems | statement and solution as bullets | talking points explain *why* each step of the official solution is taken |

The design principle still holds: **the narration uses only approved material.** The talking
points are approved with the slides, and the script step sees nothing else.

## Checks

| File | What it measures |
|---|---|
| `grounding.json` | For every talking point, the share of its content words found in its source (lecture notes; or problem + official solution). Below 0.7 is flagged for the lecturer |
| `alignment.json` | Coverage of bullets, equation explanations **and talking points** by the narration; plus `spoken_to_slide_word_ratio` (reference: ≈ 16 in the MIT lecture; reading the slides out loud gives ≈ 1-2) |

## Sources

- MIT OCW 6.041SC Fall 2013, Lecture 2: [transcript](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/tlutv5v0rme_transcript/), [slides](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l02/) (CC BY-NC-SA; quoted for analysis only)
- Mayer, Heiser & Lonn (2001), *Cognitive constraints on multimedia learning: when presenting more material results in less understanding*, J. Educational Psychology 93(1)
- Yue, Bjork & Bjork (2013), *Reducing verbal redundancy in multimedia learning*, J. Educational Psychology 105(2)
- Guo, Kim & Rubin (2014), *How video production affects student engagement: an empirical study of MOOC videos*, ACM Learning at Scale

## Initial result on the MIT 18.05 course (20-minute target)

Initial development runs with an LLM; to be reproduced with gpt-oss-120b.

Same three documents, same LLM, before and after this change:

| | Reading the slides (v1) | Lecture style (now) |
|---|---|---|
| Content slides | 24 | 14 (8 theory, 3 exercise, 3 solution) |
| Words per bullet on screen | 13.2 (max 25) | 7.6 (max 14) |
| Words spoken per slide | 140 | 246 |
| Spoken words per word shown | ≈ 1-2 | 7.2 (MIT lecture: ≈ 16) |
| Video length | 22.9 min | 23.4 min |
| Talking points flagged by `grounding.json` | n/a | 8 of ~70 |

The 8 flags: 4 framing sentences of the "lecturer voice" kind ("before computing, ask
yourself whether the answers should match"), and 4 solution steps of Problem 3 whose numbers
the model re-derived because the official probability tree is a **figure that the parser
dropped**. The numbers are correct, but they are not in the source, which is exactly the
case a lecturer must check.

Excerpt of the narration (Bayes' theorem slide, 4 bullets + 2 formulas on screen):

> We've computed P of A given B many times. But what if we know P of A given B and need P of B
> given A? Bayes' theorem inverts conditional probabilities … Why bother? Because the two
> conditionals can be very different, and confusing them is the classic mistake. Toss a coin
> five times …
