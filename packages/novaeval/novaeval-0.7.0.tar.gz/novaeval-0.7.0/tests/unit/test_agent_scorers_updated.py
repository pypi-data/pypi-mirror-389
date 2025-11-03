"""
Updated unit tests for agent scorers using ScoreResult.

Tests the simplified agent scoring system with consistent ScoreResult return type.
"""

import pytest

from novaeval.agents.agent_data import AgentData, ToolCall, ToolSchema
from novaeval.scorers.agent_scorers import (
    AgentScorers,
    parse_llm_score_response,
    task_progression_scorer,
    tool_relevancy_scorer,
)
from novaeval.scorers.base import ScoreResult

pytestmark = pytest.mark.unit


class MockLLMModel:
    """Mock LLM model for testing."""

    def generate(self, prompt: str) -> str:
        """Return mock JSON response."""
        return '{"score": 8.5, "reasoning": "Test reasoning"}'


def test_parse_llm_score_response_basic():
    """Test basic JSON parsing."""
    response = '{"score": 8.5, "reasoning": "Good answer"}'
    result = parse_llm_score_response(response, threshold=7.0)

    assert isinstance(result, ScoreResult)
    assert result.score == 8.5
    assert result.reasoning == "Good answer"
    assert result.passed


def test_parse_llm_score_response_markdown():
    """Test parsing with markdown code blocks."""
    response = """```json
{
    "score": 9.0,
    "reasoning": "Excellent response"
}
```"""
    result = parse_llm_score_response(response, threshold=7.0)

    assert isinstance(result, ScoreResult)
    assert result.score == 9.0
    assert result.reasoning == "Excellent response"


def test_parse_llm_score_response_with_metadata():
    """Test parsing with extra metadata fields."""
    response = '{"score": 7.5, "reasoning": "Good", "confidence": 0.95, "original_task": "Test task"}'
    result = parse_llm_score_response(response, threshold=7.0)

    assert isinstance(result, ScoreResult)
    assert result.score == 7.5
    assert result.metadata.get("confidence") == 0.95
    assert result.metadata.get("original_task") == "Test task"


def test_parse_llm_score_response_error():
    """Test error handling."""
    response = '{"score": -1, "reasoning": "Error occurred"}'
    result = parse_llm_score_response(response, threshold=7.0)

    assert isinstance(result, ScoreResult)
    assert result.score == -1.0
    assert not result.passed
    assert "Error occurred" in result.reasoning


def test_tool_relevancy_scorer_returns_score_result():
    """Test that tool_relevancy_scorer returns ScoreResult."""
    mock_model = MockLLMModel()

    agent_data = AgentData(
        tools_available=[ToolSchema(name="test_tool", description="Test")],
        tool_calls=[ToolCall(tool_name="test_tool", parameters={}, call_id="123")],
    )

    result = tool_relevancy_scorer(agent_data, mock_model)

    # Should return list of ScoreResult
    assert isinstance(result, list)
    assert len(result) > 0
    assert isinstance(result[0], ScoreResult)
    assert hasattr(result[0], "score")
    assert hasattr(result[0], "reasoning")
    assert hasattr(result[0], "metadata")


def test_task_progression_scorer_returns_score_result():
    """Test that task_progression_scorer returns ScoreResult."""
    mock_model = MockLLMModel()
    mock_model.generate = (
        lambda p: '{"score": 8.0, "reasoning": "Good progress", "original_task": "Complete task"}'
    )

    agent_data = AgentData(
        agent_task="Test task",
        agent_role="Test role",
        system_prompt="Test prompt",
        agent_response="Test response",
    )

    result = task_progression_scorer(agent_data, mock_model)

    assert isinstance(result, ScoreResult)
    assert result.score == 8.0
    assert result.reasoning == "Good progress"
    assert result.metadata.get("original_task") == "Complete task"


def test_agent_scorers_class():
    """Test AgentScorers class."""
    mock_model = MockLLMModel()
    scorers = AgentScorers(mock_model)

    # Check all methods exist
    assert hasattr(scorers, "score_tool_relevancy")
    assert hasattr(scorers, "score_task_progression")
    assert hasattr(scorers, "score_role_adherence")
    assert hasattr(scorers, "score_context_relevancy")
    assert hasattr(scorers, "score_goal_achievement")
    assert hasattr(scorers, "score_conversation_coherence")
    assert hasattr(scorers, "score_all")


def test_score_all_returns_dict():
    """Test that score_all returns dict of ScoreResult objects."""
    mock_model = MockLLMModel()
    mock_model.generate = lambda p: '{"score": 8.0, "reasoning": "Test"}'

    scorers = AgentScorers(mock_model)

    agent_data = AgentData(
        agent_task="Test",
        agent_role="Test",
        system_prompt="Test",
        agent_response="Test",
        tools_available=[],
        tool_calls=[],
        trace=[],
        agent_exit=True,
    )

    results = scorers.score_all(agent_data)

    assert isinstance(results, dict)
    assert len(results) == 8  # All 8 scorers

    # Check all scorers present
    assert "tool_relevancy" in results
    assert "task_progression" in results
    assert "role_adherence" in results
    assert "context_relevancy" in results
    assert "goal_achievement" in results
    assert "conversation_coherence" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
