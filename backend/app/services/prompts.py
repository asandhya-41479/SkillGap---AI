JOB_EXTRACTION_PROMPT = """You are extracting technical and professional requirements from a job description.

Rules:
- Extract ONLY skills, technologies, tools, or concepts that are actually stated or clearly implied in the text.
- Do NOT invent skills that are not mentioned.
- Do NOT extract irrelevant words (company names, generic phrases like "team player", soft skills unrelated to technical ability).
- Normalize obvious variations where appropriate (e.g. "Python 3" -> "Python").
- Classify each skill into exactly one category from this list: programming_language, framework, library, database, ai_ml, cloud, devops, api, tool, concept, other.
- Classify importance as "required" only if the text uses language like "must have", "required", "X+ years experience in Y". Use "preferred" for "nice to have", "bonus", "familiarity with". If importance cannot be determined from context, use "optional".
- Return ONLY valid JSON, no markdown fences, no explanation text before or after.

Output format (a JSON array, nothing else):
[
  {{"name": "Python", "category": "programming_language", "importance": "required"}},
  {{"name": "FastAPI", "category": "framework", "importance": "preferred"}}
]

Job description:
{job_description}
"""