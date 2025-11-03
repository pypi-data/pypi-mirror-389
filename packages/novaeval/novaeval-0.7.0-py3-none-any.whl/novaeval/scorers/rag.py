"""
RAG (Retrieval-Augmented Generation) specific scorers for NovaEval.

This module implements various metrics for evaluating RAG systems including:
- Answer Relevancy
- Faithfulness
- Contextual Precision
- Contextual Recall
- Contextual Relevancy
- RAGAS metrics
"""

import asyncio
import logging
from typing import Any, Optional, Union

import numpy as np

from novaeval.models.base import BaseModel as LLMModel
from novaeval.scorers.base import BaseScorer, ScoreResult
from novaeval.scorers.conversational import (
    _run_async_in_sync_context,
    parse_score_with_reasoning,
)
from novaeval.scorers.rag_prompts import RAGPrompts
from novaeval.utils.parsing import parse_claims

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    # Fallback for when sentence_transformers is not installed
    SentenceTransformer = None  # type: ignore


class RAGScorerMixin:
    """
    Mixin class providing common methods for RAG scorers.

    This mixin provides the evaluate_multiple_queries and _evaluate_single_query_with_contexts
    methods that are expected by the test suite for all RAG scorers.
    """

    async def _call_generate(self, *args: Any, **kwargs: Any) -> str:
        """
        Coroutine-safe adapter for model.generate that handles both sync and async implementations.

        This method detects whether self.model.generate is a coroutine function or returns an
        awaitable, and if it's synchronous, runs it safely in a thread via asyncio.to_thread
        to avoid blocking the event loop.
        """
        import asyncio
        import inspect

        gen = self.model.generate  # type: ignore[attr-defined]
        if inspect.iscoroutinefunction(gen):
            return await gen(*args, **kwargs)  # type: ignore[misc]
        # Offload sync call
        result = await asyncio.to_thread(gen, *args, **kwargs)
        # Some sync wrappers may return an awaitable; handle it
        if inspect.isawaitable(result):
            return await result  # type: ignore[misc]
        return result  # type: ignore[return-value]

    async def evaluate_multiple_queries(
        self,
        queries: list[str],
        contexts: list[list[str]],
        answer: str,
    ) -> list[float]:
        """Evaluate multiple queries and return scores."""
        if len(queries) != len(contexts):
            raise ValueError("Length mismatch between queries and contexts")

        scores = []
        for query, context_list in zip(queries, contexts):
            context_text = " ".join(context_list) if context_list else ""
            # Type ignore: evaluate method is provided by the concrete scorer class
            result = await self.evaluate(  # type: ignore[attr-defined]
                input_text=query,
                output_text=answer,
                context=context_text,
            )
            scores.append(result.score)
        return scores

    async def _evaluate_single_query_with_contexts(
        self,
        query: str,
        contexts: list[str],
        answer: str,
        expected_output: Optional[str] = None,
    ) -> float:
        """Evaluate a single query with multiple contexts."""
        if not contexts:
            return 0.0

        context_text = " ".join(contexts) if contexts else ""
        # Type ignore: evaluate method is provided by the concrete scorer class
        result = await self.evaluate(  # type: ignore[attr-defined]
            input_text=query,
            output_text=answer,
            expected_output=expected_output,
            context=context_text,
        )
        return result.score


class AnswerRelevancyScorer(RAGScorerMixin, BaseScorer):
    """
    Evaluates how relevant the answer is to the given question.

    This metric measures whether the response directly addresses the question
    and provides relevant information.
    """

    def __init__(
        self,
        model: LLMModel,
        threshold: float = 0.7,
        embedding_model: str = "all-MiniLM-L6-v2",
        **kwargs: Any,
    ) -> None:
        super().__init__(name=kwargs.pop("name", "AnswerRelevancyScorer"), **kwargs)
        self.threshold = threshold
        self.model = model
        self.embedding_model_name = embedding_model
        self.embedding_model: Optional[SentenceTransformer] = None
        self._model_loaded = False

        # Load embedding model during initialization
        self._load_embedding_model()

    def _load_embedding_model(self) -> None:
        """Load the sentence transformer model with error handling."""
        if self._model_loaded:
            return  # Already loaded, return early to make function idempotent

        try:
            if SentenceTransformer is None:
                raise ImportError("sentence_transformers not available")

            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self._model_loaded = True
        except ImportError:
            self.embedding_model = None
            logging.warning(
                "sentence_transformers not installed. "
                "Answer relevancy scoring will use fallback method."
            )
            self._model_loaded = True  # Set to True to prevent re-attempting
        except Exception as e:
            self.embedding_model = None
            logging.exception(f"Could not load SentenceTransformer model: {e}")
            self._model_loaded = True  # Set to True to prevent re-attempting

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Union[float, dict[str, float], ScoreResult]:
        """Synchronous wrapper for the async evaluate method."""

        # Extract context from dict if available
        context_text = context.get("context") if context else None
        question = context.get("question") if context else ground_truth

        # Run async evaluation (safe in both sync/async callers)
        result = _run_async_in_sync_context(
            self.evaluate(
                input_text=(
                    question if question is not None else ""
                ),  # Use actual question as input
                output_text=prediction,
                context=context_text,
            )
        )

        # Return full ScoreResult to preserve reasoning (not just score float)
        return result

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Evaluate answer relevancy."""

        # Handle None inputs
        if not input_text or not output_text:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Input text or output text is empty or None",
                metadata={},
            )

        # Special case: Simple conversational greetings/acknowledgments
        greeting_keywords = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "thanks",
            "thank you",
            "ok",
            "okay",
            "yes",
            "no",
            "bye",
            "goodbye",
        ]
        input_lower = input_text.lower().strip()
        output_lower = output_text.lower().strip()

        if (
            len(input_lower.split()) <= 3
            and any(kw in input_lower for kw in greeting_keywords)
        ) or (
            len(output_lower.split()) <= 10
            and any(kw in output_lower for kw in greeting_keywords)
        ):
            # This is a simple conversational exchange
            return ScoreResult(
                score=8.5,  # High relevancy for appropriate greeting responses
                passed=True,
                reasoning="Simple conversational greeting/acknowledgment - appropriate response with high relevancy",
                metadata={"special_case": "greeting_exchange"},
            )

        # Special case: Very short questions (1-3 words) with detailed answers
        # Example: "Ivr?" → detailed IVR setup instructions
        # Note: We use semantic validation to ensure the answer is actually relevant
        input_words = input_lower.split()
        output_words = output_lower.split()

        if len(input_words) <= 3 and len(output_words) > 20:
            # Extract key words from input (remove punctuation)
            import re

            input_key_words = [
                re.sub(r"[^\w\s]", "", w) for w in input_words if len(w) > 1
            ]

            # Check if ANY key input word appears in output (preliminary filter)
            if input_key_words:
                for key_word in input_key_words:
                    if key_word and key_word in output_lower:
                        # Keyword found - now validate semantic relevance
                        # Use LLM-based semantic similarity to confirm the answer is actually relevant
                        similarity_prompt = f"""Rate the semantic relevance between this question and answer on a scale of 0-10:

Question: {input_text}
Answer: {output_text[:500]}

10 = Answer directly and completely addresses the question
9-8 = Answer is highly relevant and addresses the question well
7-6 = Answer is relevant with minor gaps
5-4 = Answer is somewhat relevant but incomplete
3-2 = Answer is loosely related
1 = Answer is not relevant to the question

Respond with ONLY a number from 0-10, nothing else."""

                        try:
                            sim_response = await self._call_generate(similarity_prompt)
                            # Extract number from response
                            match = re.search(
                                r"\b([0-9]|10)(?:\.\d+)?\b", sim_response.strip()
                            )
                            semantic_score = float(match.group(0)) if match else 5.0

                            # Only return high score if semantic validation passes
                            if semantic_score >= 7.0:
                                return ScoreResult(
                                    score=semantic_score,
                                    passed=True,
                                    reasoning=f"Short question '{input_text}' answered with semantically relevant detailed response (semantic score: {semantic_score:.1f}/10)",
                                    metadata={
                                        "special_case": "short_question_detailed_answer",
                                        "input_length": len(input_words),
                                        "semantic_score": semantic_score,
                                        "matched_keyword": key_word,
                                    },
                                )
                        except Exception:
                            # If semantic validation fails, fall through to main evaluation
                            pass

        # Generate questions that the answer could be answering
        question_generation_prompt = f"""
        Given the following answer, generate 3-5 questions that this answer could be responding to.
        The questions should be specific and directly related to the content of the answer.

        Answer: {output_text}

        Generate questions in the following format:
        1. [Question 1]
        2. [Question 2]
        3. [Question 3]
        ...
        """

        try:
            generated_questions_response = await self._call_generate(
                question_generation_prompt
            )
            generated_questions = self._parse_questions(generated_questions_response)

            if not generated_questions:
                return ScoreResult(
                    score=0.0,
                    passed=False,
                    reasoning="Failed to generate questions from the answer",
                    metadata={"error": "question_generation_failed"},
                )

            # Calculate semantic similarity between original question and generated
            # questions
            self._load_embedding_model()

            # Track whether we used a fallback method
            used_fallback = False
            fallback_reason = None

            if self.embedding_model is None:
                # Fallback to LLM-based similarity if embedding model is not available
                # LLM fallback is much better than token-overlap for semantic similarity
                used_fallback = True
                fallback_reason = "embedding_model_not_available_using_llm"
                similarities = []

                for gen_question in generated_questions:
                    # Use LLM to evaluate semantic similarity (0-10 scale)
                    similarity_prompt = f"""Rate the semantic similarity between these two questions on a scale of 0-10:

Question 1: {input_text}
Question 2: {gen_question}

10 = Identical meaning, asking the exact same thing
9-8 = Very similar, minor wording differences
7-6 = Similar core intent with some differences
5-4 = Somewhat related but different focus
3-2 = Loosely related
1 = Completely different

Respond with ONLY a number from 0-10, nothing else."""

                    try:
                        sim_response = await self._call_generate(similarity_prompt)
                        # Extract number from response
                        import re

                        match = re.search(
                            r"\b([0-9]|10)(?:\.\d+)?\b", sim_response.strip()
                        )
                        sim_score = float(match.group(0)) / 10.0 if match else 0.5
                    except Exception:
                        sim_score = 0.5  # Default to neutral on error

                    similarities.append(sim_score)
            else:
                # Use embedding model for semantic similarity
                try:
                    original_embedding = await asyncio.to_thread(
                        self.embedding_model.encode, [input_text]
                    )
                    generated_embeddings = await asyncio.to_thread(
                        self.embedding_model.encode, generated_questions
                    )

                    # Calculate cosine similarities
                    similarities = []
                    for gen_embedding in generated_embeddings:
                        similarity = np.dot(original_embedding[0], gen_embedding) / (
                            np.linalg.norm(original_embedding[0])
                            * np.linalg.norm(gen_embedding)
                        )
                        # Normalize cosine similarity from [-1,1] to [0,1] to match token-overlap scale
                        similarity_norm = (similarity + 1.0) / 2.0
                        similarities.append(similarity_norm)
                except Exception as e:
                    # Log the embedding error and fall back to LLM-based similarity
                    logging.warning(
                        f"Embedding encoding failed, falling back to LLM similarity: {e}"
                    )
                    used_fallback = True
                    fallback_reason = f"embedding_encoding_failed_using_llm: {e!s}"

                    # Fallback to LLM-based similarity evaluation
                    similarities = []
                    for gen_question in generated_questions:
                        similarity_prompt = f"""Rate the semantic similarity between these two questions on a scale of 0-10:

Question 1: {input_text}
Question 2: {gen_question}

10 = Identical meaning, asking the exact same thing
9-8 = Very similar, minor wording differences
7-6 = Similar core intent with some differences
5-4 = Somewhat related but different focus
3-2 = Loosely related
1 = Completely different

Respond with ONLY a number from 0-10, nothing else."""

                        try:
                            sim_response = await self._call_generate(similarity_prompt)
                            import re

                            match = re.search(
                                r"\b([0-9]|10)(?:\.\d+)?\b", sim_response.strip()
                            )
                            sim_score = float(match.group(0)) / 10.0 if match else 0.5
                        except Exception:
                            sim_score = 0.5  # Default to neutral on error

                        similarities.append(sim_score)

            # Use mean similarity as the relevancy score (scale to 1-10)
            mean_similarity = float(np.mean(similarities))
            relevancy_score = mean_similarity * 10.0  # Convert 0-1 to 1-10 scale

            # Build reasoning with fallback information
            if used_fallback:
                if fallback_reason and "llm" in fallback_reason.lower():
                    similarity_method = "LLM-based semantic similarity"
                else:
                    similarity_method = "fallback method"
            else:
                similarity_method = "semantic embedding"

            fallback_info = f" (fallback: {fallback_reason})" if used_fallback else ""

            reasoning = f"""Answer Relevancy Analysis:
- Generated {len(generated_questions)} questions from the answer
- Calculated {similarity_method} with original question{fallback_info}
- Individual similarities: {[f'{s:.3f}' for s in similarities]}
- Mean similarity: {mean_similarity:.3f} (0-1 scale)
- Relevancy score: {relevancy_score:.1f}/10

Generated questions:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(generated_questions))}"""

            metadata = {
                "generated_questions": generated_questions,
                "similarities": similarities,
                "mean_similarity": mean_similarity,
                "raw_score": relevancy_score,
                "similarity_method": similarity_method,
            }

            if used_fallback:
                metadata["fallback_reason"] = fallback_reason

            # Return with 1-10 scaled score
            return ScoreResult(
                score=relevancy_score,  # 1-10 scale
                passed=relevancy_score
                >= (self.threshold * 10.0 if self.threshold < 1.0 else self.threshold),
                reasoning=reasoning.strip(),
                metadata=metadata,
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Answer relevancy evaluation failed: {e!s}",
                metadata={"error": str(e)},
            )

    def _parse_questions(self, response: str) -> list[str]:
        """Parse generated questions from LLM response."""
        questions = []
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line and (
                line[0].isdigit() or line.startswith("-") or line.startswith("*")
            ):
                # Remove numbering and bullet points
                question = line
                for prefix in ["1.", "2.", "3.", "4.", "5.", "-", "*"]:
                    if question.startswith(prefix):
                        question = question[len(prefix) :].strip()
                        break

                if question and question.endswith("?"):
                    questions.append(question)

        return questions


class FaithfulnessScorer(RAGScorerMixin, BaseScorer):
    """
    Evaluates whether the answer is faithful to the provided context.

    This metric measures if the response contains information that can be
    verified from the given context without hallucinations.
    """

    def __init__(self, model: LLMModel, threshold: float = 0.8, **kwargs: Any) -> None:
        super().__init__(name=kwargs.pop("name", "FaithfulnessScorer"), **kwargs)
        self.threshold = threshold
        self.model = model

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Union[float, dict[str, float], ScoreResult]:
        """Synchronous wrapper for the async evaluate method."""

        # Extract context from dict if available
        context_text = context.get("context") if context else None
        question = context.get("question") if context else ground_truth

        # Run async evaluation (safe in both sync/async callers)
        result = _run_async_in_sync_context(
            self.evaluate(
                input_text=(
                    question if question is not None else ""
                ),  # Use actual question as input
                output_text=prediction,
                context=context_text,
            )
        )

        # Return full ScoreResult to preserve reasoning
        return result

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Evaluate faithfulness to context."""

        if not context:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context provided for faithfulness evaluation",
                metadata={"error": "no_context"},
            )

        # Extract claims from the answer
        claims_extraction_prompt = f"""
        Extract all factual claims from the following answer.
        List each claim as a separate statement that can be verified.

        Answer: {output_text}

        Format your response as:
        1. [Claim 1]
        2. [Claim 2]
        3. [Claim 3]
        ...
        """

        try:
            claims_response = await self._call_generate(claims_extraction_prompt)
            claims = self._parse_claims(claims_response)

            if not claims:
                return ScoreResult(
                    score=-1.0,  # No claims means no unfaithful content
                    passed=True,
                    reasoning="No factual claims found in the answer",
                    metadata={"claims": []},
                )

            # Verify each claim against the context
            verification_results = []
            claim_scores = []

            for claim in claims:
                verification_prompt = f"""
Context: {context}

Claim to verify: {claim}

Evaluate how well this claim is supported by the context.

Evaluate on a scale of 1-10:
10 = Fully supported, directly stated in context
9-8 = Strongly supported with clear evidence
7-6 = Well supported with good evidence
5-4 = Partially supported, some evidence present
3-2 = Weakly supported, minimal evidence
1 = Not supported or contradicts context

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the verification"
}}

Your response should be ONLY the JSON object, nothing else.
"""

                verification_response = await self._call_generate(verification_prompt)
                parsed_result = parse_score_with_reasoning(verification_response)
                verification_results.append((claim, parsed_result))
                claim_scores.append(parsed_result.score)

            # Calculate faithfulness score (average of claim scores on 1-10 scale)
            total_claims = len(claims)
            faithfulness_score = sum(claim_scores) / total_claims

            # Build reasoning from individual claim verifications
            reasoning_parts = [
                "Faithfulness Analysis:",
                f"- Extracted {total_claims} claims from the answer",
                f"- Average claim support score: {sum(claim_scores) / total_claims:.2f}/10",
                f"- Overall faithfulness score: {faithfulness_score:.2f}/10",
                "",
                "Claim verification details:",
            ]

            for claim, result in verification_results:
                reasoning_parts.append(f"• Claim: {claim}")
                reasoning_parts.append(f"  Score: {result.score}/10")
                reasoning_parts.append(f"  {result.reasoning}")
                reasoning_parts.append("")

            return ScoreResult(
                score=faithfulness_score,
                passed=faithfulness_score >= self.threshold,
                reasoning="\n".join(reasoning_parts).strip(),
                metadata={
                    "claims": claims,
                    "claim_scores": claim_scores,
                    "average_claim_score": sum(claim_scores) / total_claims,
                    "total_claims": total_claims,
                },
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Faithfulness evaluation failed: {e!s}",
                metadata={"error": str(e)},
            )

    def _parse_claims(self, response: str) -> list[str]:
        """Parse claims from LLM response."""
        return parse_claims(response)


class ContextualPrecisionScorer(RAGScorerMixin, BaseScorer):
    """
    Evaluates the precision of the retrieved context.

    This metric measures whether the retrieved context contains relevant
    information for answering the question.
    """

    def __init__(self, model: LLMModel, threshold: float = 0.7, **kwargs: Any) -> None:
        super().__init__(name=kwargs.pop("name", "ContextualPrecisionScorer"), **kwargs)
        self.threshold = threshold
        self.model = model

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Union[float, dict[str, float], ScoreResult]:
        """Synchronous wrapper for the async evaluate method."""

        # Extract context from dict if available
        context_text = context.get("context") if context else None
        question = context.get("question") if context else ground_truth

        # Run async evaluation (safe in both sync/async callers)
        result = _run_async_in_sync_context(
            self.evaluate(
                input_text=(
                    question if question is not None else ""
                ),  # Use actual question as input
                output_text=prediction,
                context=context_text,
            )
        )

        # Return full ScoreResult to preserve reasoning
        return result

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Evaluate contextual precision."""

        if not context:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context provided for contextual precision evaluation",
                metadata={"error": "no_context"},
            )

        # Split context into chunks (assuming it's a concatenated retrieval result)
        context_chunks = self._split_context(context)

        if not context_chunks:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="No context chunks found",
                metadata={"error": "no_chunks"},
            )

        try:
            # Evaluate relevance of each context chunk
            chunk_results = []
            relevance_scores = []

            for i, chunk in enumerate(context_chunks):
                relevance_prompt = RAGPrompts.get_numerical_chunk_relevance_1_10(
                    input_text, chunk
                )

                relevance_response = await self._call_generate(relevance_prompt)
                parsed_result = parse_score_with_reasoning(relevance_response)
                chunk_results.append((i + 1, chunk, parsed_result))
                relevance_scores.append(parsed_result.score)

            # Calculate precision as the average relevance score on 1-10 scale
            precision_score = sum(relevance_scores) / len(relevance_scores)

            # Build reasoning from individual chunk evaluations
            reasoning_parts = [
                "Contextual Precision Analysis:",
                f"- Evaluated {len(context_chunks)} context chunks",
                f"- Average relevance score: {sum(relevance_scores) / len(relevance_scores):.2f}/10",
                f"- Precision score: {precision_score:.2f}/10",
                "",
                "Chunk relevance details:",
            ]

            for chunk_num, chunk_text, result in chunk_results:
                chunk_preview = (
                    chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
                )
                reasoning_parts.append(f"• Chunk {chunk_num}: {result.score}/10")
                reasoning_parts.append(f"  Preview: {chunk_preview}")
                reasoning_parts.append(f"  {result.reasoning}")
                reasoning_parts.append("")

            return ScoreResult(
                score=precision_score,
                passed=precision_score >= self.threshold,
                reasoning="\n".join(reasoning_parts).strip(),
                metadata={
                    "context_chunks": len(context_chunks),
                    "relevance_scores": relevance_scores,
                    "average_relevance": sum(relevance_scores) / len(relevance_scores),
                },
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Contextual precision evaluation failed: {e!s}",
                metadata={"error": str(e)},
            )

    def _split_context(self, context: str) -> list[str]:
        """Split context into chunks for evaluation."""
        # Simple splitting by double newlines or sentences
        chunks = []

        # Try splitting by double newlines first
        parts = context.split("\n\n")
        if len(parts) > 1:
            chunks = [part.strip() for part in parts if part.strip()]
        else:
            # Split by sentences if no paragraph breaks
            import re

            sentences = re.split(r"[.!?]+", context)
            chunks = [sent.strip() for sent in sentences if sent.strip()]

        # Ensure chunks are not too small
        min_length = 50
        filtered_chunks = [chunk for chunk in chunks if len(chunk) >= min_length]

        return filtered_chunks if filtered_chunks else [context]


class ContextualRecallScorer(RAGScorerMixin, BaseScorer):
    """
    Evaluates the recall of the retrieved context.

    This metric measures whether all necessary information for answering
    the question is present in the retrieved context.
    """

    def __init__(self, model: LLMModel, threshold: float = 0.7, **kwargs: Any) -> None:
        super().__init__(name=kwargs.pop("name", "ContextualRecallScorer"), **kwargs)
        self.threshold = threshold
        self.model = model

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        """Synchronous wrapper for the async evaluate method."""

        # Extract context and expected_output from dict if available
        context_text = context.get("context") if context else None
        expected_output = context.get("expected_output") if context else None
        question = context.get("question") if context else ground_truth

        # Run async evaluation (safe in both sync/async callers)
        result = _run_async_in_sync_context(
            self.evaluate(
                input_text=(
                    question if question is not None else ""
                ),  # Use actual question as input
                output_text=prediction,
                expected_output=expected_output,
                context=context_text,
            )
        )

        return result

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Evaluate contextual recall."""

        if not context or not expected_output:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning="Both context and expected output are required for contextual recall evaluation",
                metadata={"error": "missing_inputs"},
            )

        try:
            # Extract key information from expected output
            key_info_prompt = f"""
            Extract the key pieces of information from the following expected answer.
            List each key fact or piece of information separately.

            Expected Answer: {expected_output}

            Format your response as:
            1. [Key information 1]
            2. [Key information 2]
            3. [Key information 3]
            ...
            """

            key_info_response = await self._call_generate(key_info_prompt)
            key_information = self._parse_claims(key_info_response)

            if not key_information:
                return ScoreResult(
                    score=-1.0,  # No key info means perfect recall
                    passed=True,
                    reasoning="No key information extracted from expected output",
                    metadata={"key_information": []},
                )

            # Check if each key information is present in the context
            recall_results = []
            info_scores = []

            for info in key_information:
                recall_prompt = f"""
Context: {context}

Key information to find: {info}

Evaluate how well this key information is represented in the context.

Evaluate on a scale of 1-10:
10 = Fully present, explicitly stated in context
9-8 = Strongly present with clear evidence
7-6 = Well represented with good evidence
5-4 = Partially present, some evidence found
3-2 = Weakly present, minimal evidence
1 = Not present or missing from context

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the presence assessment"
}}

Your response should be ONLY the JSON object, nothing else.
"""

                recall_response = await self._call_generate(recall_prompt)
                parsed_result = parse_score_with_reasoning(recall_response)
                recall_results.append((info, parsed_result))
                info_scores.append(parsed_result.score)

            # Calculate recall score (average of info scores on 1-10 scale)
            total_info = len(key_information)
            recall_score = sum(info_scores) / total_info

            # Build reasoning from individual information checks
            reasoning_parts = [
                "Contextual Recall Analysis:",
                f"- Extracted {total_info} key pieces of information from expected output",
                f"- Average presence score: {sum(info_scores) / total_info:.2f}/10",
                f"- Recall score: {recall_score:.2f}/10",
                "",
                "Information presence details:",
            ]

            for info, result in recall_results:
                reasoning_parts.append(f"• Key information: {info}")
                reasoning_parts.append(f"  Score: {result.score}/10")
                reasoning_parts.append(f"  {result.reasoning}")
                reasoning_parts.append("")

            return ScoreResult(
                score=recall_score,
                passed=recall_score >= self.threshold,
                reasoning="\n".join(reasoning_parts).strip(),
                metadata={
                    "key_information": key_information,
                    "info_scores": info_scores,
                    "average_info_score": sum(info_scores) / total_info,
                    "total_info": total_info,
                },
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"Contextual recall evaluation failed: {e!s}",
                metadata={"error": str(e)},
            )

    def _parse_claims(self, response: str) -> list[str]:
        """Parse claims/information from LLM response."""
        return parse_claims(response)


class RAGASScorer(RAGScorerMixin, BaseScorer):
    """
    Composite RAGAS (Retrieval-Augmented Generation Assessment) scorer.

    Combines multiple RAG metrics into a single comprehensive score.
    """

    def __init__(
        self,
        model: LLMModel,
        threshold: float = 0.7,
        weights: Optional[dict[str, float]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=kwargs.pop("name", "ragas_scorer"), **kwargs)
        self.threshold = threshold
        self.model = model

        # Default weights for different metrics
        self.weights = weights or {
            "answer_relevancy": 0.25,
            "faithfulness": 0.35,
            "contextual_precision": 0.2,
            "contextual_recall": 0.2,
        }

        # Initialize individual scorers
        self.answer_relevancy_scorer = AnswerRelevancyScorer(model, threshold=0.7)
        self.faithfulness_scorer = FaithfulnessScorer(model, threshold=0.8)
        self.contextual_precision_scorer = ContextualPrecisionScorer(
            model, threshold=0.7
        )
        self.contextual_recall_scorer = ContextualRecallScorer(model, threshold=0.7)

    def score(
        self,
        prediction: str,
        ground_truth: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ScoreResult:
        """Synchronous wrapper for the async evaluate method."""

        # Extract context from dict if available
        context_text = context.get("context") if context else None
        expected_output = context.get("expected_output") if context else None
        question = context.get("question") if context else ground_truth

        # Run async evaluation (safe in both sync/async callers)
        result = _run_async_in_sync_context(
            self.evaluate(
                input_text=(
                    question if question is not None else ""
                ),  # Use actual question as input
                output_text=prediction,
                context=context_text,
                expected_output=expected_output,
            )
        )

        return result

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Evaluate using RAGAS methodology."""

        try:
            # Run all individual evaluations in parallel
            results = await asyncio.gather(
                self.answer_relevancy_scorer.evaluate(
                    input_text, output_text, expected_output, context
                ),
                self.faithfulness_scorer.evaluate(
                    input_text, output_text, expected_output, context
                ),
                self.contextual_precision_scorer.evaluate(
                    input_text, output_text, expected_output, context
                ),
                self.contextual_recall_scorer.evaluate(
                    input_text, output_text, expected_output, context
                ),
                return_exceptions=True,
            )

            # Extract scores and handle exceptions
            scores = {}
            reasonings = {}

            metric_names = [
                "answer_relevancy",
                "faithfulness",
                "contextual_precision",
                "contextual_recall",
            ]

            for _i, (metric_name, result) in enumerate(zip(metric_names, results)):
                if isinstance(result, Exception):
                    scores[metric_name] = 0.0
                    reasonings[metric_name] = f"Error: {result!s}"
                elif hasattr(result, "score") and hasattr(result, "reasoning"):
                    scores[metric_name] = result.score  # type: ignore
                    reasonings[metric_name] = result.reasoning  # type: ignore
                else:
                    scores[metric_name] = 0.0
                    reasonings[metric_name] = "Unknown result type"

            # Calculate weighted average
            total_weight = sum(self.weights.values())
            ragas_score = (
                sum(scores[metric] * self.weights[metric] for metric in scores)
                / total_weight
            )

            # Compile comprehensive reasoning
            reasoning = f"""
            RAGAS Evaluation Results:

            Individual Metric Scores:
            • Answer Relevancy: {scores['answer_relevancy']:.3f} (weight: {self.weights['answer_relevancy']})
            • Faithfulness: {scores['faithfulness']:.3f} (weight: {self.weights['faithfulness']})
            • Contextual Precision: {scores['contextual_precision']:.3f} (weight: {self.weights['contextual_precision']})
            • Contextual Recall: {scores['contextual_recall']:.3f} (weight: {self.weights['contextual_recall']})

            Weighted RAGAS Score: {ragas_score:.3f}

            Detailed Analysis:
            {chr(10).join(f'{metric.replace("_", " ").title()}:{chr(10)}{reasoning}{chr(10)}' for metric, reasoning in reasonings.items())}
            """

            return ScoreResult(
                score=ragas_score,
                passed=ragas_score >= self.threshold,
                reasoning=reasoning.strip(),
                metadata={
                    "individual_scores": scores,
                    "weights": self.weights,
                    "ragas_score": ragas_score,
                },
            )

        except Exception as e:
            return ScoreResult(
                score=0.0,
                passed=False,
                reasoning=f"RAGAS evaluation failed: {e!s}",
                metadata={"error": str(e)},
            )


# Make SentenceTransformer available at module level for tests/mocking/etc.
SentenceTransformer = SentenceTransformer
