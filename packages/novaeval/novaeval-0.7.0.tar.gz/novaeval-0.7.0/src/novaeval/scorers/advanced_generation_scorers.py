"""
Advanced Generation Evaluation Scorers for RAG.

This module implements sophisticated generation evaluation scorers specifically designed for RAG scenarios,
focusing on context-conditioned generation quality.

Key Features:
- Context-Aware Generation Scorers
- Hallucination Detection
- Answer Quality Enhancement
- Multi-Context Integration
- Domain-Specific Evaluation
"""

import json
from typing import Any, Optional, Union

from novaeval.scorers.base import BaseScorer, ScoreResult
from novaeval.scorers.rag_prompts import RAGPrompts
from novaeval.utils.json_parser import parse_llm_json_response
from novaeval.utils.llm import call_llm
from novaeval.utils.parsing import parse_claims


def _context_to_str(context: Optional[Union[str, dict[str, Any]]]) -> Optional[str]:
    """Convert context to string if it's a dict."""
    if context is None:
        return None
    if isinstance(context, dict):
        return json.dumps(context)
    return context


# CONTEXT-AWARE GENERATION SCORERS
class BiasDetectionScorer(BaseScorer):
    """
    Bias detection in generated content.
    """

    def __init__(self, model: Any, threshold: float = 8.0, **kwargs: Any) -> None:
        super().__init__(name="BiasDetectionScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_bias_detection_evaluation(
            input_text=input_text, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)  # Use shared parser

            # Get quality score directly from JSON (prompt now asks for quality, not bias level)
            quality_score = result.get("score", -1.0)
            reasoning = result.get("reasoning", "No reasoning provided")

            # Error check
            if quality_score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            # No inversion needed - prompt directly returns quality score (10=no bias, 1=major bias)
            passed = quality_score >= self.threshold

            # Store all extra fields in metadata
            metadata = {
                "bias_types": result.get("bias_types", []),
                "specific_examples": result.get("specific_examples", []),
                "confidence": result.get("confidence", 0.0),
            }

            return ScoreResult(
                score=quality_score,
                passed=passed,
                reasoning=f"Bias-free quality: {quality_score:.1f}/10. {reasoning}",
                metadata=metadata,
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


# HALLUCINATION DETECTION SCORERS
class FactualAccuracyScorer(BaseScorer):
    """
    Verify factual claims against contexts.
    """

    def __init__(self, model: Any, threshold: float = 8.0, **kwargs: Any) -> None:
        super().__init__(name="FactualAccuracyScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text or not context:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No answer or context provided",
                metadata={},
            )

        # Extract context intelligently (same as HallucinationDetectionScorer)
        context_str = ""
        if isinstance(context, dict):
            parts = []

            # Add KB retrieved context if available (HIGHEST PRIORITY - source of truth)
            if context.get("context"):
                kb_text = context["context"]
                if isinstance(kb_text, str) and kb_text.strip():
                    parts.append(f"Retrieved Knowledge Base Context:\n{kb_text}")

            # Add agent role/capabilities from system_prompt
            if context.get("system_prompt"):
                sys_prompt = context["system_prompt"]
                # Truncate if extremely long
                if isinstance(sys_prompt, str) and len(sys_prompt) > 2000:
                    sys_prompt = sys_prompt[:2000] + "... (truncated)"
                parts.append(f"Agent Role & Capabilities:\n{sys_prompt}")

            # Add full conversation for context
            if context.get("full_conversation"):
                conv = context["full_conversation"]
                recent = conv[-10:] if len(conv) > 10 else conv
                conv_text = "\n".join(
                    [
                        f"{t.get('speaker')}: {t.get('message', '')}"
                        for t in recent
                        if isinstance(t, dict)
                    ]
                )
                parts.append(f"Conversation History:\n{conv_text}")

            context_str = "\n\n".join(parts) if parts else "No context provided"
        elif isinstance(context, str):
            context_str = context or "No context provided"
        else:
            context_str = "No context provided"

        prompt = RAGPrompts.get_factual_accuracy_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)  # Use shared parser

            # Get score directly (1-10 range)
            score = result.get("score", -1.0)
            reasoning = result.get("reasoning", "No reasoning provided")

            # Error check
            if score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            # Store extra fields in metadata
            metadata = {
                "issues": result.get("issues", []),
                "confidence": result.get("confidence", 0.0),
            }

            # Check if score meets threshold (both in 1-10 range)
            passed = score >= self.threshold
            return ScoreResult(
                score=score, passed=passed, reasoning=reasoning, metadata=metadata
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ClaimVerificationScorer(BaseScorer):
    """
    Verify specific claims in generated answers.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ClaimVerificationScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Extract claims from the answer
        claims_prompt = RAGPrompts.get_claim_extraction_evaluation(
            output_text=output_text
        )

        try:
            claims_response = await self._call_model(claims_prompt)
            claims_result = parse_llm_json_response(claims_response)
            claims = claims_result.get("claims", [])

            if not claims:
                return ScoreResult(
                    score=1.0,
                    passed=True,
                    reasoning="No specific claims found",
                    metadata={"claims": []},
                )

            # Verify each claim
            verified_claims = []
            total_score = 0.0

            # Convert context to string if it's a dict
            context_str = _context_to_str(context) or "No context provided"

            for claim in claims:
                verification_prompt = RAGPrompts.get_claim_verification_evaluation(
                    context=context_str, claim=claim
                )

                verification_response = await self._call_model(verification_prompt)
                verification_result = parse_llm_json_response(verification_response)
                score = verification_result.get("verification_score", 3.0)
                total_score += score
                verified_claims.append(
                    {
                        "claim": claim,
                        "score": score,
                        "supported": verification_result.get("supported", False),
                        "reasoning": verification_result.get("reasoning", ""),
                        "confidence": verification_result.get("confidence", 0.0),
                        "supporting_evidence": verification_result.get(
                            "supporting_evidence", []
                        ),
                        "contradicting_evidence": verification_result.get(
                            "contradicting_evidence", []
                        ),
                        "verification_method": verification_result.get(
                            "verification_method", ""
                        ),
                    }
                )

            avg_score = total_score / len(claims)  # Average score on 1-10 scale
            passed = avg_score >= self.threshold

            reasoning = f"Verified {len(claims)} claims. Average verification: {avg_score:.1f}/10"

            return ScoreResult(
                score=avg_score,
                passed=passed,
                reasoning=reasoning,
                metadata={
                    "verified_claims": verified_claims,
                    "total_claims": len(claims),
                    "claim_extraction": {
                        "reasoning": claims_result.get("reasoning", ""),
                        "confidence": claims_result.get("confidence", 0.0),
                        "claim_types": claims_result.get("claim_types", []),
                        "total_claims": claims_result.get("total_claims", len(claims)),
                    },
                },
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


# ANSWER COMPLETENESS AND RELEVANCE SCORERS
class InformationDensityScorer(BaseScorer):
    """
    Information richness evaluation.
    """

    def __init__(self, model: Any, threshold: float = 6.0, **kwargs: Any) -> None:
        super().__init__(name="InformationDensityScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_information_density_evaluation(
            input_text=input_text, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)

            # Get score directly from JSON (prompt enforces "score" field, returns -1 on error)
            score = result.get("score", -1.0)
            reasoning = result.get(
                "reasoning", f"No reasoning provided (score: {score})"
            )

            # If score is -1, it's an error from the LLM
            if score == -1.0:
                return ScoreResult(
                    score=-1.0,
                    passed=False,
                    reasoning=reasoning,
                    metadata={"error": "LLM returned -1 or parsing failed"},
                )

            passed = score >= self.threshold
            return ScoreResult(
                score=score, passed=passed, reasoning=reasoning, metadata={}
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ClarityAndCoherenceScorer(BaseScorer):
    """
    Answer readability and logic evaluation.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ClarityAndCoherenceScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_clarity_coherence_evaluation(
            input_text="", output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)  # Use shared parser

            # Get score directly
            score = result.get("score", -1.0)
            reasoning = result.get("reasoning", "No reasoning provided")

            # Error check
            if score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            # Store extra fields in metadata
            metadata = {
                "clarity_issues": result.get("clarity_issues", []),
                "coherence_issues": result.get("coherence_issues", []),
                "confidence": result.get("confidence", 0.0),
            }

            passed = score >= self.threshold
            return ScoreResult(
                score=score, passed=passed, reasoning=reasoning, metadata=metadata
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


# MULTI-CONTEXT INTEGRATION SCORERS
class ConflictResolutionScorer(BaseScorer):
    """
    Handling contradictory information across contexts.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ConflictResolutionScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or ""
        if not context_str:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context provided",
                metadata={},
            )

        # Split context into chunks to check for conflicts
        context_chunks = context_str.split("\n\n")
        if len(context_chunks) < 2:
            return ScoreResult(
                score=10.0,
                passed=True,
                reasoning="Single context provided - no conflicts possible",
                metadata={"chunks": 1},
            )

        prompt = RAGPrompts.get_context_faithfulness_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Conflict resolution: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={"context_chunks": len(context_chunks)},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ContextPrioritizationScorer(BaseScorer):
    """
    Appropriate context weighting evaluation.
    """

    def __init__(self, model: Any, threshold: float = 6.0, **kwargs: Any) -> None:
        super().__init__(name="ContextPrioritizationScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or ""

        prompt = RAGPrompts.get_context_faithfulness_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get(
                "reasoning", f"Context prioritization: {score:.1f}/10"
            )

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class CitationQualityScorer(BaseScorer):
    """
    Quality of source references evaluation.
    """

    def __init__(self, model: Any, threshold: float = 6.0, **kwargs: Any) -> None:
        super().__init__(name="CitationQualityScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_source_attribution_evaluation(
            context="", output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Citation quality: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


# DOMAIN-SPECIFIC EVALUATION SCORERS
class ToneConsistencyScorer(BaseScorer):
    """
    Appropriate tone for domain evaluation.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ToneConsistencyScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Build enhanced input with conversation context for proper tone evaluation
        enhanced_input = input_text
        if isinstance(context, dict) and context.get("full_conversation"):
            conv = context["full_conversation"]
            # Use last 5 turns for context
            recent = conv[-5:] if len(conv) > 5 else conv
            conv_text = "\n".join(
                [
                    (
                        f"{t.get('speaker')}: {t.get('message', '')[:100]}..."
                        if len(t.get("message", "")) > 100
                        else f"{t.get('speaker')}: {t.get('message', '')}"
                    )
                    for t in recent
                    if isinstance(t, dict)
                ]
            )
            enhanced_input = f"[Recent Conversation]\n{conv_text}\n\n[Current Question]: {input_text}"

        prompt = RAGPrompts.get_clarity_coherence_evaluation(
            input_text=enhanced_input, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)

            # Get score from JSON (prompt enforces "score" field name)
            score = result.get("score", -1.0)
            reasoning = result.get("reasoning", f"Tone consistency: {score:.1f}/10")

            # Error check - consistent with other scorers
            if score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            passed = score >= self.threshold

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={"raw_score": score, "parsed_result": result},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class TerminologyConsistencyScorer(BaseScorer):
    """
    Consistent use of domain terms evaluation.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="TerminologyConsistencyScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_clarity_coherence_evaluation(
            input_text="", output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get(
                "reasoning", f"Terminology consistency: {score:.1f}/10"
            )

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ContextFaithfulnessScorerPP(BaseScorer):
    """
    Enhanced faithfulness detection with fine-grained analysis.
    Analyzes each claim in the answer against the provided context.
    """

    def __init__(self, model: Any, threshold: float = 8.0, **kwargs: Any) -> None:
        super().__init__(name="ContextFaithfulnessScorerPP", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Extract claims from the answer
        claims_prompt = RAGPrompts.get_claim_extraction_evaluation(
            output_text=output_text
        )

        try:
            claims_response = await self._call_model(claims_prompt)
            claims = self._parse_claims(claims_response)

            if not claims:
                return ScoreResult(
                    score=10.0,
                    passed=True,
                    reasoning="No factual claims found - perfect faithfulness by default",
                    metadata={"claims": []},
                )

            # Verify each claim against context
            verified_claims = []
            total_score = 0.0

            # Convert context to string if it's a dict
            context_str = _context_to_str(context) or ""

            for _i, claim in enumerate(claims):
                verification_prompt = RAGPrompts.get_claim_verification_evaluation(
                    context=context_str, claim=claim
                )

                verification_response = await self._call_model(verification_prompt)
                result = parse_llm_json_response(verification_response)
                score = result.get("score", -1.0)
                total_score += score
                verified_claims.append({"claim": claim, "score": score})

            avg_score = total_score / len(claims)  # Average score on 1-10 scale
            passed = avg_score >= self.threshold

            reasoning = f"Verified {len(claims)} claims. Average faithfulness: {avg_score:.1f}/10"

            return ScoreResult(
                score=avg_score,
                passed=passed,
                reasoning=reasoning,
                metadata={
                    "verified_claims": verified_claims,
                    "total_claims": len(claims),
                },
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def _parse_claims(self, text: str) -> list[str]:
        return parse_claims(text)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ContextGroundednessScorer(BaseScorer):
    """
    Ensures answers are grounded in provided context.
    Evaluates how well the answer is supported by the given context.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ContextGroundednessScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or ""

        prompt = RAGPrompts.get_context_faithfulness_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Groundedness score: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ContextCompletenessScorer(BaseScorer):
    """
    Evaluates if context fully supports the answer.
    Checks whether the provided context contains all necessary information.
    """

    def __init__(self, model: Any, threshold: float = 6.0, **kwargs: Any) -> None:
        super().__init__(name="ContextCompletenessScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or ""

        prompt = RAGPrompts.get_answer_completeness_evaluation(
            input_text=input_text, context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Context completeness: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class ContextConsistencyScorer(BaseScorer):
    """
    Consistency across multiple contexts.
    Evaluates if the answer is consistent when multiple contexts are provided.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="ContextConsistencyScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or ""
        if not context_str:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context provided",
                metadata={},
            )

        # Split context into multiple chunks
        context_chunks = context_str.split("\n\n")
        if len(context_chunks) < 2:
            return ScoreResult(
                score=10.0,
                passed=True,
                reasoning="Single context provided - perfect consistency",
                metadata={"chunks": 1},
            )

        # Evaluate consistency across chunks
        consistency_scores = []
        for _i, chunk in enumerate(context_chunks):
            prompt = RAGPrompts.get_context_faithfulness_evaluation(
                context=chunk, output_text=output_text
            )

            try:
                response = await self._call_model(prompt)
                result = parse_llm_json_response(response)
                score = result.get("score", -1.0)
                consistency_scores.append(score)
            except Exception:
                consistency_scores.append(-1.0)  # Default to error state

        avg_score = sum(consistency_scores) / len(consistency_scores)
        passed = avg_score >= self.threshold

        reasoning = (
            f"Consistency across {len(context_chunks)} chunks: {avg_score:.1f}/10"
        )

        return ScoreResult(
            score=avg_score,
            passed=passed,
            reasoning=reasoning,
            metadata={
                "consistency_scores": consistency_scores,
                "chunks": len(context_chunks),
            },
        )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class RAGAnswerQualityScorer(BaseScorer):
    """
    Comprehensive RAG generation evaluation.
    Evaluates the overall quality of RAG-generated answers.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="RAGAnswerQualityScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        prompt = RAGPrompts.get_question_answer_alignment_evaluation(
            input_text=input_text, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Answer quality: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class HallucinationDetectionScorer(BaseScorer):
    """
    Identify factual inconsistencies in generated answers.
    """

    def __init__(self, model: Any, threshold: float = 8.0, **kwargs: Any) -> None:
        super().__init__(name="HallucinationDetectionScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Extract conversation context if available (from enhanced context dict)
        context_text = ""
        if isinstance(context, dict):
            parts = []

            # Add KB retrieved context if available (HIGHEST PRIORITY - source of truth)
            if context.get("context"):
                kb_text = context["context"]
                if isinstance(kb_text, str) and kb_text.strip():
                    parts.append(f"Retrieved Knowledge Base Context:\n{kb_text}")

            # Add agent role/capabilities from system_prompt
            if context.get("system_prompt"):
                sys_prompt = context["system_prompt"]
                # Truncate if extremely long (keep full for hallucination detection context)
                if isinstance(sys_prompt, str) and len(sys_prompt) > 2000:
                    sys_prompt = sys_prompt[:2000] + "... (truncated)"
                parts.append(f"Agent Role & Capabilities:\n{sys_prompt}")

            # Add full conversation for context
            if context.get("full_conversation"):
                conv = context["full_conversation"]
                recent = conv[-10:] if len(conv) > 10 else conv
                conv_text = "\n".join(
                    [
                        f"{t.get('speaker')}: {t.get('message', '')}"
                        for t in recent
                        if isinstance(t, dict)
                    ]
                )
                parts.append(f"Conversation History:\n{conv_text}")

            context_text = "\n\n".join(parts) if parts else "No context provided"
        elif isinstance(context, str):
            context_text = context or "No context provided"
        else:
            context_text = "No context provided"

        prompt = RAGPrompts.get_hallucination_detection_evaluation(
            context=context_text, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)  # Use shared parser

            # Get quality score directly from JSON (prompt now asks for quality, not hallucination level)
            quality_score = result.get("score", -1.0)
            reasoning = result.get("reasoning", "No reasoning provided")

            # Error check
            if quality_score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            # No inversion needed - prompt directly returns quality score (10=no hallucinations, 1=severe hallucinations)
            passed = quality_score >= self.threshold

            # Store all extra fields in metadata
            metadata = {
                "hallucination_types": result.get("hallucination_types", []),
                "specific_examples": result.get("specific_examples", []),
                "confidence": result.get("confidence", 0.0),
            }

            return ScoreResult(
                score=quality_score,
                passed=passed,
                reasoning=f"Hallucination-free quality: {quality_score:.1f}/10. {reasoning}",
                metadata=metadata,
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class SourceAttributionScorer(BaseScorer):
    """
    Proper citation and source attribution evaluation.
    """

    def __init__(self, model: Any, threshold: float = 6.0, **kwargs: Any) -> None:
        super().__init__(name="SourceAttributionScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or "No context provided"

        prompt = RAGPrompts.get_source_attribution_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Source attribution: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class AnswerCompletenessScorer(BaseScorer):
    """
    Comprehensive answer coverage evaluation.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="AnswerCompletenessScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Extract conversation context if available (from enhanced context dict)
        context_text = ""
        if isinstance(context, dict):
            # Build comprehensive context string
            parts = []

            # Add KB retrieved context if available (HIGHEST PRIORITY - source of truth)
            if context.get("context"):
                kb_text = context["context"]
                if isinstance(kb_text, str) and kb_text.strip():
                    parts.append(f"Retrieved Knowledge Base Context:\n{kb_text}")

            # Add conversation history
            if context.get("full_conversation"):
                conv = context["full_conversation"]
                recent = conv[-10:] if len(conv) > 10 else conv  # Last 10 turns
                conv_text = "\n".join(
                    [
                        f"{t.get('speaker', 'unknown')}: {t.get('message', '')}"
                        for t in recent
                        if isinstance(t, dict)
                    ]
                )
                parts.append(f"Conversation History:\n{conv_text}")

            # Add system prompt summary (agent role/capabilities)
            if context.get("system_prompt"):
                sys_prompt = context["system_prompt"]
                # Truncate if extremely long
                if isinstance(sys_prompt, str) and len(sys_prompt) > 500:
                    sys_prompt = sys_prompt[:500] + "... (truncated)"
                parts.append(f"Agent Role: {sys_prompt}")

            context_text = "\n\n".join(parts) if parts else "No context provided"
        elif isinstance(context, str):
            context_text = context or "No context provided"

        prompt = RAGPrompts.get_answer_completeness_evaluation(
            input_text=input_text, context=context_text, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)  # Use shared parser

            # Get score directly from JSON (prompt enforces "score" field, returns -1 on error)
            score = result.get("score", -1.0)
            reasoning = result.get("reasoning", "No reasoning provided")

            # If score is -1, it's an error
            if score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            # Store additional fields in metadata
            metadata = {
                "covered_aspects": result.get("covered_aspects", []),
                "missing_aspects": result.get("missing_aspects", []),
                "confidence": result.get("confidence", 0.0),
            }

            passed = score >= self.threshold
            return ScoreResult(
                score=score, passed=passed, reasoning=reasoning, metadata=metadata
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class QuestionAnswerAlignmentScorer(BaseScorer):
    """
    Direct question addressing evaluation.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="QuestionAnswerAlignmentScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Extract conversation context if available
        conversation_context = ""
        if isinstance(context, dict) and context.get("full_conversation"):
            conv = context["full_conversation"]
            recent = conv[-10:] if len(conv) > 10 else conv
            conversation_context = "\n".join(
                [
                    (
                        f"{t.get('speaker')}: {t.get('message', '')[:100]}..."
                        if len(t.get("message", "")) > 100
                        else f"{t.get('speaker')}: {t.get('message', '')}"
                    )
                    for t in recent
                    if isinstance(t, dict)
                ]
            )

        # Build enhanced input with context
        enhanced_input = input_text
        if conversation_context:
            enhanced_input = f"[Previous Conversation]\n{conversation_context}\n\n[Current Question]: {input_text}"

        prompt = RAGPrompts.get_question_answer_alignment_evaluation(
            input_text=enhanced_input, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)

            # Get score from JSON (prompt enforces "score" field name)
            score = result.get("score", -1.0)
            reasoning = result.get(
                "reasoning", f"Question-answer alignment: {score:.1f}/10"
            )

            # Error check - consistent with other scorers
            if score == -1.0:
                return ScoreResult(
                    score=-1.0, passed=False, reasoning=reasoning, metadata={}
                )

            passed = score >= self.threshold

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={"raw_score": score, "parsed_result": result},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class CrossContextSynthesisScorer(BaseScorer):
    """
    Quality of information synthesis across multiple contexts.
    """

    def __init__(self, model: Any, threshold: float = 7.0, **kwargs: Any) -> None:
        super().__init__(name="CrossContextSynthesisScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not context or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context or output provided",
                metadata={},
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context)
        if not context_str:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context provided",
                metadata={},
            )

        # Split context into chunks
        context_chunks = context_str.split("\n\n")
        if len(context_chunks) < 2:
            return ScoreResult(
                score=10.0,
                passed=True,
                reasoning="Single context provided - perfect synthesis by default",
                metadata={"chunks": 1},
            )

        prompt = RAGPrompts.get_context_faithfulness_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get(
                "reasoning", f"Cross-context synthesis: {score:.1f}/10"
            )

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={"context_chunks": len(context_chunks)},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result


class TechnicalAccuracyScorer(BaseScorer):
    """
    Technical domain accuracy evaluation.
    """

    def __init__(self, model: Any, threshold: float = 8.0, **kwargs: Any) -> None:
        super().__init__(name="TechnicalAccuracyScorer", **kwargs)
        self.threshold = threshold
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[Union[str, dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        if not output_text:
            return ScoreResult(
                score=0.0, passed=False, reasoning="No answer provided", metadata={}
            )

        # Convert context to string if it's a dict
        context_str = _context_to_str(context) or "No context provided"

        prompt = RAGPrompts.get_technical_accuracy_evaluation(
            context=context_str, output_text=output_text
        )

        try:
            response = await self._call_model(prompt)
            result = parse_llm_json_response(response)
            score = result.get("score", -1.0)
            passed = score >= self.threshold

            reasoning = result.get("reasoning", f"Technical accuracy: {score:.1f}/10")

            return ScoreResult(
                score=score,
                passed=passed,
                reasoning=reasoning,
                metadata={},
            )

        except Exception as e:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=f"Error: {e!s}", metadata={}
            )

    async def _call_model(self, prompt: str) -> str:
        import asyncio

        return await asyncio.to_thread(call_llm, self.model, prompt)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        import asyncio

        # Pass the full context dict to evaluate() - it handles dicts or strings
        # Don't extract context["context"] - that loses enhanced fields!
        context_to_pass = context

        # Run async evaluation
        result = asyncio.run(
            self.evaluate(
                input_text=ground_truth, output_text=prediction, context=context_to_pass
            )
        )

        return result
