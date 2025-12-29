# AGENTS

- The CENTAUR pipeline is canonical. Report metrics from data_work/diagnostics outputs.
- Keep documentation lean and task-focused. Move large text dumps to doc/logs/.
- The manuscript in manuscript_quarto/ is not a source of truth for pipeline metrics.

## Synthetic Peer Review Handling

- Break down each critique into discrete items and assess validity (valid/partial/unclear/unsupported).
- Report back which items are valid and can be fixed quickly; implement only the simple fixes.
- For substantive changes (analysis reruns, pipeline changes, major rewrites), summarize options and confirm with the user before implementing.
- Track intake/response using the review files in doc/reviews/ and store full review text in doc/logs/.
