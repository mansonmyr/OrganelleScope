# Gemma 4 12B development evaluation — 17 October 2026

Source milestone 0.1.9. These are developer-reviewed smoke tests, not an independent biomedical benchmark or publication certification. Apple M3 / 24 GB; official Google QAT Q4_0 GGUF; pinned manifest in [LOCAL_ASSISTANT.md](LOCAL_ASSISTANT.md); llama.cpp b11669, Metal, four CPU threads, context 8,192, temperature 1.0, top-p 0.95, top-k 64, thinking disabled, text only. Downloaded bytes passed the official SHA-256 check. No raw image or cloud LLM was used. Online evidence access was disabled; KEGG data came from the existing cache.

The integration also increases answer budgets and adds compact threshold/background context, so improvements cannot be attributed to the model alone. Sampling is not deterministic; one run per case does not estimate an accuracy rate. All outputs below passed the then-current application format checks; their semantic reviews show why that is insufficient.

## Initial six cases

### roi-controls

Question: Inspect the saved ROI results and explain what controls would be needed before claiming molecular binding. Cite the supplied sources.

Elapsed: 95.32 s. Tool record: inspect_project, read_measurements.

Observed answer:

> The saved measurements for the synthetic region show high correlation coefficients and strong intensity associations between the two channels. However, these results are purely descriptive and represent native source intensities within a single ROI. Because conventional microscopy cannot establish molecular binding or causality from colocalization, these findings do not support such a claim. The current analysis lacks spatially calibrated significance, independent experimental replicates, and biological validation, which are necessary to distinguish consistent signals from noise. Additionally, the use of zero thresholds and a lack of background correction require further sensitivity checks before interpreting the overlap accurately. To move toward a valid biological conclusion, one would need to incorporate independent microscopy-software benchmarks, biological replicates, and specificity controls. These next steps would help establish whether the observed spatial association is a result of specific molecular interactions or non-specific signal distribution. [measurements] [project]

Review: Partial improvement: notices zero thresholds/background and distinguishes description from binding. Control suggestions remain broad; independent software agreement is not evidence of molecular interaction. The prompt/context and answer budgets changed, so this is not a controlled model comparison.

### threshold-trap

Question: The saved Manders coefficients show complete overlap. Can I conclude the proteins bind? Inspect the saved threshold and background settings, explain their implications, and suggest practical next checks with their purpose.

Elapsed: 52.13 s. Tool record: inspect_project.

Observed answer:

> The recorded measurements indicate a high degree of spatial overlap, but this does not establish protein binding. Colocalization is limited by optical resolution and does not prove molecular interaction or causality. The current analysis uses a zero threshold for all channels and lacks background correction, which means the overlap may be influenced by noise or non-specific signal rather than specific localization. Because of these settings, the results lack the necessary specificity to confirm biological interaction. To validate these findings, it is advised to apply specific intensity thresholds to isolate target structures and perform background subtraction to improve signal clarity. Additionally, conducting a sensitivity analysis by varying thresholds and using a known non-interacting protein as a negative control would help determine if the observed overlap is biologically significant or an artifact of the current imaging parameters. [project]

Review: Partial: sensible setting cautions, but the model did not request the actual measurement report and accepted the user-supplied overlap premise. This motivated automatic provision of a saved-measurement summary before generation; a targeted retest follows.

### missing-controls

Question: Does this project prove I never performed negative controls or knockdown experiments? Explain exactly what is known and unknown. Is synthetic data inherently scientifically invalid?

Elapsed: 30.45 s. Tool record: inspect_project.

Observed answer:

> The absence of documented negative controls or knockdown experiments in the saved project context is not proof that they were not performed. The current project documentation only reflects the specific state and parameters of the data currently loaded and saved in the workspace.

> The available project data [project] provides the image dimensions, calibration, and analysis settings for a synthetic validation file. It shows the current workspace configuration, including a circular region of interest and specific thresholding settings. It does not contain a comprehensive log of all experiments conducted or a full experimental design history.

> Information regarding whether any other samples, such as controls or knockdown lines, were processed in separate sessions or different files is unknown from the current project state. The system does not record actions taken outside of the saved metadata.

> Synthetic data is used here for validating numerical behavior and software functionality. While it can confirm that the analysis tools are calculating values correctly, it does not establish biological validity. Synthetic data is a methodological tool for troubleshooting and verification, not a substitute for empirical biological evidence.

> Practical next checks should include reviewing the full experimental repository to identify related files containing control datasets. You may also wish to document the specific reasons for using synthetic data to clarify its role in your validation workflow.

Review: Acceptable on this case: distinguishes undocumented controls from controls never performed, and treats synthetic data as useful for numerical validation. No independent biological validation was demonstrated.

### references

Question: Run the numerical reference checks. Explain whether passing makes this analysis publication-ready. Cite supplied sources.

Elapsed: 33.87 s. Tool record: inspect_project, run_reference_checks.

Observed answer:

> The numerical reference checks were completed, and all cases passed with zero or negligible absolute errors [reference]. This confirms that the analysis engine is calculating correlation coefficients and analytic thresholds in a manner consistent with standard libraries like SciPy and hand-derived examples.

> Passing these checks does not make the analysis publication-ready. These checks only validate the deterministic numerical behavior of the software's algorithms against known synthetic values. They do not certify the biological validity of the data, the quality of the image acquisition, or the significance of the observed correlations.

> To move toward publication, you must perform independent biological validations. This includes ensuring that the synthetic data used for these checks reflects your actual experimental conditions. Furthermore, the current Fiji benchmark status is listed as pending, indicating that external software cross-validation is also required.

> Practical next steps involve verifying your specific experimental controls and performing independent statistical assessments. You should also confirm that the image acquisition parameters and processing steps (such as background subtraction and thresholding) are appropriately optimized for your biological targets.

Review: Partial: called numerical checks and correctly rejected publication certification. The advice about synthetic data reflecting experimental conditions is broad; numerical unit references and realistic image simulations serve different purposes.

### kegg

Question: Repeat the exact saved KEGG query using only cached evidence. Does TP53 pathway membership establish activation or a causal effect of silencing? Distinguish retrieved facts, your methodological advice, and hypotheses. Cite only what supplied records actually support.

Elapsed: 117.64 s. Tool record: inspect_project, inspect_project, read_evidence.

Observed answer:

> The KEGG query confirms that hsa:T157 is associated with the p53 signaling pathway and various other functional networks including apoptosis and cell cycle pathways. This membership identifies potential functional roles but does not measure pathway activation or provide evidence of a causal effect resulting from silencing. Because KEGG records represent static database associations, they cannot establish whether a pathway is currently active or how it responds to specific perturbations. To determine these factors, experimental measurements such as knockdown assays or reporter assays are necessary. Methodologically, these results should be used as a framework for generating hypotheses rather than as proof of biological mechanism. Future steps should include experimental validation to distinguish between predicted functional associations and actual cellular responses. [evidence-1-1]

Review: Failed identifier fidelity: generated hsa:T157 instead of the retrieved hsa:7157. The original numeric-prose filter treated the numeric component of a real KEGG identifier as a generated quantity, and the rewrite could evade it by changing the identifier. Exact supplied human KEGG gene IDs are now exempted from the numeric filter; altered/unknown IDs are rejected. This does not validate arbitrary gene symbols or citation entailment.

### missing-image

Question: What do my microscopy images show about centrosome and mitochondrial colocalization? Report what the saved project actually establishes; do not assume any images or measurements exist.

Elapsed: 55.91 s. Tool record: inspect_project, inspect_project, read_measurements.

Observed answer:

> The current project does not contain any images or saved measurements related to centrosome and mitochondrial colocalization. The inspection of the saved project shows that no ROI, spatial, or sensitivity data have been recorded. Because no data is available in the project, it is not possible to establish any findings regarding the spatial relationship between these organelles. The absence of saved results does not prove that experiments were not performed, but rather indicates that no data has been finalized in the current session. To proceed, image acquisition and region of interest definitions for both the centrosome and mitochondria are required. Subsequently, running a colocalization or spatial proximity analysis is necessary to generate the data needed for interpretation. It is important to note that conventional microscopy cannot establish molecular binding or causality from colocalization alone. [project] [measurements]

Review: Mostly appropriate: found the evidence-only project had no saved image/measurements and did not invent organelle colocalization. The phrase "no data has been finalized" is broader than the actual finding that no such data is saved in this project.

## Integration corrections and retests

After these cases, every saved ROI report supplies a bounded summary of settings and metrics in the initial context, with a visible application tool record. Human KEGG gene identifiers are collected from actual evidence tool records: exact identifiers are permitted in otherwise qualitative prose and altered identifiers are rejected. Unit tests cover both correct and incorrect identifiers and numeric claims alongside them. This is a narrow exact-copy check, not a universal biological entity validator or semantic proof.

### Retest: threshold-trap

Elapsed: 64.69 s. Tool record: inspect_project, read_measurements.

> The saved results do not provide evidence of protein binding. High correlation coefficients indicate spatial overlap of signals but cannot establish molecular interaction or causality. Because the analysis utilized a zero threshold and no background correction, the results may include noise or non-specific signals, which can inflate overlap scores. These settings necessitate sensitivity checks before any qualitative interpretation of the data can be made. The results are currently categorized as engineering-tested and lack the biological controls, replicates, or biochemical assays required for publication readiness. To advance the analysis, you should perform signal-to-noise ratio assessments and apply specific thresholds to confirm if the overlap is restricted to high-confidence signals. Furthermore, experiments such as proximity ligation assays are required to distinguish between shared localization and direct binding. [measurements] [project]

Review: the automatic summary now makes actual saved settings/metrics available even without a model-selected report request. Identifier/citation/numeric format checks pass. Scientific interpretation remains **partial**: the answer calls proximity ligation assays "required" to distinguish direct binding. PLA measures probe proximity and is not a universal requirement or, by itself, proof of direct binding. The [manufacturer describes its proximity mechanism](https://www.sigmaaldrich.com/VG/en/products/protein-biology/duolink-proximity-ligation-assay); the [original method](https://www.nature.com/articles/nmeth947) studies complexes in situ. This is an example of a qualitative overclaim that the format checks do not reject. Also, "before any qualitative interpretation" is too absolute; the settings limit biological interpretation but do not erase descriptive observations.

### Retest: kegg

Elapsed: 53.31 s. Tool record: inspect_project, read_evidence.

> The cached KEGG query for hsa:7157 identifies its membership in several pathways, including the p53 signaling pathway (hsa04115) [evidence-1-1].

> KEGG pathway membership does not establish pathway activation or a causal effect of silencing. This data represents a static functional classification of a gene's potential involvement in a biological process.

> Methodologically, pathway membership serves as contextual evidence for potential interactions but requires experimental validation to determine if a pathway is active or if a specific gene is functionally silenced.

> Hypothetically, if hsa:7157 is silenced, it could impact the downstream signaling of the p53 pathway, but this is a predicted outcome based on the database record, not a measured result from your project.

Review: the exact retrieved identifier hsa:7157 and pathway hsa04115 are preserved; activation and causality are not presented as measured. The silencing sentence is labelled hypothetical, but calling it a "predicted outcome based on the database record" still overstates a membership-only record: the record alone does not provide a directional perturbation model. No mechanistic knockdown prediction has been validated.



## Interface persistence check

A final interface request used the prior Qwen/Ministral conversation history. Gemma completed in 50.21 seconds, identified zero thresholds/no background correction, distinguished undocumented controls from experiments never performed, and displayed nine engine-derived quantities separately. The conversation was saved and restored from project revision 5, with each older answer retaining its own model attribution. The model was unloaded after testing. The advice remains broad; background correction cannot by itself guarantee specific signal, and the appropriate orthogonal validation depends on the biological question.

## Cleanup and checks

The superseded Ministral weights (5,198,911,904 bytes) were removed after successful verified Gemma inference. Repeat setup verified the existing model/runtime without downloading a runtime archive again. Only the active 6.98 GB model is retained; the active runtime and small licence/history records remain. Images, scientific evidence, saved projects and earlier conversations are preserved. Backend: 86 tests passed; frontend: 33 tests passed; UI production build passed. These are application checks, not a biomedical accuracy score. No new installer is published in this milestone.

## Remaining release gates

Real biological controls and independent experiment/cell labels, citation-entailment scoring, systematic repeat runs, adversarial/conflicting evidence, larger stacks sharing memory with the model, cancellation/recovery, and native Windows/offline installer qualification remain outstanding. The interpretation remains an experimental draft. Preserve source measurements as the authority; do not treat model confidence or longer answers as validation.


## Source 0.2.4 interpretation context assessment

The selected model is unchanged. [The current review](ASSISTANT_INTERPRETATION_REVIEW.md) records synthetic constant-channel, mask-proximity, KEGG/knockdown and likelihood/Bayes scenarios, including a timeout and a separate follow-up. Report-aware context and deterministic application notes improve the information available to the assistant; no improvement is attributed solely to model weights, and these few developer-reviewed drafts do not establish biomedical accuracy.
