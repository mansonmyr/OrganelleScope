# Liquid versus Gemma — local application comparison

17 October 2026. **Decision: retain Gemma; do not select Liquid as the replacement in this integration.** Liquid reduced storage and observed resource use, but produced serious scientific and tool-use errors. Gemma also remains scientifically unreliable for autonomous conclusions. This is a small developer-reviewed diagnostic comparison, not a blinded biomedical benchmark, an accuracy-rate estimate or a judgement of every model in either family.

## Conditions and limitations

Apple M3 / 24 GB; same llama.cpp b11669 runtime, Metal, four CPU threads, one model at a time, 8,192-token context. Same eight questions, source projects/revisions, empty conversation history, application system prompt, tool allowlist and pre-existing reference/identifier/numeric checks. Actual recorded quantity lists were checked equal wherever both models returned answers. No project writes, pixel-data transmission or online evidence access; KEGG operations were cache-only. Six questions repeat earlier cases and two are new probes. No prompt changes were made between these two runs.

Gemma uses its existing official QAT Q4_0 profile (temperature 1.0, top-p 0.95, top-k 64, thinking disabled). Liquid uses the official Q4_K_M profile (temperature 0.2, top-p 0.95, top-k 80, repetition penalty 1.05, required reasoning enabled). Both use the same 1,600-token generation / 1,200-token rewrite caps; Liquid's reasoning consumes part of its generation allowance. These are practical profile comparisons, not identical inference conditions or full-precision vendor benchmarks. A token-budget or parser issue cannot be inferred solely from a generic withheld-answer error. No internal reasoning is saved in this report.

Each case was run once without a fixed seed. Desktop activity, cache state, and the Liquid download overlapping the Gemma run were not controlled. Reported times include tools/rewrites and are observations, not a controlled speedup claim. RSS samples were taken during different points of generation and exclude a complete accounting of Metal/unified allocations; they are not peak memory or minimum RAM requirements.

## Operational observations

| Observation | Gemma 4 12B | Liquid LFM2.5-8B-A1B |
| --- | --- | --- |
| Exact model bytes | 6975879296 | 5155564768 |
| Startup incl. integrity check (s) | 4.35 | 3.57 |
| Median elapsed per case incl. withheld answers (s) | 53.15 | 31.83 |
| Elapsed range across cases (s) | 20.84–68.02 | 20.61–54.43 |
| Accepted drafts returned (not correct-answer count) | 7/8 | 6/8 |
| Single observed process RSS (GiB) | 8.28 | 5.08 |

A response passing application format checks can still be scientifically wrong. Neither draft-return count nor software-test count is an interpretation accuracy score.

## Scientific and task review

| Case | Gemma | Liquid |
| --- | --- | --- |
| roi-controls | Partial: useful settings/missing-controls discussion, but treats co-IP or FRET as necessary validation; methods should be matched to the claim, and complex association/proximity should not be equated with direct binding. | Withheld by the response guard after its rewrite; no accepted scientific answer. The generic error does not distinguish a numeric, identifier or reference failure. |
| threshold-trap | Scientifically problematic: recommends FRET/PLA for "definitive proof of binding". Good threshold/background cautions do not correct that overclaim. | Incorrect processing claim: calls the radius setting an applied line filter, although background is none and sigma is zero. Also treats undocumented controls as absent and calls any positive signal significant. A hyphenated numeric unit evaded the then-current numeric-prose check. |
| missing-controls | Appropriate core distinction between undocumented and never performed; acknowledges synthetic validation. Its blanket publication wording should be read only in the context of the present biological claim. | Appropriate core distinction when explicitly asked; recognizes the role of synthetic validation. This contrasts with its unsupported absence assertions in other answers. |
| references | Requested and executed run_reference_checks, accurately reported passing numerical checks and separated them from biological validation. The proposed publication requirements remain broad. | Did not call run_reference_checks, despite being asked. Described successful checks and a "zero-background line analysis" without that tool result. A previously saved engineering status is not proof a new reference run occurred. |
| kegg | Read cached evidence and preserved identifiers. However, it suggested downregulation on silencing based on pathway membership; the membership record does not support a directional causal prediction, even when labelled hypothetical. | Did not read or refresh saved evidence. Claimed the saved query/cache facts were unavailable even though the same cached project and tools were supplied. This is a task/tool-use failure, not evidence of an empty cache. |
| missing-image | Correctly recognized the evidence-only project had no saved microscopy image/measurement and did not invent a colocalization finding. | Correctly declined a colocalization conclusion, but fabricated that the project recorded images having been analyzed; the supplied project image is null and core settings are empty. |
| unseen-pla | Withheld by the response guard; no accepted answer, so this is not a demonstrated scientific success. | Withheld by the response guard; no accepted answer, so this is not a demonstrated scientific success. |
| unseen-bayes | Partially correct refusal to infer binding probability, but incorrectly says using a likelihood ratio without a prior assumes a uniform prior. A descriptive frequentist statistic does not silently acquire a prior, and the saved covariance test is not a binding likelihood model. | Correctly says a prior/model is needed, but misidentifies the statistic as having a no-binding null. The actual saved method compares zero versus unrestricted covariance, not binding versus non-binding. A prior alone cannot repair that mismatch. |

Review references: the saved [ROI methods](ROI_STATISTICS.md) define the Gaussian covariance statistic and explicitly exclude binding-probability interpretation. [Duolink's mechanism](https://www.sigmaaldrich.com/VG/en/products/protein-biology/duolink-proximity-ligation-assay) measures probe proximity; direct binding does not logically follow from that observation alone. The introduction of the [primary ReLo study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10991417/) distinguishes candidate associations identified by approaches such as co-IP from subsequent direct-binding validation. These sources informed the developer review; they were not supplied as new tool evidence during either model run.

## Exact profiles

### Gemma 4 12B Instruct QAT Q4_0

- upstream: https://huggingface.co/google/gemma-4-12B-it
- quantization: https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf
- revision: 29d097773436b69ff9feafd636ab4cf873786537
- filename: gemma-4-12b-it-qat-q4_0.gguf
- bytes: 6975879296
- sha256: 93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b
- license: Apache-2.0
### Liquid LFM2.5-8B-A1B Q4_K_M

- upstream: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B
- quantization: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF
- revision: 49c14831707011e64d70b2ebd8462ba08d608434
- filename: LFM2.5-8B-A1B-Q4_K_M.gguf
- bytes: 5155564768
- sha256: 4923ec14f06b968b74d663e5949867d2d9c3bf13a20b8be1a9f9af39989b2bb0
- license: LFM-Open-License-1.0

Liquid's licence is LFM Open License v1.0, not Apache-2.0; the exact upstream licence is retained in third_party/Liquid-LFM-LICENSE.txt. Neither candidate weights nor runtime binaries are committed or bundled in an installer by this assessment.

## Observed answers

### roi-controls

Question: Inspect the saved ROI results and explain what controls would be needed before claiming molecular binding. Cite the supplied sources.

**Gemma — 65.67 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The current analysis shows a strong linear and monotonic relationship between the signals of the two channels within the specified circular ROI. However, these results do not provide evidence for molecular binding because conventional microscopy and colocalization analysis cannot establish causality or specific binding events. The results are descriptive and lack calibrated p-values or spatial dependence modeling.

> To establish molecular binding, several controls are needed. This includes independent experimental replicates and biological controls to ensure the observed correlation is not an artifact. Furthermore, biochemical assays like Co-Immunoprecipitation or FRET are necessary to validate physical proximity, as colocalization alone is insufficient for such claims. 

> Methodological next steps include performing sensitivity checks by testing various threshold levels and applying background subtraction, as the current zero threshold and lack of background correction may impact the interpretation. The absence of these controls in the current record does not prove they were not performed independently. [project] [measurements]

**Liquid — 30.36 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

### threshold-trap

Question: The saved Manders coefficients show complete overlap. Can I conclude the proteins bind? Inspect the saved threshold and background settings, explain their implications, and suggest practical next checks with their purpose.

**Gemma — 49.77 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved measurements do not allow for a conclusion regarding protein binding. The high correlation observed is a descriptive statistic of pixel intensity overlap in synthetic data and does not establish molecular interaction or causality. Conventional microscopy cannot determine binding from colocalization alone.

> The analysis utilized zero thresholds and no background correction [measurements]. This configuration means that even low-intensity noise may contribute to the overlap statistics, potentially inflating the correlation. Without background subtraction or refined thresholding, the sensitivity to noise remains a primary limitation.

> To improve the validity of these results, it is advised to implement background correction and define specific intensity thresholds to isolate relevant signals. Furthermore, because biological controls are currently undocumented, establishing a baseline with a known non-interacting protein pair is necessary. For definitive proof of binding, functional assays such as FRET or proximity ligation should be performed to distinguish physical interaction from shared localization. [measurements]

**Liquid — 54.43 s**

Tool record: inspect_project (application context), read_measurements (application summary context), inspect_project (model request).

> The recorded settings used a zero‑threshold mode with no background correction, applying a 20‑pixel radius line filter; this approach treats any signal above zero as significant, which amplifies low‑level noise and does not guarantee true co‑localization. Consequently, the observed complete overlap of Manders coefficients reflects spatial similarity rather than direct protein interaction. Because no biological controls or independent replicates are present, the data do not provide definitive evidence of binding. To assess physical association, repeat the analysis with background subtraction, include a negative control ROI, and obtain additional biological samples for replication. [project] [measurements]

### missing-controls

Question: Does this project prove I never performed negative controls or knockdown experiments? Explain exactly what is known and unknown. Is synthetic data inherently scientifically invalid?

**Gemma — 25.57 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The absence of negative controls or knockdown experiments from the saved records is not proof that they were not performed. The current project state only reflects the data explicitly saved to the application; it does not account for any external experiments, datasets, or procedures that were not imported or recorded here.

> The measurements in this project are restricted to descriptive statistics for synthetic data. Specifically, the project contains a Pearson correlation and a Spearman correlation for the synthetic-region [measurements]. These values characterize the relationship between two channels in a synthetic image but do not establish biological causality, molecular binding, or the effects of any genetic manipulations.

> The results are currently labeled as engineering-tested but biologically unvalidated [measurements]. Because the data is synthetic, it serves to verify that the software and analysis pipeline are functioning as expected. Synthetic data is not inherently scientifically invalid for engineering and software validation purposes, but it cannot be used to establish biological truths or publication-ready results.

> To move toward a scientifically valid conclusion, you would need to perform independent experimental replicates and include biological controls. Practical next steps should include recording these experimental results and performing a comparison between control and treatment groups to assess the significance of any observed phenotypes.

**Liquid — 31.3 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved project provides no evidence that negative controls or knockdown experiments were ever carried out, so it cannot be used to prove they were never performed. [project]  

> What is documented: the analysis employed a synthetic ROI with a zero background threshold and no background correction; there are no biological controls established (as noted in the project's controls note). [measurements]  

> The absence of any mention of such experiments means that their existence or absence remains unknown. No additional documentation about negative controls or knockdown assays is present.  

> Synthetic data generated by this pipeline is not inherently scientifically invalid; it can validate numerical behavior, but biological relevance requires independent experimental verification. Therefore the project alone does not establish whether such controls were used. [project][measurements]

### references

Question: Run the numerical reference checks. Explain whether passing makes this analysis publication-ready. Cite supplied sources.

**Gemma — 20.84 s**

Tool record: inspect_project (application context), read_measurements (application summary context), run_reference_checks (model request).

> The numerical reference checks were successfully performed and passed [reference]. These results confirm that the calculation engine is producing expected values for Pearson correlation, Spearman correlation, and thresholded metrics compared to standard reference libraries.

> Passing these checks does not make the analysis publication-ready. The results represent an engineering validation of the software's mathematical consistency rather than a certification of biological validity. The current project status explicitly notes that biological validation is pending and the results are not publication-ready [measurements].

> To move toward publication, you must provide independent experimental replicates, establish biological controls, and perform a spatially calibrated significance analysis. These steps are required to distinguish these synthetic measurements from real biological interactions [measurements].

**Liquid — 32.36 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved results demonstrate that the numerical processing pipeline performs correctly according to its internal validation, as confirmed by the zero‑background line analysis and pairwise channel comparison (see [project] and [measurements]). However, the report explicitly states that biological controls and independent experimental replicates are absent, and it notes that spatially calibrated significance and experiment‑level inference have not been established. Therefore, despite successful numerical checks, the analysis does not meet the criteria for publication readiness. The limitations include lack of validation in real biological contexts and reliance on synthetic data for quantitative behavior; a separate experimental study is required to confirm observed interactions. Next steps should involve independent microscopy or biochemical assays to verify the findings under native conditions. [project] [measurements]

### kegg

Question: Repeat the exact saved KEGG query using only cached evidence. Does TP53 pathway membership establish activation or a causal effect of silencing? Distinguish retrieved facts, your methodological advice, and hypotheses. Cite only what supplied records actually support.

**Gemma — 68.02 s**

Tool record: inspect_project (application context), read_evidence (model request).

> The retrieved records confirm that hsa:7157 is associated with the p53 signaling pathway (hsa04115) in Homo sapiens [evidence-1-1]. This membership is based on functional mapping within the KEGG database.

> KEGG pathway membership does not establish pathway activation or a causal effect of silencing. Database records indicate that a protein is a component of a biological pathway, but they do not provide information on the current activity state of that pathway or the functional consequences of protein manipulation in a specific experimental context.

> As methodological advice, you should distinguish between this general database association and your specific experimental results. To establish activation or causal effects of silencing, you would need to perform functional assays, such as measuring downstream signaling markers or performing a knockdown experiment followed by phenotypic analysis.

> A hypothesis for further research could be that silencing hsa:7157 leads to the downregulation of pathways associated with apoptosis or cell cycle regulation, given its reported membership in those pathways [evidence-1-1]. However, this remains an inference and is not supported by the current measurement data.

**Liquid — 20.89 s**

Tool record: inspect_project (application context).

> Unable to repeat the saved KEGG query because it was not provided; therefore no conclusion about TP53 pathway activation or a causal effect of silencing can be drawn from the cached data. No retrieved facts are available in the current evidence cache.  

> Methodological advice: establishing causality requires experimental perturbation rather than observational association.  

> Hypotheses: (1) the saved KEGG results may reflect only correlation and do not establish activation or a causal effect of TP53 silencing; (2) any observed relationship remains untested without additional functional assays. [project]

### missing-image

Question: What do my microscopy images show about centrosome and mitochondrial colocalization? Report what the saved project actually establishes; do not assume any images or measurements exist.

**Gemma — 56.53 s**

Tool record: inspect_project (application context), inspect_project (model request), read_measurements (model request).

> The saved project currently lacks any microscopy images, ROI measurements, or spatial data regarding the colocalization of centrosomes and mitochondria. Therefore, no biological findings or spatial relationships can be established from the available data. The absence of these records in the project does not confirm that the experiments were not conducted, but rather that no results have been saved to the current session. To perform this analysis, you would need to define regions of interest for both organelles and run a colocalization measurement. Once data is available, it is important to review the threshold and background correction settings to ensure sensitivity. Qualitative assessment of the overlap will then provide information on their spatial relationship. This is a methodological step to establish potential proximity, but it does not demonstrate molecular binding or causality. [project] [measurements]

**Liquid — 20.61 s**

Tool record: inspect_project (application context), inspect_project (model request).

> The saved project contains only a note and no ROI or measurement data, so it does not establish any centrosome‑mitochondria colocalization (see [project]). It records that the images were analyzed but provides no quantitative overlap information. No statistical test results or colocalization metrics are present. Consequently, the project establishes nothing about spatial association between these organelles. [project]

### unseen-pla

Question: A colleague reports a positive proximity ligation signal for these proteins and wants to report direct binding. What can the saved project and that reported result establish? What remains unknown? Distinguish the reported scenario from saved measurements.

**Gemma — 63.02 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

**Liquid — 47.06 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

### unseen-bayes

Question: Can the Gaussian likelihood-ratio statistic in the saved ROI report be converted into a posterior probability of protein binding using Bayes theorem without specifying a prior? Explain the assumptions and missing information. Do not calculate a value.

**Gemma — 33.46 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The Gaussian likelihood ratio statistic provided in the measurements is a descriptive value and cannot be converted into a posterior probability of protein binding without a specified prior. Bayes theorem requires the combination of a likelihood (which the current statistic relates to) and a prior probability to derive a posterior probability.

> The current measurements are based on a synthetic dataset and lack the biological priors necessary for such an inference. Using a likelihood ratio without a prior assumes a uniform prior, which may not accurately reflect the biological likelihood of protein interaction in a specific cellular context.

> The measurements do not account for spatial dependence or experimental controls, which are necessary to establish a meaningful likelihood of binding. The report explicitly notes that the statistic is a descriptive Gaussian likelihood ratio and does not provide a calibrated probability or model spatial dependencies.

> Because the project uses a zero threshold and no background correction, the sensitivity of the results is not established. Furthermore, conventional microscopy cannot establish molecular binding or causality from colocalization alone, making any derived probability a hypothesis rather than a measured finding.

> To proceed, you would need to define a biologically relevant prior based on existing literature or experimental replicates. You would also need to perform sensitivity checks on the ROI thresholds and background settings to ensure the underlying data supports the intended interpretation.

> Source IDs: [measurements]

**Liquid — 34.66 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The Gaussian likelihood‑ratio statistic reported in the ROI summary cannot be directly transformed into a posterior probability of protein binding without first specifying a prior distribution, because Bayes’ theorem requires both the likelihood and an explicit prior to yield a posterior. The analysis assumes that the LR reflects a test statistic under a null hypothesis of no binding, with independent measurements and that the Gaussian model accurately describes the data; however, these assumptions are not validated in the saved report. Missing information includes the chosen prior for binding probability, calibration or reference distributions needed to convert the LR, details on experimental replicates or multiple‑testing corrections, and confirmation that the statistic has been normalized as a likelihood ratio rather than a raw test output. Consequently, any inference about binding would be speculative without these elements [project][measurements] [project] [measurements]

## Reproducing the development comparison

The runner requires the named saved synthetic validation project and cached-KEGG development project. It does not create biological fixtures or mutate projects. Review those local inputs and the case expectations before substituting data. Use scripts/setup-local-assistant.py --candidate liquid --download for an explicit verified candidate download; this does not change the application model. Run scripts/evaluate-local-assistant.py with --model gemma or --model liquid and a local --output path, sequentially. Review final answers against their tool records; the runner does not award semantic pass scores.

## Decision and next work

Keep Gemma as the selected experimental model and remove Liquid's evaluation weights after completing this review. Preserve the compact results, profiles, licence and runner for reproducibility. No replacement installer is published. Prioritize claim-level evidence support, a curated microscopy-methods knowledge source, explicit checks that requested actions actually ran, and an expert-reviewed biological/statistical evaluation set before considering any local model a trustworthy scientific interpreter.

## Cleanup and application checks

After both owned evaluation processes stopped, the verified Liquid candidate weights were removed, reclaiming 5,155,564,768 bytes. Evaluation runtime logs were removed; the current Gemma weights/runtime, images, projects, measurements, conversations and evidence were preserved. The application model remains Gemma. All 88 backend tests passed for the comparison/profile support. No frontend implementation changed in this assessment.
