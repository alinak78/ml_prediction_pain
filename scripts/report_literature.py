"""Build the literature review and scientific figure from saved aggregate results."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pipeline import plt


def run():
    evidence = json.loads((ROOT / 'reports/literature_evidence.json').read_text())
    results = json.loads((ROOT / 'reports/literature_factor_results.json').read_text())
    metrics = {(r['dataset'], r['model']): r for r in results['metrics']}
    differences = {(r['dataset'], r['model'], r['reference'], r['metric']): r
                   for r in results['paired_differences']}
    names = {'somatic': 'Somatic symptoms', 'stress_mood': 'Stress / mood',
             'sleep': 'Sleep', 'activity': 'Activity', 'bleeding': 'Bleeding history',
             'background': 'Age / menarche age', 'physiology': 'Wearable physiology'}

    def score(dataset, model, metric='average_precision'):
        return metrics[dataset, model][metric]

    def delta(model, reference, dataset='mcphases', metric='average_precision'):
        row = differences[dataset, model, reference, metric]
        value = score(dataset, model, metric) - score(dataset, reference, metric)
        return value, row['delta_ci_low'], row['delta_ci_high']

    def delta_text(model, reference, dataset='mcphases', metric='average_precision'):
        value, low, high = delta(model, reference, dataset, metric)
        return f'{value:+.3f} [{low:+.3f}, {high:+.3f}]'

    def table(dataset, models):
        rows = ['| Model | Average precision | Balanced accuracy | Macro F1 |',
                '|---|---:|---:|---:|']
        for label, model in models:
            r = metrics[dataset, model]
            rows.append(f"| {label} | {r['average_precision']:.3f} | {r['balanced_accuracy']:.3f} | {r['macro_f1']:.3f} |")
        return '\n'.join(rows)

    figure_dir = ROOT / 'reports/figures'
    figure_dir.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6), sharey=True)
    for col, ax in enumerate(axes):
        for i, block in enumerate(names):
            model, reference = ((f'rf_history_plus_{block}', 'rf_history_severity') if col == 0
                                else ('rf_full', f'rf_full_without_{block}'))
            value, low, high = delta(model, reference)
            color = '#156c81' if low > 0 else '#6c7480'
            ax.plot([low, high], [i, i], lw=2, color=color)
            ax.scatter([value], [i], s=45, color=color, zorder=3)
        ax.axvline(0, color='#8f969e', lw=1, linestyle='--')
        ax.set_yticks(range(len(names)), list(names.values()))
        ax.set_xlim(-0.065, 0.16)
        ax.grid(axis='x', alpha=.2)
        ax.set_xlabel('Change in average precision (AP)')
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].invert_yaxis()
    axes[0].set_title('Add each block to prior-day pain severity\nReference AP = 0.526', fontsize=11)
    axes[1].set_title('Contribution within the full model\nFull model AP minus AP without that block', fontsize=11)
    fig.suptitle('Which other factors help rank next-day menstrual cramp risk?', fontsize=15, y=.98)
    fig.text(.02, .025, 'mcPHASES: 42 people, 3,320 target days, 517 positive days. Fixed participant-held-out predictions.\n'
             'Bars: 95% conditional participant-bootstrap intervals (2,000 resamples); exploratory comparisons, no multiplicity adjustment.',
             fontsize=9, color='#45515e')
    fig.tight_layout(rect=(0, .105, 1, .91))
    fig.savefig(figure_dir / 'literature_feature_blocks.png', dpi=180)
    svg_path = figure_dir / 'literature_feature_blocks.svg'
    fig.savefig(svg_path)
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
    plt.close(fig)

    sections = ['# Literature review and multifactor menstrual-pain analysis',
                'Completed November 1, 2026. All results below are measured from saved predictions; no paper’s participant records were downloaded or merged into our cohorts.',
                '## Research question',
                '**Do prior-day bodily symptoms, sleep, stress/mood, activity, bleeding history and wearable physiology improve next-day moderate-or-higher cramp prediction beyond prior-day cramp severity?**',
                'The project now tests multiple domains explicitly. Its quality rests on appropriate measurements, time ordering, participant-held-out comparisons and uncertainty—not on requiring every extra feature to improve performance. The four sources motivate hypotheses; their different populations, outcomes and time horizons do not establish next-day predictive validity for our features.',
                '## 1. Datasets and findings in the four supplied papers']
    for i, p in enumerate(evidence['papers'], 1):
        source_url = p.get('source_url') or 'https://doi.org/' + p['doi']
        paragraphs = [f"### {i}. {p['title']}",
                      f"**Dataset:** {p['dataset']}. **Sample:** {p['sample']}.",
                      f"**Design and outcome:** {p['design']}. {p['outcome']}.",
                      '**Measured attributes:** ' + '; '.join(p['measures']) + '.',
                      '**What the findings support:** ' + p['finding'],
                      '**Use in our project:** ' + p['project_use'],
                      '**Data access:** ' + p['access'],
                      f"Source: [{p['title']}]({source_url}) — supplied file `{p['file']}`, {p['source_pages']}."]
        if p.get('source_url'):
            paragraphs.append(f"Publication page: [{p.get('author_year', 'Source')}]({p['source_url']}).")
        if p.get('access_url'):
            paragraphs.append(f"Current access policy: [Raine researcher FAQs]({p['access_url']}).")
        if p.get('doi'):
            paragraphs.append(f"Primary study DOI: [{p['doi']}](https://doi.org/{p['doi']}).")
        sections.extend(paragraphs)

    sections += [
        '### Important differences between these datasets and our target',
        'The IASP file is an explainer of a study, rather than a new dataset paper. The adult thesis models recalled pain trajectories over years. EMPATHY has prospective severity diaries but concerns adolescents around menarche and has no public raw download identified here. The DES paper measures discomfort presence/frequency rather than daily severity. None supplies a verified, immediately available external dataset matching prior-day wearables plus next-day pain severity.',
        'The adult thesis recruited a pain-enriched sample and retained 157 participants with sufficient follow-up. Its reported recruitment population was predominantly White and nulliparous; attrition and recruitment affect generalization. EMPATHY was predominantly White and relatively affluent. The DES analysis has a narrow age range and a specific historical recruitment frame. Results cannot be pooled as if all papers studied the same population.',
        '## 2. Evidence-to-feature mapping',
        '| Domain | Literature motivation | What we can actually model | Interpretation |',
        '|---|---|---|---|',
        '| Bodily symptom burden | BSI-18 somatization in the thesis; CSSI-24 in EMPATHY; multisite pain in Raine | mcPHASES prior-day headache, fatigue, bloating, indigestion, breast soreness; MPIS prior-day symptom count | Diary symptom proxies, not validated somatization scores |',
        '| Sleep | PROMIS sleep disturbance in the thesis; sleep covariate in Raine | mcPHASES prior-day sleep difficulty, duration, awake minutes, efficiency, score, deep sleep, restlessness | Testable domain; the thesis did not show significant sleep contrasts |',
        '| Stress and mood | Psychological assessments in Raine, the thesis and EMPATHY | mcPHASES prior-day stress and mood swings; MPIS prior-day mood | These do not measure clinical depression, anxiety or catastrophizing |',
        '| Bleeding and timing | DES discomfort near bleeding onset; EMPATHY bleeding diaries | mcPHASES prior-day flow and observed bleeding clocks; MPIS prior-day menstruation, baseline cycle length and period duration | Only information observed before the prediction day; no retrospective phase labels |',
        '| Activity and physiology | Activity covariate in Raine; plausible contextual physiology | mcPHASES sedentary/light/moderate/vigorous activity, resting HR, HRV, respiratory rate, nightly skin temperature, Fitbit stress score | Wearables measure behavior/physiology, not experimental pain sensitivity; wearable rationale is partly exploratory |',
        '| Reproductive and clinical context | Age, BMI, menarche, parity, contraception and nonmenstrual pain in the sources | mcPHASES approximate age and menarche age; MPIS BMI, menarche age, cycle length, period duration, live births, endometriosis/adenomyosis status, nonmenstrual pain frequency | Baseline self-reports; suspected and diagnosed conditions remain distinct |',
        '| Medication | Daily analgesic use in EMPATHY and DES | MPIS prior-day tablet count | May reflect both symptom burden and treatment; not a treatment-effect estimate or a pain-label substitute |',
        '| Catastrophizing, validated mental-health scores, family history, QST | PCS, PROMIS, maternal history and lab testing in the sources | Not measured in the current model tables | Require actual new measurements; do not fabricate from proxies |',
        '## 3. Work implemented and safeguards',
        'The mcPHASES extension evaluates **29 candidate predictors**: ordinal prior-day cramp severity plus 28 features across seven non-history domains. This replaces the previous binary-history representation for the main incremental comparisons, adds five somatic symptoms, approximate age, menarche age and a conservative observed-flow-onset clock. A richer pain-history comparator prevents attributing gains merely to recovering severity information lost in a binary prior-pain flag.',
        'All changing features are joined from exact day t−1; they are not shifted across missing days. Age is approximated as 2022 minus birth year. The onset clock starts only after an observed adjacent-day transition from no/spotting flow to light-or-heavier flow; a gap or missing flow resets it. It is a bleeding-history proxy, not a hormone-derived cycle phase. The target remains the original project definition: moderate/high/very high cramp reports versus lower levels.',
        'The original 3,320 target days, 42 participants and five participant-held-out folds are preserved. The original 21-feature forest’s predictions are reproduced to 1e−12. Fixed forest settings are unchanged (200 trees, depth 6, minimum leaf 5, balanced subsampling, seed 42). Logistic regression provides a second model family. No threshold tuning or test-fold hyperparameter search was performed.',
        'For every model, missingness filtering (>60% missing), median imputation with indicators, scaling and fitting occur inside training folds. The full specification offers 29 features, but the new onset clock is observed on only 1,288/3,320 days and survives filtering in **one of five folds**; the other 28 candidates survive all five. Thus “29” describes the candidate specification, not a claim that every fold used 29 complete measurements.',
        'The analysis includes pain-only baselines, each added domain, the full model, seven leave-one-domain-out models and models without prior-day cramp severity. These are block ablations rather than causal explanations or proof that each individual symptom is useful.',
        'MPIS adds seven baseline clinical/reproductive variables to its original observed-only pairs. Missing/sentinel values are handled explicitly, including unknown live births; suspected diagnosis is not converted to confirmed disease. It retains the ≥4/10 project threshold and leave-one-participant-out folds. The previous MPIS history model is reproduced exactly. Its primary cohort remains 105 observed pairs from 14 people with 14 positive days; the stricter pre-intervention sensitivity has 77 pairs from 13 people.',
        'The studies remain separate. No current-day outcome proxies, future cycle labels, source-imputed targets, model-generated labels or participant identifiers enter the predictors. Data from the four papers have not been obtained; their published findings inform feature design. Detailed features and predictions stay in ignored private run folders.',
        '## 4. Initial results from the expanded analysis',
        '### mcPHASES: adding factors beyond pain severity',
        table('mcphases', [('Binary pain-history forest (earlier reference)', 'rf_history_binary'),
                          ('Ordinal pain-severity forest', 'rf_history_severity')] +
                         [('Pain severity + '+label.lower(), 'rf_history_plus_'+block) for block,label in names.items()] +
                         [('Full model: 29 candidate predictors', 'rf_full'),
                          ('Full model excluding cramp history', 'rf_no_pain_history'),
                          ('Original 21-feature forest', 'rf_original21')]),
        'Average precision (AP) evaluates ranking across score cutoffs; the positive prevalence is 0.156. Balanced accuracy averages sensitivity and specificity. Macro F1 averages the two class F1 scores. A better AP does not necessarily mean a better classifier at the fixed decision threshold, and these scores are not calibrated clinical probabilities.',
        '**Somatic symptoms are the strongest added block for ranking in the pain-only comparison:** AP rises from 0.526 to 0.623; paired change ' + delta_text('rf_history_plus_somatic','rf_history_severity') + '. Balanced accuracy falls from 0.804 to 0.795, and macro F1 changes from 0.754 to 0.761. This supports further investigation of the symptom block; it does not identify a causal effect or establish which individual symptom contributes.',
        '**Bleeding history also helps ranking:** paired AP change ' + delta_text('rf_history_plus_bleeding','rf_history_severity') + ', while macro F1 falls from 0.754 to 0.740. Other block-level AP intervals include zero. No general claim that sleep, mood or every wearable improves prediction is supported.',
        '**The full model improves ranking beyond severity alone:** AP 0.526 → 0.602, paired change ' + delta_text('rf_full','rf_history_severity') + '. Balanced accuracy decreases from 0.804 to 0.781; the paired interval for that change is ' + delta_text('rf_full','rf_history_severity',metric='balanced_accuracy') + '. Compared with the original 21-feature forest, AP rises from 0.555 to 0.602, but that paired change is uncertain: ' + delta_text('rf_full','rf_original21') + '.',
        '**Within the full model, evidence is less decisive for somatic symptoms:** full AP 0.602 versus 0.547 without somatic symptoms, paired change ' + delta_text('rf_full','rf_full_without_somatic') + '. The interval includes zero. Removing bleeding lowers AP to 0.585; its paired contribution is ' + delta_text('rf_full','rf_full_without_bleeding') + '. This distinction prevents overstating the pain-only block comparison as unique importance after all other factors.',
        '**There is predictive signal without previous-day cramps:** the non-history forest has AP 0.495, balanced accuracy 0.718 and macro F1 0.714. This supports a multifactor signal in this cohort, while retaining pain history gives better classification. Logistic full-model AP is 0.537 versus 0.528 for severity alone, with paired interval ' + delta_text('lr_full','lr_history_severity') + '; the forest result is not consistent across model families.',
        '![Exploratory feature-block comparisons](figures/literature_feature_blocks.png)',
        'The left panel adds each domain to prior-day pain severity. The right panel compares the full model with an otherwise identical model omitting that domain. Intervals resample participants, condition on fixed held-out predictions and have no multiple-comparison adjustment.',
        '### MPIS: clinical/reproductive factors in a second cohort',
        table('mpis_control_only', [('Pain history only', 'lr_history'),
                                  ('Pain + clinical/reproductive block', 'lr_history_clinical'),
                                  ('Pain + clinical + background', 'lr_history_background_clinical'),
                                  ('Full literature model', 'lr_full_literature'),
                                  ('Full model excluding pain history', 'lr_no_pain_history')]),
        'The clinical/reproductive block increases primary balanced accuracy from 0.720 to 0.775, but the paired 95% interval is ' + delta_text('lr_history_clinical','lr_history',dataset='mpis_control_only',metric='balanced_accuracy') + '. Its AP gain is also uncertain: ' + delta_text('lr_history_clinical','lr_history',dataset='mpis_control_only') + '. Only 14 people and 14 positive days support this comparison.',
        'In the stricter pre-intervention-only sensitivity, clinical-block balanced accuracy is 0.745 versus 0.745 for history alone, and macro F1 falls from 0.724 to 0.686. Adding every feature does not consistently help. MPIS has no wearable recordings. These are separately fitted within-MPIS models, not external evaluation of a frozen mcPHASES model; participant non-overlap and source provenance remain unverified.',
        '### Limits of the evidence',
        'All new analyses are exploratory extensions of previously inspected cohorts. Reported 95% intervals use 2,000 paired participant bootstrap resamples of fixed out-of-fold predictions; they do not refit models, correct many comparisons or account for research decisions made after seeing earlier results. Missingness, shared diary reporting, symptom correlations and prior pain influencing sleep/activity can contribute to observed associations. Repeated days are not independent people. Neither these models nor the papers establish causal drivers or treatment effects.',
        '## 5. What to say in the project',
        '> We evaluated menstrual-pain forecasting as a multifactor problem, using prior-day bodily symptoms, sleep, mood/stress, activity, bleeding history and wearable physiology, together with reproductive context. Somatic symptoms improved risk ranking beyond prior-day pain severity in mcPHASES, while gains in fixed-threshold classification and a second cohort were inconsistent. Pain history remains an important benchmark rather than the only factor considered.',
        'The project can support a careful conclusion about **which measured domains add predictive information under this evaluation**. It cannot support “all these attributes cause menstrual pain,” “psychological factors always predict pain,” or “wearables independently diagnose pain.”',
        '## 6. Measurement priorities and remaining finalization',
        'For a future prospective extension, prioritize validated somatic-symptom and sleep instruments, short validated depression/anxiety measures and PCS if relevant; capture analgesic type/dose/timestamp and hormonal-contraception status; record diagnosed versus suspected conditions, nonmenstrual pain, reproductive/family history and bleeding timing. These are new measurements, not values recoverable from the current proxies. Any claimed clinical diagnosis needs appropriate verification. Experimental QST would require a separate protocol and is not essential to finish this course project.',
        'The current literature review, feature extension and fixed-model experiments are completed. Remaining delivery tasks are final table/figure review, incorporating the new evidence into the written report and presentation, rehearsal and submission by **November 30, 2026**. Restricted-dataset applications, new participant collection and independent prospective validation are optional future research, not unfinished major course milestones. The older October presentation is preserved and has not automatically been overwritten.',
        '## 7. Reproduce and inspect',
        '```sh\n.venv/bin/python -m src.literature_analysis\n.venv/bin/python scripts/report_literature.py\n.venv/bin/python -m pytest -q\n```',
        'Prerequisites: existing authorized mcPHASES extraction and completed `src.mcphases`/`src.mpis` runs. Modeling preserves original inputs and run directories.',
        '- `reports/literature_evidence.json`: paper-by-paper dataset, measures, findings, source pages and access notes.\n- `reports/literature_factor_results.json`: aggregate metrics, bootstrap intervals, feature coverage, fold retention and hashes.\n- `reports/runs/literature_factors/`: ignored participant-level features/predictions, detailed aggregate CSVs and retained-feature audit.\n- `src/literature_analysis.py`: modeling and timing rules.\n- `tests/test_literature_analysis.py`: onset-clock causality, gap handling and clinical sentinel/diagnosis checks.\n- `reports/figures/literature_feature_blocks.png` and `.svg`: reusable scientific figure.',
    ]
    report = '\n\n'.join(sections) + '\n'
    report = re.sub(r'(?m)(^\|[^\n]*\|)\n\n(?=\|)', r'\1\n', report)
    (ROOT / 'reports/literature_review_and_feature_plan.md').write_text(report)
    print('Created reports/literature_review_and_feature_plan.md and reports/figures/literature_feature_blocks.{png,svg}')


if __name__ == '__main__':
    run()
