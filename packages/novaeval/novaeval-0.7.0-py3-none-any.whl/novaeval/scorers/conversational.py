"""
Conversational AI metrics for NovaEval.

This module implements comprehensive metrics for evaluating conversational AI systems including:
- Knowledge Retention with sophisticated knowledge extraction and tracking
- Conversation Completeness with intention analysis
- Conversation Relevancy with sliding window context
- Role Adherence with detailed role analysis
- Comprehensive conversation-level metrics with outcome-based evaluation

Based on best practices from DeepEval and research in conversational AI evaluation.
"""

import asyncio
import json
import re
import threading
from collections.abc import Coroutine
from typing import Any, Optional, TypeVar

from pydantic import BaseModel, Field

from novaeval.models.base import BaseModel as LLMModel
from novaeval.scorers.base import BaseScorer, ScoreResult

T = TypeVar("T")


class ScoreWithReasoning(BaseModel):
    """Pydantic model for score with reasoning."""

    score: float = Field(description="Numerical score")
    reasoning: str = Field(description="Explanation for the score")


def parse_score_with_reasoning(response: str) -> ScoreWithReasoning:
    """
    Parse LLM response to extract score and reasoning with fallback handling.

    Args:
        response: Raw LLM response string

    Returns:
        ScoreWithReasoning object
    """
    try:
        # Clean and parse JSON response
        cleaned_response = response.strip()

        # Try to extract JSON from response if it's embedded in text
        if "{" in cleaned_response and "}" in cleaned_response:
            start_idx = cleaned_response.find("{")
            end_idx = cleaned_response.rfind("}") + 1
            json_str = cleaned_response[start_idx:end_idx]
        else:
            json_str = cleaned_response

        try:
            parsed_response = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try to extract score from response text using regex
            # Updated regex to better handle 1-10 scores
            score_match = re.search(
                r'["\']?score["\']?\s*:\s*([0-9]+\.?[0-9]*)',
                cleaned_response,
                re.IGNORECASE,
            )
            # Improved reasoning extraction - handles both single and double quotes
            reasoning_match = re.search(
                r'["\']?reasoning["\']?\s*:\s*["\']([^"\']*)["\']',
                cleaned_response,
                re.IGNORECASE,
            )

            if score_match:
                return ScoreWithReasoning(
                    score=float(score_match.group(1)),
                    reasoning=(
                        reasoning_match.group(1)
                        if reasoning_match
                        else "No reasoning provided"
                    ),
                )
            else:
                # Try to find any number in the response as a score (prioritize 1-10 range)
                # First try to find numbers in 1-10 range
                number_match = re.search(
                    r"\b(10(?:\.\d+)?|[1-9](?:\.\d+)?)\b", cleaned_response
                )
                if not number_match:
                    # Fallback to any number
                    number_match = re.search(r"\b([0-9.]+)\b", cleaned_response)
                if number_match:
                    return ScoreWithReasoning(
                        score=float(number_match.group(1)),
                        reasoning=f"Extracted score from response: {cleaned_response[:100]}...",
                    )
                else:
                    return ScoreWithReasoning(
                        score=-1.0,
                        reasoning=f"Could not parse response: {cleaned_response[:100]}...",
                    )

        # Extract score and reasoning from parsed JSON
        if (
            isinstance(parsed_response, dict)
            and "score" in parsed_response
            and "reasoning" in parsed_response
        ):
            return ScoreWithReasoning(
                score=float(parsed_response["score"]),
                reasoning=str(parsed_response["reasoning"]),
            )
        elif isinstance(parsed_response, dict) and "score" in parsed_response:
            return ScoreWithReasoning(
                score=float(parsed_response["score"]),
                reasoning="No reasoning provided in response",
            )
        else:
            # Check if it's just a number
            if isinstance(parsed_response, (int, float)):
                return ScoreWithReasoning(
                    score=float(parsed_response),
                    reasoning="Score provided without reasoning",
                )
            else:
                return ScoreWithReasoning(
                    score=-1.0,
                    reasoning=f"Unexpected response format: {parsed_response!s}",
                )

    except Exception as e:
        return ScoreWithReasoning(
            score=-1.0, reasoning=f"Failed to parse response: {e!s}"
        )


def _run_async_in_sync_context(coro: Coroutine[Any, Any, T]) -> T:
    """
    Helper function to run async code from sync context.

    Handles both cases:
    - When called from outside an event loop (uses asyncio.run)
    - When called from within an existing event loop (uses loop.run_until_complete in thread)
    """
    try:
        # Check if we're already in a running event loop
        asyncio.get_running_loop()
    except RuntimeError:
        # No running event loop, we can use asyncio.run
        return asyncio.run(coro)

    # We're in a running loop, we need to run in a separate thread
    # Use a sentinel object to track completion status
    _SENTINEL = object()
    result: Any = _SENTINEL
    exception: Optional[BaseException] = None

    def run_in_thread() -> None:
        nonlocal result, exception
        try:
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result = new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        except (
            BaseException
        ) as e:  # Catch ALL exceptions, including SystemExit, KeyboardInterrupt
            exception = e

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()

    if exception is not None:
        raise exception

    # Ensure thread completed successfully and we have a valid result
    if result is _SENTINEL:
        raise RuntimeError(
            "Thread completed without setting result or raising exception"
        )

    return result  # type: ignore[return-value]  # We've verified result is not sentinel


class ConversationTurn(BaseModel):
    """Represents a single turn in a conversation."""

    speaker: str = Field(description="Speaker identifier (user, assistant, system)")
    message: str = Field(description="The message content")
    timestamp: Optional[str] = Field(default=None, description="Optional timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class Conversation(BaseModel):
    """Represents a complete conversation with metadata."""

    turns: list[ConversationTurn] = Field(description="List of conversation turns")
    context: Optional[str] = Field(
        default=None, description="Overall conversation context or system role"
    )
    topic: Optional[str] = Field(default=None, description="Conversation topic")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class KnowledgeItem(BaseModel):
    """Represents a piece of knowledge extracted from conversation."""

    content: str = Field(description="The knowledge content")
    turn_index: int = Field(description="Turn where this knowledge was introduced")
    speaker: str = Field(description="Who provided this knowledge")
    confidence: float = Field(description="Confidence in extraction (0-1)")


class KnowledgeRetentionScorer(BaseScorer):
    """
    Evaluates knowledge retention in conversations.

    Uses sophisticated knowledge extraction and tracking to determine if the LLM
    retains information provided by users throughout the conversation.
    """

    def __init__(self, model: LLMModel, window_size: int = 10):
        super().__init__(
            name="Knowledge Retention",
            description="Evaluates knowledge retention in conversations by tracking information recall and consistency across dialogue turns",
        )
        self.model = model
        self.window_size = window_size

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Evaluate knowledge retention in conversation.

        Args:
            input_text: The input/context for the conversation
            output_text: The model's response to evaluate
            expected_output: Expected response (optional)
            context: Additional context including conversation history

        Returns:
            ScoreResult with score, pass/fail status, and reasoning
        """
        # Input validation with proper type checking
        if not isinstance(output_text, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: output_text must be a string",
                metadata={
                    "error": "type_error",
                    "input_type": type(output_text).__name__,
                },
            )

        if expected_output is not None and not isinstance(expected_output, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: expected_output must be a string or None",
                metadata={
                    "error": "type_error",
                    "expected_type": type(expected_output).__name__,
                },
            )

        # Additional validation for empty strings (safe now that we've checked types)
        if not output_text or not output_text.strip():
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only output text",
                metadata={"error": "empty_output"},
            )

        if expected_output is not None and (
            not expected_output or not expected_output.strip()
        ):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only expected output",
                metadata={"error": "empty_expected"},
            )

        try:
            result = await self._evaluate_knowledge_retention_async(
                output_text, expected_output or "", context
            )
            self._track_score(result.score)

            passed = result.score >= 7.0  # Default threshold on 1-10 scale

            return ScoreResult(
                score=result.score,
                passed=passed,
                reasoning=result.reasoning,
                metadata={
                    "scorer": "knowledge_retention",
                    "model": (
                        self.model.name if hasattr(self.model, "name") else "unknown"
                    ),
                    "window_size": self.window_size,
                },
            )
        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {e!s}",
                metadata={"error": "evaluation_error", "exception": str(e)},
            )

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> float:
        """
        Legacy synchronous score method for backward compatibility.

        Note: This method is deprecated. Use evaluate() for new code.
        """
        # Input validation with proper type checking
        if not isinstance(prediction, str) or not isinstance(ground_truth, str):
            return 0.0

        # Safe to call strip() now
        if (
            not prediction
            or not prediction.strip()
            or not ground_truth
            or not ground_truth.strip()
        ):
            return 0.0

        try:
            result = _run_async_in_sync_context(
                self.evaluate(
                    input_text="",  # Not used in knowledge retention
                    output_text=prediction,
                    expected_output=ground_truth,
                    context=context,
                )
            )
            return result.score
        except Exception:
            return 0.0

    async def _evaluate_knowledge_retention_async(
        self, prediction: str, ground_truth: str, context: Optional[dict[str, Any]]
    ) -> ScoreWithReasoning:
        """Async evaluation of knowledge retention."""
        if not context or "conversation" not in context:
            return await self._simple_retention_score(prediction, ground_truth)

        conversation = context["conversation"]
        if not isinstance(conversation, Conversation):
            return await self._simple_retention_score(prediction, ground_truth)

        # Extract knowledge from conversation history
        knowledge_items = await self._extract_conversation_knowledge(conversation)

        if not knowledge_items:
            return ScoreWithReasoning(
                score=-1.0,
                reasoning="No specific knowledge to retain from conversation history.",
            )

        # Build knowledge summary
        knowledge_summary = "\n".join([f"- {item.content}" for item in knowledge_items])

        # Evaluate knowledge retention using LLM
        retention_prompt = f"""Evaluate the assistant's knowledge retention in this conversation.

Information the USER previously provided (that the assistant should remember):
{knowledge_summary}

Current assistant response: "{prediction}"

Knowledge retention measures whether the assistant REMEMBERS and USES information the USER shared earlier.

Evaluate on a scale of 1-10:
10 = Perfect retention - uses all relevant user-provided info appropriately, doesn't ask for already-given info
9-8 = Excellent retention - remembers and applies user info with minimal gaps
7-6 = Good retention - recalls most user info but may miss some details
5-4 = Moderate retention - remembers some user info but misses important pieces or asks for already-provided info
3-2 = Poor retention - forgets most user-provided info or repeatedly asks for same information
1 = No retention - completely ignores or forgets user-provided information

IMPORTANT NOTES:
- If the user provided NO specific personal information/preferences/facts to remember, score should be -1 (not applicable)
- Answering the CURRENT question differently than PREVIOUS questions is NORMAL and CORRECT (not a retention issue)
- Only penalize if the assistant forgets/ignores information the USER explicitly shared

Format your response as a JSON object:
{{
  "score": <1-10 or -1 if not applicable>,
  "reasoning": "Your detailed explanation of what user information should be retained and whether it was used appropriately"
}}

Your response should be ONLY the JSON object, nothing else."""

        try:
            if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                self.model.generate
            ):
                response = await self.model.generate(retention_prompt)
            else:
                response = self.model.generate(retention_prompt)

            result = parse_score_with_reasoning(response)
            return result
        except Exception as e:
            return ScoreWithReasoning(
                score=0.5, reasoning=f"Failed to evaluate knowledge retention: {e!s}"
            )

    async def _extract_conversation_knowledge(
        self, conversation: Conversation
    ) -> list[KnowledgeItem]:
        """Extract knowledge items from recent conversation history within the sliding window."""
        knowledge_items = []

        # Apply sliding window to limit the conversation turns processed
        current_turn_index = len(conversation.turns) - 1
        window_start = max(0, current_turn_index - self.window_size)
        relevant_turns = conversation.turns[window_start:]

        for i, turn in enumerate(relevant_turns, start=window_start):
            if turn.speaker == "user":  # Only extract knowledge from user messages
                knowledge_prompt = f"""Extract factual information that the ASSISTANT should remember from this user message.

User message: "{turn.message}"

Identify ONLY information the user is PROVIDING (not questions they're asking):
- Personal details (name, location, role, preferences)
- Business context (company size, industry, specific needs)
- Stated constraints or requirements
- Previously mentioned facts about their situation
- Explicit preferences or choices

DO NOT extract:
- Questions the user is asking (these are requests for info, not knowledge to retain)
- General topic areas (unless user states a specific fact about themselves)

Output as a numbered list:
1. [Knowledge item 1]
2. [Knowledge item 2]
...

If the user is ONLY asking questions without providing personal information, respond with "None"."""

                try:
                    if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                        self.model.generate
                    ):
                        response = await self.model.generate(knowledge_prompt)
                    else:
                        response = self.model.generate(knowledge_prompt)
                    extracted_knowledge = self._parse_knowledge_items(
                        response, i, turn.speaker
                    )
                    knowledge_items.extend(extracted_knowledge)
                except Exception:
                    continue

        return knowledge_items

    def _parse_knowledge_items(
        self, response: str, turn_index: int, speaker: str
    ) -> list[KnowledgeItem]:
        """Parse knowledge items from LLM response."""
        items: list[KnowledgeItem] = []

        if response.strip().lower() == "none":
            return items

        # Extract numbered list items
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            # Match numbered items like "1. Something" or "1) Something"
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                content = match.group(1).strip()
                if content and len(content) > 5:  # Filter out very short items
                    items.append(
                        KnowledgeItem(
                            content=content,
                            turn_index=turn_index,
                            speaker=speaker,
                            confidence=0.8,  # Default confidence
                        )
                    )

        return items

    async def _simple_retention_score(
        self, prediction: str, ground_truth: str
    ) -> ScoreWithReasoning:
        """Fallback simple retention scoring when conversation context unavailable."""
        # Simple heuristic: check if prediction asks questions about basic info
        question_patterns = [
            r"\bwhat is your name\b",
            r"\bwho are you\b",
            r"\bwhere are you from\b",
            r"\bhow old are you\b",
            r"\bwhat do you do\b",
        ]

        prediction_lower = prediction.lower()
        for pattern in question_patterns:
            if re.search(pattern, prediction_lower):
                return ScoreWithReasoning(
                    score=0.3,
                    reasoning="Response asks basic questions that should have been answered in context.",
                )

        return ScoreWithReasoning(
            score=0.7,
            reasoning="No conversation context available for detailed knowledge retention evaluation.",
        )


class ConversationRelevancyScorer(BaseScorer):
    """
    Evaluates conversation relevancy using sliding window approach.

    Assesses whether responses are relevant to recent conversation context,
    using a sliding window to consider appropriate conversation history.
    """

    def __init__(self, model: LLMModel, window_size: int = 5):
        super().__init__(
            name="Conversation Relevancy",
            description="Measures how relevant and contextually appropriate responses are within the conversation flow",
        )
        self.model = model
        self.window_size = window_size

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Evaluate conversation relevancy.

        Args:
            input_text: The input/context for the conversation
            output_text: The model's response to evaluate
            expected_output: Expected response (optional)
            context: Additional context including conversation history

        Returns:
            ScoreResult with score, pass/fail status, and reasoning
        """
        # Input validation with proper type checking
        if not isinstance(output_text, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: output_text must be a string",
                metadata={
                    "error": "type_error",
                    "input_type": type(output_text).__name__,
                },
            )

        # Additional validation for empty strings (safe now that we've checked types)
        if not output_text or not output_text.strip():
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only output text",
                metadata={"error": "empty_output"},
            )

        try:
            result = await self._evaluate_relevancy_async(
                output_text, expected_output or "", context
            )
            self._track_score(result.score)

            passed = result.score >= 7.0  # Default threshold on 1-10 scale

            return ScoreResult(
                score=result.score,
                passed=passed,
                reasoning=result.reasoning,
                metadata={
                    "scorer": "conversation_relevancy",
                    "model": (
                        self.model.name if hasattr(self.model, "name") else "unknown"
                    ),
                    "window_size": self.window_size,
                },
            )
        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {e!s}",
                metadata={"error": "evaluation_error", "exception": str(e)},
            )

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> float:
        """
        Legacy synchronous score method for backward compatibility.

        Note: This method is deprecated. Use evaluate() for new code.
        """
        # Input validation with proper type checking
        if not isinstance(prediction, str) or not isinstance(ground_truth, str):
            return 0.0

        # Safe to call strip() now
        if (
            not prediction
            or not prediction.strip()
            or not ground_truth
            or not ground_truth.strip()
        ):
            return 0.0

        try:
            result = _run_async_in_sync_context(
                self.evaluate(
                    input_text="",
                    output_text=prediction,
                    expected_output=ground_truth,
                    context=context,
                )
            )
            return result.score
        except Exception:
            return 0.0

    async def _evaluate_relevancy_async(
        self, prediction: str, ground_truth: str, context: Optional[dict[str, Any]]
    ) -> ScoreWithReasoning:
        """Async evaluation of conversation relevancy with sliding window."""
        if not context or "conversation" not in context:
            return await self._simple_relevancy_score(prediction, ground_truth)

        conversation = context["conversation"]
        if not isinstance(conversation, Conversation):
            return await self._simple_relevancy_score(prediction, ground_truth)

        # Get relevant context window
        current_turn_index = len(conversation.turns) - 1
        window_start = max(0, current_turn_index - self.window_size)
        relevant_turns = conversation.turns[window_start:current_turn_index]

        if not relevant_turns:
            return await self._simple_relevancy_score(prediction, ground_truth)

        # Build context summary
        context_summary = self._build_context_summary(relevant_turns)

        relevancy_prompt = f"""Evaluate the relevancy of an assistant's response to the recent conversation context.

Recent conversation context:
{context_summary}

Assistant response: "{prediction}"

Evaluate on a scale of 1-10:
10 = Highly relevant, directly addresses the conversation flow
9-8 = Very relevant, mostly appropriate with minor tangents
7-6 = Mostly relevant, somewhat focused but could be better
5-4 = Somewhat relevant but could be more focused
3-2 = Loosely relevant, partially addresses context
1 = Not relevant, off-topic or ignoring context

Consider:
- Does the response address the most recent user input?
- Does it maintain conversation flow and coherence?
- Is it appropriate given the conversation history?

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the relevancy assessment"
}}

Your response should be ONLY the JSON object, nothing else."""

        try:
            if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                self.model.generate
            ):
                response = await self.model.generate(relevancy_prompt)
            else:
                response = self.model.generate(relevancy_prompt)

            result = parse_score_with_reasoning(response)
            return result
        except Exception as e:
            return ScoreWithReasoning(
                score=0.5, reasoning=f"Failed to evaluate relevancy: {e!s}"
            )

    def _build_context_summary(self, turns: list[ConversationTurn]) -> str:
        """Build a summary of conversation turns for context."""
        summary_parts = []
        for _i, turn in enumerate(turns):
            summary_parts.append(f"{turn.speaker}: {turn.message}")
        return "\n".join(summary_parts)

    async def _simple_relevancy_score(
        self, prediction: str, ground_truth: str
    ) -> ScoreWithReasoning:
        """Fallback simple relevancy scoring when conversation context unavailable."""
        # Simple word overlap heuristic
        pred_words = set(prediction.lower().split())
        truth_words = set(ground_truth.lower().split())

        if not pred_words or not truth_words:
            return ScoreWithReasoning(
                score=0.0, reasoning="Empty prediction or ground truth provided."
            )

        overlap = len(pred_words.intersection(truth_words))
        union = len(pred_words.union(truth_words))

        if union == 0:
            return ScoreWithReasoning(
                score=0.0,
                reasoning="No words to compare in prediction and ground truth.",
            )

        score = overlap / union
        return ScoreWithReasoning(
            score=score,
            reasoning=f"No conversation context available. Using word overlap heuristic: {overlap}/{union} words overlap.",
        )


class ConversationCompletenessScorer(BaseScorer):
    """
    Evaluates conversation completeness by analyzing user intentions and fulfillment.

    Determines whether user requests and intentions throughout the conversation
    have been adequately addressed and fulfilled.
    """

    def __init__(self, model: LLMModel):
        super().__init__(
            name="Conversation Completeness",
            description="Assesses whether responses provide comprehensive coverage of topics and address all aspects of user queries",
        )
        self.model = model

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Evaluate conversation completeness.

        Args:
            input_text: The input/context for the conversation
            output_text: The model's response to evaluate
            expected_output: Expected response (optional)
            context: Additional context including conversation history

        Returns:
            ScoreResult with score, pass/fail status, and reasoning
        """
        # Input validation with proper type checking
        if not isinstance(output_text, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: output_text must be a string",
                metadata={
                    "error": "type_error",
                    "input_type": type(output_text).__name__,
                },
            )

        # Additional validation for empty strings (safe now that we've checked types)
        if not output_text or not output_text.strip():
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only output text",
                metadata={"error": "empty_output"},
            )

        try:
            result = await self._evaluate_completeness_async(
                output_text, expected_output or "", context
            )
            self._track_score(result.score)

            passed = result.score >= 7.0  # Default threshold on 1-10 scale

            return ScoreResult(
                score=result.score,
                passed=passed,
                reasoning=result.reasoning,
                metadata={
                    "scorer": "conversation_completeness",
                    "model": (
                        self.model.name if hasattr(self.model, "name") else "unknown"
                    ),
                },
            )
        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {e!s}",
                metadata={"error": "evaluation_error", "exception": str(e)},
            )

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> float:
        """
        Legacy synchronous score method for backward compatibility.

        Note: This method is deprecated. Use evaluate() for new code.
        """
        # Input validation with proper type checking
        if not isinstance(prediction, str) or not isinstance(ground_truth, str):
            return 0.0

        # Safe to call strip() now
        if (
            not prediction
            or not prediction.strip()
            or not ground_truth
            or not ground_truth.strip()
        ):
            return 0.0

        try:
            result = _run_async_in_sync_context(
                self.evaluate(
                    input_text="",
                    output_text=prediction,
                    expected_output=ground_truth,
                    context=context,
                )
            )
            return result.score
        except Exception:
            return 0.0

    async def _evaluate_completeness_async(
        self, prediction: str, ground_truth: str, context: Optional[dict[str, Any]]
    ) -> ScoreWithReasoning:
        """Async evaluation of conversation completeness."""
        if not context or "conversation" not in context:
            return await self._simple_completeness_score(prediction, ground_truth)

        conversation = context["conversation"]
        if not isinstance(conversation, Conversation):
            return await self._simple_completeness_score(prediction, ground_truth)

        # Extract user intentions from conversation
        intentions = await self._extract_user_intentions(conversation)

        if not intentions:
            return ScoreWithReasoning(
                score=-1.0,
                reasoning="No specific user intentions identified that require fulfillment.",
            )

        # Build intentions summary
        intentions_summary = "\n".join([f"- {intent}" for intent in intentions])

        # Get all assistant responses
        assistant_responses = [
            turn.message for turn in conversation.turns if turn.speaker == "assistant"
        ]
        combined_responses = "\n".join(assistant_responses)

        # Extract bot role/domain from context if available
        bot_role_context = ""
        if context.get("system_prompt"):
            sys_prompt = context["system_prompt"]
            # Extract bot identity/role from system prompt
            if isinstance(sys_prompt, str) and len(sys_prompt) > 100:
                # Truncate to first 500 chars to get core identity
                sys_prompt = sys_prompt[:500] + "... (truncated)"
            bot_role_context = f"\n\nBot Role/Domain Context:\n{sys_prompt}\n\nNote: When user questions are ambiguous, the bot may reasonably interpret them within its domain context."

        # Evaluate completeness with LLM
        completeness_prompt = f"""Evaluate how completely the assistant has addressed the user's intentions.

User intentions identified:
{intentions_summary}

Assistant responses:
{combined_responses}{bot_role_context}

Evaluate on a scale of 1-10:
10 = Completely fulfilled, all user goals fully achieved with requested information provided
9-8 = Very well fulfilled - all intentions acknowledged and addressed (even if some info wasn't available, honest responses given), OR reasonable domain-specific interpretation of ambiguous query
7-6 = Mostly fulfilled - all intentions acknowledged, but some gaps in addressing them
5-4 = Partially fulfilled - some intentions addressed, others ignored or poorly handled, OR ambiguous query with single interpretation (no clarification)
3-2 = Minimally fulfilled - most intentions ignored or inadequately addressed
1 = Not fulfilled - intentions completely ignored or dismissed

IMPORTANT: When evaluating ambiguous questions, consider if the bot's interpretation is reasonable given its domain/role.

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the completeness assessment"
}}

Your response should be ONLY the JSON object, nothing else."""

        try:
            if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                self.model.generate
            ):
                response = await self.model.generate(completeness_prompt)
            else:
                response = self.model.generate(completeness_prompt)

            result = parse_score_with_reasoning(response)
            return result
        except Exception as e:
            return ScoreWithReasoning(
                score=0.5, reasoning=f"Failed to evaluate completeness: {e!s}"
            )

    async def _extract_user_intentions(self, conversation: Conversation) -> list[str]:
        """Extract user intentions from conversation."""
        user_messages = [
            turn.message for turn in conversation.turns if turn.speaker == "user"
        ]

        if not user_messages:
            return []

        combined_messages = "\n".join(user_messages)

        intention_prompt = f"""Analyze the user messages and identify their main intentions or goals.

User messages:
{combined_messages}

What does the user want to achieve? List the main intentions as:
1. [Intention 1]
2. [Intention 2]
...

If no clear intentions are present, respond with "None"."""

        try:
            if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                self.model.generate
            ):
                response = await self.model.generate(intention_prompt)
            else:
                response = self.model.generate(intention_prompt)
            return self._parse_intentions(response)
        except Exception:
            return []

    def _parse_intentions(self, response: str) -> list[str]:
        """Parse intentions from LLM response."""
        intentions: list[str] = []

        if response.strip().lower() == "none":
            return intentions

        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            # Match numbered items
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                intention = match.group(1).strip()
                if intention:
                    intentions.append(intention)

        return intentions

    async def _simple_completeness_score(
        self, prediction: str, ground_truth: str
    ) -> ScoreWithReasoning:
        """Fallback simple completeness scoring."""
        # Simple heuristic based on response length and content
        if len(prediction.strip()) < 10:
            return ScoreWithReasoning(
                score=0.2,
                reasoning="Response is very short (< 10 characters), likely incomplete.",
            )

        if "sorry" in prediction.lower() or "can't" in prediction.lower():
            return ScoreWithReasoning(
                score=0.4,
                reasoning="Response contains apologetic or refusal language, suggesting partial completeness.",
            )

        return ScoreWithReasoning(
            score=0.7,
            reasoning="No conversation context available. Response appears substantial based on length.",
        )


class RoleAdherenceScorer(BaseScorer):
    """
    Evaluates role adherence in conversations.

    Assesses whether the assistant maintains its assigned role throughout
    the conversation and behaves consistently with role expectations.
    """

    def __init__(self, model: LLMModel, expected_role: Optional[str] = None):
        super().__init__(
            name="Role Adherence",
            description="Evaluates how well responses maintain consistency with assigned persona, role, or character throughout conversations",
        )
        self.model = model
        self.expected_role = expected_role

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Evaluate role adherence.

        Args:
            input_text: The input/context for the conversation
            output_text: The model's response to evaluate
            expected_output: Expected response (optional)
            context: Additional context including conversation history

        Returns:
            ScoreResult with score, pass/fail status, and reasoning
        """
        # Input validation with proper type checking
        if not isinstance(output_text, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: output_text must be a string",
                metadata={
                    "error": "type_error",
                    "input_type": type(output_text).__name__,
                },
            )

        # Additional validation for empty strings (safe now that we've checked types)
        if not output_text or not output_text.strip():
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only output text",
                metadata={"error": "empty_output"},
            )

        try:
            result = await self._evaluate_role_adherence_async(output_text, context)
            self._track_score(result.score)

            passed = result.score >= 7.0  # Default threshold on 1-10 scale

            return ScoreResult(
                score=result.score,
                passed=passed,
                reasoning=result.reasoning,
                metadata={
                    "scorer": "role_adherence",
                    "model": (
                        self.model.name if hasattr(self.model, "name") else "unknown"
                    ),
                    "expected_role": self.expected_role,
                },
            )
        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {e!s}",
                metadata={"error": "evaluation_error", "exception": str(e)},
            )

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> float:
        """
        Legacy synchronous score method for backward compatibility.

        Note: This method is deprecated. Use evaluate() for new code.
        """
        # Input validation with proper type checking
        if not isinstance(prediction, str) or not isinstance(ground_truth, str):
            return 0.0

        # Safe to call strip() now
        if (
            not prediction
            or not prediction.strip()
            or not ground_truth
            or not ground_truth.strip()
        ):
            return 0.0

        try:
            result = _run_async_in_sync_context(
                self.evaluate(
                    input_text="",
                    output_text=prediction,
                    expected_output=ground_truth,
                    context=context,
                )
            )
            return result.score
        except Exception:
            return 0.0

    async def _evaluate_role_adherence_async(
        self, prediction: str, context: Optional[dict[str, Any]]
    ) -> ScoreWithReasoning:
        """Async evaluation of role adherence."""
        # Determine expected role - prioritize system_prompt from context
        role = self.expected_role

        # First try to get system_prompt from context (most detailed role definition)
        if context and "system_prompt" in context:
            role = context["system_prompt"]
        # Fallback to conversation context
        elif not role and context and "conversation" in context:
            conversation = context["conversation"]
            if isinstance(conversation, Conversation) and conversation.context:
                role = conversation.context

        if not role:
            return ScoreWithReasoning(
                score=-1.0, reasoning="No role defined; perfect adherence by default."
            )

        # Check if retrieval was used (from context metadata)
        retrieval_used = context.get("retrieval_used", False) if context else False
        tool_calls = context.get("tool_calls", []) if context else []
        retrieval_queries = context.get("retrieval_queries", []) if context else []

        # Build detailed retrieval info string for prompt
        retrieval_info = ""
        if retrieval_used and retrieval_queries:
            queries_str = ", ".join(
                [
                    q.get("query", "") if isinstance(q, dict) else str(q)
                    for q in retrieval_queries[:3]
                ]
            )
            retrieval_info = f"\n\nRetrieval Info: Agent called knowledge retrieval tool with queries: [{queries_str}] (followed truth_first rule ✓)"
        elif tool_calls:
            tool_names = ", ".join(
                [
                    tc.get("tool_name", "") if isinstance(tc, dict) else ""
                    for tc in tool_calls[:3]
                ]
            )
            retrieval_info = f"\n\nRetrieval Info: Agent called tools: [{tool_names}] but no KB retrieval"
        else:
            retrieval_info = "\n\nRetrieval Info: Agent did NOT call ANY tools or retrieval (may violate truth_first if role requires it for this question)"

        role_prompt = f"""Evaluate how well this response adheres to the expected role:

Expected Role: {role}{retrieval_info}
Response: "{prediction}"

Evaluate on a scale of 1-10:
10 = Perfect role adherence, stays completely in character AND follows all rules
9-8 = Excellent adherence with very minor deviations
7-6 = Good adherence, mostly appropriate
5-4 = Adequate adherence with some inconsistencies, OR politely declining out-of-scope questions
3-2 = Poor adherence, significant role breaks
1 = No adherence, actively breaking character OR severe rule violations

IMPORTANT SCORING GUIDELINES:

**For conversational pleasantries** (greetings, acknowledgments, thanks):
- User: "Hi/Hello/Ok/Thanks/Got it" → Bot: polite response WITHOUT retrieval = Score 8-10 (appropriate - no knowledge needed)
- These are social interactions, NOT knowledge queries - retrieval is NOT required

**For "truth_first" / knowledge-based roles (KNOWLEDGE QUERIES ONLY):**
- User asks factual question AND retrieval was used: Score normally (8-10 if good)
- User asks factual question AND NO retrieval used BUT answer seems accurate: Score 3-4 (probable violation)
- User asks factual question AND NO retrieval used AND answer is generic/hallucinated: Score 1-2 (severe violation)
- Simple procedural question answered correctly WITHOUT retrieval: Score 5-6 (adequate - might be common knowledge)

**For out-of-scope questions:**
- **Politely declining** = Score 4-5 (adequate - should redirect but doesn't break character)
- **Actively answering out-of-domain as if in-domain** = Score 1-2 (complete role break)

**For persona rule violations:**
- Mentioning competitors, forbidden phrases, privacy violations = Score 1-3 (severe)

Consider:
- Does the response match the expected personality/expertise?
- Is the tone and language appropriate?
- Does it maintain role consistency?
- If retrieval is required, was it used? If not, is the answer still appropriate?
- If out-of-scope: Does it politely decline OR actively break character?

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the role adherence assessment"
}}

Your response should be ONLY the JSON object, nothing else."""

        try:
            if hasattr(self.model, "generate") and asyncio.iscoroutinefunction(
                self.model.generate
            ):
                response = await self.model.generate(role_prompt)
            else:
                response = self.model.generate(role_prompt)

            result = parse_score_with_reasoning(response)
            return result
        except Exception as e:
            return ScoreWithReasoning(
                score=0.5, reasoning=f"Failed to evaluate role adherence: {e!s}"
            )


class ConversationalMetricsScorer(BaseScorer):
    """
    Comprehensive conversational metrics scorer.

    Combines multiple conversational metrics to provide a holistic evaluation
    of conversation quality, including knowledge retention, relevancy,
    completeness, and role adherence.
    """

    def __init__(
        self,
        model: LLMModel,
        include_knowledge_retention: bool = True,
        include_relevancy: bool = True,
        include_completeness: bool = True,
        include_role_adherence: bool = True,
        window_size: int = 5,
        expected_role: Optional[str] = None,
    ):
        super().__init__(
            name="Conversational Metrics",
            description="Comprehensive conversational evaluation combining multiple metrics: knowledge retention, relevancy, completeness, and role adherence",
        )
        self.model = model
        self.include_knowledge_retention = include_knowledge_retention
        self.include_relevancy = include_relevancy
        self.include_completeness = include_completeness
        self.include_role_adherence = include_role_adherence

        # Initialize individual scorers
        if include_knowledge_retention:
            self.knowledge_scorer = KnowledgeRetentionScorer(model, window_size)
        if include_relevancy:
            self.relevancy_scorer = ConversationRelevancyScorer(model, window_size)
        if include_completeness:
            self.completeness_scorer = ConversationCompletenessScorer(model)
        if include_role_adherence:
            self.role_scorer = RoleAdherenceScorer(model, expected_role)

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """
        Evaluate using multiple conversational metrics.

        Args:
            input_text: The input/context for the conversation
            output_text: The model's response to evaluate
            expected_output: Expected response (optional)
            context: Additional context including conversation history

        Returns:
            ScoreResult with combined scores and detailed reasoning
        """
        # Input validation with proper type checking
        if not isinstance(output_text, str):
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Invalid input: output_text must be a string",
                metadata={
                    "error": "type_error",
                    "input_type": type(output_text).__name__,
                },
            )

        # Additional validation for empty strings (safe now that we've checked types)
        if not output_text or not output_text.strip():
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Empty or whitespace-only output text",
                metadata={"error": "empty_output"},
            )

        scores = {}
        results = {}

        try:
            # Evaluate each enabled metric
            if self.include_knowledge_retention:
                result = await self.knowledge_scorer.evaluate(
                    input_text, output_text, expected_output, context
                )
                scores["knowledge_retention"] = result.score
                results["knowledge_retention"] = result

            if self.include_relevancy:
                result = await self.relevancy_scorer.evaluate(
                    input_text, output_text, expected_output, context
                )
                scores["relevancy"] = result.score
                results["relevancy"] = result

            if self.include_completeness:
                result = await self.completeness_scorer.evaluate(
                    input_text, output_text, expected_output, context
                )
                scores["completeness"] = result.score
                results["completeness"] = result

            if self.include_role_adherence:
                result = await self.role_scorer.evaluate(
                    input_text, output_text, expected_output, context
                )
                scores["role_adherence"] = result.score
                results["role_adherence"] = result

            # Calculate overall score as average
            overall_score = sum(scores.values()) / len(scores) if scores else 0.0
            passed = overall_score >= 7.0  # Default threshold on 1-10 scale

            # Generate combined reasoning
            reasoning = self._generate_combined_reasoning(scores, results)

            self._track_score(overall_score)

            return ScoreResult(
                score=overall_score,
                passed=passed,
                reasoning=reasoning,
                metadata={
                    "scorer": "conversational_metrics",
                    "individual_scores": scores,
                    "enabled_metrics": {
                        "knowledge_retention": self.include_knowledge_retention,
                        "relevancy": self.include_relevancy,
                        "completeness": self.include_completeness,
                        "role_adherence": self.include_role_adherence,
                    },
                },
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {e!s}",
                metadata={"error": "evaluation_error", "exception": str(e)},
            )

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, float]:
        """
        Legacy synchronous score method for backward compatibility.

        Note: This method is deprecated. Use evaluate() for new code.

        Returns:
            Dictionary with individual metric scores and overall score
        """
        # Input validation with proper type checking
        if not isinstance(prediction, str) or not isinstance(ground_truth, str):
            return {"overall": 0.0}

        # Safe to call strip() now
        if (
            not prediction
            or not prediction.strip()
            or not ground_truth
            or not ground_truth.strip()
        ):
            return {"overall": 0.0}

        try:
            result = _run_async_in_sync_context(
                self.evaluate(
                    input_text="",
                    output_text=prediction,
                    expected_output=ground_truth,
                    context=context,
                )
            )
            # Extract individual scores from metadata
            individual_scores = result.metadata.get("individual_scores", {})
            individual_scores["overall"] = result.score
            return individual_scores
        except Exception:
            return {"overall": 0.0}

    def _generate_combined_reasoning(
        self, scores: dict[str, float], results: dict[str, ScoreResult]
    ) -> str:
        """Generate combined reasoning from all metric results."""
        overall_score = sum(scores.values()) / len(scores) if scores else 0.0

        reasoning_parts = [
            f"Combined conversational metrics score: {overall_score:.2f}\n"
        ]
        reasoning_parts.append("Individual metric breakdown:\n")

        for metric, score in scores.items():
            metric_name = metric.replace("_", " ").title()
            reasoning_parts.append(f"--- {metric_name} (Score: {score:.2f}) ---")

            # Include the actual reasoning from each scorer
            if metric in results:
                reasoning_parts.append(f"{results[metric].reasoning}\n")

        return "\n".join(reasoning_parts)
