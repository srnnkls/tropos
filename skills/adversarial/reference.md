# Adversarial Techniques — Reference

Sources for the techniques cited in [SKILL.md](SKILL.md).

---

## Round 1 — Frame Attack

**Pre-Mortem (Klein, 2007).** Imagine the project has already failed; work backward to enumerate causes. Exploits "prospective hindsight" (Mitchell, Russo, Pennington, 1989), which raises risk-identification accuracy by roughly 30%. Counters groupthink and silent dissent.
- [Klein, *Performing a Project Premortem*, HBR 2007](https://hbr.org/2007/09/performing-a-project-premortem)
- [Klein on the Premortem method](https://www.gary-klein.com/premortem)

**Inversion (Jacobi → Munger).** "Invert, always invert." Don't ask how to succeed; ask how to guarantee failure, then avoid those paths. Counters optimism bias and forward-only reasoning.
- [Inversion — Farnam Street](https://fs.blog/inversion/)

---

## Round 2 — Solution Attack

**Analysis of Competing Hypotheses (Heuer, CIA).** Generate every plausible hypothesis up front, then evaluate evidence against each by *inconsistency*, not consistency. The winner is the least-disconfirmed. Forces an evidence-vs-hypothesis grid instead of narrative.
- [CIA Tradecraft Primer (PDF)](https://www.stat.berkeley.edu/~aldous/157/Papers/Tradecraft%20Primer-apr09.pdf)
- [ACH critique — ReliaQuest](https://reliaquest.com/blog/the-devil-the-details-and-the-analysis-of-competing-hypothesis/)

**Devil's Advocacy / Red Team Analysis (Heuer & Pherson, *Structured Analytic Techniques*).** Assigned role attacks the consensus view using the strongest available counter-arguments. Empirically the most effective Structured Analytic Technique in intelligence work; meta-analyses (Schwenk) show higher-quality decisions than consensus groups.
- [Heuer & Pherson, *Structured Analytic Techniques*](https://books.google.com/books/about/Structured_Analytic_Techniques_for_Intel.html?id=Js1w15Q7X4gC)
- [Devil's Advocacy meta-analysis (Schwenk)](https://www.sciencedirect.com/science/article/abs/pii/074959789090051A)

**Steelmanning.** Construct the strongest possible version of an opposing argument before attacking. Counters strawmanning and AI sycophancy. Operationalized in tools that decompose claims and run several adversarial rounds.
- [Steelman tool](https://www.steelman.cloud/)

---

## Round 3 — Verification Attack

**Falsification (Popper, 1934).** A claim is meaningful only if you can specify what observation would refute it. Demand a *risky prediction* — an experiment designed to break the theory, not confirm it. Direct counter to confirmation bias.
- [Stanford Encyclopedia: Karl Popper](https://plato.stanford.edu/entries/popper/)
- [Falsifiability — Wikipedia](https://en.wikipedia.org/wiki/Falsifiability)

**Self-Consistency (Wang et al., 2022).** Sample N diverse reasoning paths; the convergent answer is more likely correct. +17.9% on GSM8K vs. greedy chain-of-thought. Extensions: Confidence-Improved Self-Consistency (CISC), Adaptive Self-Consistency (RASC).
- [Wang et al., *Self-Consistency Improves Chain-of-Thought Reasoning* (arXiv:2203.11171)](https://arxiv.org/abs/2203.11171)
- [Confidence-Improved Self-Consistency](https://arxiv.org/pdf/2502.06233)

---

## LLM Self-Review Pitfalls

**Verbal self-critique is weak without grounding.** Miao et al. (2023) and Kambhampati (2024) show that asking an LLM "are you sure?" barely improves accuracy; confidence scores cluster too tightly. Effective critique needs sampled paths, tool grounding, or an adversarial agent (CRITIC, Multi-Agent Debate).
- [CRITIC framework](https://openreview.net/forum?id=Sx038qxjek)
- [Multi-Agent Debate against adversarial attacks](https://arxiv.org/html/2401.05998v1)
- [Persuasion-driven adversarial influence in MAD](https://www.nature.com/articles/s41598-026-42705-7)

---

## Cognitive Biases

**Cargo Cult Science (Feynman, Caltech 1974).** Reproducing the form of a working method without its substance. The canonical "looks correct but isn't" failure mode for experimental work. Includes the Millikan electron-charge anchoring example.
- [Feynman, *Cargo Cult Science*](https://calteches.library.caltech.edu/51/2/CargoCult.htm)

**Narrative Fallacy (Taleb, *The Black Swan*).** Imposing causal stories on random or complex sequences; makes solutions feel right because they fit a story.
- [Narrative Fallacy — Farnam Street](https://fs.blog/narrative-fallacy/)

**General bias catalog.**
- [List of cognitive biases — Wikipedia](https://en.wikipedia.org/wiki/List_of_cognitive_biases)

---

## Related Methods (further reading)

**FMEA (Failure Mode and Effects Analysis).** Systematic enumeration of failure modes, severity, and detectability. Engineering analog to the pre-mortem.
- [FMEA — Wikipedia](https://en.wikipedia.org/wiki/Failure_mode_and_effects_analysis)
