# Examples

Two sample input files (`sample_lease_contract.txt`, `sample_work_memo.txt`).
The analysis reports (`*.report.pdf`) are **not** checked in — they are
generated on demand, since producing them requires a live Azure OpenAI
resource.

To generate them against your own Azure OpenAI (or Groq) credentials:

```bash
cp .env.example .env       # fill in your real credentials
docker compose up -d
docker compose exec api python -m scripts.generate_examples
```
