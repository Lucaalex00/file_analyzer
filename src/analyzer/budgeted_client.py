from src.analyzer.demo_client import DemoAIClient


class _BudgetedCompletions:
    def __init__(self, real_client, demo_client, budget):
        self._real_client = real_client
        self._demo_client = demo_client
        self._budget = budget

    def create(self, **kwargs):
        if self._budget.try_consume():
            return self._real_client.chat.completions.create(**kwargs)
        return self._demo_client.chat.completions.create(**kwargs)


class _BudgetedChat:
    def __init__(self, real_client, demo_client, budget):
        self.completions = _BudgetedCompletions(real_client, demo_client, budget)


class BudgetedAIClient:
    """Wraps a real AI client and degrades to the demo one when the hourly
    budget is spent.

    Duck-types the same surface DocumentAnalyzer/DocumentComparator use, so
    neither has to know a budget exists. Falling back (rather than raising)
    keeps the public demo usable for whoever opens the link next: the answer
    is simulated, and says so.
    """

    def __init__(self, real_client, budget, demo_client=None):
        self.real_client = real_client
        self.chat = _BudgetedChat(real_client, demo_client or DemoAIClient(), budget)
