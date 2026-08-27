# Examples

Two sample input files (`sample_lease_contract.txt`, `sample_work_memo.txt`) and
their generated analysis reports (`*.report.pdf`), so you can see the tool's
output without configuring Azure OpenAI credentials yourself.

To regenerate the reports against your own Azure OpenAI resource:

```bash
cp .env.example .env  # fill in your real credentials
python scripts/generate_examples.py
```
