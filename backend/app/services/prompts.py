JOB_EXTRACTION_PROMPT = """You are extracting technical and professional requirements from a job description.

Rules:
- Extract ONLY skills, technologies, tools, or concepts that are actually stated or clearly implied in the text.
- Do NOT invent skills that are not mentioned.
- Do NOT extract irrelevant words (company names, generic phrases like "team player", soft skills unrelated to technical ability).
- Normalize obvious variations where appropriate (e.g. "Python 3" -> "Python").
- Classify each skill into exactly one category from this list: programming_language, framework, library, database, ai_ml, cloud, devops, api, tool, concept, other.
- Classify importance as "required" only if the text uses language like "must have", "required", "X+ years experience in Y". Use "preferred" for "nice to have", "bonus", "familiarity with". If importance cannot be determined from context, use "optional".
- Alternatives: when the text offers options for ONE need (e.g. "Pinecone, FAISS or Chroma", "AWS or GCP", "React/Vue"), output ONE item for that need. Use the general need as "name" if the text names one (e.g. "Vector Databases"), otherwise the first option. Put the other options, written exactly as in the text, in "alternatives". Do NOT also list those options as separate items. Use "alternatives": [] when there are none.
- Return ONLY valid JSON, no markdown fences, no explanation text before or after.

Output format (a JSON array, nothing else):
[
  {{"name": "Python", "category": "programming_language", "importance": "required", "alternatives": []}},
  {{"name": "Vector Databases", "category": "database", "importance": "required", "alternatives": ["Pinecone", "FAISS", "Chroma"]}},
  {{"name": "FastAPI", "category": "framework", "importance": "preferred", "alternatives": []}}
]

Job description:
{job_description}
"""