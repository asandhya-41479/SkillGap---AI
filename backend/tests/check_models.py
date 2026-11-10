from app.services.roadmap import roadmap_llm as r

for m in ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.7-flash"):
    try:
        print(m, "OK", r._client().models.generate_content(model=m, contents="Say ok").text.strip()[:20])
    except Exception as e:
        print(m, "FAIL", str(e)[:200].replace("\n", " "))