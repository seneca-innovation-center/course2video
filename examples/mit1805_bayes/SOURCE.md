# Real course example: MIT 18.05, class 3

A real university course package with three separate documents, the case course2video is
built for:

| Role | File | Content |
|---|---|---|
| lecture | `lecture/mit18_05_s22_class03-prep.pdf` | Reading 3: Conditional Probability, Independence and Bayes' Theorem (12 pages) |
| exercises | `exercises/mit18_05_s22_pset02.pdf` | Problem Set 2 (6 problems; problems 1-3 are used) |
| solutions | `solutions/mit18_05_s22_pset02_sol.pdf` | Official solutions to Problem Set 2 |

**Source:** Jeremy Orloff and Jonathan Bloom, *18.05 Introduction to Probability and
Statistics*, Spring 2022. MIT OpenCourseWare,
<https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/>.

**Licence: CC BY-NC-SA 4.0** (Attribution, NonCommercial, ShareAlike). Because this differs
from the project's Apache-2.0 licence:

- the PDFs are **not committed**; `scripts/fetch_mit1805_example.sh` downloads them;
- slides, scripts and videos generated from them are derivatives and must also be shared
  under CC BY-NC-SA 4.0, with attribution, and not used commercially;
- only `course.yaml` and this file (our own text) are in the repository.

Run:

```bash
./scripts/fetch_mit1805_example.sh
course2video run examples/mit1805_bayes --out out/mit_bayes --config configs/gpt-oss-vllm.yaml
# review out/mit_bayes/slides.md, then
course2video continue out/mit_bayes --from md
```
