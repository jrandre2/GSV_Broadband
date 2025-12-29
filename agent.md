# Agent Guidance: Journal of Information Policy (JIP)

Use this guidance for copy edits and manuscript revisions targeting JIP.

## Tone
- Formal, neutral, policy-relevant, evidence-first.
- Avoid hype, marketing language, or unqualified claims.
- Prefer cautious phrasing ("suggests," "indicates," "may") unless the evidence is definitive.

## Level of detail
- Keep paragraphs concise (3-5 sentences) and tightly scoped.
- Prioritize methodological transparency over extended narrative.
- Avoid large text dumps; compress lists into compact sentences when possible.

## Terminology
- Use consistent terms: "estimated broadband usage (>=25/3 Mbps)" as the target.
- Distinguish usage/adoption from availability/infrastructure.
- Describe our image pipeline as "pretrained CNN embeddings (no fine-tuning)" when relevant.

## Evidence and metrics
- Report metrics from data_work/diagnostics outputs only.
- Provide exact values and note the evaluation protocol (holdout vs spatial CV).
- Do not infer trends beyond what diagnostics support.

## Copy-editing rules
- Preserve citations when rephrasing; do not remove core sources.
- Reduce redundancy and tighten long literature review sections.
- Prefer active voice when it improves clarity.
- Keep ASCII unless the existing file requires non-ASCII.
- Keep the manuscript standalone; avoid metacommentary about prior drafts, pipeline iterations, or review responses.
- Use $R^2$ formatting (superscript) instead of plain "R2".

## Review docs
- Use review IDs (for example, SR-001) in filenames; record dates inside the files, not in filenames.
- Check doc/reviews/INDEX.md for the current review and treat older IDs as archived inputs.
- If the user references SN-001, treat it as an alias for SR-001 unless asked to rename.
