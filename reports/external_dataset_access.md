# External dataset access

Checked October 29, 2026. These are candidate sources, not completed external validations.

## PhysioPain v4 — public download

- Dataset: https://data.mendeley.com/datasets/mf2cgph9cy/4
- Official Download All endpoint: https://data.mendeley.com/public-api/zip/mf2cgph9cy/download/4
- DOI: 10.17632/mf2cgph9cy.4
- License: CC BY 4.0, as displayed by Mendeley.
- Expected archive size: 1,249,961,678 bytes.
- Publisher-provided SHA-256: `ed87a1add1466f031b235e71883f43a939f329ba711323ba800aee215cfc7d9c`.
- Local destination: `data/raw/external/physiopain-v4/mf2cgph9cy-4.zip`.

Download completed October 29, 2026. The exact byte size and publisher-provided SHA-256 matched, and every ZIP entry passed its CRC check. The archive contains 1,011 entries and approximately 5.24 GB uncompressed. It remains compressed; `source_metadata.json`, `verification.json`, and `archive_inventory.json` are saved beside it. All of these raw-data files are excluded from Git.

To download manually, open the dataset page, choose **Download All**, and save the archive in the local destination folder. Use the Mendeley download endpoint rather than the unsigned S3 URL returned in its archive metadata: the unsigned URL returned HTTP 403 during this check.

Study methods: https://pmc.ncbi.nlm.nih.gov/articles/PMC12410463/

These are approximately 20-minute physiological recordings, not consecutive daily observations. They support a separate pain-detection experiment, not direct validation of next-day menstrual-pain forecasting. The dataset includes several pain types; total participant count must not be reported as the menstrual-pain sample size. Verify the actual menstrual-pain participant and label counts from the files before analysis; the published pain-category/severity counts contain inconsistencies.

## U.S. Oura menstrual-cycle study — inquire about access first

- Study: https://doi.org/10.1177/07487304241265018
- Author manuscript: https://pmc.ncbi.nlm.nih.gov/articles/PMC11416332/
- Corresponding author: Fiona C. Baker, `Fiona.baker@sri.com` (listed in the published paper).
- No public participant-data download or guaranteed data-access policy was located. Ask whether sharing is possible; access is not established.

Request individual daily pain ratings, the exact wording of the pain question, linked daily wearable records, anonymized participant IDs, consistent dates/relative day indices, a data dictionary, and reuse terms. Confirm that the pain item measures menstrual pain, not undifferentiated pain. Request counts of moderate-or-higher pain days and participants with such days. The cohort was selected for generally good health and low menstrual symptom burden, so adequate positive outcomes are not established.

The 2022 Oura paper (https://pmc.ncbi.nlm.nih.gov/articles/PMC9005074/) describes 26 participants reused in the 2024 study. Do not treat those papers as independent cohorts.

## Japanese menstrual-pain wearable pilot — author request

- Study and data-availability statement: https://link.springer.com/article/10.1186/s13104-025-07098-2
- Corresponding author: Hideyuki Hirayama, `hideyuki.hirayama.r8@dc.tohoku.ac.jp`.
- The paper states that the analyzed datasets are available from the corresponding author upon request. No public raw-data download was identified.

Ask for timestamped pain-intensity/location logs, participant IDs, wearable signals, and the full recording period including premenstrual days if available. Five participants and 60 pain-change reports are too small to establish broad generalizability. Reports of pain changes are not a complete standardized daily target.

## FEMFIT — author request

- Study: https://mhealth.jmir.org/2024/1/e50135
- Corresponding author: Anna-Lena Lang, `annalena.lang.26@gmail.com`.
- The paper states that datasets are available from the corresponding author on reasonable request.

First ask whether an individual daily menstrual-cramp/pain severity item exists. The published daily PMS questionnaire lists other symptoms, including joint pain and headache, and does not establish our required menstrual-pain target. Public supplementary questionnaires are study instruments, not participant datasets. Only proceed with a data request for forecasting if the required target is actually available.

## Suggested access-request email

Subject: Request for de-identified daily pain and wearable data for student research

Dear Dr. [Surname],

I am working on a student machine-learning project predicting next-day moderate-or-higher menstrual pain using prior-day symptoms and wearable measurements. We currently use mcPHASES and are looking for a separate cohort for external evaluation.

Would it be possible to access de-identified participant-level records from your study for this purpose? We would need individual pain severity ratings with the exact questionnaire wording, linked wearable measurements, anonymous participant identifiers, and consistent dates or relative day indices that preserve consecutive-day alignment. A data dictionary and recording/time-zone conventions would also be helpful.

Could you confirm whether the pain item specifically measures menstrual pain, the number of participants and moderate-or-higher pain days available, and whether your cohort was independently recruited without reuse of mcPHASES participants or records? Please also let us know the access requirements, permitted research uses, and any data-use agreement or institutional approvals required.

Thank you for considering the request.

[Name, institution/course, supervisor if applicable]

No request has been sent. Availability upon request does not guarantee approval. Keep received participant records under `data/`, which this repository ignores. Never commit participant-level records or credentials. Before external evaluation, predefine the outcome mapping and compatible predictors, confirm prior-day availability, and freeze the relevant trained model/preprocessing. A model newly trained for a different task is a separate experiment.

## MPIS — downloaded November 1, 2026

- Source: https://zenodo.org/records/21538147
- DOI: 10.5281/zenodo.21538147
- Zenodo API reports open access and CC BY 4.0.
- All eight published files downloaded into `data/raw/external/mpis-21538147/` (2,664,906 bytes total). Every file's size and published MD5 checksum were verified; local SHA-256 hashes are also saved.
- `zenodo_metadata.json` preserves the source metadata. `download_verification.json` records the download checks.

Files downloaded:

1. `cleaned_studyu_data.csv` — English daily trial data, including imputations.
2. `cleaned_studyu_data_de.csv` — German daily trial data; not an independent cohort.
3. `final_upsurvey_data_labeled_mpisapp.csv` — baseline survey.
4. `variable_lookup.csv` — baseline codebook.
5. `study_flow_validation.csv` — participant flow and phase checks.
6. `raw_ai_responses_medgemma-27b-it.json` — model-generated extraction responses/prompts.
7. `raw_ai_responses_mistral-large-3-675b-instruct-2512.json` — model-generated extraction responses/prompts.
8. `parsed_ai_results_standardized_mistral-large-3-675b-instruct-2512.csv` — parsed model-generated outputs.

The observed-only audit and analysis are completed in `reports/mpis_analysis.md`. Only 304 of 2,160 daily rows are observed, from 19 participants; all imputed outcomes and prior-day inputs are excluded. The primary control-phase prediction cohort contains 105 adjacent-day pairs from 14 people. Do not treat model-extracted labels as independently observed outcomes. The source metadata contains inconsistent publication/creation dates and a placeholder trial-registry link; author confirmation remains necessary before describing it as a validated external cohort.

## KI EndoLIST — sign-in and project-specific agreement required

- Source: https://physionet.org/content/ki-endolist/1.0.0/
- Access page: https://physionet.org/sign-dua/ki-endolist/1.0.0/
- PhysioNet states that access requires a registered user who signs this project's data-use agreement. The available browser session was not signed in when checked November 1, 2026; no participant files were downloaded.

Use your existing PhysioNet account to log in, review and accept the EndoLIST agreement yourself, then return to the dataset's **Files** section and use the download option it provides. Access to mcPHASES does not establish acceptance of this project's agreement. Save the authorized archive or files under `data/raw/external/ki-endolist-1.0.0/`. Do not send passwords or authentication tokens in chat.

The public description lists onboarding information, longitudinal per-user files, data dictionaries, symptom mappings, and `gettingStarted.R`. Exact downloadable filenames and archive size are not visible before access; they have not been guessed. This dataset has no listed wearable recordings and uses personalized symptom scales.
