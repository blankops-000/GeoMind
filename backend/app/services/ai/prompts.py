"""
Prompts for AI Service provider operations.
Enforces ground truth rules, structured JSON output, and evidence verification.
"""

UNDERSTAND_QUERY_PROMPT = """
You are a geospatial analysis query parser.
Convert the user's question into a JSON object matching this schema:
{schema}

User Question: {question}
Context: {context}

RULES:
- Extract geographic scope, intent type, target features, and required analysis types (spatial_analysis or computer_vision).
- Return ONLY valid JSON. No Markdown formatting wrappers, no explanations or extra text.
"""

CREATE_PLAN_PROMPT = """
You are a geospatial analysis planner.
Given a QueryIntent and available datasets/operations, generate a detailed AnalysisPlan matching this schema:
{schema}

Query Intent: {intent_json}
Available Capabilities: {available_json}

RULES:
- Select only available datasets and valid operations.
- Return ONLY valid JSON. No prose or explanations.
"""

INTERPRET_EVIDENCE_PROMPT = """
You are interpreting structured geographic evidence from spatial computation, statistics, and computer vision models.

EVIDENCE GROUNDING RULES:
- You MUST NOT invent numbers, locations, measurements, statistics, or detections.
- Every number or statistic you mention MUST appear explicitly in the evidence below.
- Express uncertainty if data quality flags exist or confidence scores are low.
- Return a JSON object with keys "summary" (str) and "notable_items" (list of str).

Evidence Package:
{evidence_json}

Return ONLY valid JSON.
"""

GENERATE_INSIGHT_PROMPT = """
You are generating a final executive geospatial insight based on verified evidence and interpretation.

EVIDENCE GROUNDING RULES:
- Never invent facts, measurements, or findings not backed by the evidence.
- Match this schema format:
{schema}

Evidence: {evidence_json}
Interpretation: {interpretation_json}

Return ONLY valid JSON with keys: "headline", "summary", "key_findings", "confidence".
"""
