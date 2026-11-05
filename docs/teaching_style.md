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

## Result with gpt-oss-120b on the MIT 18.05 course (20-minute target)

gpt-oss-120b on our internal server, three documents (reading, problem set, official
solutions), slides approved without edits ([`examples/demo.md`](../examples/demo.md)):

| | Result |
|---|---|
| Content slides | 17 (11 theory, 3 exercise, 3 solution) |
| Words per bullet on screen | 5.7 (max 11) |
| Words spoken per slide | 212 |
| Spoken words per word shown | 9.1 (MIT lecture: ≈ 16; reading the slides out loud: ≈ 1-2) |
| Talking points | 79, of which 8 flagged by `grounding.json` (phrasing and correct derived numbers) |
| Video length | 23.9 min |

Excerpt of the narration (slide "Bayes' Theorem and Independence Paradox"):

> Having settled what independence means, let's explore a subtle edge case and then see how
> Bayes' theorem lets us flip conditional statements. First, consider an event that never
> happens, so its probability is zero. Plugging that into the independence condition … gives
> zero equals zero, which technically satisfies independence, although it is a vacuous case …
