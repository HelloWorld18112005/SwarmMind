import pytest
from app.orchestration.budgets import BudgetEnforcer


def test_budget_token_tracking_and_cost():
    budget = BudgetEnforcer(run_id="run-budget-test")

    # Record 100,000 prompt tokens and 50,000 completion tokens
    budget.record_tokens(prompt=100_000, completion=50_000)

    assert budget.prompt_tokens == 100_000
    assert budget.completion_tokens == 50_000
    assert budget.total_tokens == 150_000

    # 100k prompt at $0.50/M = $0.05
    # 50k completion at $1.50/M = $0.075
    # Total = $0.125
    assert budget.estimated_cost_usd == pytest.approx(0.125, rel=1e-3)


def test_budget_step_limit_enforcement():
    budget = BudgetEnforcer(run_id="run-step-test")
    budget.max_agent_steps = 3

    budget.record_agent_step("critic")
    budget.record_agent_step("critic")
    budget.record_agent_step("critic")

    # 4th step exceeds limit
    with pytest.raises(RuntimeError) as exc_info:
        budget.record_agent_step("critic")
    assert "budget exceeded" in str(exc_info.value).lower()


def test_budget_cost_ceiling_enforcement():
    budget = BudgetEnforcer(run_id="run-ceiling-test")
    budget.max_budget_usd = 0.05

    # 100k prompt = $0.05, 50k completion = $0.075 -> Total $0.125 exceeds $0.05
    with pytest.raises(RuntimeError) as exc_info:
        budget.record_tokens(prompt=100_000, completion=50_000)
    assert "cost budget exceeded" in str(exc_info.value).lower()
