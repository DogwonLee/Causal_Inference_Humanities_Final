# A Causal-Inference Pipeline for Humanities Data
### "Did the League of Nations' inaction *cause* its loss of credibility?" — *Evening Star*, 17 June 1920

**Course:** Causal Inference and AI — *Analyzing Relationships in Humanities Data*
**Textbook:** Judea Pearl & Dana Mackenzie, *The Book of Why* (2018)
**Track:** B (design-your-own), built entirely in Python — Step 3 Option B, Step 4 Options B/C, Step 6 Option A/C.

This repository carries one day's newspaper from raw OCR all the way to a causal
model and causal inference, and uses that model to do the one thing the
assignment is really about: **separate causation *asserted* by historical actors
from causation an analyst can actually *identify*.**

---

## TL;DR

A single 1920 article reports that the League of Nations council postponed
helping Persia, and the British press immediately declared the League
"discredited" and "already dead." Those are confident **rung-two** causal claims
(*inaction → death of the League*) resting on **zero rung-one evidence**. By
forcing every claim into an explicit, evidence-linked DAG, the pipeline shows the
asserted effect is **not identified**: the only backdoor path `T ← U → O` runs
through a confounder (post-WWI great-power politics) the article never measures.
Same gap as the worked eugenics example — different century, same lesson.

---

## How to run

```bash
pip install -r requirements.txt
python run_pipeline.py          # runs all six steps end to end
```
Each step is also a standalone module under `src/` (e.g. `python src/causal_model.py`).
Everything is **offline and rule-based** — no API key, fully reproducible.

## Repository layout

```
data/1920-06-17.txt        Source OCR (Evening Star, LCCN sn83045462)
src/clean_newspapers.py    Step 2  clean + segment
src/extract_ekg.py         Step 3  entities / events / causal assertions
src/build_graph.py         Step 4  networkx property graph -> CSV + GraphML
src/causal_model.py        Step 5  DAG, asserted-vs-analyst edges, backdoor finder
src/inference.py           Step 6  motif leaderboard, contradictions, verdict
src/confounding_demo.py    Step 6  quantitative backdoor demo (naive vs adjusted)
run_pipeline.py            orchestrator
notebook.ipynb             same pipeline, narrated cell by cell
outputs/                   nodes.csv, edges.csv, ekg.graphml, *_records, verdict
figures/causal_dag.png     the causal diagram (Figure 1)
```

---

# Report

## 0. Causal question

> **Did the League of Nations' *inaction* on Persia's June 1920 plea for defense
> *cause* the collapse of the League's credibility** — the British press's
> verdict that it was "discredited" and "already dead"?

The unit of analysis is one article, *"Leagues' Inaction in Persia's Plea Given
Criticism,"* with time/place metadata (`Washington, D.C., 1920-06-17`; wires from
London, Teheran, Moscow). Temporal ordering matters here: the council's decision
precedes the press verdict by a day, which is exactly what tempts a causal read.

## 1. Acquire and select (Step 1)

Source: the Library of Congress *Chronicling America* OCR of the *Evening Star*,
17 June 1920 (LCCN `sn83045462`) — 28,060 lines, 32 pages, ~865 KB. I kept the
whole issue as the corpus so the discourse-level analytics in Step 6 have
something to chew on, then **zoomed to one article** for the focused causal
model. This is Track B / Option C: a different title and date from the example,
chosen because the issue is dense with explicit causal language (37 "because,"
19 "led to," plus "owing to," "due to," "the cause of," …).

## 2. Clean and normalize (Step 2)

`clean_newspapers.py` is rule-based and **logs every transformation**
(`outputs/clean_log.txt`):

* strip `===== PAGE n =====` markers and running headers;
* repair line-end word breaks — explicit hyphens join with no space; a long
  lowercase fragment + short lowercase tail across a newline is treated as one
  broken word; **all other single newlines become spaces** so real word
  boundaries (`men / who`) are preserved rather than fused (`menwho`);
* normalize whitespace/encoding and a small map of recurrent OCR artifacts;
* segment the issue into **585 article fragments** using ALL-CAPS headline lines
  as anchors.

The segmentation is deliberately simple and its imperfection is *visible* in the
log, not hidden — 1920s OCR has no reliable article boundaries, and an honest
heuristic with a logged fragment count is more defensible than a black box.

## 3. Extract entities, events, relations (Step 3)

`extract_ekg.py` is a transparent classic-NLP pass (Step 3 **Option B**), chosen
over an LLM precisely because every record must stay auditable:

* **NER:** capitalized multi-token spans, filtered by a stoplist and typed by
  gazetteer cues (`Senator/Professor →` Person, org-cue words `→` Organization,
  a place gazetteer `→` Place).
* **Causal assertions:** a **causal-cue lexicon** (`because`, `because of`,
  `owing to`, `due to`, `the cause of`, `led to`, `resulted in`, `in order to`,
  `will produce/bring/cause`, `prevent`). Each cue carries a *direction* (is the
  text after the cue the cause or the effect?), a `relationType`
  (`causes`/`enables`/`prevents`), a `polarity`, and a confidence proxy.
* Every assertion is **reified** as a `CausalAssertion` node with `CAUSE`,
  `EFFECT`, `EVIDENCE` (the exact sentence) and `DERIVED_FROM` edges — you can
  always trace a claim back to its quote.

Result: **83 causal assertions**, 4,747 person mentions, 212 organizations, 100
places, 160 concepts. (Recall/precision are lower than an LLM would give; the
trade-off buys full transparency and reproducibility, and is the right call when
the *point* is auditing claims.)

## 4. Build the knowledge graph (Step 4)

`build_graph.py` loads the records into a **networkx** `MultiDiGraph` (Step 4
**Option B**) — a labeled, typed property graph with no external database —
and exports `nodes.csv` / `edges.csv` (**Option C**) plus `ekg.graphml`
(openable in Gephi, yEd, or Neo4j-import). Provenance is first-class: every node
ties to its `Source` via `DERIVED_FROM`; every assertion keeps its `EVIDENCE`
mention. Totals: **5,971 nodes, 6,824 edges**.

## 5. Build the causal model (Step 5)

`causal_model.py` translates the article's *asserted* causal content into a DAG
over five variables and **adds the confounder the source omits**. See
`figures/causal_dag.png` (**Figure 1**).

| Var | Meaning | Role |
|----|----------------------------------------------|------|
| **T** | League **inaction** on Persia's plea | treatment |
| **O** | League **credibility** ("is it dead?") | outcome |
| **M** | perceived failure of the "first practical test" | mediator |
| **N** | Teheran–Moscow negotiations underway | stated reason for delay |
| **U** | post-WWI great-power / imperial politics | **unobserved confounder** |

**Edges asserted in the text** (solid, blue), each with a supporting quote in the
code:

* `T → O` — Times: *"Malice was the cause of discredit being brought upon the league."*
* `T → M → O` — supporters expected action as the *"first practical test of its
  power to settle international disputes"*; failing it is *"one way of killing the league."*
* `N → T` — the council delayed *"in order to give every opportunity for success
  of the exchanges … between Teheran and Moscow."*

**Edges added by the analyst** (dashed, amber):

* `U → T` — great powers wanted to *avoid* commitments (Bonar Law in the Commons:
  the government was *"endeavoring to reduce its commitments"*), which drives
  inaction.
* `U → O` — the same imperial character is what critics invoke to delegitimize it
  (Herald: *"the men who formed it were militarists and imperialists"*).

So `U` is a **common cause** of treatment and outcome, opening a backdoor path.
`M` is correctly a **mediator** (on the `T → O` path), *not* a confounder — the
code distinguishes them, and the DAG is verified acyclic.

## 6. Do causal inference (Step 6)

`inference.py` works at rungs one and two through graph queries:

* **Causal-motif leaderboard** (`motif_leaderboard.csv`): cause-type → effect-type,
  weighted by stated confidence. Honestly, the issue's discourse is dominated by
  *commercial* causation (delivery delays "cause" sales), with the political
  motifs — *"… → discredit being brought upon the league," "… → killing the
  league"* — surfacing below the advertising noise. That itself is a finding
  about what 1920 newspaper causal language is mostly *for*.
* **Contradictions / evidence density** (`contradictions.csv`,
  `evidence_density.csv`): how much text backs each claim.
* **Backdoor analysis** (in `causal_model.py`): a hand-rolled d-separation check
  enumerates the backdoor paths between `T` and `O`. There is exactly one,
  `T ← U → O`, and the **minimal adjustment set is `{U}`**.

**The verdict, keeping the three apart:**

* *Correlation*: the article shows inaction and discredit co-occurring (one day apart).
* *Asserted causation*: named actors confidently claim inaction **caused** the
  discredit — pure rung-two language.
* *Identified effect*: **none.** Identifying `T → O` requires adjusting for `U`,
  and `U` is never measured in the source — the Herald even states `U → O`
  outright while Bonar Law supplies `U → T`. The backdoor stays open; the effect
  is not identified from this text.

**A quantitative check** (`confounding_demo.py`): since the article has no
measurements, the real effect cannot be estimated — but the backdoor criterion
can be shown as a number. Simulating 200,000 cases that obey the DAG with **no**
true `T → O` effect, the naive estimate that ignores `U` returns a spurious
**+0.49** risk difference, while the **backdoor-adjusted** estimate returns
**−0.00**, recovering the truth. The whole apparent effect is confounding by the
one variable the article never measures.

This is precisely the worked example's payoff in a new setting: a confident
historical *"because"* sitting on no rung-one evidence and no identification
strategy. **What would change the conclusion:** a measured time series of the
League's standing around datable decisions, plus a proxy for great-power
commitment (`U`), would permit a backdoor adjustment or a difference-in-
differences design around the Persia vote — the quantitative tools this course
builds toward.

---

## What to submit (mapping to the brief)

1. **Code / notebook** — `src/`, `run_pipeline.py`, `notebook.ipynb`.
2. **Knowledge-graph export** — `outputs/nodes.csv`, `outputs/edges.csv`, `outputs/ekg.graphml`.
3. **Causal diagram** — `figures/causal_dag.png`.
4. **Report** — `report.docx` (5-page formatted report; `report.pdf` is a preview copy). This README mirrors its content (Sections 0–7).

## Honest limitations

Rule-based extraction misses implicit causation and mis-segments some OCR;
`U` is a qualitative confounder, not a measured variable, so the identification
claim is argued, not estimated; and the "credibility" outcome is press rhetoric,
not a metric. These are stated so the reader knows exactly how far the analysis
reaches — which is the discipline the whole pipeline is meant to teach.

**Data source:** Library of Congress, *Chronicling America* (*Evening Star*, LCCN `sn83045462`), 17 June 1920. Public domain.
