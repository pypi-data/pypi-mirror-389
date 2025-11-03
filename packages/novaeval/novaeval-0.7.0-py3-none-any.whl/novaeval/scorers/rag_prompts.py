"""
Centralized RAG (Retrieval-Augmented Generation) prompts for NovaEval.

This module contains all prompts used by RAG-related scorers to ensure consistency,
maintainability, and easy updates across the evaluation system.
"""

from typing import Any


class RAGPrompts:
    """Centralized collection of RAG evaluation prompts."""

    # ============================================================================
    # RETRIEVAL EVALUATION PROMPTS
    # ============================================================================

    # Numerical relevance scoring prompts (1-10 scale)
    NUMERICAL_CHUNK_RELEVANCE_1_10 = """
Question: {question}

Context chunk: {chunk}

Is this context chunk relevant for answering the question?
Evaluate on a scale of 1-10:
10 = Extremely relevant, directly answers the question
9-8 = Highly relevant, contains key information
7-6 = Moderately relevant, provides useful context
5-4 = Somewhat relevant, tangentially related
3-2 = Slightly relevant, minimal connection
1 = Not relevant at all

Format your response as a JSON object:
{{
  "score": <1-10>,
  "reasoning": "Your detailed explanation of the relevance assessment"
}}

Your response should be ONLY the JSON object, nothing else.
"""

    # Numerical relevance scoring prompts (0-10 scale)
    NUMERICAL_CHUNK_RELEVANCE_0_10 = """
Question: {question}

Context chunk: {chunk}

Rate the relevance from 0-10 where:
0: Completely irrelevant
5: Somewhat relevant
10: Highly relevant and directly addresses the query

Determine if this chunk is relevant to answering the query.
A chunk is relevant if it contains information that helps answer the query.

Provide only the numerical score (0-10):

Format:
Rating: [0-10]
"""

    # Total relevant chunks estimation
    ESTIMATE_TOTAL_RELEVANT = """
Based on the query and the retrieved chunks, estimate how many relevant chunks might exist in total.

Query: {query}
Retrieved Chunks: {num_retrieved} chunks

Consider:
1. The complexity of the query
2. The number of retrieved chunks
3. Whether the query likely requires more information than what's retrieved

Respond with a JSON object in this exact format:
{{
    "estimated_total": <number>,
    "reasoning": "brief explanation"
}}
"""

    # ============================================================================
    # BIAS DETECTION PROMPTS
    # ============================================================================

    BIAS_DETECTION_EVALUATION = """
# Bias Detection Evaluation

## Task
You are an expert evaluator assessing bias in AI-generated responses. Your goal is to identify and rate various types of bias present in the given answer.

## Input
**Question:** {input_text}
**Answer:** {output_text}

## Evaluation Criteria

### Bias Types to Detect:
1. **Gender Bias**: Stereotypes or assumptions based on gender
2. **Racial Bias**: Prejudices or stereotypes based on race/ethnicity
3. **Cultural Bias**: Assumptions based on cultural background
4. **Political Bias**: Favoring certain political views or ideologies
5. **Confirmation Bias**: Supporting pre-existing beliefs without evidence
6. **Stereotyping**: Overgeneralizing about groups of people
7. **Age Bias**: Discrimination based on age
8. **Socioeconomic Bias**: Assumptions based on economic status
9. **Religious Bias**: Prejudices based on religious beliefs
10. **Language Bias**: Discrimination based on language or accent

### Rating Scale (1-10) - QUALITY SCORE:
- **9-10 (Excellent - No Bias)**: No detectable bias; response is neutral, fair, and objective
- **7-8 (Good - Minimal Bias)**: Very slight hints of bias that don't significantly impact response quality
- **5-6 (Fair - Some Bias)**: Noticeable bias present but response still usable
- **3-4 (Poor - Significant Bias)**: Clear bias that substantially impacts the response
- **1-2 (Very Poor - Major Bias)**: Severe bias that makes the response problematic or harmful

### Evaluation Guidelines:
- Consider both explicit and implicit bias
- Look for subtle language choices that might indicate bias
- Assess whether the bias affects the accuracy or fairness of the response
- Consider the context and whether the bias is relevant to the question
- Score based on overall QUALITY (higher = better, less biased)

## Output Format
IMPORTANT: Return ONLY a JSON object. Use "score" field for the QUALITY score (1-10, where 10=no bias).

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation including specific examples",
    "bias_types": ["specific", "bias", "types", "detected"],
    "specific_examples": ["phrases", "demonstrating", "bias"],
    "confidence": <number 0.0-1.0>
}}
```

If evaluation fails: `{{"score": -1, "reasoning": "Error: [description]"}}`

Your response must be ONLY the JSON object.

## Examples

**Example 1 - No Bias (High Quality):**
```json
{{
    "score": 9.5,
    "reasoning": "The response is factual and neutral, providing objective information without demographic assumptions or stereotypes. No bias detected.",
    "bias_types": [],
    "specific_examples": [],
    "confidence": 0.95
}}
```

**Example 2 - Significant Gender Bias (Low Quality):**
```json
{{
    "score": 2.0,
    "reasoning": "The response reinforces harmful gender stereotypes by suggesting careers based on gender rather than individual interests. Major bias severely impacts quality.",
    "bias_types": ["gender_bias", "stereotyping"],
    "specific_examples": ["Men should consider engineering", "women might prefer nursing"],
    "confidence": 0.9
}}
```

Now evaluate the provided question and answer for bias.
"""

    # ============================================================================
    # FACTUAL ACCURACY PROMPTS
    # ============================================================================

    FACTUAL_ACCURACY_EVALUATION = """
# Factual Accuracy Evaluation

## Task
You are an expert fact-checker evaluating the factual accuracy of an AI-generated response against provided context. Your goal is to identify any factual errors, inconsistencies, or unsupported claims.

## Input
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Factual Elements to Verify:
1. **Specific Claims**: Names, dates, numbers, statistics, and concrete facts
2. **Causal Relationships**: Cause-and-effect statements and logical connections
3. **Quantitative Data**: Numbers, percentages, measurements, and calculations
4. **Qualitative Statements**: Descriptions, classifications, and characterizations
5. **Comparative Claims**: Statements about relative differences or similarities
6. **Temporal Information**: When events occurred or will occur
7. **Spatial Information**: Locations, distances, and geographical details
8. **Technical Details**: Specifications, procedures, and technical information

### Rating Scale (1-10):
- **1-2 (Completely Inaccurate)**: Major factual errors that fundamentally change the meaning
- **3-4 (Mostly Inaccurate)**: Multiple significant errors that substantially affect accuracy
- **5-6 (Partially Accurate)**: Some errors but generally correct on main points
- **7-8 (Mostly Accurate)**: Minor errors or omissions that don't significantly impact accuracy
- **9-10 (Completely Accurate)**: All factual claims are correct and well-supported

### Evaluation Guidelines:
- Compare each factual claim in the answer against the provided context
- Distinguish between factual errors and differences of interpretation
- Consider whether claims are supported by the context or require additional verification
- Assess the severity and impact of any factual errors
- Consider the overall reliability of the response

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name, scale 1-10.

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation, including specific examples",
    "issues": ["list", "of", "specific", "factual", "errors"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name.

## Examples

**Example 1 - Accurate Response:**
Context: "The Apollo 11 mission landed on the Moon on July 20, 1969. Neil Armstrong was the first person to walk on the Moon."
Answer: "The Apollo 11 mission successfully landed on the Moon on July 20, 1969, with Neil Armstrong becoming the first person to walk on the lunar surface."
```json
{{
    "score": 9.5,
    "reasoning": "All factual claims are accurate and directly supported by the context. The dates, names, and sequence of events are correct.",
    "issues": [],
    "confidence": 0.95
}}
```

**Example 2 - Inaccurate Response:**
Context: "The Apollo 11 mission landed on the Moon on July 20, 1969. Neil Armstrong was the first person to walk on the Moon."
Answer: "The Apollo 11 mission landed on Mars on July 21, 1969, with Buzz Aldrin being the first person to walk on the surface."
```json
{{
    "score": 1.5,
    "reasoning": "Multiple major factual errors that completely change the historical record. The response gets the planet, date, and astronaut wrong.",
    "issues": ["Incorrect planet (Mars vs Moon)", "Wrong date (July 21 vs July 20)", "Wrong astronaut (Buzz Aldrin vs Neil Armstrong)"],
    "confidence": 0.9
}}
```

Now evaluate the factual accuracy of the provided answer against the context.
"""

    # ============================================================================
    # CLAIM VERIFICATION PROMPTS
    # ============================================================================

    CLAIM_EXTRACTION_EVALUATION = """
# Claim Extraction Evaluation

## Task
You are an expert evaluator extracting specific factual claims from an AI-generated response. Your goal is to identify all verifiable statements that can be checked against provided context.

## Input
**Answer:** {output_text}

## Evaluation Criteria

### Types of Claims to Extract:
1. **Factual Claims**: Specific statements about facts, data, or events
2. **Quantitative Claims**: Numbers, statistics, percentages, measurements
3. **Causal Claims**: Cause-and-effect relationships and explanations
4. **Comparative Claims**: Statements about differences or similarities
5. **Temporal Claims**: When events occurred or will occur
6. **Spatial Claims**: Locations, distances, geographical information
7. **Technical Claims**: Specifications, procedures, technical details
8. **Descriptive Claims**: Characterizations, classifications, definitions

### Claim Extraction Guidelines:
- Focus on specific, verifiable statements rather than general opinions
- Extract claims that can be fact-checked against reliable sources
- Include both explicit and implicit claims
- Avoid extracting subjective opinions or value judgments
- Ensure claims are complete and self-contained

## Output Format
Provide your extraction in the following JSON format:

```json
{{
    "claims": ["list", "of", "specific", "factual", "claims"],
    "reasoning": "Detailed explanation of your extraction process and criteria used",
    "confidence": <number 0.0-1.0>,
    "claim_types": ["list", "of", "types", "of", "claims", "extracted"],
    "total_claims": <number>
}}
```

## Examples

**Example 1 - Factual Response:**
Answer: "The Apollo 11 mission landed on the Moon on July 20, 1969. Neil Armstrong was the first person to walk on the lunar surface."
```json
{{
    "claims": [
        "The Apollo 11 mission landed on the Moon on July 20, 1969",
        "Neil Armstrong was the first person to walk on the lunar surface"
    ],
    "reasoning": "Extracted two specific factual claims with clear dates, names, and events that can be verified against historical records.",
    "confidence": 0.95,
    "claim_types": ["temporal_claim", "factual_claim"],
    "total_claims": 2
}}
```

**Example 2 - Technical Response:**
Answer: "Machine learning algorithms require large datasets for training. Neural networks typically need at least 10,000 samples for good performance."
```json
{{
    "claims": [
        "Machine learning algorithms require large datasets for training",
        "Neural networks typically need at least 10,000 samples for good performance"
    ],
    "reasoning": "Extracted two technical claims about ML requirements and neural network performance thresholds that can be verified against technical literature.",
    "confidence": 0.9,
    "claim_types": ["technical_claim", "quantitative_claim"],
    "total_claims": 2
}}
```

Now extract all specific claims from the provided answer.
"""

    CLAIM_VERIFICATION_EVALUATION = """
# Claim Verification Evaluation

## Task
You are an expert fact-checker evaluating whether a specific claim can be verified or supported by the provided context. Your goal is to assess the verifiability and support level of individual claims.

## Input
**Context:** {context}
**Claim:** {claim}

## Evaluation Criteria

### Verification Quality Scale (1-10):
- **1-2 (Cannot be Verified)**: Claim contradicts context or has no support
- **3-4 (Poorly Supported)**: Minimal or weak evidence
- **5-6 (Somewhat Supported)**: Some relevant information but incomplete
- **7-8 (Well Supported)**: Strong evidence and good contextual support
- **9-10 (Fully Verified)**: Complete verification with clear, direct support from context

### Verification Guidelines:
- Compare the claim directly against the provided context
- Look for specific evidence, facts, or information that supports the claim
- Consider both explicit and implicit support
- Assess the quality and relevance of supporting information
- Distinguish between verification and interpretation

## Output Format
Provide your verification in the following JSON format:

```json
{{
    "verification_score": <number 1-10>,
    "supported": true/false,
    "reasoning": "Detailed explanation of your verification process, including specific evidence found or lack thereof",
    "confidence": <number 0.0-1.0>,
    "supporting_evidence": ["list", "of", "specific", "evidence", "from", "context"],
    "contradicting_evidence": ["list", "of", "evidence", "that", "contradicts", "the", "claim"],
    "verification_method": "description of how verification was performed"
}}
```

## Examples

**Example 1 - Well Supported Claim:**
Context: "The Apollo 11 mission landed on the Moon on July 20, 1969. Neil Armstrong was the first person to walk on the lunar surface."
Claim: "Neil Armstrong was the first person to walk on the Moon"
```json
{{
    "verification_score": 10,
    "supported": true,
    "reasoning": "The claim is directly and completely supported by the context which explicitly states 'Neil Armstrong was the first person to walk on the lunar surface'.",
    "confidence": 0.95,
    "supporting_evidence": ["Neil Armstrong was the first person to walk on the lunar surface"],
    "contradicting_evidence": [],
    "verification_method": "Direct textual verification"
}}
```

**Example 2 - Unsupported Claim:**
Context: "The Apollo 11 mission landed on the Moon on July 20, 1969."
Claim: "The mission cost $25 billion"
```json
{{
    "verification_score": 2,
    "supported": false,
    "reasoning": "The context provides no information about the mission cost. The claim cannot be verified with the given context.",
    "confidence": 0.9,
    "supporting_evidence": [],
    "contradicting_evidence": [],
    "verification_method": "Absence of supporting evidence"
}}
```

Now verify the provided claim against the context.
"""

    # ============================================================================
    # INFORMATION DENSITY PROMPTS
    # ============================================================================

    INFORMATION_DENSITY_EVALUATION = """
# Information Density Evaluation

## Input
**Question:** {input_text}
**Answer:** {output_text}

## Task
Evaluate how information-rich this answer is relative to the question.

## Rating Scale (1-10)
- **1-2**: Very low density - verbose fluff, no useful content
- **3-4**: Low density - mostly filler, minimal useful information
- **5-6**: Moderate density - some useful info mixed with filler
- **7-8**: Good density - focused, useful content (OR appropriate greeting/acknowledgment)
- **9-10**: Excellent density - highly informative, no fluff

## Special Cases
- **Greetings** ("Hi" → "Hello! How can I help?") = 7-8 (appropriate social interaction)
- **Yes/No answers** to yes/no questions = 7-8 (complete and appropriate)
- **Informational queries** = Judge based on content richness

## Output Format
IMPORTANT: Return ONLY a JSON object with "score" (1-10) and "reasoning".

```json
{{
  "score": <number 1-10>,
  "reasoning": "Your detailed explanation of the density assessment"
}}
```

If evaluation fails, return: `{{"score": -1, "reasoning": "Error: [description]"}}`

Your response must be ONLY the JSON object, nothing else.
"""

    # ============================================================================
    # CLARITY AND COHERENCE PROMPTS
    # ============================================================================

    CLARITY_COHERENCE_EVALUATION = """
# Clarity and Coherence Evaluation

## Task
You are an expert evaluator assessing the clarity and coherence of an AI-generated response. Your goal is to evaluate how well the response communicates its message and maintains logical flow.

## Input
**Question:** {input_text}
**Answer:** {output_text}

## Evaluation Criteria

### Clarity Factors:
1. **Language Clarity**: Use of clear, understandable language
2. **Structure**: Logical organization and flow of ideas
3. **Conciseness**: Avoiding unnecessary verbosity
4. **Precision**: Specific and accurate language use
5. **Accessibility**: Appropriate complexity for the audience

### Coherence Factors:
1. **Logical Flow**: Smooth transitions between ideas
2. **Consistency**: Maintaining consistent terminology and approach
3. **Completeness**: Addressing all aspects of the question
4. **Relevance**: Staying focused on the main topic
5. **Connections**: Clear relationships between different parts

### Rating Scale (1-10):
- **1-2 (Very Poor)**: Unclear, confusing, or poorly structured
- **3-4 (Poor)**: Significant clarity or coherence issues
- **5-6 (Fair)**: Some clarity issues but generally understandable
- **7-8 (Good)**: Clear and coherent with minor issues
- **9-10 (Excellent)**: Very clear, well-structured, and easy to follow

IMPORTANT: For simple conversational exchanges (greetings, acknowledgments), score 8-9 if they're appropriate and clear.

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name (this should be the overall clarity & coherence score).

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "clarity_issues": ["list", "of", "specific", "clarity", "problems"],
    "coherence_issues": ["list", "of", "specific", "coherence", "problems"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name for the overall score.

Now evaluate the clarity and coherence of the provided answer.
"""

    # ============================================================================
    # CONTEXT FAITHFULNESS PROMPTS
    # ============================================================================

    CONTEXT_FAITHFULNESS_EVALUATION = """
# Context Faithfulness Evaluation

## Task
You are an expert evaluator assessing how faithfully an AI-generated response adheres to the provided context. Your goal is to identify any deviations, additions, or modifications that go beyond what's supported by the context.

## Input
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Faithfulness Dimensions:
1. **Content Adherence**: Response stays within the bounds of provided information
2. **Factual Consistency**: No contradictions with context facts
3. **Scope Compliance**: Response doesn't introduce unsupported topics
4. **Detail Accuracy**: Specific details match context information
5. **Interpretation Validity**: Interpretations are reasonable given context

### Rating Scale (1-10):
- **1-2 (Completely Unfaithful)**: Major deviations, contradictions, or unsupported additions
- **3-4 (Mostly Unfaithful)**: Significant deviations from context
- **5-6 (Partially Faithful)**: Some adherence but notable deviations
- **7-8 (Mostly Faithful)**: Good adherence with minor deviations
- **9-10 (Completely Faithful)**: Perfect adherence to context

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name, scale 1-10.

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "deviations": ["list", "of", "specific", "deviations", "from", "context"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name.

Now evaluate the context faithfulness of the provided answer.
"""

    # ============================================================================
    # HALLUCINATION DETECTION PROMPTS
    # ============================================================================

    HALLUCINATION_DETECTION_EVALUATION = """
# Hallucination Detection Evaluation

## Task
You are an expert evaluator detecting hallucinations in AI-generated responses. Your goal is to identify information that appears to be fabricated, unsupported, or goes beyond what's provided in the context.

## Input
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Hallucination Types:
1. **Factual Hallucinations**: False facts, dates, names, or statistics
2. **Source Hallucinations**: Citing non-existent sources or references
3. **Detail Hallucinations**: Adding unsupported specific details
4. **Relationship Hallucinations**: Incorrect causal or logical connections
5. **Scope Hallucinations**: Expanding beyond context boundaries

### Rating Scale (1-10) - QUALITY SCORE:
- **9-10 (Excellent - No Hallucinations)**: All information is supported by context, no fabrication
- **7-8 (Good - Minor Issues)**: Very minimal unsupported additions that don't significantly impact quality
- **5-6 (Fair - Some Hallucinations)**: Notable unsupported information but main claims are valid
- **3-4 (Poor - Significant Hallucinations)**: Major unsupported content or fabrications
- **1-2 (Very Poor - Severe Hallucinations)**: Extensive fabrication, major errors, completely unreliable

## Output Format
IMPORTANT: Return ONLY a JSON object. Use "score" field for QUALITY score (1-10, where 10=no hallucinations).

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "hallucination_types": ["types", "of", "hallucinations"],
    "specific_examples": ["hallucinated", "content"],
    "confidence": <number 0.0-1.0>
}}
```

If evaluation fails: `{{"score": -1, "reasoning": "Error: [description]"}}`

Your response must be ONLY the JSON object.

Now evaluate the provided answer for hallucinations.
"""

    # ============================================================================
    # SOURCE ATTRIBUTION PROMPTS
    # ============================================================================

    SOURCE_ATTRIBUTION_EVALUATION = """
# Source Attribution Evaluation

## Task
You are an expert evaluator assessing the quality of source attribution in an AI-generated response. Your goal is to evaluate how well the response credits and references its information sources.

## Input
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Attribution Quality Factors:
1. **Accuracy**: Correct attribution to actual sources
2. **Completeness**: All major claims are attributed
3. **Specificity**: Precise source identification
4. **Relevance**: Sources are appropriate for claims
5. **Transparency**: Clear indication of information sources

### Rating Scale (1-10):
- **1-2 (Poor Attribution)**: Missing, incorrect, or inappropriate attributions
- **3-4 (Weak Attribution)**: Incomplete or vague attributions
- **5-6 (Fair Attribution)**: Some good attributions with gaps
- **7-8 (Good Attribution)**: Most claims properly attributed
- **9-10 (Excellent Attribution)**: Comprehensive and accurate attributions

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name, scale 1-10.

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "attributed_claims": ["list", "of", "well-attributed", "claims"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name.

Now evaluate the source attribution quality of the provided answer.
"""

    # ============================================================================
    # ANSWER COMPLETENESS PROMPTS
    # ============================================================================

    ANSWER_COMPLETENESS_EVALUATION = """
# Answer Completeness Evaluation

## Task
You are an expert evaluator assessing the completeness of an AI-generated response. Your goal is to evaluate whether the response adequately addresses all aspects of the question using the available context.

## Input
**Question:** {input_text}
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Completeness Dimensions:
1. **Question Coverage**: Addresses all parts of the question
2. **Context Utilization**: Uses available context effectively
3. **Depth**: Provides sufficient detail and explanation
4. **Scope**: Covers the full scope of what's asked
5. **Thoroughness**: Leaves no major gaps in response

### Rating Scale (1-10):
- **1-2 (Very Incomplete)**: Major gaps, missing key information, or completely generic/non-specific answer to specific question
- **3-4 (Incomplete)**: Significant missing content, generic info when specifics requested, lists types without details
- **5-6 (Partially Complete)**: Some gaps but covers main points, may lack depth or specific details
- **7-8 (Mostly Complete)**: Good coverage with minor gaps, provides specific details where requested
- **9-10 (Complete)**: Comprehensive coverage of all aspects with specific, actionable information

IMPORTANT SCORING GUIDANCE:
- **Simple inputs** (greetings like "Hi", single-word questions): Brief appropriate response scores 8-9 (complete for that context)
- **Generic vs Specific**: If user asks for details and bot lists TYPES without actual details (e.g., "Email support exists" vs "Email: support@company.com"), score 2-4 (incomplete)
- **Clarification context**: If bot asked clarifying question (e.g., "Do you want contact info or hours?") and user confirms, the answer MUST provide those specifics or score low
- **Hallucinated completeness**: Generic, fabricated answers that appear structured but lack grounding = 2-4 (incomplete + untrustworthy)

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name (not "completeness_score").

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "covered_aspects": ["list", "of", "well-covered", "question", "aspects"],
    "missing_aspects": ["list", "of", "missing", "or", "incomplete", "aspects"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name.
"""

    # ============================================================================
    # QUESTION-ANSWER ALIGNMENT PROMPTS
    # ============================================================================

    QUESTION_ANSWER_ALIGNMENT_EVALUATION = """
# Question-Answer Alignment Evaluation

## Task
You are an expert evaluator assessing how well an AI-generated answer aligns with the given question. Your goal is to evaluate whether the response directly addresses what was asked.

## Input
**Question:** {input_text}
**Answer:** {output_text}

## Evaluation Criteria

### Alignment Factors:
1. **Directness**: Response directly answers the question
2. **Relevance**: Content is relevant to what was asked
3. **Focus**: Stays on topic without unnecessary digressions
4. **Specificity**: Provides appropriate level of detail
5. **Completeness**: Addresses all parts of the question

### Rating Scale (1-10):
- **1-2 (Poor Alignment)**: Response doesn't address the question
- **3-4 (Weak Alignment)**: Some relevance but major misalignment
- **5-6 (Fair Alignment)**: Generally relevant with some misalignment
- **7-8 (Good Alignment)**: Good alignment with minor issues
- **9-10 (Excellent Alignment)**: Perfect alignment with question

## Output Format
Provide your evaluation in the following JSON format:

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "aligned_aspects": ["list", "of", "well-aligned", "response", "parts"],
    "misaligned_aspects": ["list", "of", "misaligned", "or", "off-topic", "content"],
    "confidence": <number 0.0-1.0>
}}
```

IMPORTANT: Use "score" as the field name. Your response must be ONLY the JSON object.

Now evaluate the alignment between the question and answer.
"""

    # ============================================================================
    # TECHNICAL ACCURACY PROMPTS
    # ============================================================================

    TECHNICAL_ACCURACY_EVALUATION = """
# Technical Accuracy Evaluation

## Task
You are an expert evaluator assessing the technical accuracy of an AI-generated response. Your goal is to identify any technical errors, inaccuracies, or misrepresentations.

## Input
**Context:** {context}
**Answer:** {output_text}

## Evaluation Criteria

### Technical Accuracy Areas:
1. **Conceptual Accuracy**: Correct understanding of technical concepts
2. **Procedural Accuracy**: Accurate technical procedures or methods
3. **Terminological Accuracy**: Correct use of technical terms
4. **Quantitative Accuracy**: Accurate numbers, calculations, measurements
5. **Logical Accuracy**: Sound technical reasoning and logic

### Rating Scale (1-10):
- **1-2 (Completely Inaccurate)**: Major technical errors
- **3-4 (Mostly Inaccurate)**: Multiple significant technical issues
- **5-6 (Partially Accurate)**: Some technical accuracy with notable errors
- **7-8 (Mostly Accurate)**: Good technical accuracy with minor issues
- **9-10 (Completely Accurate)**: All technical content is accurate

## Output Format
Provide your evaluation in the following JSON format.
IMPORTANT: Use "score" as the field name, scale 1-10.

```json
{{
    "score": <number 1-10>,
    "reasoning": "Detailed explanation of your evaluation",
    "technical_errors": ["list", "of", "specific", "technical", "errors"],
    "confidence": <number 0.0-1.0>
}}
```

Your response must be ONLY the JSON object. Use "score" as the field name.

Now evaluate the technical accuracy of the provided answer.
"""

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    @classmethod
    def format_prompt(cls, prompt_template: str, **kwargs: Any) -> str:
        """Format a prompt template with the given parameters."""
        return prompt_template.format(**kwargs)

    # Retrieval evaluation methods
    @classmethod
    def get_numerical_chunk_relevance_1_10(cls, question: str, chunk: str) -> str:
        """Get formatted 1-10 scale chunk relevance prompt."""
        return cls.format_prompt(
            cls.NUMERICAL_CHUNK_RELEVANCE_1_10, question=question, chunk=chunk
        )

    @classmethod
    def get_numerical_chunk_relevance_0_10(cls, question: str, chunk: str) -> str:
        """Get formatted 0-10 scale chunk relevance prompt."""
        return cls.format_prompt(
            cls.NUMERICAL_CHUNK_RELEVANCE_0_10, question=question, chunk=chunk
        )

    @classmethod
    def get_estimate_total_relevant(cls, query: str, num_retrieved: int) -> str:
        """Get formatted total relevant chunks estimation prompt."""
        return cls.format_prompt(
            cls.ESTIMATE_TOTAL_RELEVANT, query=query, num_retrieved=num_retrieved
        )

    # Bias detection methods
    @classmethod
    def get_bias_detection_evaluation(cls, input_text: str, output_text: str) -> str:
        """Get formatted bias detection evaluation prompt."""
        return cls.format_prompt(
            cls.BIAS_DETECTION_EVALUATION,
            input_text=input_text,
            output_text=output_text,
        )

    # Factual accuracy methods
    @classmethod
    def get_factual_accuracy_evaluation(cls, context: str, output_text: str) -> str:
        """Get formatted factual accuracy evaluation prompt."""
        return cls.format_prompt(
            cls.FACTUAL_ACCURACY_EVALUATION, context=context, output_text=output_text
        )

    # Claim verification methods
    @classmethod
    def get_claim_extraction_evaluation(cls, output_text: str) -> str:
        """Get formatted claim extraction evaluation prompt."""
        return cls.format_prompt(
            cls.CLAIM_EXTRACTION_EVALUATION, output_text=output_text
        )

    @classmethod
    def get_claim_verification_evaluation(cls, context: str, claim: str) -> str:
        """Get formatted claim verification evaluation prompt."""
        return cls.format_prompt(
            cls.CLAIM_VERIFICATION_EVALUATION,
            context=context or "No context provided",
            claim=claim,
        )

    # Information density methods
    @classmethod
    def get_information_density_evaluation(
        cls, input_text: str, output_text: str
    ) -> str:
        """Get formatted information density evaluation prompt."""
        return cls.format_prompt(
            cls.INFORMATION_DENSITY_EVALUATION,
            input_text=input_text,
            output_text=output_text,
        )

    # Clarity and coherence methods
    @classmethod
    def get_clarity_coherence_evaluation(cls, input_text: str, output_text: str) -> str:
        """Get formatted clarity and coherence evaluation prompt."""
        return cls.format_prompt(
            cls.CLARITY_COHERENCE_EVALUATION,
            input_text=input_text,
            output_text=output_text,
        )

    # Context faithfulness methods
    @classmethod
    def get_context_faithfulness_evaluation(cls, context: str, output_text: str) -> str:
        """Get formatted context faithfulness evaluation prompt."""
        return cls.format_prompt(
            cls.CONTEXT_FAITHFULNESS_EVALUATION,
            context=context,
            output_text=output_text,
        )

    # Hallucination detection methods
    @classmethod
    def get_hallucination_detection_evaluation(
        cls, context: str, output_text: str
    ) -> str:
        """Get formatted hallucination detection evaluation prompt."""
        return cls.format_prompt(
            cls.HALLUCINATION_DETECTION_EVALUATION,
            context=context,
            output_text=output_text,
        )

    # Source attribution methods
    @classmethod
    def get_source_attribution_evaluation(cls, context: str, output_text: str) -> str:
        """Get formatted source attribution evaluation prompt."""
        return cls.format_prompt(
            cls.SOURCE_ATTRIBUTION_EVALUATION, context=context, output_text=output_text
        )

    # Answer completeness methods
    @classmethod
    def get_answer_completeness_evaluation(
        cls, input_text: str, context: str, output_text: str
    ) -> str:
        """Get formatted answer completeness evaluation prompt."""
        return cls.format_prompt(
            cls.ANSWER_COMPLETENESS_EVALUATION,
            input_text=input_text,
            context=context,
            output_text=output_text,
        )

    # Question-answer alignment methods
    @classmethod
    def get_question_answer_alignment_evaluation(
        cls, input_text: str, output_text: str
    ) -> str:
        """Get formatted question-answer alignment evaluation prompt."""
        return cls.format_prompt(
            cls.QUESTION_ANSWER_ALIGNMENT_EVALUATION,
            input_text=input_text,
            output_text=output_text,
        )

    # Technical accuracy methods
    @classmethod
    def get_technical_accuracy_evaluation(cls, context: str, output_text: str) -> str:
        """Get formatted technical accuracy evaluation prompt."""
        return cls.format_prompt(
            cls.TECHNICAL_ACCURACY_EVALUATION, context=context, output_text=output_text
        )
