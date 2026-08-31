# Selective ticket routing

In August 2026, Astana Hub published a technology task on behalf of **TechDrive LLC**, an Almaty company: replace the manual sorting of incoming Service Desk tickets with an AI model that classifies and routes them automatically. The brief asked for routing accuracy above 95%, a confidence gate at 85% with manual review below it, and, separately, analytics that would be 100% reliable.

This repository is the answer to that brief, and the working code behind it.

[**The proposal**](PROPOSAL.md) is the response as it would have been submitted: architecture, phasing, acceptance criteria, risks, commercial terms, and the questions the brief left unanswered.

[**The report**](reports/REPORT.md) is what happened when the central mechanism of that proposal was actually built and measured, including the two findings it forced me to retract.

[**The interactive version**](web/index.html) lets you set the routing precision yourself and watch what it costs.

---

## The question the brief turns on

Automating ticket routing is not one number. It is two, and they trade against each other.

- **coverage**: the share of tickets routed without a human
- **precision**: the share of routed tickets sent to the right team

Demand higher precision and fewer tickets qualify. So "we want 95% accuracy" is not a specification until someone says what coverage that leaves, and nobody can say that before measuring the client's own data.

The brief also asks for something that cannot exist. A confidence gate is usually described as the safeguard on data quality: uncertain tickets go to a human, so the tags stay clean. But the human path is the least accurate path in the system, and it is the one the brief itself identifies as the source of bad tags. Measured here, the best achievable analytics quality is 95.2%, not 100%, and past the optimum **raising precision makes the analytics worse**, because every withheld ticket is handed to a worse process.

## What was measured

The threshold-setting mechanism was implemented end to end on a public corpus chosen for having the same long-tailed category shape as a support taxonomy, then stress-tested.

**Tuning a threshold on held-out data misses its own target in 67% of trials.** Risk control misses it in none, at a cost of 4 to 9 points of coverage. That failure is invisible on any single run, and a single run is what a demo shows.

**Only one category in 53 can carry its own guarantee.** A global threshold reports one number over a mixture; split per category, the long tail has nowhere near enough calibration data. Roughly 300 labelled examples per category are needed before a per-team promise can be made at all.

**One kind of drift is safe and one is invisible.** When the category mix moves, coverage falls and the guarantee holds: the system pays in automation rather than in mistakes. When the taxonomy is redefined, coverage does not move by a tenth of a point while the error rate triples. Nothing inside the system detects the second kind, which is why capturing every manual re-route is a requirement of the design rather than a nicety.

## Quick start

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('reuters')"

python run_all.py      # regenerates every number in the report
pytest tests/ -q       # 12 tests
```

`run_all.py` takes a few minutes, most of it in the repeated-trials section. Console output is kept in `reports/run_all.log`, so every figure in the report can be traced to the run that produced it.

For the interactive page:

```bash
python export_web_data.py   # curves on a threshold grid, from the same calibration path
python build_web.py         # inlines them into web/index.html
```

## Layout

| Path | Contents |
|---|---|
| `PROPOSAL.md` | The response to the TechDrive brief |
| `reports/REPORT.md` | Measurements, the decisions made by measurement, and the limits |
| `src/data.py` | Corpus loading, deduplication, random and temporal splits |
| `src/encoder.py` | Encoder interface and a local TF-IDF plus SVD implementation |
| `src/classifier.py` | Retrieval classifier returning prediction, confidence and supporting evidence |
| `src/conformal.py` | Loss definition, two concentration bounds, three selection procedures, per-category certification |
| `src/drift.py` | Two distribution shift modes: class mix, and taxonomy redefinition |
| `tests/` | Tests targeting the claims the report makes |
| `run_all.py` | Single entry point reproducing everything |
| `web/` | The interactive page and its build |

## Read the limits before the results

The report has a limits section and it is not boilerplate. The encoder here is TF-IDF, not the multilingual sentence model that belongs in production. The corpus is newswire, which is cleaner and easier than real support tickets. Two findings in an earlier draft turned out to be artifacts of bugs the test suite later caught, and one of them had already been recommended for the proposal.

Those are in the report because a measurement you cannot check is not a measurement.

## References

Angelopoulos and Bates, *Learn then Test* (arXiv:2110.01052) and *A Gentle Introduction to Conformal Prediction* (arXiv:2107.07511). Maurer and Pontil, *Empirical Bernstein Bounds* (COLT 2009). NLMK IT's published account of the same problem in Russian-language IT support, which supplies the only real-world comparison figures used here. Full list in the report.

---

Thomas Hotton, August 2026.
