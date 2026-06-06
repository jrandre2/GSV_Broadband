# Peer Review (SR-007)

Review date: 2025-12-29.
Source: Reference audit report provided by user.
Journal: Not specified.

## Full review text

Reference audit report for the preprint
Document reviewed: “Predicting Broadband Usage: A Comparison of Computer Vision and Rural-Urban Typology Machine Learning Models” (Andrews & Hollman).
index
I checked (1) whether each in-text citation/footnote plausibly supports the specific claim it is attached to, and (2) whether each bibliography entry contains a correct DOI or a stable URL where one should exist, plus any formatting problems that could break DOI/URL copying.
1) Do the citations support the specific claims where used?
The paper uses footnote-style citations (1–24) concentrated in the literature review.
Most of them are conceptually well-matched to the statements they follow, but a few spots look like partial support or category mismatch (access vs. adoption), and one citation appears to need verification.
Footnote-by-footnote alignment notes
Footnote 1 (digital divide persists, rural lags) — mostly OK, but one referenced item needs verification
Claim: rural areas lag urban/suburban counterparts despite investment.
index

Cites Ali (book) + Strover (2019) + Hollman et al. (Rural Measures).
index
Ali (2021) and Hollman et al. are clearly on-topic.
Potential issue: I could not reliably corroborate the Strover (2019) “Journal of Information Policy” bibliographic details (see bibliography section below). Online results strongly show a similarly titled Strover piece as a 2014 journal article with a different venue/DOI, which suggests the preprint’s “Journal of Information Policy 9 (2019)” entry may be misattributed and should be verified.
Footnote 2 (interaction of geography/markets/socioeconomics/policy) — OK
Cites two Hollman et al. 2024 papers, which appear directly relevant.
index
Footnote 3 (USF as principal federal equalization tool) — OK
Cites Ali + American Consumer Institute report.
Footnote 4 (legal challenges/fiscal pressures around USF authority) — OK and externally verifiable
Cites Glass & Tardiff + Harvard Law Review note + Supreme Court opinion link.
The cited Supreme Court opinion link corresponds to an actual Supreme Court PDF for FCC v. Consumers’ Research (June 27, 2025).
Footnote 5 (BEAD/ACP/USDA programs expand infrastructure; evidence positive but uneven) — potential mismatch / incomplete coverage
This is the largest citation-to-claim risk I found.
Claim text explicitly lists BEAD and ACP alongside USDA programs: “Other programs (BEAD, ACP, USDA Community Connect, ReConnect)…”
Footnote 5 cites: Deller et al. (business startup rates), Whitacre et al. (economic growth), Kandilov et al. (USDA Broadband Loan Program), and Goldstein & Pender (USDA Community Connect).
Those sources plausibly support (a) broadband impacts and (b) USDA program effects (loan/community connect), but they do not obviously support BEAD (NTIA program) and do not obviously support ACP (demand-side subsidy) as part of that specific “evidence” bundle. The paper does separately cite ACP ending and ACP uptake elsewhere (footnotes 7–8), which is good—but footnote 5 specifically is not a clean support for the BEAD + ACP part of that sentence.
Suggested fix: either (i) split the sentence and cite BEAD/ACP with program-specific sources, or (ii) remove BEAD/ACP from that sentence and reserve them for the later ACP-focused citations already present.
Footnote 6 (demographic disparities persist in approved service areas) — likely OK
Cites USDA ERS report on areas/populations served.
Footnote 7 (ACP ended June 1, 2024 due to no additional funding) — OK
Cites USAC ACP page + CRS report.
Footnote 8 (ACP uptake varies with eligibility/local context) — OK
Cites Horrigan et al. (Telecommunications Policy; ACP uptake).
Footnote 9 (FCC census-block granularity overestimates rural availability) — plausible, but would benefit from a more direct mapping-data citation
Cites Grubesic & Mack (2015).
This might be directionally correct, but the claim is very specific to FCC collection granularity and systematic overstatement; a direct FCC/GAO mapping reference would make this tighter. (They do cite a GAO mapping report in footnote 15, but that’s tied to a different sentence.)
Footnote 10 (speed test datasets are socioeconomically biased) — OK
Cites Saxon & Black (2022).
Footnote 11 (ACS adoption gap) — OK
Cites ACS report (Mejia).
Footnote 12 (“other sources report higher access rates”) — conceptually OK, but access vs adoption needs clarification
Cites ASCE 2025 broadband report card PDF.
ASCE reporting includes a high availability/access figure (e.g., “94% of American households can access…”), which supports the “higher access rates” framing.
However, the sentence juxtaposes ACS “adoption” (subscription/use) with ASCE “access” (availability). That’s not necessarily wrong, but it should explicitly label this as access vs. adoption to avoid implying the two sources directly conflict on the same metric.
Footnote 13 (Major et al. reverse-engineered ISP checkers; FCC maps overstate) — OK
Footnote 14 (rural heterogeneity motivates typologies/zoning frameworks) — plausible, but “zoning frameworks” could use a more directly planning-oriented cite
index

Footnote 15 (GIS/zoning + LiDAR/parcel data for prioritization) — OK
Footnotes 16–23 (CV / multimodal ML / agent-based modeling) — OK
Footnote 24 (RUCA codes source) — OK
2) Are the reference entries themselves accurate and complete?
A. Entries missing a DOI or stable link where one likely exists
1) Hollman, Obermier & Burger (2021) “Rural Measures…” — DOI missing
In the bibliography, this entry has no DOI/URL.
A DOI exists for this paper: 10.5325/jinfopoli.11.2021.0176.
Suggested corrected entry (example formatting):
Hollman, A. K., T. R. Obermier, & P. R. Burger. (2021).
Rural Measures: A Quantitative Study of the Rural Digital Divide.
Journal of Information Policy, 11, 176–201. https://doi.org/10.5325/jinfopoli.11.2021.0176
2) Grubesic & Mack (2015) “Spatially Explicit Approaches…” — DOI missing
The bibliography entry lists journal/volume/pages but no DOI.
Telecommunications Policy articles typically have DOIs; this should be checked and added (I did not find a DOI in the preprint itself).
3) Strover (2019) “The U.S. Digital Divide: A Call for a New Philosophy.” — DOI missing and venue/year needs verification
The bibliography lists it as Journal of Information Policy 9 (2019): 275–300 with no DOI/URL.
Potential discrepancy: online results clearly show a similarly titled Strover work as a 2014 journal article with DOI 10.1080/15295036.2014.922207 (different venue).
I can’t conclusively say the 2019 JIP item is wrong (because a full JIP lookup was blocked during checking), but it is uncertain enough that it should be verified against the journal’s table of contents and then corrected with the accurate DOI/URL.
Suggested action:
Confirm whether the cited work is:
a 2019 Journal of Information Policy article (then add its DOI), or
the 2014 Critical Studies in Media Communication article (then change venue/year/pages and add DOI), or
another format (book chapter) with correct editors/publisher details.
B. Potential bibliographic descriptor mismatch
Krell et al. (2023) “Enabling Decision Support Systems Through Automated Cell Tower Detection.”
Bibliography format: “Proceedings of the 37th Conference on Neural Information Processing Systems (NeurIPS 2023)… https://arxiv.org/abs/2311.07840.”
This may be fine if it truly appears in the NeurIPS proceedings, but if the arXiv version is the only public artifact, it would be cleaner to cite as arXiv preprint (and optionally add the NeurIPS proceedings link if officially published).
3) DOI/URL formatting problems that could break copying or linking
Across multiple entries, DOIs and URLs are split across lines and/or contain hyphenation artifacts (visible in the parsed PDF text as a “￾” character) that can break copy/paste. Examples in the bibliography include:
American Consumer Institute report URL contains a break artifact:
ASCE broadband PDF URL is line-wrapped:
Several DOIs are split after 10. or mid-string (e.g., Deller, Gebru).
USDA RUCA URL shows hyphenation/line-wrap issues in the parsed text.
CRS link shows a break artifact (crs￾product).
Why this matters: even if the PDF’s clickable hyperlinks work, the visible text version in the references can become invalid when copied into browsers, citation managers, or preprint indexing systems.
Suggested fix:
In the source (Word/LaTeX), insert DOIs/URLs as unbroken strings and disable discretionary hyphenation in bibliography formatting.
Prefer the canonical DOI form https://doi.org/<doi> (single contiguous string).
4) Missing references for key data sources used in the paper
The paper’s outcome/label is the Microsoft Research “U.S. Broadband Usage Percentages” dataset, used throughout (abstract + methods).
However, there is no corresponding bibliography entry giving:
dataset landing page / repository URL,
version or release date,
access date,
documentation describing how estimates were produced.
Given this dataset is central to the dependent variable, this is a meaningful omission.
Suggested reference entry template (fill in the official dataset URL/version):
Microsoft Research. U.S. Broadband Usage Percentages [Data set]. (Year).
Version X.Y. Retrieved Month Day, Year, from <official dataset URL>
Related “method/data source” items that may also warrant formal citation (depending on venue expectations):
Google Street View Static API / Terms of Service (you mention compliance).
OpenStreetMap data used to generate sampling points (“OSM building points”). (Shown in Figure pipeline.)
index
5) Quick “action list” of discrepancies to fix
Highest priority (likely to be flagged by reviewers or readers):
Add DOI for Hollman et al. (2021) Rural Measures (missing in bibliography).
Verify and correct Strover (2019) entry (missing DOI; possible venue/year mismatch with a well-known 2014 item).
Footnote 5: either add BEAD/ACP-specific sources or remove BEAD/ACP from that sentence; current citations don’t clearly support the full list of programs.
Clarify Footnote 12 sentence as “access vs adoption” to avoid metric confusion.
index
Add a formal reference entry for the Microsoft broadband usage dataset (currently used but uncited).
Add DOI (or stable link) for Grubesic & Mack (2015) if available.
De-hyphenate and unbreak URLs/DOIs in the bibliography to prevent copy/paste failures.
