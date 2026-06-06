# Peer Review (SR-005)

Review date: 2025-12-29.
Source: AI references audit provided by user.
Journal: Not specified.

## Full review text

Reference audit report

Document reviewed: Predicting Broadband Usage: A Comparison of Computer Vision and Rural-Urban Typology Machine Learning Models

I checked two things:

1. Citation-to-claim alignment (the footnote references 1-20 in the body): whether the sources listed in each footnote plausibly support the specific sentence they are attached to.

2. Reference list integrity (the References section): whether entries look bibliographically correct, and whether they include an appropriate DOI or stable URL (and whether those DOIs/URLs correspond to the cited work).

---

## 1) Do the in-text citations support the specific lines they are attached to?

Most footnotes are directionally consistent with the surrounding text, but there are several high-impact mismatches / questionable pairings where the cited sources do not clearly support the specific sentence they are attached to.

### A. Footnote 4 mixes relevant and likely irrelevant support

Where used: The paper states that analysts note "fiscal pressures and legal uncertainty," then cites footnote 4.
What footnote 4 contains: It includes (i) a Census ACS report on computer/internet use (Mejia), (ii) a Telecom Policy piece on universal access funding reform (Glass and Tardiff), and (iii) a Wiley legal alert about a USF constitutional ruling.

Issue:

- Glass and Tardiff and Class et al. (Wiley legal alert) plausibly relate to funding/legal uncertainty.
- Mejia (ACS-56) is a descriptive usage/adoption report and does not obviously support a claim about USF fiscal pressures or legal uncertainty. This looks like a mis-attached citation (or an over-broad bundle footnote).

Recommendation:

- Keep Glass/Tardiff + Class et al. here, but move Mejia to the later adoption-gap sentence where it is already used (footnote 10), or remove it from footnote 4.

---

### B. Footnote 7 does not clearly support the sentence about ACP ending/funding uncertainty

Where used: "With the ACP ending in 2024 and funding uncertainty remaining..." is supported by footnote 7.
What footnote 7 contains: a Benton Institute blog post about "Project 2025: Brendan Carr's Agenda for the FCC" and a paper on NECA tariffs and rural internet access costs.

Issue: Neither cited item is an obvious direct source for the factual claim that ACP ended in 2024 and that funding uncertainty remains. The Benton piece may touch regulatory agenda generally (and might mention ACP), and the NECA tariff paper is about tariff impacts -- not ACP program termination.

Recommendation:

- Replace or supplement footnote 7 with a primary source on ACP funding exhaustion/termination (FCC/USAC/NTIA, Congressional documentation), and keep Obermier and Hollman only if the sentence is broadened to include tariff-related affordability dynamics.

(Existence of the Benton post itself is verifiable.)

---

### C. Footnote 13 is attached to a highly specific "LiDAR + parcel data" claim, but the sources do not clearly match -- and one reference appears incorrect

Where used: The paper claims rural heterogeneity motivates typologies and "GIS-based zoning approaches, including LiDAR and parcel data... and vertical assets," citing footnote 13.
What footnote 13 cites: Strover (digital divide philosophy), Hollman et al. (rural internet consumer policy), Hossain et al. (a GIS-based approach for rural broadband expansion), and Kostelnick et al. (mapping/spatial analysis for rural broadband).

Issues:

1. Over-specific claim vs. mixed citations. Strover and Hollman (consumer/policy framing) are not clearly about LiDAR/parcel identification of vertical assets. This looks like citation drift: relevant to "rural heterogeneity motivates typologies," but not to "LiDAR and parcel data ... vertical assets."
2. The Hossain et al reference appears wrong in the bibliography (details in Section 2 below).

Recommendation:

- Split the sentence and re-cite:
  - Keep Strover/Hollman for conceptual rural heterogeneity/typology framing.
  - Use only the GIS/remote sensing sources (and ideally more directly LiDAR/parcel-specific sources) for the LiDAR/parcel/vertical-asset claim.
- Fix or replace the Hossain et al entry (see Section 2.A).

---

### D. Footnote 15 may not support the specific "poles, cables, and other linear assets" claim

Where used: The text says civil engineering computer vision can identify "poles, cables, and other linear assets," citing footnote 15.
What footnote 15 cites: Koch et al. (review on defect detection for concrete/asphalt infrastructure) and "Chow et al., Computer Vision Methods for Civil Infrastructure Inspection (2020)."

Issues:

- Koch et al. is specifically about concrete/asphalt defect detection and condition assessment, which is related to civil infrastructure CV generally, but not clearly a source for "poles/cables/linear utility assets."
- Chow et al. (2020) is too incomplete to verify (no venue/publisher/DOI/URL in the reference list), so it is hard to confirm it supports this claim at all.

Recommendation:

- Either (a) tighten the sentence to "civil infrastructure inspection (e.g., pavements/structures)" to match Koch, or (b) add a pole/wire/utility-asset CV citation that directly covers those objects, and fully specify the Chow reference (see Section 2.B).

---

### E. Footnote 19 may overstate what the cited sources support

Where used: "Recent work merges crowdsourced speed tests with income data and behavioral models..." cites footnote 19.
Footnote 19 cites: Saxon and Black (internet inequality in Chicago) and Agarwal and Canfield (agent-based adoption model).

Issue: These are plausible adjacent supports (internet inequality; behavioral/adoption modeling), but the sentence is quite specific ("merges speed tests with income data and behavioral models"). If neither paper explicitly does that three-way merge, the citation is partially misattached.

Recommendation:

- If your intent is "these are examples of (a) crowdsourced measurement bias + (b) behavioral adoption modeling," split the claim and cite separately.
- If the intent is truly "speed-test + income + behavioral modeling merged in one pipeline," add a source that explicitly does that.

---

## 2) Are the reference list entries accurate and do they include proper DOI/links?

### A. High-severity bibliographic error: "Hossain et al., Journal of Rural Studies 105 (2024): 103192" appears misattributed

In the paper's References section, the entry is:

Hossain, M. A., F. T. Mou, and S. Akter. "A GIS Based Approach for Identifying Priority Zones for Rural Broadband Expansion." Journal of Rural Studies 105 (2024): 103192.

Problem: On ScienceDirect / journal indexing, article number 103192 corresponds to a different paper (about land inequality and forest loss in Chile), not a rural broadband GIS prioritization study.

Implication:

- This is not just "missing DOI" -- it suggests the reference entry is incorrect (wrong title/authors attached to that volume/article number), and therefore the in-text support at footnote 13 is compromised.

Fix needed:

- Verify what GIS-based rural broadband zoning paper you intended to cite and replace this entry with correct metadata (authors, title, journal/year, article number/pages, DOI).

---

### B. Incomplete references that cannot be reliably verified

These entries are too incomplete to confirm accuracy or to locate a DOI/link:

1. Chow, C. et al. Computer Vision Methods for Civil Infrastructure Inspection. 2020.
   No publisher, journal, conference, report series, editors, or DOI/URL given.

2. Amini, M. Enhancing 5G Fixed Wireless Access in Rural Settings via Machine Learning-Driven Resource Optimization. West Virginia University, 2024.
   Likely a thesis/dissertation, but no repository URL/handle is provided.

3. Krell et al. NeurIPS 2023 proceeding
   Conference papers typically need a stable link (OpenReview/NeurIPS proceedings/ACM/DOI if assigned). None is given.

---

### C. References missing DOIs that can be added (verified)

The References section includes many peer-reviewed items without DOI/URL. Below are verified DOIs you can add.

(Where the paper already has a DOI/URL, I list it as "already present" or suggest strengthening.)

Journal articles

- Agarwal and Canfield (PLOS ONE, 2024): DOI 10.1371/journal.pone.0302146.
- Baltrusaitis et al. (IEEE TPAMI): DOI 10.1109/TPAMI.2018.2798607.
- Deller et al. (AJAE, 2022): DOI 10.1111/ajae.12259.
- Egli et al. (Geographical Research, 2019): DOI 10.1111/1745-5871.12291.
- Fan et al. (Computers, Environment and Urban Systems, 2025): DOI 10.1016/j.compenvurbsys.2025.102253.
- Gebru et al. (PNAS, 2017): DOI 10.1073/pnas.1700035114.
- Glass and Tardiff (Telecommunications Policy, 2021): DOI 10.1016/j.telpol.2020.102037.
- Goldstein and Pender (Telecommunications Policy, 2025): DOI 10.1016/j.telpol.2025.102930.
- Hollman et al. (Telecommunications Policy, 2024): DOI 10.1016/j.telpol.2024.102762.
- Hollman et al. (Rural Society, 2024): DOI 10.1080/10371656.2024.2307595.
- Kandilov et al. (Applied Economic Perspectives and Policy, 2017): DOI 10.1093/aepp/ppx022.
- Kim and Paudel (European Review of Agricultural Economics, 2025): DOI 10.1093/erae/jbaf015.
- Koch et al. (Advanced Engineering Informatics, 2015): DOI 10.1016/j.aei.2015.01.008.
- Kostelnick et al. (Papers in Applied Geography, 2024): DOI 10.1080/23754931.2024.2332238.
- Nguyen et al. (Public Health Reports, 2021): DOI 10.1177/0033354920968799.
- Saxon and Black (Computers, Environment and Urban Systems, 2022): DOI 10.1016/j.compenvurbsys.2022.101874.
- Schmit and Severson (Telecommunications Policy, 2021): DOI 10.1016/j.telpol.2021.102114.
- Whitacre and Gallardo (Telecommunications Policy, 2020): DOI 10.1016/j.telpol.2020.102025.

Conference proceedings

- Liu et al. (ACM Multimedia 2017): DOI 10.1145/3123266.3123271.
- Major et al. (ACM IMC 2020): DOI 10.1145/3419394.3423652.

Already has DOI in the reference list (good)

- Whitacre, Gallardo, and Strover (Telecommunications Policy, 2014): DOI already present in the paper.

---

### D. Web/report references where the URL is present but formatting may break copying

Several URLs in the PDF appear split across lines or include soft-hyphen/line-break artifacts (e.g., the Ookla entry is missing a URL entirely; other entries include line breaks in the URL). Examples include the ACS report link, the ERS report link, and the USF PDF link as rendered in the PDF extraction.

Recommendation: Make URLs copy-safe by:

- using a single unbroken URL string, and/or
- using DOI links where possible, and/or
- adding "Accessed YYYY-MM-DD" if your citation style expects it.

---

### E. Items that need a URL added (or strengthened)

- Ookla (2021): no URL provided in References.
- USDA RUCA codes: no URL provided in References.

Suggested stable landing page to cite (official ERS RUCA data page):

If you want the actual URL text in your bibliography, use:
https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes/

---

## 3) Cross-check: references listed but not cited in the body

Based on a text search of the main body (excluding the References section), I found no in-text citation occurrences for:

- Amini (2024)
- Kim and Paudel (2025)
- Schmit and Severson (2021)
- Whitacre and Gallardo (2020)

This is not inherently wrong (some styles allow uncited background reading), but in most academic formats every reference entry should be cited at least once. If these are meant as background, consider integrating them into the literature review (with explicit claims they support) or removing them from the reference list.

---

## 4) Prioritized discrepancy list

High severity (should fix before submission)

1. Hossain et al (Journal of Rural Studies 105:103192) appears incorrect/misattributed.
2. Chow et al (2020) reference is incomplete (cannot verify what it is).

Medium severity (likely impacts argument support)

3. Footnote 7 is likely not the right support for "ACP ending in 2024 and funding uncertainty."
4. Footnote 13 supports a highly specific LiDAR/parcel claim with mixed conceptual sources; should be split and re-cited.
5. Footnote 15: Koch et al is about concrete/asphalt defects; may not support poles/cables claim.

Low severity (format/metadata quality)

6. Most journal/conference references lack DOIs (even when readily available; see the DOI list above).
7. Several URLs appear line-broken, which can break copying.
8. Several references appear uncited in the main text (Section 3).

---

## 5) Suggested "clean" bibliographic fixes you can apply immediately

If you want a quick, high-impact cleanup:

- Add the verified DOIs listed in Section 2.C to the corresponding reference entries.
- Replace/repair the Hossain reference entirely (do not keep the 103192 metadata unless you intended to cite the Chile land inequality paper).
- Fill in missing metadata for:
  - Chow et al. (venue/publisher + DOI/URL)
  - Amini (repository URL/handle)
  - Krell et al. (NeurIPS/OpenReview URL)
  - Ookla (direct URL)
