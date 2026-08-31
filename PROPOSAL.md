# Technical Proposal

**Project:** Integration of an AI model for automatic classification and routing of Service Desk tickets

**Client:** TechDrive LLC, Almaty (BIN 210540001910)
**Client contact:** Tankaeva Zhamiliya
**Source:** Astana Hub technology task board
**Submitted by:** Thomas Hotton, AI-native operator and builder
**Contact:** thomas.hotton@gmail.com | https://thomas2143.github.io/Portfolio/
**Date:** 26 August 2026
**Version:** 3

---

## 1. Executive summary

TechDrive wants incoming Service Desk tickets classified and routed automatically, in seconds, with manual moderation below a confidence threshold of 85%.

This proposal commits to building and shipping that microservice, inside TechDrive's own repository and CI/CD pipeline, meeting every acceptance criterion and every Definition of Done item in the technical specification.

Its central argument is this: **routing precision is a dial TechDrive sets, and coverage is what the data gives back.** These are two different numbers, and the task description currently treats them as one.

The 95% routing accuracy target in the task description is achievable. It is achievable as a statistical guarantee on the subset of tickets the system routes automatically, using conformal risk control to set the confidence threshold. What cannot be known before measurement is what share of tickets that leaves automated. Set the precision requirement higher and coverage falls. Set it lower and coverage rises. TechDrive owns that trade-off, and this proposal delivers the mechanism that makes it explicit and adjustable rather than accidental.

A published comparable project gives an order of magnitude for what to expect. NLMK, working with the vendor Axenix on the same problem in Russian, trained on close to one million tickets collected over two years. At a confidence threshold of 0.8, 61% of tickets were classified automatically and 84% of those were correct. Their own contact centre operators, doing the job manually, were correct 75% of the time.

That last figure is the one that matters most, and it points at the real risk in this project. If TechDrive's first line routes at a comparable rate, then roughly a quarter of the labels in the historical archive are wrong. The technical specification proposes training on that archive. The task description states that manual tags are incorrect and distort analytics. Both describe the same data. Phase 0 of this engagement measures the actual error rate before any model is trained on it.

Three phases separate this proposal from a standard build.

- **Phase 0 measures the training data** and produces a clean reference set, a corrected taxonomy, and TechDrive's real first-line baseline.
- **Phase 2 runs the service against live traffic while writing nothing**, so the accuracy figure is proven on TechDrive's own tickets before automated routing touches anything.
- **Rollout is per category**, because a single aggregate accuracy number hides the categories where the system is not good enough.

Sixteen weeks in the full version, with a compressed eleven week option in section 11.

---

## 2. Understanding of the task and scope

### 2.1 Functional scope

On ticket creation, through either the web interface or the Telegram bot, the Service Desk backend sends the ticket text asynchronously to an AI microservice via API. The service returns a category ID and a confidence score. At confidence at or above threshold, the system writes the metadata and assigns the responsible group. Below threshold, the ticket goes to manual moderation flagged as requiring review.

### 2.2 Scope boundary, and why it is probably a compliance boundary

Acceptance criterion 5 requires that for other brands and systems outside the non-subsidised pool, the original business logic is preserved with no regression.

Kazakhstan operates a state subsidised preferential auto lending programme: 4% annual rate for domestically assembled vehicles, delivered through participating second-tier banks, with an electronic queue and IIN verification. Combined with the ticket category example given in the task description, "bank integration bug", this suggests TechDrive operates in or adjacent to that programme, and that the subsidised pool is subject to regulatory and audit constraints the non-subsidised pool is not.

**This is a hypothesis, not a finding.** It is stated here because if it is correct, criterion 5 is not a technical convenience but a compliance boundary, and it should be treated with the seriousness that implies. Question 1 in section 12 asks TechDrive to confirm or correct it.

Either way, this proposal treats the boundary as enforced rather than merely tested. A scope guard runs before any classification logic: tickets outside the agreed brand and pool set return as out of scope and no write operation occurs. Criterion 5 is then satisfied by design, with the regression suite confirming it rather than being the only thing preventing a violation.

### 2.3 Explicit exclusions, per the specification

Online learning is out of scope. Retraining happens offline on a monthly cadence. Generative AI drafting of replies to users is out of scope.

Both constraints are respected. The reference index used for classification is rebuilt on the same monthly schedule, versioned, and promoted only after the regression suite passes. There is no continuous adaptation between builds.

### 2.4 Integration contract

The specification defines the interface at the level that matters: a category ID and a confidence score returned to the Service Desk backend. That contract is honoured exactly. The internal composition of the service is a delivery decision, evaluated on measured accuracy, latency, cost and explainability.

---

## 3. Reference case and realistic targets

### 3.1 The comparable project

NLMK published a detailed account of an AI classification and routing system for IT support, built with the vendor Axenix. It is the closest public reference to this task: Russian-language tickets, an ITSM backend, manual first-line classification being replaced, a confidence threshold with a manual fallback below it.

| Measure | NLMK result |
|---|---|
| Training data | Close to 1 million tickets over 2 years |
| Confidence threshold used | 0.8 |
| Tickets classified automatically | 61% |
| Precision on those tickets | 84% |
| Effective coverage (61% x 84%) | 51.24% |
| Human contact centre baseline | 75% correct per day |
| Model selected | LaBSE, after testing GPT2, BERT and other transformers |
| Tickets usable for training as-is | 79% (short tickets under 500 characters) |
| Tickets with image attachments | 34%, and extracting data from them did not improve accuracy |
| Taxonomy shape | Half the volume in 7 services / 14 categories / 15 groups, the rest spread across 50 services / 107 categories / 83 groups, about 5300 unique combinations |
| Forward projection | Up to 80% automated, up to 84% correctly routed |

Source: NLMK IT, published on Habr, June 2024. https://habr.com/ru/companies/nlmk/articles/824126/

### 3.2 What this implies for TechDrive

**84% precision was achieved with roughly one million labelled tickets and a dedicated vendor team.** The task description targets above 95%. Unless TechDrive's ticket flow is unusually clean and its taxonomy unusually small, 95% precision at a high automation rate is unlikely to be reachable.

That is not a reason to lower ambition. It is a reason to state the target correctly.

**Precision is the constraint TechDrive sets. Coverage is the outcome.** Using conformal risk control (section 5.5), the threshold can be set so that precision on automatically routed tickets satisfies a chosen bound, per category. If TechDrive wants 95%, it can have 95%, and the measured cost will be a lower automation rate. If TechDrive wants 80% of tickets automated, precision will be whatever the data supports at that coverage. The dial is real and TechDrive controls it. What no supplier can honestly promise before Phase 1 is where both numbers land simultaneously.

**The right benchmark is TechDrive's own first line, not an abstract percentage.** At NLMK, human operators routed correctly 75% of the time. The AI at 84% was not merely acceptable, it was better than the process it replaced. TechDrive's first-line baseline is currently unmeasured. Measuring it is part of Phase 0, and it is what turns the acceptance criteria from an arbitrary number into a business case.

**The 75% figure also quantifies the data risk.** If TechDrive's first line performs comparably, around a quarter of the historical archive is mislabelled. That archive is what the technical specification proposes to train on. This is the single largest determinant of the achievable result and it is currently unknown to everyone, TechDrive included.

**The "100% reliable analytics" objective needs restating, and the reason is not the obvious one.**

The obvious objection is arithmetic: at 95% precision, one auto-routed ticket in twenty carries a wrong category into the database, so the analytics are not clean. True, but it understates the problem.

The specification presents manual moderation as the safeguard on data quality. It is the least accurate path in the system. Tickets below the threshold are not routed to perfection, they are routed to first line, which is the process the task description identifies as the source of incorrect tags in the first place. At NLMK the equivalent path was correct 75% of the time.

So a confidence gate does not produce one clean stream and one uncertain stream. It produces two imperfect streams, and the manual one is the dirtier of the two.

Measured on the harness described in section 10, taking composite analytics quality as the share of **all** tickets ending up correctly tagged:

| First line correct at | All manual | Full automation | Best achievable | Reached at |
|---|---|---|---|---|
| 75% | 75.0% | 92.2% | **95.2%** | coverage 89.0% |
| 85% | 85.0% | 92.2% | **96.3%** | coverage 88.1% |
| 95% | 95.0% | 92.2% | **98.3%** | coverage 78.3% |

Three consequences for TechDrive.

**There is an optimal operating point for data quality, and it is neither extreme.** Not full automation, not maximum precision.

**Past that point, raising precision makes the analytics worse.** Every ticket withheld from automation is handed to a path less accurate than the model was on it. Tightening the gate in pursuit of cleaner reporting produces dirtier reporting. This is the opposite of what the stated objective assumes.

**The best achievable figure is not 100%.** With first line at 75%, it is 95.2%. And the target is unverifiable in any case: confirming that a tag set is 100% correct requires a correct reference set, which is exactly what a Service Desk with unreliable tags does not have. An acceptance criterion that cannot be tested is not an acceptance criterion.

**What can be delivered at 100% is traceability.** Every ticket carries an auditable record of how its category was assigned, by which pipeline stage, on which evidence, under which index version. TechDrive does not get perfect analytics. It gets analytics with a known error bar, which is what allows a management decision to account for its own uncertainty. Correctness is delivered at the measured figure, per category.

This also sets the right target for Phase 0: measuring TechDrive's actual first-line accuracy is what fixes the row of the table above that applies, and therefore what determines the operating point worth aiming at.

---

## 4. Findings from the source documents

### 4.1 The specification and the task description disagree about the training data

The specification calls the historical archive structured and proposes training on it. The task description lists incorrect manual tags as one of three critical problems. Both refer to the same archive.

Phase 0 resolves this by measurement rather than assumption.

### 4.2 An 85% confidence score is not an 85% probability of being correct

A raw model confidence score is not a calibrated probability. Applying the specification's threshold to an uncalibrated score produces a gate whose real behaviour nobody can predict.

Worse, the obvious fix is unsound. Selective accuracy, meaning accuracy computed only over the high-confidence subset, is not guaranteed to be monotone in the threshold. Tuning a cutoff on a held-out set until the number looks right does not give a guarantee, and can give a misleading one. The correct treatment is conformal risk control, described in section 5.5.

Note also that probability calibration methods such as temperature scaling improve the agreement between predicted confidence and empirical frequency, but they do not specify when to defer or how to trade prediction against abstention. Calibration and deferral are two separate problems and both need solving.

### 4.3 Language coverage

Ticket text is presumably Russian, possibly with Kazakh content. LaBSE is the primary candidate: a 12-layer transformer covering 109 languages in a single model, and the model NLMK selected for this exact task after testing alternatives.

It is a candidate, not a conclusion. The Sentence Transformers documentation notes that LaBSE performs less well at assessing similarity between sentence pairs that are not translations of each other, which is precisely the regime this task operates in. It is benchmarked against alternatives on TechDrive's own ticket sample in Phase 0.

### 4.4 Data residency is an architectural constraint, not a footnote

Kazakh law requires that databases containing personal data of Kazakh citizens be located on the territory of Kazakhstan. This is a requirement on the physical storage location, independent of where the company is registered. It is not the same as a prohibition on cross-border transfer, which is regulated separately and under its own conditions.

If TechDrive operates in the subsidised auto lending space, ticket text will routinely contain personal data. On that basis, **the self-hosted path is the default architecture in this proposal**, not the fallback. LaBSE runs on TechDrive's own infrastructure, embeddings and the reference index never leave it, and no ticket text is transmitted to an external AI provider.

The external API path remains designed for and available if TechDrive's legal function confirms it is permissible and prefers it. The decision is taken at the end of Phase 0 with legal input, not assumed by the supplier.

### 4.5 Rare categories will not reach the target, and should not be forced to

NLMK's taxonomy had roughly half its volume concentrated in a small set of categories and the remainder spread across a long tail totalling about 5300 unique combinations. TechDrive's distribution is likely to be similarly imbalanced.

Categories with few historical examples will not clear a high precision bar. Forcing them there degrades the categories that would otherwise pass. Low volume categories stay on manual routing, which is why rollout is per category rather than all at once.

### 4.6 Attachments

At NLMK, 34% of tickets carried image attachments, and extracting data from them did not improve model accuracy.

This proposal therefore includes no OCR or image analysis pipeline. A cheap presence flag is retained as a feature, because a ticket arriving with a log file attached behaves differently from one without, but no extraction work is in scope unless Phase 1 evidence justifies it.

### 4.7 The Definition of Done implies work inside TechDrive's engineering process

Peer review, merge to main, unit and integration tests, green CI/CD, updated ADRs, regression testing of adjacent modules, deployment to production.

This is not a black box handover. It is production code inside TechDrive's chain, reviewed by TechDrive's engineers. That is accepted and planned for, and it requires repository and environment access from the start of Phase 1.

---

## 5. Proposed architecture

### 5.1 API contract

**Request** (from Service Desk backend, asynchronous, on ticket creation):

```json
{
  "ticket_id": "TD-2026-104882",
  "source": "web | telegram",
  "subject": "string",
  "body": "string",
  "brand_id": "string",
  "pool": "subsidised | non_subsidised",
  "attachments": [{"type": "image | log | document"}],
  "created_at": "2026-08-26T09:14:22Z"
}
```

**Response:**

```json
{
  "ticket_id": "TD-2026-104882",
  "decision": "auto_route | manual_moderation | out_of_scope",
  "category_id": 42,
  "assignee_group_id": "grp_bank_integrations",
  "confidence": 0.91,
  "threshold_applied": 0.88,
  "target_precision": 0.95,
  "pipeline_stage": "rules | retrieval | llm",
  "evidence": [
    {"historical_ticket_id": "TD-2025-88104", "category_id": 42, "distance": 0.11},
    {"historical_ticket_id": "TD-2025-91237", "category_id": 42, "distance": 0.14}
  ],
  "index_version": "idx-2026.09.1",
  "trace_id": "uuid",
  "latency_ms": 184
}
```

The `evidence` array is deliberately part of the contract. When a category is disputed, TechDrive can see the specific historical tickets that produced the decision. This is what turns the analytics from a number management is asked to trust into a number management can audit.

`threshold_applied` and `target_precision` are returned per ticket so that the decision rule in force at the time is recoverable from the log alone.

### 5.2 Pipeline

**Stage 0, scope guard.** Brand and pool checked against the agreed scope. Out of scope returns immediately with no write operation.

**Stage 1, normalisation.** Signature and quoted reply stripping, Telegram markup handling, language detection, attachment presence flags. Long tickets are summarised before embedding, following the NLMK finding that only short tickets were usable as-is.

**Stage 2, deterministic pre-filter.** Rules for high volume unambiguous patterns. Zero model cost, fully predictable, trivially auditable, and it absorbs a meaningful share of the flow before any model runs.

**Stage 3, retrieval classification.** The ticket is embedded with LaBSE and compared against an index of labelled historical tickets. The category comes from a distance weighted vote over nearest neighbours.

Chosen over a trained classifier for three reasons specific to this client:

1. **It is explainable.** The decision is justified by named historical tickets. A client whose stated problem is that it cannot trust its own analytics gets a system whose every decision can be inspected.
2. **It absorbs taxonomy change without retraining.** When categories are added, merged or split, the index is rebuilt on the monthly cadence. No training run, no model artefact to revalidate from scratch.
3. **It runs entirely on TechDrive's infrastructure.** LaBSE is self-hostable, which is what makes the data residency position in section 4.4 straightforward rather than negotiated.

**Stage 4, LLM adjudication, ambiguous cases only.** When the neighbour vote margin is too narrow, a call to a self-hosted instruction-tuned model with structured JSON output at temperature 0, constrained to the taxonomy enum, resolves the case. This is the expensive path and it runs on a minority of tickets by design. Whether it earns its cost is measured in Phase 1 by ablation, and if it does not, it is removed.

**Stage 5, conformal decision.** See section 5.5.

**Stage 6, write back and decision log.** Category, tags and assignee group written to the ticket. Full decision record written to the log with index version, stage, evidence, scores and thresholds.

### 5.3 Index structure, conditioned on volume

The reference index holds one vector per labelled historical ticket. LaBSE produces 768-dimensional vectors.

The structure depends on a number TechDrive has not yet provided:

| Labelled tickets in index | Structure |
|---|---|
| Up to roughly 100,000 | Precomputed in-memory matrix with exact search. No vector database. Fewer moving parts to operate and to break |
| Roughly 100,000 to 1 million | In-memory with an approximate nearest neighbour index (HNSW or IVF), still no external service |
| Above 1 million | Dedicated vector store, operated as a separate component with its own availability requirements |

The decision is made in Phase 0 once the archive size is known. It is recorded as an ADR either way. **This proposal does not commit to a structure before the volume is known**, and any proposal that does is guessing.

### 5.4 Degradation

| Failure | Behaviour |
|---|---|
| LLM adjudication unavailable | Stages 1 to 3 only. Cases that would have gone to adjudication go to manual moderation |
| Embedding service unavailable | Stage 2 only. Everything else to manual moderation |
| Microservice unavailable | Ticket is created exactly as today and enters the manual queue |

Classification never blocks ticket creation. The worst case for TechDrive is the process it runs today.

One rule is absolute: embedding calls never fall back to a different model. Vectors produced by different embedding models are not comparable, and silently substituting one returns confident nonsense rather than an error. This is an engineering decision taken from direct production experience, referenced in section 10.

### 5.5 Threshold setting by conformal risk control

This is the mechanism that makes the precision target real rather than aspirational.

The requirement TechDrive has described is a selective accuracy guarantee: the probability that a routing decision is wrong, given that the system chose to route it automatically, must stay below a chosen bound. Formally, find a threshold such that the error probability conditional on confidence exceeding that threshold is at most alpha.

Two properties make the naive approach unsafe and this one necessary:

- Selective accuracy is not guaranteed to be monotone in the threshold. Raising the cutoff does not reliably raise precision, so tuning a cutoff until the held-out number looks acceptable produces no guarantee.
- Split conformal methods provide distribution-free, finite-sample validity under exchangeability, which is what allows a threshold selected on a calibration set to carry a stated guarantee onto new tickets.

**How this is used here.** TechDrive names the precision it requires, per category if it wishes. The threshold is derived from the calibration set to satisfy that bound. Coverage is the reported outcome, not an input. The specification's 85% becomes a floor below which no category is ever auto-routed, and the conformal threshold sits at or above it.

**This mechanism has been built and measured.** Rather than propose a method on the strength of its literature, it was implemented end to end on a public corpus with the same long-tailed category shape as a support taxonomy, and stress-tested. Over 15 independent splits, threshold tuning missed the target it promised in 67% of trials while risk control missed it in none. The measured cost of the guarantee was 4 to 9 points of coverage against the tuned threshold, which is the price of the promise being true. Full report, source and tests are available; see section 10.

**Honest limits.** Conformal guarantees hold under exchangeability. A live ticket stream drifts, and measurement on the harness showed that the two ways it drifts are not equally dangerous.

**When the category mix moves**, which is what a product launch or a seasonal campaign does to a queue, the guarantee survives. Unfamiliar tickets score low and fall below the threshold, so the system pays for the drift in automation rather than in mistakes. Coverage fell from 87% to 69% under an extreme mix shift while the error rate stayed under its bound. This mode is self-correcting, and it is visible on a dashboard.

**When the taxonomy changes**, it does not. A category is split, two teams swap ownership of an issue type, a product rename makes an old label mean something else. The tickets still look familiar, the model stays confident, and the correct answer has moved underneath it. In measurement, redefining 8% of a single high-volume category pushed the error rate past its bound while coverage did not move by a tenth of a point.

**The operational consequence is specific: coverage is not a health signal.** Nothing inside the service detects the second mode. The only thing that does is ground truth coming back from production, which is why the feedback capture below is a requirement of this design rather than a refinement of it.

### 5.6 Operational properties

**Idempotency.** Key is ticket_id plus index_version. Replays are safe, which matters for an asynchronous integration with retries.

**Version pinning.** Every production decision is attributable to a specific index build. When accuracy moves, it is traceable to a specific promotion.

**Monthly rebuild, per specification section 5.** Scheduled job, versioned output, promoted only after the regression suite passes against the frozen gold set and the conformal thresholds are recalibrated. No online learning between builds.

**Feedback capture.** Every manual re-route of an auto-classified ticket is written to a feedback table alongside the original prediction. It costs the agent nothing, because re-routing is an action they already perform.

This is not a reporting convenience. Per section 5.5, it is the only mechanism in the system capable of detecting a taxonomy change, which is the drift mode that breaks the guarantee while every internal metric stays flat. The re-route rate per category is therefore the primary production health metric, and the trigger for recalibrating ahead of the monthly schedule when it moves.

---

## 6. Delivery methodology

### Phase 0, data, taxonomy and baseline (3 weeks)

- Stratified sample of closed tickets across categories, brands, channels and time periods.
- Blind double labelling of that sample by two TechDrive support experts.
- Inter-annotator agreement measured. If the two experts disagree with each other, the taxonomy is ambiguous and no model can resolve it. That finding belongs before the build, not after.
- Historical label error rate measured against the re-labelled set.
- **First-line baseline measured**, so that every later accuracy figure is compared against the process being replaced rather than an abstract target.
- Taxonomy v2: systematically confused categories merged, catch-all categories split.
- Embedding benchmark on real TechDrive ticket text, LaBSE against alternatives, including Kazakh content if present.
- Archive size established, index structure decided per section 5.3.
- Data residency position confirmed with TechDrive legal, hosting path fixed.

**Deliverables:** frozen gold set, taxonomy v2 with rationale, data quality report with measured historical error rate and first-line baseline, embedding benchmark, index and hosting ADRs.

**This phase is separately contractable.** Its output determines whether the targets are reachable and at what coverage. Both sides then decide on the full build with numbers in hand.

### Phase 1, measured baseline and calibration (3 weeks)

- Stages 0 to 4 built and evaluated against the gold set.
- Per-category confusion matrix and precision versus coverage curve.
- Conformal thresholds derived per category at TechDrive's chosen precision bound.
- Retrieval-only ablation, establishing whether the LLM adjudication stage earns its cost. If it does not, it is removed and the architecture simplifies.

**Deliverable:** baseline report giving the achievable coverage at each candidate precision bound, on TechDrive's own data. The dial, with numbers on it.

### Phase 2, shadow mode (4 weeks, live traffic, no writes)

The service runs against real production traffic, logs every prediction, and writes nothing to any ticket. Predictions are compared daily against what first line actually did.

This is where the accuracy claim is proven or corrected on real traffic, including the tickets that never appear in a historical archive: the badly written ones, the ones in the wrong language, the ones that are three questions at once. It is also where drift against the calibration set first becomes visible.

**Deliverable:** shadow mode report, per category, on live data. Go or no-go per category.

### Phase 3, progressive rollout (4 weeks)

Automated routing enabled one category at a time, starting with those whose shadow-mode precision clears the bound. Independent kill switch per category. Re-route rate monitored per category from day one.

### Phase 4, Telegram parity, analytics and handover (2 weeks)

- Verified behavioural parity between web and Telegram on a paired test set.
- Analytics views for management reporting, built on the decision log.
- Feedback loop and monthly rebuild job in production.
- ADRs, runbook and handover to the TechDrive team.

---

## 7. Proposed acceptance criteria

The specification's five criteria are binary and unmeasured. Each is preserved below and given a number. Figures marked as set in Phase 1 are deliberately open, because committing to them before measuring the data would be guesswork.

| Spec criterion | Measurable form |
|---|---|
| AC1: model intercepts ticket creation and assigns the correct category | Precision on auto-routed tickets meets the bound TechDrive selects, per category, verified on the frozen gold set and in shadow mode. Automation rate reported as the measured outcome at that bound, and required to exceed the floor agreed at end of Phase 1 |
| AC2: automatic reassignment of the responsible group by category | Category to group mapping is deterministic and covered by tests. 100% correct group assignment given a correct category |
| AC3: below-threshold tickets go to manual review with a moderation flag | 100% of below-threshold tickets carry the flag and appear in the manual queue. Zero silent drops, verified by reconciliation of created tickets against classified tickets |
| AC4: functions for both web and Telegram | Identical decisions on a paired test set of equivalent tickets submitted through both channels |
| AC5: no regression for other brands and pools | Zero write operations on out-of-scope tickets, enforced by the stage 0 scope guard and verified by the regression suite |

**What a per-category guarantee costs, measured.** The criterion above is written per category deliberately, and the harness in section 10 quantifies what that demands. Certifying each category on its own calibration data rather than relying on an aggregate requires roughly 300 labelled examples per category. Below that, a distribution-free guarantee cannot be established at a 5% error target, and the category stays on manual routing.

On the harness corpus, where the median category held single-digit calibration examples, exactly one category of 53 could carry its own guarantee. The aggregate figure looked healthy at 87% coverage and 2% error; split per category it left 52 of 53 unautomatable, and 10 of those were never even predicted by the classifier, which is a failure mode below the level a per-category guarantee can describe.

This has a direct consequence for Phase 0. The labelling exercise should be sized not by a global sample target but by how many categories TechDrive wants automated, at roughly 300 examples each. Categories that cannot reach that count are not failures of the model, they are categories that stay with first line until the archive supports the promise. It also means the correct reading of any aggregate accuracy figure, including the 95% in the task description, is that it is a statement about the ticket mixture and not about what any individual team receives.

**Business criterion proposed in addition:** precision on auto-routed tickets exceeds TechDrive's measured first-line baseline by a margin agreed at end of Phase 0. This is the criterion that answers whether the project was worth doing.

**Operational criteria:** p95 end-to-end latency within the budget agreed at Phase 1, measured from webhook receipt to write-back. Cost per classified ticket reported and tracked. Production re-route rate reported per category as the ongoing accuracy signal after go-live.

On the 100% analytics objective: what is committed is 100% traceability, meaning every ticket carries an auditable record of how its category was assigned. Correctness is committed at the measured figure, because 100% correctness is not compatible with any confidence gate, including the 85% gate the specification itself requires.

---

## 8. Definition of Done compliance

| Specification requirement | Delivery commitment |
|---|---|
| Source code passes peer review and is merged to main | Work delivered as reviewable pull requests against TechDrive's repository, sized for review, from Phase 1 onward |
| Unit and integration tests written, CI/CD green | Unit tests on normalisation, rules, scope guard, threshold logic and write-back. Integration tests against a Service Desk staging environment. Evaluation suite runs in CI against the frozen gold set, so an accuracy regression fails the build like any other test |
| Technical documentation and ADRs updated | ADRs for retrieval over trained classifier, index structure by volume, self-hosted versus external inference, the no-fallback rule on embeddings, and conformal threshold selection |
| Regression testing of adjacent modules | Regression suite covering out-of-scope brand and pool paths, and the existing manual moderation flow |
| Deployed to the target production environment | Deployment through TechDrive's existing pipeline, with per-category kill switches and the full degradation ladder in place |

---

## 9. Risks and assumptions

**Assumptions carried into this proposal.** Each is a question in section 12 or Annex A, and each is replaced by a fact before Phase 1.

- The historical archive contains enough closed tickets per category to build a reference index. Volume unknown.
- TechDrive can make two support experts available for the Phase 0 labelling exercise.
- The Service Desk product exposes an API sufficient for asynchronous classification and write-back.
- Repository, staging and production access can be granted to an external contributor within TechDrive's security policy.
- TechDrive has infrastructure capable of hosting a LaBSE inference service, or can provision it.

**Risks and mitigations.**

| Risk | Impact | Mitigation |
|---|---|---|
| Historical label error rate is high, comparable to the 25% implied by the NLMK human baseline | Achievable precision drops at any given coverage | Measured in Phase 0 before commitment. Gold set built from re-labelled data, never from raw history |
| 95% precision proves reachable only at low coverage | Business case weakens | The dial is explicit from Phase 1. TechDrive chooses the operating point with both numbers visible rather than discovering the trade-off after go-live |
| Taxonomy changes during operation break the guarantee invisibly | Precision degrades in production with no internal signal, since coverage stays flat | Per-category re-route rate is the monitored metric, not coverage. Recalibration is triggered by that rate rather than only by the calendar. Measured breaking point on the harness: 8% of one high-volume category redefined |
| Category mix shifts | Coverage falls, automation rate drops | Self-correcting: low-confidence tickets go to moderation rather than to the wrong team. Monitored, but not a correctness risk |
| Expert availability for labelling slips | Phase 0 extends, everything shifts | Sample size agreed up front against a defined time budget per expert |
| Embedding quality on Kazakh text is poor | Accuracy gap on a subset | Benchmarked in Phase 0. If insufficient, those tickets route to manual moderation by language rather than degrading silently |
| Data residency position is stricter than expected | Architecture constrained | Self-hosted is already the default path. This risk is largely retired by the design |
| Taxonomy changes during the project | Rework | Retrieval-based classification absorbs taxonomy change through an index rebuild rather than a retraining cycle. A primary reason for the architecture choice |
| Rare categories cannot reach target precision | Coverage lower than hoped | Left on manual routing. Per-category rollout means this affects coverage, not correctness |
| Class imbalance hides poor performance behind a good headline number | False confidence | All reporting is per category. No aggregate figure is used as an acceptance criterion |

---

## 10. Relevant experience

**Inbound email triage agent, built and running.** A three-tier triage system: deterministic rule pre-filter, LLM classification at temperature 0, human escalation for what the rules and the model cannot settle. Built in n8n with HubSpot integration, with verified execution logs. Structurally the same problem as this task: incoming free text, a taxonomy, a confidence boundary, and a human path below it.

https://thomas2143.github.io/Portfolio/middlecorp/index.html

**A working implementation of the mechanism proposed here.** The selective classification and threshold certification described in section 5.5, built end to end and measured on a public corpus chosen for having the same long-tailed category distribution as a support taxonomy. It includes the retrieval classifier with its evidence output, threshold certification by risk control with two concentration bounds and two multiple-testing procedures compared, the naive baseline it is measured against, and a distribution shift module implementing both drift modes.

Findings that shaped this proposal: threshold tuning breached its target in 67% of trials against 0% for risk control; a Hoeffding bound could not certify anything at the target error rates and was replaced by an empirical Bernstein bound after measurement; fixed sequence testing bought 4 to 9 points of coverage over Bonferroni at identical guarantees, though neither dominates and both are run; and the taxonomy drift result in section 5.5 that made feedback capture a requirement.

It ships with a test suite, a single reproducible entry point, an interactive interface, and a written limits section naming three things it does not do. Two findings in an earlier draft were artifacts of bugs the test suite caught, and the report says which.

**Grounded retrieval assistant with a measured evaluation harness.** A retrieval-based assistant over a vendor knowledge base, with 45 labelled evaluation cases, 0.978 behaviour accuracy, 0.000 hallucination rate and $0.0024 per passing query. The distance ceiling was calibrated off the evaluation distribution rather than guessed, with a retrieval-only ablation and a regression suite. Vectors precomputed at build time and held in memory.

This is the same measurement discipline proposed for TechDrive in Phases 0 to 2. It is also where the rule that embedding calls never fall back to a different model comes from.

Live: https://meridian-chat-avkz.vercel.app/
Case study: https://thomas2143.github.io/Portfolio/meridian/index.html

**API-level integration, not no-code.** Node and Express application performing full CRUD against the HubSpot CRM REST API v3, credentials held in environment variables. Practicum behind the Integrating With HubSpot I certification, scored 57/60.

https://github.com/thomas2143/thomas-hotton-iwh-i-practicum

**Production systems with real users.** Two deployed applications with serverless backends, server-side API key handling, token-based authentication scoped per user, relational Postgres models and webhook signature verification.

**Provider outage, handled.** On 16 August 2026 a hosted model this stack depended on was taken offline by its provider. The response was provider-agnostic abstraction, a fallback model and graceful degradation. That experience is why the degradation ladder in section 5.4 is part of this design from the start, and part of why the self-hosted path is preferred here.

**Working languages:** English and French fluent, Russian in progress. Time zone UTC+6 from Almaty.

---

## 11. Timeline and commercial structure

### Full engagement

| Phase | Duration | Milestone deliverable |
|---|---|---|
| 0. Data, taxonomy and baseline | 3 weeks | Gold set, taxonomy v2, data quality report, first-line baseline, benchmarks and ADRs |
| 1. Measured baseline and calibration | 3 weeks | Precision versus coverage curve, conformal thresholds, ablation result |
| 2. Shadow mode | 4 weeks | Live traffic accuracy report, per-category go/no-go |
| 3. Progressive rollout | 4 weeks | Automated routing live, category by category |
| 4. Telegram parity, analytics, handover | 2 weeks | Full acceptance, ADRs, runbook |

**Total: 16 weeks.**

### Compressed option

If TechDrive prefers a faster route to production, the following variant reaches go-live in 11 weeks. It trades evidence for speed, and the trade is stated rather than hidden.

| Phase | Duration | Change from full version |
|---|---|---|
| 0. Data, taxonomy and baseline | 2 weeks | Smaller labelling sample. Wider confidence interval on the measured error rate |
| 1. Measured baseline and calibration | 3 weeks | Unchanged. This phase is not compressible without losing the calibration guarantee |
| 2. Shadow mode | 2 weeks | Shorter observation window. Less exposure to weekly and monthly seasonality before go-live |
| 3. Progressive rollout | 3 weeks | Faster category cadence |
| 4. Telegram parity, analytics, handover | 1 week | Analytics views reduced to the core set |

**Total: 11 weeks.**

The recommendation is the full version. A two week shadow window can miss a monthly cycle entirely, and the whole point of shadow mode is to see the traffic that a gold set does not contain.

### Commercial

Fixed price per phase, payable at milestone acceptance.

| Phase | Effort | Amount |
|---|---|---|
| 0. Data, taxonomy and baseline | approx. 90 h | 1,600,000 KZT |
| 1. Measured baseline and calibration | approx. 110 h | 1,900,000 KZT |
| 2. Shadow mode | approx. 70 h | 1,200,000 KZT |
| 3. Progressive rollout | approx. 100 h | 1,800,000 KZT |
| 4. Telegram parity, analytics, handover | approx. 60 h | 1,000,000 KZT |
| **Total** | **approx. 430 h** | **7,500,000 KZT** |

This works out at roughly 17,400 KZT per hour, below agency rates for comparable NLP integration work and consistent with senior contract engineering in Kazakhstan. Effort figures are estimates and are not billed hourly: each phase is a fixed price against a defined deliverable.

Phase 0 can be contracted on its own. If its findings show the targets are not reachable at a coverage that justifies the investment, TechDrive stops there holding a clean labelled reference set, a corrected taxonomy, a measured first-line baseline and a documented data quality position. All four have standalone value regardless of what follows.

---

## 12. Blocking questions

Six answers are needed before a firm estimate can be given. The remainder are in Annex A.

1. **Scope.** Which brands and pools are in scope for automated routing, and which must retain existing logic under acceptance criterion 5? Is that boundary driven by regulatory or audit requirements, as section 2.2 hypothesises?
2. **Archive size.** How many closed tickets are in the historical archive, and over what period? This determines the index structure in section 5.3.
3. **Taxonomy.** How many distinct categories exist today, flat or hierarchical, and how often has it changed in the last 12 months?
4. **Service Desk system.** Which product and version, self-hosted or SaaS, and does it support outbound webhooks on ticket creation?
5. **Data residency.** May ticket text be processed by an AI service outside Kazakhstan, or must inference remain in-country? This is a question for TechDrive's legal function and it fixes the hosting path.
6. **Labelling capacity.** Which two support experts can be made available for the Phase 0 exercise, and for how many hours?

---

## Annex A: further clarifying questions

**Service Desk system**

- Which API is available for writing category, tags and assignee group back to a ticket?
- What are the current environments, and can an external contributor be granted access to each?
- What is the latency budget from ticket creation to metadata being written?

**Data**

- What is the ticket volume per day, and what does a peak period look like in numbers?
- What is the language distribution between Russian, Kazakh and any others?
- What proportion of tickets arrive via Telegram versus web, and do they differ in length or structure?
- What proportion of tickets carry attachments?

**Organisation**

- How many routing groups exist, and what is the current category to group mapping?
- Is there a defined escalation or re-routing procedure today, and is a re-route recorded as an event?
- How is the current first reaction SLA defined and measured, so improvement is reported against TechDrive's existing baseline?

**Infrastructure and security**

- What infrastructure is available for hosting an inference service, and what are its constraints?
- Does ticket text contain personal data, and what handling requirements apply?
- What is the security review process for an external contributor merging to the main branch?

**Commercial**

- Is there a budget range, and is phase-by-phase contracting acceptable?
- Who signs off on phase acceptance?

---

## Annex B: sources

1. NLMK IT, "Маршрутизация обращений: автоматизация в ИТ-поддержке с помощью ИИ и языковых моделей", Habr, June 2024. https://habr.com/ru/companies/nlmk/articles/824126/
2. Feng et al., "Language-agnostic BERT Sentence Embedding" (LaBSE). Google Research. https://research.google/blog/language-agnostic-bert-sentence-embedding/
3. Sentence Transformers, pretrained model documentation, LaBSE limitations. https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
4. Angelopoulos and Bates, "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification", section on selective classification. https://arxiv.org/abs/2107.07511
5. "Conformal Risk Control for Non-Monotonic Losses", selective classification formulation. https://arxiv.org/pdf/2602.20151
6. Republic of Kazakhstan, Law on Personal Data and their Protection No. 94-V, data localisation requirement. Cross-border transfer regulated separately.
7. Kazakhstan preferential auto lending programme, terms and participating banks, 2026.
