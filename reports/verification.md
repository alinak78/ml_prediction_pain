# Verification record — October 24, 2026

- Full raw directory inventoried: 23 CSVs, 110,135,462 CSV records and 3,676,157,365 bytes across downloaded files. Source files were read without modification.
- Verified actual diary labels, per-interval counts, sensor schemas, duplicate records and available demographic columns against the supplied README and CSVs.
- Real primary run completed: 2022, 42 participants, 3,320 observed target days, five participant-grouped folds, 21 predictors. Three full classifiers, three baselines and two feature-ablation configurations completed.
- Model code asserts disjoint training/test participant groups. Evaluation checks that each participant belongs to one test fold, each model has one prediction per target day, and OOF coverage matches the forecast table.
- Training-fold-only missingness filtering, imputation and scaling; no outcome imputation.
- 2,000 paired participant-cluster bootstrap resamples; coverage sensitivity; supported demographic subgroup audit.
- Eight targeted unit tests pass, covering exact-day lagging/participant boundaries, gaps, missing labels, missing aggregation sums, unknown labels, duplicate diary rows, training-only filtering, causal flow-history construction and count-based uncertainty metrics.
- Detailed evidence is in ignored `reports/runs/mcphases_2022/`: metrics, OOF predictions, per-fold metrics, CIs, paired differences, sensitivity, subgroup results, missingness, retained features, coefficients, forest permutation importance, plots and cleaning/run metadata.
- Source SHA256 hashes for the nine selected tables are recorded in `cleaning_audit.json`. They identify the processed inputs; comparison with the publisher's checksum list has not been performed.
- Updated presentation uses aggregate real-data results. Native tables and editable text are checked by the presentation finalizer and visual rendering workflow.

Limits: no independent final cohort, no clinical validation, no prospective ingestion latency verification, no causal interpretation, no pilot collection. Bootstrap intervals condition on fixed OOF predictions. Subgroup findings are exploratory.

## October 29 follow-up

Twelve tests pass. Four matched feature-set forests use identical participants, folds, settings and preprocessing. The all-feature forest reproduces the original labels and probabilities (absolute tolerance 1e-12). Added onset eligibility, precision/recall, average precision, false alarms per 100 days, 2,000 paired participant-cluster resamples and a descriptive coverage check. Original October 24 run files remain unchanged. Detailed evidence is in `reports/runs/wearable_followup/`; aggregate results are in `reports/followup_results.json`.
## November 1: supplementary PhysioPain analysis

- All **18 tests pass**, including E4 metadata removal, UTC channel alignment with equal ten-minute windows, empty/sparse IBI handling, no HRV calculation across missing-beat gaps, explicit cohort/label mapping, and rejection of unknown severity values.
- Actual source audit: 99 survey participants, 86 raw wristband participants, nine explicit menstrual-pain reports; two abdominal-pain reports in the processed menstrual folder are excluded.
- The 17-person current-pain cohort contains eight moderate-or-higher menstrual-pain cases, one mild menstrual-pain comparison, and eight female no-pain controls. Missing current severity is not filled except that explicit no-pain responses define the control outcome.
- Checked 17 unique held-out participants per model, zero train/test participant overlap, a strict predictor allowlist, and fixed 600-second feature windows. Independently recalculated balanced accuracy, macro F1, and average precision from saved predictions match aggregate metrics.
- Reviewed the confusion-matrix figure. Raw data, converted surveys, labels, features, and individual predictions remain ignored by Git.
- This is a separate exploratory session-level experiment. It does not validate the mcPHASES next-day forecasting model or establish independent participant identities.

## November 1: MPIS observed-only forecasting replication

- **26 tests pass**, including observed-only target/prior-day selection, exact relative-day joins with timestamp consistency, exclusion of imputed outcomes, control-phase eligibility, baseline sentinel handling, duplicate/unknown-label rejection, and complete-key selection over the release's partially populated `id` field.
- Source audit: 2,160 grid rows, 1,856 imputed rows excluded, 304 observed reports from 19 participants. Exact observed-day forecasting pairs total 178 from 16 participants. The primary control-phase cohort has 105 pairs from 14 people and 14 positive outcomes at the project threshold of ≥4/10.
- Six fixed learned model configurations and two baseline rules evaluated with leave-one-participant-out folds. Stricter A1-only and all-phase sensitivity models are fitted and evaluated separately.
- Independently checked every retained target and lag against the original observed source rows. Recomputed all pooled macro F1, balanced accuracy, AP and AUC values from predictions, checked unique coverage and participant folds, and confirmed unchanged source hashes.
- Checked participant-bootstrap weighted AP against scikit-learn on independent random resamples, including tied scores. Saved 2,000-resample conditional intervals and paired differences; no model refitting occurs inside the bootstrap.
- Primary persistence macro F1 is 0.740 and balanced accuracy 0.747 (conditional 95% interval 0.488–0.849). The added diary/baseline blocks show no consistent advantage. Equal-person weighting and the stricter pre-intervention sensitivity are included.
- No source-imputed pain, LLM-generated labels, current-day predictors, future-derived phase fields, or participant IDs enter the learned predictors. Raw and participant-level derivative records remain ignored by Git.
- MPIS has no wearable measurements. This is a within-MPIS replication with new fitted models, not external validation of the frozen mcPHASES model. Date shifting, provenance inconsistencies, small sample size and intervention carry-over remain limitations.


## November 1: literature-informed multifactor analysis

- **30 tests pass**. New tests cover past-only onset clocks, spotting, missing flow/day resets, participant boundaries, invariance to future observations and row order, clinical missing codes and distinction between suspected and diagnosed conditions.
- Reviewed all four supplied PDFs; visually checked the thesis predictor table (PDF page 47) and EMPATHY predictor table (PDF page 20). The paper review distinguishes source datasets, daily versus recalled outcomes, associations versus forecasting and significant versus null results.
- Completed **32 model configurations**: 22 mcPHASES configurations including seven leave-one-domain-out forests, plus five MPIS logistic configurations in each of two scopes. Preserved 42 people/3,320 labels/517 positives and original five participant folds in mcPHASES; preserved observed-only MPIS pairs and participant folds.
- Exact reproduction checks pass for original mcPHASES full-forest probabilities/predictions and MPIS history logistic targets/folds/probabilities/predictions (probability tolerance 1e-12).
- Independently recomputed macro F1, balanced accuracy and AP for every saved configuration. Checked unique participant-day predictions and one held-out fold per person. Rejoined all six newly used cramp/somatic ordinal fields to their original exact t−1 source records; all values and missingness agree. Source and modeling-code SHA256 hashes match the aggregate audit.
- Feature retention is saved per model/fold. The 29-feature full specification retains 28 candidates in every fold; the new observed-flow-onset clock survives the training-only missingness rule in one of five folds. No claim of complete 29-feature coverage is made.
- Saved 2,000-resample paired participant-bootstrap intervals, seven leave-one-domain-out comparisons, clinical-block sensitivity results, source hashes and a visually reviewed PNG/SVG scientific figure. These intervals condition on fixed predictions, do not refit models and have no multiple-comparison correction.
- No participant data from the four papers were obtained. No current-day/future-derived predictors, fabricated psychological-scale scores or imputed pain outcomes were added. This is a literature-informed exploratory extension on previously inspected cohorts, not confirmatory or clinical validation.
