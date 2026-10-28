# Verified source notes

Accessed October 22, 2026: https://physionet.org/content/mcphases/1.0.0/

- mcPHASES v1.0.0 is restricted to registered users who sign its data-use agreement. The user confirms that access is still needed.
- 42 participants consented to data release from the 2022 interval; 20 returned in 2024.
- Recruitment through Greater Toronto Area women's-health advocacy groups; eligibility excluded recent hormonal contraception and diabetes. This limits generalization.
- 23 tables: demographics, self-report/hormones, glucose, and 20 Fitbit-derived tables.
- Fitbit Sense, Mira hormone measurements, Dexcom G6 in interval 1, and diary reports.
- Common linkage: `id`, `day_in_study`. Sleep has extra start/end day fields.
- Second-round observations resume around day 905; diaries were optional in that round.
- The published data preserve missingness and were not additionally imputed or cleaned.

Not yet verified: download size, exact file paths, label encoding, full column schema, pain-class distribution, missingness rates, subgroup sample sizes, and usable forecast rows. The source page does not expose the restricted files to this session.

Dataset citation: Lin, B., Li, J. Y., Kalani, K., Truong, K., & Mariakakis, A. (2025). mcPHASES: A Dataset of Physiological, Hormonal, and Self-reported Events and Symptoms for Menstrual Health Tracking with Wearables (version 1.0.0). PhysioNet. https://doi.org/10.13026/zx6a-2c81

## Local verification — October 24, 2026

The user supplied the authorized download in the sibling mcPHASES v1.0.0 directory. Files are read in place. The earlier access blocker is resolved.

The measured download has 23 CSVs, 3,676,157,365 bytes across all files, and 110,135,462 CSV records. The diary contains 5,659 participant-days and 3,327 observed cramp responses: 3,320 in 2022 and only 7 in 2024. The primary analysis therefore uses 2022. Exact response strings and actual column schemas are now verified; processing rules and selected source hashes are saved in the real run's cleaning audit.

An important documentation mismatch: income is mentioned in the README's demographic description but is absent from the actual `subject-info.csv` columns. It cannot support an economic subgroup audit. The README also describes some variables as approximations; do not treat it as proof of clinical measurement validity or prospective availability.

Current results and limitations replace the access-pending status in earlier records. See `reports/midpoint_checkpoint.md` and `reports/initial_results.json`. The original proposal and the October 22 deck are historical artifacts, not claims about current completion.
