from src.api.ai_budget import AIBudget


def test_allows_calls_up_to_the_limit():
    budget = AIBudget(max_calls=3)

    assert [budget.try_consume() for _ in range(3)] == [True, True, True]


def test_refuses_calls_once_the_limit_is_reached():
    budget = AIBudget(max_calls=2)
    budget.try_consume()
    budget.try_consume()

    assert budget.try_consume() is False


def test_forgets_calls_that_fell_out_of_the_window():
    clock = [1000.0]
    budget = AIBudget(max_calls=1, window_seconds=3600, now=lambda: clock[0])

    assert budget.try_consume() is True
    assert budget.try_consume() is False

    clock[0] += 3601

    assert budget.try_consume() is True


def test_a_limit_of_zero_means_no_limit():
    budget = AIBudget(max_calls=0)

    assert all(budget.try_consume() for _ in range(100))


def test_is_exhausted_reports_the_state_without_spending_it():
    budget = AIBudget(max_calls=1)

    assert budget.is_exhausted() is False
    assert budget.try_consume() is True
    assert budget.is_exhausted() is True
    # Asking twice must not itself consume anything.
    assert budget.is_exhausted() is True
