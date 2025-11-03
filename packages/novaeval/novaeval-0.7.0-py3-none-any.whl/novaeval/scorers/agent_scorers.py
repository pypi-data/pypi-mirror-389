"""
Agent scorers for evaluating agent performance using G-Eval architecture.

This module contains scoring functions for various aspects of agent behavior
including tool usage, task progression, and context relevancy.

All scorers return ScoreResult with:
- score: float (1-10 or -1 on error)
- reasoning: str (full, never truncated)
- metadata: dict (extra fields like original_task, etc.)
- passed: bool
"""

import json
from typing import Any, Union

from novaeval.agents.agent_data import AgentData
from novaeval.models.base import BaseModel as LLMModel
from novaeval.scorers.agent_scorers_system_prompts import (
    CONTEXT_RELEVANCY_PROMPT,
    PARAMETER_CORRECTNESS_PROMPT,
    ROLE_ADHERENCE_PROMPT,
    TASK_PROGRESSION_PROMPT,
    TOOL_CORRECTNESS_PROMPT,
    TOOL_RELEVANCY_PROMPT,
)
from novaeval.scorers.base import ScoreResult

# Import shared JSON parser
from novaeval.utils.json_parser import parse_llm_json_response


def safe_serialize_union_field(field_value: Any, field_name: str) -> str:
    """
    Safely serialize a union type field that can be either its original type or a string.

    Args:
        field_value: The field value which could be a complex type (list, dict, ToolCall, etc.) or string
        field_name: Name of the field (for error reporting)

    Returns:
        String representation suitable for prompt formatting
    """
    if isinstance(field_value, str):
        # If it's already a string, return it directly
        return field_value
    elif field_value is None:
        return ""
    else:
        # If it's a complex type, serialize it to JSON
        try:
            if hasattr(field_value, "model_dump"):
                # Single Pydantic model
                return json.dumps(field_value.model_dump(), indent=2)
            elif (
                isinstance(field_value, list)
                and field_value
                and hasattr(field_value[0], "model_dump")
            ):
                # List of Pydantic models
                return json.dumps([item.model_dump() for item in field_value], indent=2)
            else:
                # Plain dict, list, or other JSON-serializable type
                return json.dumps(field_value, indent=2)
        except (TypeError, AttributeError):
            # Fallback: convert to string if JSON serialization fails
            try:
                return str(field_value)
            except Exception:
                print(
                    f"Error serializing field {field_name}: {type(field_value).__name__}"
                )
                return "Error serializing field"


def safe_get_boolean_field(field_value: Any) -> bool:
    """
    Safely convert a union boolean field that can be either bool or string to boolean.

    Args:
        field_value: The field value which could be bool or string

    Returns:
        Boolean value
    """
    if isinstance(field_value, bool):
        return field_value
    elif isinstance(field_value, str):
        lower_val = field_value.lower().strip()
        return lower_val in ("true", "1", "yes", "on")
    else:
        # Fallback: convert to bool
        return bool(field_value)


# Removed ScoreWithReasoning and ScoreWithOriginalTask - using ScoreResult everywhere


def escape_json_for_format(json_str: str) -> str:
    """Escape JSON string for use in .format() method."""
    return json_str.replace("{", "{{").replace("}", "}}")


def parse_llm_score_response(
    response: str, threshold: float = 7.0, **extra_metadata: Any
) -> ScoreResult:
    """
    Parse LLM response and return ScoreResult.
    Uses shared parser that handles markdown code blocks.

    Args:
        response: Raw LLM response string
        threshold: Score threshold for passed/failed
        **extra_metadata: Additional metadata to include

    Returns:
        ScoreResult with score (1-10 or -1), reasoning (FULL, not truncated), metadata
    """
    try:
        # Use shared parser that handles markdown
        result = parse_llm_json_response(response)

        # Extract score and reasoning
        score = result.get("score", -1.0)
        reasoning = result.get("reasoning", "No reasoning provided")

        # Error check
        if score == -1:
            return ScoreResult(
                score=-1.0, passed=False, reasoning=reasoning, metadata={}
            )

        # Store ALL extra fields in metadata
        metadata = {k: v for k, v in result.items() if k not in ["score", "reasoning"]}
        metadata.update(extra_metadata)  # Add any passed metadata

        passed = score >= threshold
        return ScoreResult(
            score=float(score),
            passed=passed,
            reasoning=str(reasoning),  # FULL reasoning, never truncated
            metadata=metadata,
        )

    except Exception as e:
        return ScoreResult(
            score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
        )


# Removed Pydantic models - using ScoreResult everywhere for consistency


def tool_relevancy_scorer(
    agent_data: AgentData, model: LLMModel
) -> Union[list[ScoreResult], ScoreResult]:
    """
    Score the relevancy of tool calls given available tools.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        List of ScoreResult objects (one per tool call), or single ScoreResult with error
    """
    required_fields = {
        "tools_available": agent_data.tools_available is not None,
        "tool_calls": agent_data.tool_calls is not None
        and (isinstance(agent_data.tool_calls, str) or len(agent_data.tool_calls) > 0),
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Format the available tools once (they're the same for all calls)
    tools_available_str = escape_json_for_format(
        safe_serialize_union_field(agent_data.tools_available, "tools_available")
    )

    scores = []

    # Handle tool_calls as either list or string
    if isinstance(agent_data.tool_calls, str):
        # If tool_calls is a string, treat it as a single "tool call"
        single_tool_call_str = escape_json_for_format(agent_data.tool_calls)
        prompt = TOOL_RELEVANCY_PROMPT.format(
            tools_available=tools_available_str,
            tool_calls=f"[{single_tool_call_str}]",
        )

        try:
            response = model.generate(prompt)
            score_result = parse_llm_score_response(response, threshold=7.0)
            scores.append(score_result)
        except Exception as e:
            error_result = ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )
            scores.append(error_result)
    else:
        # Iterate over each tool call individually
        for tool_call in agent_data.tool_calls:
            # Format just this single tool call
            single_tool_call_str = escape_json_for_format(
                safe_serialize_union_field(tool_call, "tool_call")
            )

            # Create prompt for this specific tool call
            prompt = TOOL_RELEVANCY_PROMPT.format(
                tools_available=tools_available_str,
                tool_calls=f"[{single_tool_call_str}]",  # Wrap in array brackets for consistency
            )

            try:
                response = model.generate(prompt)
                score_result = parse_llm_score_response(response, threshold=7.0)
                scores.append(score_result)

            except Exception as e:
                error_result = ScoreResult(
                    score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
                )
                scores.append(error_result)

    return scores


def tool_correctness_scorer(
    agent_data: AgentData, model: LLMModel
) -> Union[list[ScoreResult], ScoreResult]:
    """
    Score the correctness of tool calls compared to expected tool call.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        List of ScoreResult objects (one per tool call), or single ScoreResult with error
    """
    required_fields = {
        "expected_tool_call": agent_data.expected_tool_call is not None,
        "tool_calls": agent_data.tool_calls is not None
        and (isinstance(agent_data.tool_calls, str) or len(agent_data.tool_calls) > 0),
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Format the expected call once (same for all comparisons)
    expected_call_str = escape_json_for_format(
        safe_serialize_union_field(agent_data.expected_tool_call, "expected_tool_call")
        if agent_data.expected_tool_call
        else ""
    )

    scores = []

    # Handle tool_calls as either list or string
    if isinstance(agent_data.tool_calls, str):
        # If tool_calls is a string, treat it as a single "tool call"
        single_tool_call_str = escape_json_for_format(agent_data.tool_calls)
        prompt = TOOL_CORRECTNESS_PROMPT.format(
            expected_tool_call=expected_call_str,
            tool_calls=f"[{single_tool_call_str}]",
        )

        try:
            response = model.generate(prompt)
            score_result = parse_llm_score_response(response, threshold=7.0)
            scores.append(score_result)
        except Exception as e:
            error_result = ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )
            scores.append(error_result)
    else:
        # Iterate over each tool call individually
        for tool_call in agent_data.tool_calls:
            # Format just this single tool call
            single_tool_call_str = escape_json_for_format(
                safe_serialize_union_field(tool_call, "tool_call")
            )

            # Create prompt for this specific tool call comparison
            prompt = TOOL_CORRECTNESS_PROMPT.format(
                expected_tool_call=expected_call_str,
                tool_calls=f"[{single_tool_call_str}]",  # Wrap in array brackets for consistency
            )

            try:
                response = model.generate(prompt)
                score_result = parse_llm_score_response(response, threshold=7.0)
                scores.append(score_result)

            except Exception as e:
                error_result = ScoreResult(
                    score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
                )
                scores.append(error_result)

    return scores


def parameter_correctness_scorer(
    agent_data: AgentData, model: LLMModel
) -> Union[list[ScoreResult], ScoreResult]:
    """
    Score the correctness of parameters passed to tool calls.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        List of ScoreResult objects (one per tool call), or single ScoreResult with error
    """
    required_fields = {
        "tool_calls": agent_data.tool_calls is not None
        and (isinstance(agent_data.tool_calls, str) or len(agent_data.tool_calls) > 0),
        "parameters_passed": agent_data.parameters_passed is not None,
        "tool_call_results": agent_data.tool_call_results is not None,
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Create a mapping of call_id to results for easier lookup
    results_by_call_id = {}
    if isinstance(agent_data.tool_call_results, str):
        # If tool_call_results is a string, we can't create a mapping, so leave it empty
        pass
    elif agent_data.tool_call_results:
        # If it's a list, create the mapping as before
        results_by_call_id = {
            result.call_id: result
            for result in agent_data.tool_call_results
            if hasattr(result, "call_id")  # Safety check in case result is a string
        }

    scores = []

    # Handle tool_calls as either list or string
    if isinstance(agent_data.tool_calls, str):
        # If tool_calls is a string, treat it as a single "tool call"
        # Create a simplified version with parameters
        single_call_with_params = {
            "tool_calls": agent_data.tool_calls,
            "mapped_parameters": safe_serialize_union_field(
                agent_data.parameters_passed, "parameters_passed"
            ),
        }

        single_tool_call_str = escape_json_for_format(
            json.dumps(single_call_with_params, indent=2)
        )
        single_result_str = escape_json_for_format(
            safe_serialize_union_field(
                agent_data.tool_call_results, "tool_call_results"
            )
        )

        prompt = PARAMETER_CORRECTNESS_PROMPT.format(
            tool_calls_with_parameters=f"[{single_tool_call_str}]",
            tool_call_results=f"[{single_result_str}]",
        )

        try:
            response = model.generate(prompt)
            score_result = parse_llm_score_response(response, threshold=7.0)
            scores.append(score_result)
        except Exception as e:
            error_result = ScoreResult(
                score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
            )
            scores.append(error_result)
    else:
        # Iterate over each tool call individually
        for tool_call in agent_data.tool_calls:
            # Find the corresponding result for this tool call
            corresponding_result = None
            if hasattr(tool_call, "call_id"):
                corresponding_result = results_by_call_id.get(tool_call.call_id)

            # Create individual tool call with parameters
            if isinstance(tool_call, str):
                # If individual tool_call is a string
                call_with_params = {
                    "tool_call": tool_call,
                    "mapped_parameters": safe_serialize_union_field(
                        agent_data.parameters_passed, "parameters_passed"
                    ),
                }
            else:
                # If tool_call is a ToolCall object
                call_with_params = {
                    "tool_call": safe_serialize_union_field(tool_call, "tool_call"),
                    "mapped_parameters": safe_serialize_union_field(
                        agent_data.parameters_passed, "parameters_passed"
                    ),
                }

            # Format just this single tool call and its result
            single_tool_call_str = escape_json_for_format(
                json.dumps(call_with_params, indent=2)
                if isinstance(call_with_params, dict)
                else str(call_with_params)
            )
            single_result_str = escape_json_for_format(
                safe_serialize_union_field(corresponding_result, "tool_call_result")
                if corresponding_result
                else "{}"
            )

            # Create prompt for this specific tool call
            prompt = PARAMETER_CORRECTNESS_PROMPT.format(
                tool_calls_with_parameters=f"[{single_tool_call_str}]",  # Wrap in array brackets
                tool_call_results=f"[{single_result_str}]",  # Wrap in array brackets
            )

            try:
                response = model.generate(prompt)
                score_result = parse_llm_score_response(response, threshold=7.0)
                scores.append(score_result)

            except Exception as e:
                error_result = ScoreResult(
                    score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
                )
                scores.append(error_result)

    return scores


def task_progression_scorer(agent_data: AgentData, model: LLMModel) -> ScoreResult:
    """
    Score how well the agent has progressed on the assigned task.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        ScoreResult with progression score (1-10 or -1 on error).
        metadata['original_task'] contains the extracted task.
    """
    required_fields = {
        "agent_task": agent_data.agent_task is not None,
        "agent_role": agent_data.agent_role is not None,
        "system_prompt": agent_data.system_prompt is not None,
        "agent_response": agent_data.agent_response is not None,
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    prompt = TASK_PROGRESSION_PROMPT.format(
        agent_role=agent_data.agent_role,
        agent_task=agent_data.agent_task,
        system_prompt=agent_data.system_prompt,
        agent_response=agent_data.agent_response,
    )

    try:
        response = model.generate(prompt)
        result = parse_llm_score_response(response, threshold=7.0)

        # Extract original_task from metadata if present, otherwise use agent_task
        if "original_task" not in result.metadata:
            result.metadata["original_task"] = agent_data.agent_task or "Unknown task"

        return result

    except Exception as e:
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Failed to evaluate task progression: {e!s}",
            metadata={"original_task": agent_data.agent_task or "Unknown task"},
        )


def context_relevancy_scorer(agent_data: AgentData, model: LLMModel) -> ScoreResult:
    """
    Score the appropriateness of the agent response given the agent's task and role.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        ScoreResult with appropriateness score (1-10 or -1 on error)
    """
    required_fields = {
        "agent_task": agent_data.agent_task is not None,
        "agent_role": agent_data.agent_role is not None,
        "agent_response": agent_data.agent_response is not None,
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    prompt = CONTEXT_RELEVANCY_PROMPT.format(
        agent_task=agent_data.agent_task,
        agent_role=agent_data.agent_role,
        agent_response=agent_data.agent_response,
    )

    try:
        response = model.generate(prompt)
        return parse_llm_score_response(response, threshold=7.0)

    except Exception as e:
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Failed to evaluate: {e!s}",
            metadata={},
        )


def role_adherence_scorer(agent_data: AgentData, model: LLMModel) -> ScoreResult:
    """
    Score whether the agent's tool calls and response adhere to its assigned role and task.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        ScoreResult with adherence score (1-10 or -1 on error)
    """
    required_fields = {
        "agent_role": agent_data.agent_role is not None,
        "agent_task": agent_data.agent_task is not None,
        "agent_response": agent_data.agent_response is not None,
        "tool_calls": agent_data.tool_calls is not None,
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Format tool calls for the prompt
    tool_calls_str = escape_json_for_format(
        safe_serialize_union_field(agent_data.tool_calls, "tool_calls")
    )

    prompt = ROLE_ADHERENCE_PROMPT.format(
        agent_role=agent_data.agent_role,
        agent_task=agent_data.agent_task,
        agent_response=agent_data.agent_response,
        tool_calls=tool_calls_str,
    )

    try:
        response = model.generate(prompt)
        return parse_llm_score_response(response, threshold=7.0)

    except Exception as e:
        return ScoreResult(
            score=-1.0, passed=False, reasoning=f"Exception: {e!s}", metadata={}
        )


def goal_achievement_scorer(agent_data: AgentData, model: LLMModel) -> ScoreResult:
    """
    Score how well the agent achieved its original goal using G-Eval structure.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        ScoreResult with goal achievement score (1-10 or -1 on error).
        metadata['original_task'] contains the extracted goal.
    """
    # Check if agent has exited
    if not safe_get_boolean_field(agent_data.agent_exit):
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning="The agent has not yet exited",
            metadata={"original_task": "N/A - Agent has not exited"},
        )

    required_fields = {
        "trace": agent_data.trace is not None
        and (isinstance(agent_data.trace, str) or len(agent_data.trace) > 0)
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Format the trace for the prompt
    trace_str = safe_serialize_union_field(agent_data.trace, "trace")

    # G-Eval structured prompt for goal achievement
    prompt = f"""# Goal Achievement Evaluation Task

## Criteria:
Evaluate how well the agent achieved its original goal based on the complete interaction trace. The agent's performance should be measured against the initial task requirements and expected outcomes.

## Score Range: 1 to 10
- 1-2: Completely failed to achieve the goal
- 3-4: Made minimal progress toward the goal
- 5-6: Made significant progress but didn't fully achieve the goal
- 7-8: Largely achieved the goal with minor issues
- 9-10: Completely achieved the goal successfully

## Evaluation Steps:
1. Identify the original task/goal from the trace
2. Analyze the agent's actions and responses throughout the interaction
3. Assess how well the agent's final state aligns with the original goal
4. Consider the effectiveness and efficiency of the agent's approach
5. Provide a final score and detailed reasoning

## Agent Trace:
{trace_str}

## Instructions:
Please evaluate the agent's goal achievement step by step following the evaluation steps above.
First, identify and extract the original task from the trace.
Then provide your reasoning for the score, and finally give a score from 1 to 10. IMPORTANT: Use decimal scores (e.g., 7.5, 8.2, 9.1) rather than round numbers (e.g., 7.0, 8.0, 9.0) to provide more nuanced evaluation.

Format your response as JSON:
{{
    "original_task": "[extracted original task from trace]",
    "score": [numerical score 1-10],
    "reasoning": "[detailed explanation of the score based on goal achievement]"
}}"""

    try:
        response = model.generate(prompt)
        result = parse_llm_score_response(response, threshold=7.0)

        # Add original_task to metadata if present in result, otherwise use agent trace
        if "original_task" not in result.metadata and isinstance(result.metadata, dict):
            # Try to extract from parsed response
            parsed = parse_llm_json_response(response)
            result.metadata["original_task"] = parsed.get(
                "original_task", "Unknown task"
            )

        return result

    except Exception as e:
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Exception: {e!s}",
            metadata={"original_task": "Error during evaluation"},
        )


def conversation_coherence_scorer(
    agent_data: AgentData, model: LLMModel
) -> ScoreResult:
    """
    Score the coherence and logical flow of the agent's conversation using the trace.

    Args:
        agent_data: AgentData object containing agent information
        model: LLM model to use for scoring

    Returns:
        ScoreResult with coherence score (1-10 or -1 on error).
        metadata['original_task'] contains the extracted task.
    """
    # Check if agent has exited
    if not safe_get_boolean_field(agent_data.agent_exit):
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning="The agent has not yet exited",
            metadata={"original_task": "N/A - Agent has not exited"},
        )

    required_fields = {
        "trace": agent_data.trace is not None
        and (isinstance(agent_data.trace, str) or len(agent_data.trace) > 0)
    }

    # Check if all required fields are available
    if not all(required_fields.values()):
        missing_fields = [
            field for field, available in required_fields.items() if not available
        ]
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Missing required fields: {', '.join(missing_fields)}",
            metadata={
                "required_fields": list(required_fields.keys()),
                "missing_fields": missing_fields,
            },
        )

    # Format the trace for the prompt
    trace_str = safe_serialize_union_field(agent_data.trace, "trace")

    # Prompt for conversation coherence evaluation
    prompt = f"""# Conversation Coherence Evaluation Task

## Criteria:
Evaluate the coherence and logical flow of the agent's conversation based on the complete interaction trace. Focus on how well the agent maintains context, responds appropriately to inputs, and creates a logical conversational flow.

## Score Range: 1 to 10
- 1-2: Completely incoherent conversation with no logical flow
- 3-4: Poor coherence with many inconsistencies and context loss
- 5-6: Moderate coherence with some logical flow but noticeable issues
- 7-8: Good coherence with clear logical flow and minimal issues
- 9-10: Excellent coherence with perfect logical flow and context maintenance

## Evaluation Steps:
1. Identify the original task/goal from the trace
2. Analyze the conversational flow and context maintenance
3. Check for logical consistency in responses and actions
4. Assess how well the agent maintains context throughout the interaction
5. Evaluate the overall coherence of the conversation
6. Provide a final score and detailed reasoning

## Agent Trace:
{trace_str}

## Instructions:
Please evaluate the agent's conversation coherence step by step following the evaluation steps above.
First, identify and extract the original task from the trace.
Then analyze the conversational flow and provide your reasoning for the score.
Finally, give a score from 1 to 10. IMPORTANT: Use decimal scores (e.g., 7.5, 8.2, 9.1) rather than round numbers (e.g., 7.0, 8.0, 9.0) to provide more nuanced evaluation.

Format your response as JSON:
{{
    "original_task": "[extracted original task from trace]",
    "score": [numerical score 1-10],
    "reasoning": "[detailed explanation of the coherence score based on conversational flow and context maintenance]"
}}"""

    try:
        response = model.generate(prompt)
        result = parse_llm_score_response(response, threshold=7.0)

        # Add original_task to metadata if present
        parsed = parse_llm_json_response(response)
        result.metadata["original_task"] = parsed.get("original_task", "Unknown task")

        return result

    except Exception as e:
        return ScoreResult(
            score=-1.0,
            passed=False,
            reasoning=f"Exception: {e!s}",
            metadata={"original_task": "Error during evaluation"},
        )


# Convenience class to group all scorers
class AgentScorers:
    """Collection of all agent scoring functions."""

    def __init__(self, model: LLMModel):
        """
        Initialize the agent scorers with an LLM model.

        Args:
            model: LLM model to use for all scoring operations
        """
        self.model = model

    def score_tool_relevancy(
        self, agent_data: AgentData
    ) -> Union[list[ScoreResult], ScoreResult]:
        """Score tool call relevancy."""
        return tool_relevancy_scorer(agent_data, self.model)

    def score_parameter_correctness(
        self, agent_data: AgentData
    ) -> Union[list[ScoreResult], ScoreResult]:
        """Score parameter correctness."""
        return parameter_correctness_scorer(agent_data, self.model)

    def score_task_progression(self, agent_data: AgentData) -> ScoreResult:
        """Score task progression."""
        return task_progression_scorer(agent_data, self.model)

    def score_context_relevancy(self, agent_data: AgentData) -> ScoreResult:
        """Score response appropriateness given task and role."""
        return context_relevancy_scorer(agent_data, self.model)

    def score_role_adherence(self, agent_data: AgentData) -> ScoreResult:
        """Score role adherence."""
        return role_adherence_scorer(agent_data, self.model)

    def score_tool_correctness(
        self, agent_data: AgentData
    ) -> Union[list[ScoreResult], ScoreResult]:
        """Score tool call correctness."""
        return tool_correctness_scorer(agent_data, self.model)

    def score_goal_achievement(self, agent_data: AgentData) -> ScoreResult:
        """Score goal achievement."""
        return goal_achievement_scorer(agent_data, self.model)

    def score_conversation_coherence(self, agent_data: AgentData) -> ScoreResult:
        """Score conversation coherence."""
        return conversation_coherence_scorer(agent_data, self.model)

    def score_all(
        self, agent_data: AgentData
    ) -> dict[str, Union[list[ScoreResult], ScoreResult]]:
        """
        Run ALL 8 agent scorers on the agent data.

        Args:
            agent_data: AgentData object to score

        Returns:
            Dictionary with all scoring results (8 scorers)
        """
        return {
            "tool_relevancy": self.score_tool_relevancy(agent_data),
            "tool_correctness": self.score_tool_correctness(agent_data),
            "parameter_correctness": self.score_parameter_correctness(agent_data),
            "task_progression": self.score_task_progression(agent_data),
            "context_relevancy": self.score_context_relevancy(agent_data),
            "role_adherence": self.score_role_adherence(agent_data),
            "goal_achievement": self.score_goal_achievement(agent_data),
            "conversation_coherence": self.score_conversation_coherence(agent_data),
        }
