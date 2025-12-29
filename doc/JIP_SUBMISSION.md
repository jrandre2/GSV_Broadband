# Journal of Information Policy Submission Guide

## Revision Plan

See [JOURNAL_REVISION_PLAN.md](reviews/JOURNAL_REVISION_PLAN.md) for the full conference-to-journal revision plan, including:

- 10 major issues identified for journal publication
- 10-step revision plan with word count estimates
- Priority matrix and file modification list

**Status:** In progress (pipeline complete; JIP renders available)

---

## Quick Reference

```bash
# Render for JIP submission
quarto render manuscript_quarto/index.qmd --profile jip

# Or use the template directly
quarto render manuscript_quarto/jip-template.qmd
```

Output: `manuscript_quarto/_output/jip/`

## Journal Requirements

| Requirement | Value |
|-------------|-------|
| Word limit | 10,000 (excluding abstract, tables, refs, footnotes) |
| Citation style | Chicago Notes-Bibliography (18th ed) |
| Font | Times New Roman 12pt |
| Spacing | Double-spaced |
| Format | Word document (.docx) |
| Figures | Separate files, 300 dpi, >= 2.25" wide, TIFF/JPG |

## File Configuration

- `manuscript_quarto/_quarto-jip.yml` - JIP-specific Quarto settings
- `manuscript_quarto/jip-template.qmd` - Article template with guidance
- `manuscript_quarto/jip-coverpage.qmd` - Cover page template
- `manuscript_quarto/jip-reference.docx` - Word formatting reference
- `manuscript_quarto/csl/chicago-fullnote-bibliography.csl` - Citation format

## Submission Checklist

### Content

- [ ] Word count <= 10,000 (main text only)
- [ ] Abstract/introductory statement (~100-200 words)
- [ ] Policy implications explicitly stated in Discussion
- [ ] All claims supported with citations

### Formatting

- [ ] Chicago Notes-Bibliography citations (footnotes, not in-text)
- [ ] Figures submitted as separate files (not embedded)
- [ ] Alt text provided for all figures and tables
- [ ] URLs include access dates

### Anonymization

- [ ] Author names removed from main document
- [ ] Institutional affiliations removed
- [ ] Self-citations anonymized ("Author, 2023" -> "Anonymous, 2023")
- [ ] Acknowledgments removed from anonymous version

### Cover Page

- [ ] Complete author information (name, affiliation, email, ORCID)
- [ ] Corresponding author designated
- [ ] Author contributions (CRediT taxonomy)
- [ ] Funding statement
- [ ] Conflicts of interest declaration
- [ ] Data availability statement
- [ ] Word counts (main text, abstract, tables, figures)

## Workflow

1. **Edit content** in `index.qmd` or `jip-template.qmd`

2. **Prepare anonymous version**:
   - Comment out or remove `author:` block
   - Remove acknowledgments
   - Anonymize self-citations

3. **Prepare cover page**:
   - Fill in `jip-coverpage.qmd` with author details
   - Update word counts
   - Render: `quarto render manuscript_quarto/jip-coverpage.qmd`

4. **Render main document**:
   ```bash
   quarto render manuscript_quarto/index.qmd --profile jip
   ```

5. **Prepare figures**:
   - Export from `manuscript_quarto/figures/` as separate files
   - Ensure 300 dpi resolution
   - Add descriptive filenames (e.g., `fig1_spatial_groups.tiff`)

6. **Final check**:
   - Open .docx and verify formatting
   - Check footnote citations render correctly
   - Verify no author identifying information remains

## Useful Commands

```bash
# Check word count (approximate)
wc -w manuscript_quarto/index.qmd

# List figures to prepare
ls manuscript_quarto/figures/*.png

# Validate references
quarto check manuscript_quarto/references.bib
```

## Resources

- [JIP Author Guidelines](https://jip.vmhost.psu.edu/ojs/index.php/jip/about/submissions)
- [Chicago Manual of Style Online](https://www.chicagomanualofstyle.org/)
- [CRediT Author Contributions](https://credit.niso.org/)
