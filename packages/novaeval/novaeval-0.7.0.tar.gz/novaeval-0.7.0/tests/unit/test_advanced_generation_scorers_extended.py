"""
Extended tests for advanced generation scorers to improve coverage.
Focuses on edge cases, error handling, and fallback logic.
"""

from unittest.mock import Mock, patch

import pytest

from src.novaeval.scorers.advanced_generation_scorers import (
    AnswerCompletenessScorer,
    BiasDetectionScorer,
    CitationQualityScorer,
    ClaimVerificationScorer,
    ClarityAndCoherenceScorer,
    ConflictResolutionScorer,
    ContextCompletenessScorer,
    ContextConsistencyScorer,
    ContextFaithfulnessScorerPP,
    ContextGroundednessScorer,
    ContextPrioritizationScorer,
    CrossContextSynthesisScorer,
    FactualAccuracyScorer,
    HallucinationDetectionScorer,
    InformationDensityScorer,
    QuestionAnswerAlignmentScorer,
    RAGAnswerQualityScorer,
    SourceAttributionScorer,
    TechnicalAccuracyScorer,
    TerminologyConsistencyScorer,
    ToneConsistencyScorer,
)
from src.novaeval.scorers.base import ScoreResult


class TestBiasDetectionScorerExtended:
    def test_init_with_custom_params(self):
        model = Mock()
        scorer = BiasDetectionScorer(model, threshold=10.0)
        assert scorer.threshold == 10.0
        assert scorer.model == model

    @pytest.mark.asyncio
    async def test_evaluate_empty_output(self):
        model = Mock()
        scorer = BiasDetectionScorer(model)

        result = await scorer.evaluate("input", "")
        assert result.score == 0.0
        assert result.passed is False
        assert "No answer provided" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_json_decode_error_fallback(self):
        model = Mock()
        scorer = BiasDetectionScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="invalid json response with quality score 7",
        ):
            result = await scorer.evaluate("input", "output")

            # Prompt now asks for quality directly (no inversion)
            # Fallback parsing extracts number 7 as quality score
            expected_quality = 7.0
            assert result.score == pytest.approx(expected_quality, rel=1e-3)

    @pytest.mark.asyncio
    async def test_evaluate_no_numbers_in_response(self):
        model = Mock()
        scorer = BiasDetectionScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="no numbers here",
        ):
            result = await scorer.evaluate("input", "output")

            # Should return error state -1.0 when no numbers found
            assert result.score == -1.0
            assert result.passed is False

    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        model = Mock()
        scorer = BiasDetectionScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            result = await scorer.evaluate("input", "output")

            # Exception should return error state -1.0
            assert result.score == -1.0
            assert result.passed is False
            assert "Exception:" in result.reasoning

    def test_score_method_sync(self):
        model = Mock()
        scorer = BiasDetectionScorer(model)

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = ScoreResult(
                score=8.0, passed=True, reasoning="Test", metadata={}
            )

            result = scorer.score("prediction", "ground_truth", {"context": "test"})
            assert result.score == 8.0


class TestFactualAccuracyScorer:
    @pytest.mark.asyncio
    async def test_evaluate_no_context(self):
        model = Mock()
        scorer = FactualAccuracyScorer(model)

        result = await scorer.evaluate("input", "output")
        assert result.score == 0.0
        assert "No answer or context provided" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        model = Mock()
        scorer = FactualAccuracyScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            result = await scorer.evaluate("input", "output", context="context")

            # Exception should return error state -1.0
            assert result.score == -1.0
            assert "Error:" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_json_parsing_fallback(self):
        model = Mock()
        scorer = FactualAccuracyScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="accuracy score is 4",
        ):
            result = await scorer.evaluate("input", "output", context="context")

            # Should extract the number 4 as fallback (scores are 1-10 range)
            assert result.score == 4.0

    def test_score_method_sync(self):
        model = Mock()
        scorer = FactualAccuracyScorer(model)

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = ScoreResult(
                score=0.9, passed=True, reasoning="Test", metadata={}
            )

            result = scorer.score("prediction", "ground_truth", {"context": "test"})
            assert result.score == 0.9


class TestClaimVerificationScorer:
    @pytest.mark.asyncio
    async def test_evaluate_no_claims(self):
        model = Mock()
        scorer = ClaimVerificationScorer(model)

        # Test with empty output to trigger the no answer case
        result = await scorer.evaluate("input", "", context="context")

        assert result.score == 0.0
        assert "No answer provided" in result.reasoning

    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        model = Mock()
        scorer = ClaimVerificationScorer(model)

        with (
            patch(
                "src.novaeval.scorers.advanced_generation_scorers.parse_claims",
                return_value=["claim1"],
            ),
            patch(
                "src.novaeval.scorers.advanced_generation_scorers.call_llm",
                side_effect=Exception("API error"),
            ),
        ):
            result = await scorer.evaluate("input", "output", context="context")

            # Exception should return error state -1.0
            assert result.score == -1.0
            assert "Error:" in result.reasoning

    def test_score_method_sync(self):
        model = Mock()
        scorer = ClaimVerificationScorer(model)

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = ScoreResult(
                score=0.7, passed=True, reasoning="Test", metadata={}
            )

            result = scorer.score("prediction", "ground_truth", {"context": "test"})
            assert result.score == 0.7


class TestInformationDensityScorer:
    @pytest.mark.asyncio
    async def test_evaluate_with_valid_response(self):
        """Test that InformationDensityScorer handles valid JSON responses."""
        model = Mock()
        scorer = InformationDensityScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value='{"score": 4, "reasoning": "high density"}',
        ):
            result = await scorer.evaluate("input", "output")
            assert result.score == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_with_fallback_parsing(self):
        """Test that InformationDensityScorer handles text with numbers."""
        model = Mock()
        scorer = InformationDensityScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="The density rating is 3 out of 5",
        ):
            result = await scorer.evaluate("input", "output")
            # Should extract the last number (5)
            assert result.score == 5.0

    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        model = Mock()
        scorer = InformationDensityScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            result = await scorer.evaluate("input", "output")

            # Exception should return error state -1.0
            assert result.score == -1.0
            assert "Exception:" in result.reasoning


class TestClarityAndCoherenceScorer:
    @pytest.mark.asyncio
    async def test_evaluate_with_valid_response(self):
        """Test that ClarityAndCoherenceScorer handles valid JSON responses."""
        model = Mock()
        scorer = ClarityAndCoherenceScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value='{"score": 5, "reasoning": "clear and coherent"}',
        ):
            result = await scorer.evaluate("input", "output")
            assert result.score == 5.0

    @pytest.mark.asyncio
    async def test_evaluate_with_fallback_parsing(self):
        """Test that ClarityAndCoherenceScorer handles text with numbers."""
        model = Mock()
        scorer = ClarityAndCoherenceScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="clarity: 3, coherence: 4",
        ):
            result = await scorer.evaluate("input", "output")
            # Should extract the last number (4)
            assert result.score == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        """Test exception handling."""
        model = Mock()
        scorer = ClarityAndCoherenceScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            result = await scorer.evaluate("input", "output")
            # Exception should return error state -1.0
            assert result.score == -1.0
            assert "Exception:" in result.reasoning


class TestConflictResolutionScorer:
    @pytest.mark.asyncio
    async def test_evaluate_single_chunk(self):
        model = Mock()
        scorer = ConflictResolutionScorer(model)

        context = "single chunk"
        result = await scorer.evaluate("input", "output", context=context)

        assert (
            result.score == 10.0
        )  # Perfect score for single chunk (no conflicts possible)
        assert "Single context provided" in result.reasoning


class TestToneConsistencyScorer:
    @pytest.mark.asyncio
    async def test_evaluate_with_valid_response(self):
        """Test that ToneConsistencyScorer handles valid JSON responses."""
        model = Mock()
        scorer = ToneConsistencyScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value='{"score": 4, "reasoning": "consistent tone"}',
        ):
            result = await scorer.evaluate("input", "output")
            assert result.score == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_with_fallback_parsing(self):
        """Test that ToneConsistencyScorer handles text with numbers."""
        model = Mock()
        scorer = ToneConsistencyScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="tone consistency: 3",
        ):
            result = await scorer.evaluate("input", "output")
            assert result.score == 3.0


class TestContextGroundednessScorer:
    @pytest.mark.asyncio
    async def test_evaluate_exception_handling(self):
        model = Mock()
        scorer = ContextGroundednessScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            result = await scorer.evaluate("input", "output", context="context")

            # Exception should return error state -1.0
            assert result.score == -1.0
            assert "Error:" in result.reasoning


class TestHallucinationDetectionScorer:
    @pytest.mark.asyncio
    async def test_evaluate_with_valid_response(self):
        """Test that HallucinationDetectionScorer handles valid JSON responses."""
        model = Mock()
        scorer = HallucinationDetectionScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value='{"score": 9, "reasoning": "excellent quality, no hallucinations"}',
        ):
            result = await scorer.evaluate("input", "output", context="context")
            # Prompt now asks for quality directly (no inversion)
            # Score 9 = high quality, minimal hallucinations
            assert result.score == 9.0

    @pytest.mark.asyncio
    async def test_evaluate_with_fallback_parsing(self):
        """Test that HallucinationDetectionScorer handles text with numbers."""
        model = Mock()
        scorer = HallucinationDetectionScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="quality score: 10",
        ):
            result = await scorer.evaluate("input", "output", context="context")
            # Prompt asks for quality, score 10 = perfect, no hallucinations
            assert result.score == 10.0


class TestQuestionAnswerAlignmentScorer:
    @pytest.mark.asyncio
    async def test_evaluate_with_valid_response(self):
        """Test that QuestionAnswerAlignmentScorer handles valid JSON responses."""
        model = Mock()
        scorer = QuestionAnswerAlignmentScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value='{"score": 4, "reasoning": "well aligned"}',
        ):
            result = await scorer.evaluate("input", "output")
            assert result.score == 4.0

    @pytest.mark.asyncio
    async def test_evaluate_with_fallback_parsing(self):
        """Test that QuestionAnswerAlignmentScorer handles text with numbers."""
        model = Mock()
        scorer = QuestionAnswerAlignmentScorer(model)

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            return_value="alignment: 3",
        ):
            result = await scorer.evaluate("input", "output")
            # Fallback parsing now correctly extracts the number 3 from "alignment: 3"
            assert result.score == 3.0


class TestCrossContextSynthesisScorer:
    @pytest.mark.asyncio
    async def test_evaluate_single_chunk(self):
        model = Mock()
        scorer = CrossContextSynthesisScorer(model)

        context = "single chunk"
        result = await scorer.evaluate("input", "output", context=context)

        assert result.score == 10.0  # Perfect score for single chunk (1-10 scale)
        assert "Single context provided" in result.reasoning


# Test edge cases and error handling
class TestAdvancedScorersErrorHandling:
    @pytest.mark.asyncio
    async def test_multiple_scorers_exception_handling(self):
        """Test that all scorers handle exceptions gracefully."""
        model = Mock()

        scorers = [
            BiasDetectionScorer(model),
            FactualAccuracyScorer(model),
            ClaimVerificationScorer(model),
            InformationDensityScorer(model),
            ClarityAndCoherenceScorer(model),
            ConflictResolutionScorer(model),
            ContextPrioritizationScorer(model),
            CitationQualityScorer(model),
            ToneConsistencyScorer(model),
            TerminologyConsistencyScorer(model),
            ContextFaithfulnessScorerPP(model),
            ContextGroundednessScorer(model),
            ContextCompletenessScorer(model),
            ContextConsistencyScorer(model),
            RAGAnswerQualityScorer(model),
            HallucinationDetectionScorer(model),
            SourceAttributionScorer(model),
            AnswerCompletenessScorer(model),
            QuestionAnswerAlignmentScorer(model),
            CrossContextSynthesisScorer(model),
            TechnicalAccuracyScorer(model),
        ]

        with patch(
            "src.novaeval.scorers.advanced_generation_scorers.call_llm",
            side_effect=Exception("API error"),
        ):
            for scorer in scorers:
                # Use multiple context chunks to force LLM call for all scorers
                # Some scorers return 10.0 for single context without calling LLM (1-10 scale)
                multi_context = "context1\n\ncontext2\n\ncontext3"
                result = await scorer.evaluate("input", "output", context=multi_context)
                # All scorers should handle exceptions gracefully
                assert hasattr(result, "score")  # Check it's a ScoreResult-like object

                # All scorers now return -1.0 error state on exception (no "neutral" defaults)
                assert result.score == -1.0
                assert result.passed is False


class TestAdvancedGenerationCoverage:
    """Additional tests to improve advanced_generation_scorers.py coverage."""

    def test_bias_detection_scorer_initialization(self):
        """Test BiasDetectionScorer initialization."""
        mock_model = Mock()
        scorer = BiasDetectionScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "BiasDetectionScorer"

    def test_factual_accuracy_scorer_initialization(self):
        """Test FactualAccuracyScorer initialization."""
        mock_model = Mock()
        scorer = FactualAccuracyScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "FactualAccuracyScorer"

    def test_clarity_coherence_scorer_initialization(self):
        """Test ClarityAndCoherenceScorer initialization."""
        mock_model = Mock()
        scorer = ClarityAndCoherenceScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "ClarityAndCoherenceScorer"

    def test_tone_consistency_scorer_initialization(self):
        """Test ToneConsistencyScorer initialization."""
        mock_model = Mock()
        scorer = ToneConsistencyScorer(model=mock_model)

        assert scorer.model == mock_model
        assert scorer.name == "ToneConsistencyScorer"

    def test_scorers_with_custom_params(self):
        """Test scorers with custom parameters."""
        mock_model = Mock()

        bias_scorer = BiasDetectionScorer(model=mock_model, threshold=8.0)
        assert bias_scorer.threshold == 8.0
        assert bias_scorer.name == "BiasDetectionScorer"

        factual_scorer = FactualAccuracyScorer(model=mock_model, threshold=0.9)
        assert factual_scorer.threshold == 0.9
        assert factual_scorer.name == "FactualAccuracyScorer"

        clarity_scorer = ClarityAndCoherenceScorer(model=mock_model, threshold=0.7)
        assert clarity_scorer.threshold == 0.7
        assert clarity_scorer.name == "ClarityAndCoherenceScorer"

        tone_scorer = ToneConsistencyScorer(model=mock_model, threshold=0.6)
        assert tone_scorer.threshold == 0.6
        assert tone_scorer.name == "ToneConsistencyScorer"
