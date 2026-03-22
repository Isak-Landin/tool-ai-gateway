
# =========================================================
# TOOLS ROUTES
# =========================================================

@app.get("/tools/archon/search")
def http_archon_search(q: str, source: str = "", match_count: int = 5, return_mode: str = "chunks"):
    raise HTTPException(status_code=501, detail="archon_search route not wired yet")


@app.post("/tools/archon/rag-query")
def http_archon_rag_query(data: dict):
    raise HTTPException(status_code=501, detail="archon_rag_query route not wired yet")


@app.get("/tools/web/search")
def http_web_search(q: str):
    raise HTTPException(status_code=501, detail="web_search route not wired yet")