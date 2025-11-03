"""
Unit tests for conversational scorers.
"""

import pytest

from novaeval.scorers.base import ScoreResult
from novaeval.scorers.conversational import (
    Conversation,
    ConversationalMetricsScorer,
    ConversationCompletenessScorer,
    ConversationRelevancyScorer,
    ConversationTurn,
    KnowledgeRetentionScorer,
    RoleAdherenceScorer,
    ScoreWithReasoning,
)

pytestmark = pytest.mark.unit


class MockLLMModel:
    """Mock LLM model for testing."""

    def __init__(self, mock_responses=None, name="MockModel", sync_generate=False):
        self.mock_responses = mock_responses or {}
        self.call_count = 0
        self.name = name
        self.sync_generate = sync_generate

    async def generate(self, prompt, **kwargs):
        """Mock generate method."""
        self.call_count += 1
        if isinstance(self.mock_responses, dict):
            # Find matching prompt patterns for more sophisticated mocking
            for pattern, response in self.mock_responses.items():
                if pattern.lower() in prompt.lower():
                    return response
            return f"Mock response {self.call_count}"
        elif isinstance(self.mock_responses, list):
            if self.call_count <= len(self.mock_responses):
                return self.mock_responses[self.call_count - 1]
            return f"Mock response {self.call_count}"
        else:
            return (
                str(self.mock_responses)
                if self.mock_responses
                else f"Mock response {self.call_count}"
            )

    def generate_sync(self, prompt, **kwargs):
        """Synchronous generate method for testing sync/async detection."""
        if self.sync_generate:
            return self.generate(prompt, **kwargs)
        raise AttributeError("generate_sync not available")


class TestKnowledgeRetentionScorer:
    """Test cases for KnowledgeRetentionScorer."""

    def test_init(self):
        """Test scorer initialization."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)
        assert scorer.name == "Knowledge Retention"
        assert scorer.model == model
        assert scorer.window_size == 10  # Default window size

    def test_score_basic_functionality(self):
        """Test basic scoring functionality."""
        model = MockLLMModel("4")
        scorer = KnowledgeRetentionScorer(model)

        score = scorer.score("Good response", "What is AI?", None)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_with_conversation_context(self):
        """Test scoring with conversation context."""
        # Mock knowledge extraction and violation detection
        mock_responses = [
            "1. User likes Python programming\n2. User is a beginner",  # Knowledge extraction
            '{"score": 8, "reasoning": "Good retention"}',  # Mock LLM response with score
        ]
        model = MockLLMModel(mock_responses)
        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(
                    speaker="user", message="I am learning Python programming"
                ),
                ConversationTurn(
                    speaker="assistant",
                    message="That's great! Python is excellent for beginners",
                ),
                ConversationTurn(speaker="user", message="What should I learn next?"),
            ]
        )

        context = {"conversation": conversation}
        score = scorer.score(
            "I recommend learning data structures", "What should I learn next?", context
        )
        assert isinstance(score, float)
        # Scores are on 1-10 scale, normalize to 0-1 for comparison
        normalized_score = (score - 1) / 9 if score > 1 else score
        assert 0.0 <= normalized_score <= 1.0

    def test_score_with_retention_violations(self):
        """Test scoring when retention violations are detected."""
        mock_responses = [
            "1. User name is John\n2. User is 25 years old",  # Knowledge extraction
            '{"score": 3, "reasoning": "Poor retention"}',  # Violations detected - low score
        ]
        model = MockLLMModel(mock_responses)
        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(
                    speaker="user", message="Hi, I'm John and I'm 25 years old"
                ),
                ConversationTurn(speaker="assistant", message="Nice to meet you John!"),
            ]
        )

        context = {"conversation": conversation}
        score = scorer.score("What's your name again?", "Question", context)
        # Score should be reduced due to violation (scores are on 1-10 scale)
        assert 1.0 <= score <= 10.0
        assert score < 10.0  # Should be less than perfect score

    def test_simple_retention_score_fallback(self):
        """Test fallback to simple retention scoring."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test asking basic questions (should get low score)
        score = scorer.score("What is your name?", "Question", None)
        assert score == 0.3  # Low score for asking basic questions

        # Test normal response (should get decent score)
        score = scorer.score("I can help you with that", "Question", None)
        assert score == 0.7  # Default decent score

    def test_parse_knowledge_items(self):
        """Test knowledge item parsing."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        response = "1. User likes Python\n2. User is a beginner programmer\n3. Short"
        items = scorer._parse_knowledge_items(response, 0, "user")

        assert len(items) == 2  # Third item filtered out for being too short
        assert items[0].content == "User likes Python"
        assert items[1].content == "User is a beginner programmer"
        assert all(item.turn_index == 0 for item in items)
        assert all(item.speaker == "user" for item in items)

    def test_parse_violations(self):
        """Test violation parsing - method no longer exists, testing knowledge extraction instead."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test knowledge item parsing instead (violation parsing was removed)
        response = "1. User name is John\n2. User is 25 years old"
        items = scorer._parse_knowledge_items(response, 0, "user")
        assert len(items) == 2
        assert "User name is John" in items[0].content

    def test_input_validation(self):
        """Test input validation."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test empty prediction
        assert scorer.score("", "ground_truth", {}) == 0.0

        # Test empty ground truth
        assert scorer.score("prediction", "", {}) == 0.0

        # Test whitespace only
        assert scorer.score("   ", "ground_truth", {}) == 0.0

    @pytest.mark.asyncio
    async def test_input_validation_non_string_types(self):
        """Test input validation with non-string types."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test non-string output_text
        result = await scorer.evaluate("input", 123, None)
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "type_error"

        result = await scorer.evaluate("input", None, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", {"dict": "value"}, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", ["list", "value"], None)
        assert result.score == 0.0
        assert not result.passed

        # Test non-string expected_output
        result = await scorer.evaluate("input", "output", 456)
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "type_error"

        # Test empty string output_text
        result = await scorer.evaluate("input", "", None)
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "empty_output"

        # Test whitespace-only output_text
        result = await scorer.evaluate("input", "   ", None)
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "empty_output"

        # Test empty expected_output
        result = await scorer.evaluate("input", "output", "")
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "empty_expected"

        # Test whitespace-only expected_output
        result = await scorer.evaluate("input", "output", "   ")
        assert result.score == 0.0
        assert not result.passed
        assert result.metadata.get("error") == "empty_expected"

    @pytest.mark.asyncio
    async def test_evaluate_knowledge_retention_async_empty_knowledge(self):
        """Test _evaluate_knowledge_retention_async with empty knowledge_items."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="assistant", message="Hello"),
            ]
        )

        result = await scorer._evaluate_knowledge_retention_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # With no user turns, knowledge_items will be empty, should return ScoreWithReasoning with score -1.0
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == -1.0

    @pytest.mark.asyncio
    async def test_evaluate_knowledge_retention_async_no_context(self):
        """Test _evaluate_knowledge_retention_async without conversation context."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        result = await scorer._evaluate_knowledge_retention_async(
            "Response", "Ground truth", None
        )
        assert isinstance(result, ScoreWithReasoning)
        # Fallback score is 0.7 (normalized) or could be on 1-10 scale from LLM
        assert 0.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_knowledge_retention_async_malformed_conversation(self):
        """Test _evaluate_knowledge_retention_async with malformed conversation."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        result = await scorer._evaluate_knowledge_retention_async(
            "Response", "Ground truth", {"conversation": "not a Conversation object"}
        )
        assert isinstance(result, ScoreWithReasoning)
        # Fallback score when conversation is malformed
        assert 0.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_knowledge_retention_async_model_exception(self):
        """Test _evaluate_knowledge_retention_async with model exceptions."""
        model = MockLLMModel()

        async def failing_generate(*args, **kwargs):
            raise Exception("Model error")

        model.generate = failing_generate

        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="I like Python"),
            ]
        )

        result = await scorer._evaluate_knowledge_retention_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # When extraction fails, no knowledge items are found, so returns -1.0
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == -1.0  # No knowledge to retain when extraction fails

    @pytest.mark.asyncio
    async def test_evaluate_knowledge_retention_async_window_size(self):
        """Test sliding window boundary cases."""
        model = MockLLMModel(["1. Knowledge item", '{"score": 7, "reasoning": "Good"}'])
        scorer = KnowledgeRetentionScorer(model, window_size=2)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message=f"Message {i}")
                for i in range(15)  # More than window_size
            ]
        )

        result = await scorer._evaluate_knowledge_retention_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        assert isinstance(result, ScoreWithReasoning)
        assert 1.0 <= result.score <= 10.0

    def test_parse_knowledge_items_none_response(self):
        """Test parsing 'None' response."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        items = scorer._parse_knowledge_items("None", 0, "user")
        assert len(items) == 0

        items = scorer._parse_knowledge_items("none", 0, "user")
        assert len(items) == 0

        items = scorer._parse_knowledge_items("NONE", 0, "user")
        assert len(items) == 0

    def test_parse_knowledge_items_numbered_formats(self):
        """Test parsing different numbered list formats."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test format with period
        response = "1. First item\n2. Second item"
        items = scorer._parse_knowledge_items(response, 0, "user")
        assert len(items) == 2

        # Test format with parenthesis
        response = "1) First item\n2) Second item"
        items = scorer._parse_knowledge_items(response, 0, "user")
        assert len(items) == 2

    def test_parse_knowledge_items_short_filtering(self):
        """Test filtering of short items."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        response = "1. Hi\n2. This is a longer item that should pass"
        items = scorer._parse_knowledge_items(response, 0, "user")
        assert len(items) == 1
        assert items[0].content == "This is a longer item that should pass"

    def test_parse_knowledge_items_empty_response(self):
        """Test parsing empty response."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        items = scorer._parse_knowledge_items("", 0, "user")
        assert len(items) == 0

        items = scorer._parse_knowledge_items("   ", 0, "user")
        assert len(items) == 0

    def test_parse_knowledge_items_confidence(self):
        """Test confidence value assignment."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        response = "1. Test knowledge item"
        items = scorer._parse_knowledge_items(response, 0, "user")
        assert len(items) == 1
        assert items[0].confidence == 0.8

    def test_parse_violations_lowercase_no(self):
        """Test parsing lowercase 'no' response - method no longer exists, testing knowledge parsing instead."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test knowledge parsing with "None" response
        items = scorer._parse_knowledge_items("none", 0, "user")
        assert len(items) == 0

        items = scorer._parse_knowledge_items("None", 0, "user")
        assert len(items) == 0

    def test_parse_violations_yes_empty(self):
        """Test parsing 'YES' with empty violations - method no longer exists, testing knowledge parsing instead."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test knowledge parsing with empty response
        items = scorer._parse_knowledge_items("", 0, "user")
        assert len(items) == 0

    def test_parse_violations_malformed(self):
        """Test parsing malformed violation response - method no longer exists, testing knowledge parsing instead."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test knowledge parsing with malformed response
        items = scorer._parse_knowledge_items("Maybe\n- Some knowledge", 0, "user")
        # Should parse numbered items if present
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_simple_retention_score_all_patterns(self):
        """Test all question patterns in _simple_retention_score."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        patterns = [
            "What is your name?",
            "Who are you?",
            "Where are you from?",
            "How old are you?",
            "What do you do?",
        ]

        for pattern in patterns:
            result = await scorer._simple_retention_score(pattern, "Ground truth")
            assert isinstance(result, ScoreWithReasoning)
            assert result.score == 0.3

        # Test default score
        result = await scorer._simple_retention_score("Normal response", "Ground truth")
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.7

    def test_evaluate_knowledge_retention_sync_exception(self):
        """Test score method with exception handling."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Mock async method to raise exception
        async def failing_async(*args, **kwargs):
            raise Exception("Test error")

        scorer._evaluate_knowledge_retention_async = failing_async

        # Use the public score method which handles exceptions
        score = scorer.score("prediction", "ground_truth", None)
        assert score == 0.0  # Should return 0.0 on exception

    def test_evaluate_knowledge_retention_sync_success(self):
        """Test score method successful execution."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Mock async method to return success
        async def successful_async(*args, **kwargs):
            from novaeval.scorers.conversational import ScoreWithReasoning

            return ScoreWithReasoning(score=8.0, reasoning="Good retention")

        scorer._evaluate_knowledge_retention_async = successful_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 8.0  # Score is on 1-10 scale

    def test_generate_reasoning_all_score_ranges(self):
        """Test _generate_reasoning for all score ranges - method no longer exists, testing evaluate instead."""
        model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model)

        # Test evaluate method which generates reasoning
        from novaeval.scorers.conversational import ScoreWithReasoning

        # Mock the async method to return different scores
        async def mock_async(pred, gt, ctx):
            return ScoreWithReasoning(score=9.5, reasoning="Excellent retention")

        scorer._evaluate_knowledge_retention_async = mock_async

        result = scorer.score("output", "ground truth", None)
        assert isinstance(result, float)
        assert 1.0 <= result <= 10.0

    def test_evaluate_with_conversation_no_knowledge_items(self):
        """Test evaluate when knowledge extraction returns empty list."""
        model = MockLLMModel(["None", "NO"])  # No knowledge items extracted
        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hello"),
            ]
        )

        result = scorer.score(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # With no knowledge items, should return -1.0
        assert result == -1.0

    def test_evaluate_with_violations_calculation(self):
        """Test retention score calculation with violations."""
        model = MockLLMModel(
            [
                "1. User name is John\n2. User is 25 years old",
                '{"score": 4, "reasoning": "Moderate retention with some violations"}',
            ]
        )
        scorer = KnowledgeRetentionScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hi, I'm John and I'm 25"),
            ]
        )

        result = scorer.score(
            "What's your name?", "Question", {"conversation": conversation}
        )
        # Score should be reduced due to violation (scores are on 1-10 scale)
        assert 1.0 <= result <= 10.0
        assert result < 10.0  # Should be less than perfect score


class TestConversationRelevancyScorer:
    """Test cases for ConversationRelevancyScorer."""

    def test_init(self):
        """Test scorer initialization."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model, window_size=3)
        assert scorer.name == "Conversation Relevancy"
        assert scorer.window_size == 3

    def test_score_with_sliding_window(self):
        """Test scoring with sliding window context."""
        model = MockLLMModel(
            '{"score": 8, "reasoning": "Highly relevant"}'
        )  # Mock relevancy score
        scorer = ConversationRelevancyScorer(model, window_size=2)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Tell me about Python"),
                ConversationTurn(
                    speaker="assistant", message="Python is a programming language"
                ),
                ConversationTurn(speaker="user", message="What about data science?"),
                ConversationTurn(
                    speaker="assistant", message="Previous response should be evaluated"
                ),
            ]
        )

        context = {"conversation": conversation}
        score = scorer.score(
            "Python is great for data science", "What about data science?", context
        )
        assert isinstance(score, float)
        # Scores are on 1-10 scale
        assert 1.0 <= score <= 10.0

    def test_simple_relevancy_score_fallback(self):
        """Test fallback to simple relevancy scoring."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        # Test word overlap
        score = scorer.score("Python programming", "Learn Python", None)
        assert score > 0.0  # Should have some overlap

        # Test no overlap
        score = scorer.score("Cooking recipes", "Math problems", None)
        assert score >= 0.0

    def test_parse_relevancy_score(self):
        """Test relevancy score parsing - method no longer exists, testing parse_score_with_reasoning instead."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        result = parse_score_with_reasoning('{"score": 5, "reasoning": "Good"}')
        assert result.score == 5.0

        result = parse_score_with_reasoning('{"score": 3, "reasoning": "Moderate"}')
        assert result.score == 3.0

        # Test fallback parsing
        result = parse_score_with_reasoning("Score: 4")
        assert isinstance(result.score, float)
        assert 1.0 <= result.score <= 10.0

    def test_build_context_summary(self):
        """Test context summary building."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        turns = [
            ConversationTurn(speaker="user", message="Hello"),
            ConversationTurn(speaker="assistant", message="Hi there"),
        ]

        summary = scorer._build_context_summary(turns)
        assert "user: Hello" in summary
        assert "assistant: Hi there" in summary

    @pytest.mark.asyncio
    async def test_input_validation_non_string_types(self):
        """Test input validation with non-string types."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        result = await scorer.evaluate("input", 123, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", "", None)
        assert result.score == 0.0
        assert not result.passed

    @pytest.mark.asyncio
    async def test_evaluate_relevancy_async_no_context(self):
        """Test _evaluate_relevancy_async without conversation context."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        result = await scorer._evaluate_relevancy_async(
            "Response", "Ground truth", None
        )
        assert isinstance(result, ScoreWithReasoning)
        # Fallback uses word overlap which returns normalized score
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_relevancy_async_empty_turns(self):
        """Test _evaluate_relevancy_async with empty relevant_turns."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        conversation = Conversation(turns=[])
        result = await scorer._evaluate_relevancy_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        assert isinstance(result, ScoreWithReasoning)
        # Should use fallback scoring
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_relevancy_async_malformed_conversation(self):
        """Test _evaluate_relevancy_async with malformed conversation."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        result = await scorer._evaluate_relevancy_async(
            "Response", "Ground truth", {"conversation": "not a Conversation"}
        )
        assert isinstance(result, ScoreWithReasoning)
        # Should use fallback scoring
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_relevancy_async_window_size(self):
        """Test sliding window boundary cases."""
        model = MockLLMModel('{"score": 7, "reasoning": "Good relevancy"}')
        scorer = ConversationRelevancyScorer(model, window_size=3)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message=f"Message {i}")
                for i in range(10)
            ]
        )

        result = await scorer._evaluate_relevancy_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        assert isinstance(result, ScoreWithReasoning)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_relevancy_async_model_exception(self):
        """Test _evaluate_relevancy_async with model exceptions."""
        model = MockLLMModel()

        async def failing_generate(*args, **kwargs):
            raise Exception("Model error")

        model.generate = failing_generate

        scorer = ConversationRelevancyScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hello"),
            ]
        )

        result = await scorer._evaluate_relevancy_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # With only one turn, relevant_turns is empty, so falls back to simple score
        # "Response" and "Ground truth" have no word overlap, so returns 0.0
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.0  # Falls back to simple score with no overlap

    def test_parse_relevancy_score_edge_cases(self):
        """Test parse_score_with_reasoning edge cases."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        # Test JSON parsing
        result = parse_score_with_reasoning('{"score": 2, "reasoning": "Test"}')
        assert result.score == 2.0

        # Test all valid scores
        for i in range(1, 11):
            result = parse_score_with_reasoning(
                f'{{"score": {i}, "reasoning": "Test"}}'
            )
            assert result.score == float(i)

    @pytest.mark.asyncio
    async def test_simple_relevancy_score_edge_cases(self):
        """Test _simple_relevancy_score edge cases."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        # Test empty sets
        result = await scorer._simple_relevancy_score("", "")
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.0

        # Test word overlap calculation
        result = await scorer._simple_relevancy_score(
            "Python programming language", "Python language"
        )
        assert isinstance(result, ScoreWithReasoning)
        assert 0.0 <= result.score <= 1.0
        assert result.score > 0.0  # Should have overlap

    def test_evaluate_relevancy_sync_exception(self):
        """Test score method with exception handling."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        async def failing_async(*args, **kwargs):
            raise Exception("Test error")

        scorer._evaluate_relevancy_async = failing_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 0.0  # Should return 0.0 on exception

    def test_evaluate_relevancy_sync_success(self):
        """Test score method successful execution."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        async def successful_async(*args, **kwargs):
            from novaeval.scorers.conversational import ScoreWithReasoning

            return ScoreWithReasoning(score=8.5, reasoning="Good relevancy")

        scorer._evaluate_relevancy_async = successful_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 8.5  # Score is on 1-10 scale

    def test_generate_relevancy_reasoning_all_score_ranges(self):
        """Test _generate_relevancy_reasoning for all score ranges - method no longer exists, testing evaluate instead."""
        model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model)

        # Test evaluate method which generates reasoning
        from novaeval.scorers.conversational import ScoreWithReasoning

        # Mock the async method to return different scores
        async def mock_async(pred, gt, ctx):
            return ScoreWithReasoning(score=9.5, reasoning="Excellent relevancy")

        scorer._evaluate_relevancy_async = mock_async

        result = scorer.score("output", "ground truth", None)
        assert isinstance(result, float)
        assert 1.0 <= result <= 10.0


class TestConversationCompletenessScorer:
    """Test cases for ConversationCompletenessScorer."""

    def test_init(self):
        """Test scorer initialization."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)
        assert scorer.name == "Conversation Completeness"

    def test_score_with_intention_analysis(self):
        """Test scoring with user intention analysis."""
        mock_responses = [
            "1. Learn about Python basics\n2. Get programming help",  # Intentions
            '{"score": 8, "reasoning": "Well fulfilled"}',  # Fulfillment score
        ]
        model = MockLLMModel(mock_responses)
        scorer = ConversationCompletenessScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(
                    speaker="user", message="I want to learn Python basics"
                ),
                ConversationTurn(
                    speaker="assistant",
                    message="Here's a comprehensive Python guide...",
                ),
            ]
        )

        context = {"conversation": conversation}
        score = scorer.score("Great explanation", "How did I do?", context)
        assert isinstance(score, float)
        # Scores are on 1-10 scale
        assert 1.0 <= score <= 10.0

    def test_simple_completeness_score_fallback(self):
        """Test fallback to simple completeness scoring."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        # Test very short response
        score = scorer.score("OK", "Question", None)
        assert score == 0.2

        # Test apologetic response
        score = scorer.score("Sorry, I can't help with that", "Question", None)
        assert score == 0.4

        # Test substantial response
        score = scorer.score(
            "Here is a detailed explanation of the topic", "Question", None
        )
        assert score == 0.7

    def test_parse_intentions(self):
        """Test intention parsing."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        # Test with intentions
        response = (
            "1. Learn programming\n2. Get help with coding\n3. Understand concepts"
        )
        intentions = scorer._parse_intentions(response)
        assert len(intentions) == 3
        assert "Learn programming" in intentions

        # Test no intentions
        response = "None"
        intentions = scorer._parse_intentions(response)
        assert len(intentions) == 0

    def test_parse_fulfillment_score(self):
        """Test fulfillment score parsing - method no longer exists, testing parse_score_with_reasoning instead."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        result = parse_score_with_reasoning('{"score": 5, "reasoning": "Good"}')
        assert result.score == 5.0

        result = parse_score_with_reasoning('{"score": 2, "reasoning": "Poor"}')
        assert result.score == 2.0

        # Test fallback parsing
        result = parse_score_with_reasoning("Score: 4")
        assert isinstance(result.score, float)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_input_validation_non_string_types(self):
        """Test input validation with non-string types."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        result = await scorer.evaluate("input", 123, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", "", None)
        assert result.score == 0.0
        assert not result.passed

    @pytest.mark.asyncio
    async def test_evaluate_completeness_async_no_context(self):
        """Test _evaluate_completeness_async without conversation context."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        result = await scorer._evaluate_completeness_async(
            "Response", "Ground truth", None
        )
        assert isinstance(result, ScoreWithReasoning)
        # Fallback uses simple heuristics which return normalized scores
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_completeness_async_empty_intentions(self):
        """Test _evaluate_completeness_async with empty intentions."""
        model = MockLLMModel("None")
        scorer = ConversationCompletenessScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hello"),
            ]
        )

        result = await scorer._evaluate_completeness_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # Should return ScoreWithReasoning with score -1.0 when no intentions
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == -1.0

    @pytest.mark.asyncio
    async def test_evaluate_completeness_async_no_assistant_responses(self):
        """Test _evaluate_completeness_async with no assistant responses."""
        model = MockLLMModel(["1. Intention", '{"score": 6, "reasoning": "Moderate"}'])
        scorer = ConversationCompletenessScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hello"),
            ]
        )

        result = await scorer._evaluate_completeness_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        assert isinstance(result, ScoreWithReasoning)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_completeness_async_malformed_conversation(self):
        """Test _evaluate_completeness_async with malformed conversation."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        result = await scorer._evaluate_completeness_async(
            "Response", "Ground truth", {"conversation": "not a Conversation"}
        )
        assert isinstance(result, ScoreWithReasoning)
        # Should use fallback scoring
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_completeness_async_model_exception(self):
        """Test _evaluate_completeness_async with model exceptions."""
        model = MockLLMModel()

        async def failing_generate(*args, **kwargs):
            raise Exception("Model error")

        model.generate = failing_generate

        scorer = ConversationCompletenessScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="Hello"),
            ]
        )

        result = await scorer._evaluate_completeness_async(
            "Response", "Ground truth", {"conversation": conversation}
        )
        # When intention extraction fails, no intentions are found, so returns -1.0
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == -1.0  # No intentions to fulfill when extraction fails

    def test_parse_intentions_empty_response(self):
        """Test parsing empty intention response."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        intentions = scorer._parse_intentions("")
        assert len(intentions) == 0

        intentions = scorer._parse_intentions("   ")
        assert len(intentions) == 0

    def test_parse_fulfillment_score_edge_cases(self):
        """Test parse_score_with_reasoning edge cases."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        # Test all valid scores
        for i in range(1, 11):
            result = parse_score_with_reasoning(
                f'{{"score": {i}, "reasoning": "Test"}}'
            )
            assert result.score == float(i)

    @pytest.mark.asyncio
    async def test_simple_completeness_score_edge_cases(self):
        """Test _simple_completeness_score edge cases."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        # Test very short response
        result = await scorer._simple_completeness_score("OK", "Question")
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.2

        # Test apologetic response variants
        result = await scorer._simple_completeness_score(
            "Sorry, I can't help", "Question"
        )
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.4

        result = await scorer._simple_completeness_score(
            "I can't help with that", "Question"
        )
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.4

        # Test substantial response
        result = await scorer._simple_completeness_score(
            "Here is a detailed explanation", "Question"
        )
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.7

    def test_evaluate_completeness_sync_exception(self):
        """Test score method with exception handling."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        async def failing_async(*args, **kwargs):
            raise Exception("Test error")

        scorer._evaluate_completeness_async = failing_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 0.0  # Should return 0.0 on exception

    def test_evaluate_completeness_sync_success(self):
        """Test score method successful execution."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        async def successful_async(*args, **kwargs):
            from novaeval.scorers.conversational import ScoreWithReasoning

            return ScoreWithReasoning(score=9.0, reasoning="Well fulfilled")

        scorer._evaluate_completeness_async = successful_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 9.0  # Score is on 1-10 scale

    def test_generate_completeness_reasoning_all_score_ranges(self):
        """Test _generate_completeness_reasoning for all score ranges - method no longer exists, testing evaluate instead."""
        model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model)

        # Test evaluate method which generates reasoning
        from novaeval.scorers.conversational import ScoreWithReasoning

        # Mock the async method to return different scores
        async def mock_async(pred, gt, ctx):
            return ScoreWithReasoning(score=9.5, reasoning="Excellent completeness")

        scorer._evaluate_completeness_async = mock_async

        result = scorer.score("output", "ground truth", None)
        assert isinstance(result, float)
        assert 1.0 <= result <= 10.0


class TestRoleAdherenceScorer:
    """Test cases for RoleAdherenceScorer."""

    def test_init(self):
        """Test scorer initialization."""
        model = MockLLMModel()
        scorer = RoleAdherenceScorer(model, expected_role="helpful assistant")
        assert scorer.name == "Role Adherence"
        assert scorer.expected_role == "helpful assistant"

    def test_score_with_role_context(self):
        """Test scoring with role context."""
        model = MockLLMModel(
            '{"score": 8, "reasoning": "Good adherence"}'
        )  # Mock role adherence score
        scorer = RoleAdherenceScorer(model, expected_role="math tutor")

        conversation = Conversation(
            turns=[ConversationTurn(speaker="user", message="Help with math")],
            context="You are a helpful math tutor",
        )

        context = {"conversation": conversation}
        score = scorer.score("Let me help you with algebra", "Math question", context)
        assert isinstance(score, float)
        # Scores are on 1-10 scale
        assert 1.0 <= score <= 10.0

    def test_score_no_role_defined(self):
        """Test scoring when no role is defined."""
        model = MockLLMModel()
        scorer = RoleAdherenceScorer(model)

        score = scorer.score("Any response", "Question", None)
        assert score == -1.0  # Perfect adherence when no role defined

    def test_parse_role_score(self):
        """Test role score parsing - method no longer exists, testing parse_score_with_reasoning instead."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        result = parse_score_with_reasoning('{"score": 4, "reasoning": "Good"}')
        assert result.score == 4.0

        result = parse_score_with_reasoning('{"score": 2, "reasoning": "Poor"}')
        assert result.score == 2.0

        # Test fallback parsing
        result = parse_score_with_reasoning("Score: 4")
        assert isinstance(result.score, float)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_input_validation_non_string_types(self):
        """Test input validation with non-string types."""
        model = MockLLMModel()
        scorer = RoleAdherenceScorer(model)

        result = await scorer.evaluate("input", 123, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", "", None)
        assert result.score == 0.0
        assert not result.passed

    @pytest.mark.asyncio
    async def test_evaluate_role_adherence_async_no_role(self):
        """Test _evaluate_role_adherence_async with no role defined."""
        model = MockLLMModel()
        scorer = RoleAdherenceScorer(model)

        result = await scorer._evaluate_role_adherence_async("Response", None)
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == -1.0  # Perfect adherence when no role defined

    @pytest.mark.asyncio
    async def test_evaluate_role_adherence_async_from_constructor(self):
        """Test _evaluate_role_adherence_async with role from constructor."""
        model = MockLLMModel('{"score": 8, "reasoning": "Good adherence"}')
        scorer = RoleAdherenceScorer(model, expected_role="math tutor")

        result = await scorer._evaluate_role_adherence_async("Response", None)
        assert isinstance(result, ScoreWithReasoning)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_role_adherence_async_from_conversation(self):
        """Test _evaluate_role_adherence_async with role from conversation.context."""
        model = MockLLMModel('{"score": 9, "reasoning": "Excellent adherence"}')
        scorer = RoleAdherenceScorer(model)

        conversation = Conversation(
            turns=[ConversationTurn(speaker="user", message="Hello")],
            context="You are a helpful assistant",
        )

        result = await scorer._evaluate_role_adherence_async(
            "Response", {"conversation": conversation}
        )
        assert isinstance(result, ScoreWithReasoning)
        assert 1.0 <= result.score <= 10.0

    @pytest.mark.asyncio
    async def test_evaluate_role_adherence_async_model_exception(self):
        """Test _evaluate_role_adherence_async with model exceptions."""
        model = MockLLMModel()

        async def failing_generate(*args, **kwargs):
            raise Exception("Model error")

        model.generate = failing_generate

        scorer = RoleAdherenceScorer(model, expected_role="tutor")

        result = await scorer._evaluate_role_adherence_async("Response", None)
        assert isinstance(result, ScoreWithReasoning)
        assert result.score == 0.5  # Default score on exception

    def test_parse_role_score_edge_cases(self):
        """Test parse_score_with_reasoning edge cases."""
        from novaeval.scorers.conversational import parse_score_with_reasoning

        # Test all valid scores
        for i in range(1, 11):
            result = parse_score_with_reasoning(
                f'{{"score": {i}, "reasoning": "Test"}}'
            )
            assert result.score == float(i)

    def test_evaluate_role_adherence_sync_exception(self):
        """Test score method with exception handling."""
        model = MockLLMModel()
        scorer = RoleAdherenceScorer(model)

        async def failing_async(*args, **kwargs):
            raise Exception("Test error")

        scorer._evaluate_role_adherence_async = failing_async

        score = scorer.score("prediction", "ground_truth", None)
        assert score == 0.0  # Should return 0.0 on exception


class TestConversationalMetricsScorer:
    """Test cases for ConversationalMetricsScorer."""

    def test_init(self):
        """Test scorer initialization."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)
        assert scorer.name == "Conversational Metrics"
        assert hasattr(scorer, "knowledge_scorer")
        assert hasattr(scorer, "relevancy_scorer")
        assert hasattr(scorer, "completeness_scorer")
        assert hasattr(scorer, "role_scorer")

    def test_init_selective_metrics(self):
        """Test initialization with selective metrics."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(
            model,
            include_knowledge_retention=True,
            include_relevancy=False,
            include_completeness=True,
            include_role_adherence=False,
        )

        assert hasattr(scorer, "knowledge_scorer")
        assert not hasattr(scorer, "relevancy_scorer")
        assert hasattr(scorer, "completeness_scorer")
        assert not hasattr(scorer, "role_scorer")

    def test_score_all_metrics(self):
        """Test scoring with all metrics enabled."""
        # Mock responses for all individual scorers
        mock_responses = [
            "1. User info",
            '{"score": 8, "reasoning": "Good retention"}',  # Knowledge retention
            '{"score": 7, "reasoning": "Good relevancy"}',  # Relevancy
            "1. Help with task",
            '{"score": 9, "reasoning": "Well fulfilled"}',  # Completeness
            '{"score": 8, "reasoning": "Good adherence"}',  # Role adherence
        ]
        model = MockLLMModel(mock_responses)
        scorer = ConversationalMetricsScorer(model)

        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="I like AI"),
                ConversationTurn(speaker="assistant", message="Great!"),
                ConversationTurn(speaker="user", message="Tell me more"),
            ],
            context="You are a helpful AI assistant",
        )

        context = {"conversation": conversation}
        scores = scorer.score("AI is fascinating", "Tell me more", context)

        assert isinstance(scores, dict)
        assert "overall" in scores
        assert "knowledge_retention" in scores
        assert "relevancy" in scores
        assert "completeness" in scores
        assert "role_adherence" in scores

        # All scores should be between -1 and 10 (allow -1.0 for defaults)
        for score in scores.values():
            assert -1.0 <= score <= 10.0

    def test_score_partial_metrics(self):
        """Test scoring with partial metrics enabled."""
        model = MockLLMModel(
            ['{"score": 8, "reasoning": "Good"}', '{"score": 7, "reasoning": "Good"}']
        )  # Mock responses
        scorer = ConversationalMetricsScorer(
            model,
            include_knowledge_retention=True,
            include_relevancy=False,
            include_completeness=True,
            include_role_adherence=False,
        )

        scores = scorer.score("Response", "Question", None)
        assert isinstance(scores, dict)
        assert "overall" in scores
        assert "knowledge_retention" in scores
        assert "completeness" in scores
        assert "relevancy" not in scores
        assert "role_adherence" not in scores
        # Scores can be on 1-10 scale (from LLM) or normalized (from fallback)
        for score in scores.values():
            assert 0.0 <= score <= 10.0

    @pytest.mark.asyncio
    async def test_input_validation_non_string_types(self):
        """Test input validation with non-string types."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)

        result = await scorer.evaluate("input", 123, None)
        assert result.score == 0.0
        assert not result.passed

        result = await scorer.evaluate("input", "", None)
        assert result.score == 0.0
        assert not result.passed

    @pytest.mark.asyncio
    async def test_evaluate_with_exception_handling(self):
        """Test exception handling when individual scorers fail."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)

        # Mock one scorer to raise exception
        async def failing_evaluate(*args, **kwargs):
            raise Exception("Scorer error")

        scorer.knowledge_scorer.evaluate = failing_evaluate

        result = await scorer.evaluate("input", "output", None)
        # Should handle exception and continue with other scorers
        assert isinstance(result, ScoreResult)
        assert 0.0 <= result.score <= 1.0

    def test_generate_combined_reasoning(self):
        """Test _generate_combined_reasoning with various score combinations."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)

        # Test high scores (on 1-10 scale)
        scores = {"knowledge_retention": 9.0, "relevancy": 9.5}
        results = {
            "knowledge_retention": ScoreResult(score=9.0, passed=True, reasoning=""),
            "relevancy": ScoreResult(score=9.5, passed=True, reasoning=""),
        }
        reasoning = scorer._generate_combined_reasoning(scores, results)
        assert (
            "9.25" in reasoning
            or "9.2" in reasoning
            or "Knowledge Retention" in reasoning
        )

        # Test low scores
        scores = {"knowledge_retention": 3.0, "relevancy": 2.0}
        results = {
            "knowledge_retention": ScoreResult(score=3.0, passed=False, reasoning=""),
            "relevancy": ScoreResult(score=2.0, passed=False, reasoning=""),
        }
        reasoning = scorer._generate_combined_reasoning(scores, results)
        assert (
            "2.50" in reasoning
            or "2.5" in reasoning
            or "Knowledge Retention" in reasoning
        )

        # Test empty scores
        reasoning = scorer._generate_combined_reasoning({}, {})
        assert "0.00" in reasoning or "0.0" in reasoning

    def test_score_with_all_metrics_empty_result(self):
        """Test score method with empty result."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)

        # Mock evaluate to return result without individual_scores
        async def mock_evaluate(*args, **kwargs):
            return ScoreResult(score=0.5, passed=False, reasoning="", metadata={})

        scorer.evaluate = mock_evaluate

        scores = scorer.score("prediction", "ground_truth", None)
        assert isinstance(scores, dict)
        assert "overall" in scores


class TestModelIntegration:
    """Test model integration with sync/async generate methods."""

    def test_model_without_name_attribute(self):
        """Test scorer with model without name attribute."""

        class ModelWithoutName:
            async def generate(self, prompt, **kwargs):
                return "response"

        model = ModelWithoutName()
        scorer = KnowledgeRetentionScorer(model)

        result = scorer.score("prediction", "ground_truth", None)
        assert isinstance(result, float)

    def test_model_with_sync_generate(self):
        """Test scorer with synchronous generate method."""

        class SyncModel:
            def generate(self, prompt, **kwargs):
                return "sync response"

        model = SyncModel()
        scorer = KnowledgeRetentionScorer(model)

        # Should handle sync generate
        conversation = Conversation(
            turns=[ConversationTurn(speaker="user", message="Hello")]
        )
        result = scorer.score(
            "prediction", "ground_truth", {"conversation": conversation}
        )
        assert isinstance(result, float)

    def test_model_without_generate_method(self):
        """Test scorer with model without generate method."""

        class ModelWithoutGenerate:
            pass

        model = ModelWithoutGenerate()
        scorer = KnowledgeRetentionScorer(model)

        # Should handle gracefully
        conversation = Conversation(
            turns=[ConversationTurn(speaker="user", message="Hello")]
        )
        result = scorer.score(
            "prediction", "ground_truth", {"conversation": conversation}
        )
        assert isinstance(result, float)


class TestInputValidation:
    """Test input validation across all scorers."""

    def test_validate_inputs(self):
        """Test input validation for all scorers."""
        model = MockLLMModel()
        scorers = [
            KnowledgeRetentionScorer(model),
            ConversationRelevancyScorer(model),
            ConversationCompletenessScorer(model),
            RoleAdherenceScorer(model),
        ]

        for scorer in scorers:
            # Test empty strings
            assert scorer.score("", "ground_truth", {}) == 0.0
            assert scorer.score("prediction", "", {}) == 0.0

            # Test whitespace only
            assert scorer.score("   ", "ground_truth", {}) == 0.0
            assert scorer.score("prediction", "   ", {}) == 0.0


class TestConversationalScorerIntegration:
    """Integration tests for conversational scorers."""

    def test_complete_conversation_flow(self):
        """Test a complete conversation evaluation flow."""
        mock_responses = [
            "1. User is learning Python\n2. User wants to build web apps",  # Knowledge extraction
            '{"score": 8, "reasoning": "Good retention"}',  # Knowledge retention
            '{"score": 7, "reasoning": "Good relevancy"}',  # Relevancy score
            "1. Learn Python\n2. Build web applications",  # Intentions
            '{"score": 9, "reasoning": "Well fulfilled"}',  # Completeness
            '{"score": 8, "reasoning": "Good adherence"}',  # Role adherence
        ]
        model = MockLLMModel(mock_responses)

        # Test individual scorers
        conversation = Conversation(
            turns=[
                ConversationTurn(
                    speaker="user", message="I'm learning Python to build web apps"
                ),
                ConversationTurn(
                    speaker="assistant",
                    message="Great! Let me guide you through web development",
                ),
                ConversationTurn(
                    speaker="user", message="What framework should I use?"
                ),
            ],
            context="You are a helpful programming mentor",
        )

        context = {"conversation": conversation}

        # Test knowledge retention
        kr_scorer = KnowledgeRetentionScorer(model)
        kr_score = kr_scorer.score(
            "I recommend Django or Flask for Python web development",
            "What framework?",
            context,
        )
        assert 1.0 <= kr_score <= 10.0

        # Test comprehensive metrics
        comp_scorer = ConversationalMetricsScorer(model)
        comp_scores = comp_scorer.score(
            "Django is great for beginners", "What framework?", context
        )
        assert isinstance(comp_scores, dict)
        assert "overall" in comp_scores

    def test_poor_conversation_scoring(self):
        """Test scoring a poor conversation scenario."""
        conversation = Conversation(
            turns=[
                ConversationTurn(speaker="user", message="What's the weather like?"),
                ConversationTurn(speaker="assistant", message="I like ice cream"),
                ConversationTurn(
                    speaker="user", message="That doesn't answer my question"
                ),
                ConversationTurn(
                    speaker="assistant", message="Purple is my favorite color"
                ),
            ],
            context="You are a helpful weather assistant",
        )

        # Mock very poor-quality responses - make them worse to ensure low scores
        mock_responses = [
            "1. User asked about weather",
            '{"score": 2, "reasoning": "Very poor retention"}',  # Very poor knowledge retention
            '{"score": 1, "reasoning": "Not relevant"}',  # Very poor relevancy
            "1. Get weather information",
            '{"score": 2, "reasoning": "Poor fulfillment"}',  # Very poor fulfillment
            '{"score": 1, "reasoning": "Poor adherence"}',  # Very poor role adherence
        ]
        model = MockLLMModel(mock_responses)

        scorer = ConversationalMetricsScorer(model)
        context = {"conversation": conversation}

        scores = scorer.score("Purple is nice", "Weather question", context)

        # Should get low scores across the board (scores are on 1-10 scale, or -1.0 for defaults)
        # Overall should be average of individual scores, which would be around 1.5
        assert scores["overall"] < 7.0  # Poor overall performance (on 1-10 scale)
        assert all(-1.0 <= score <= 10.0 for score in scores.values())

    def test_edge_case_empty_conversation(self):
        """Test edge case with empty conversation."""
        model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model)

        conversation = Conversation(turns=[])
        context = {"conversation": conversation}

        scores = scorer.score("Response", "Question", context)
        assert isinstance(scores, dict)
        assert "overall" in scores


class TestConversationalCoverage:
    """Additional tests to improve conversational.py coverage."""

    def test_knowledge_retention_scorer_initialization(self):
        """Test KnowledgeRetentionScorer initialization."""
        mock_model = MockLLMModel()
        scorer = KnowledgeRetentionScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "Knowledge Retention"

    def test_conversation_relevancy_scorer_initialization(self):
        """Test ConversationRelevancyScorer initialization."""
        mock_model = MockLLMModel()
        scorer = ConversationRelevancyScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "Conversation Relevancy"

    def test_conversation_completeness_scorer_initialization(self):
        """Test ConversationCompletenessScorer initialization."""
        mock_model = MockLLMModel()
        scorer = ConversationCompletenessScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "Conversation Completeness"

    def test_role_adherence_scorer_initialization(self):
        """Test RoleAdherenceScorer initialization."""
        mock_model = MockLLMModel()
        scorer = RoleAdherenceScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "Role Adherence"

    def test_conversational_metrics_scorer_initialization(self):
        """Test ConversationalMetricsScorer initialization."""
        mock_model = MockLLMModel()
        scorer = ConversationalMetricsScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "Conversational Metrics"
