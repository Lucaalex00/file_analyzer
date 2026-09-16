# Examples

The sample documents the web UI offers as one-click demos, each committed
alongside the PDF report the real pipeline produced from it
(`*.report.pdf`). They are checked in on purpose: someone browsing the repo
can see actual output without configuring any credentials.

| Input | What it shows |
|---|---|
| `sample_lease_contract.txt` | A lease with the kind of clauses the analyzer flags: early-termination penalty, automatic renewal, a rent increase |
| `sample_work_memo.txt` | A work email, including a request to send credentials — the phishing-style pattern the rule-based pass catches |
| `Luca_Cirio_CV.pdf` | A real PDF, so extraction runs on a genuine document rather than plain text |

The reports were generated against Azure OpenAI, so they reflect the prompt
and model in use when they were written — expect them to differ from a fresh
run after either changes.

To regenerate them with your own Azure OpenAI or Groq credentials:

```bash
cp .env.example .env       # fill in your real credentials
docker compose up -d
docker compose exec api python -m scripts.generate_examples
```

The script reads the same list the web UI does
(`src/api/example_documents.py`), so adding a sample there adds it here too.
