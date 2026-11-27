"""Swagger / OpenAPI documentation: section descriptions and a one-line summary per endpoint.

Kept in one place so the route files stay focused on logic. Only the documentation changes:
no URL, method, request or response is affected.
"""
from fastapi import APIRouter
from fastapi.routing import APIRoute

API_DESCRIPTION = """
**SkillGap AI** compares a learner's skills with a real job description, finds the gaps,
builds a personal learning roadmap, tracks progress with GitHub-verified evidence and
recommends the next career actions.

**How it decides things:** gaps, match %, readiness and priorities are calculated by
deterministic code (rules + Sentence-Transformer similarity). Gemini is used only to word
explanations and to read requirements out of job text; it never decides a score.

**Authentication:** call `POST /auth/login`, then click **Authorize** and paste the token.
Every endpoint except register, login, the GitHub OAuth callback and `/health` needs it,
and every resource is checked to belong to the logged-in user.
"""

TAGS = [
    {"name": "AUTH", "description": "Register and log in. Returns a JWT access token (bcrypt-hashed passwords)."},
    {"name": "USERS", "description": "The logged-in user's account: name and target role."},
    {"name": "SKILLS", "description": "The user's skills (name, category, level, years) and the skill profile."},
    {"name": "JOBS", "description": "Job descriptions: save the text, extract and validate requirements "
                                    "(required / preferred / optional, with alternatives)."},
    {"name": "SKILL GAP ANALYSIS", "description": "Compare skills with a job: strong, partial, transferable or gap "
                                                  "per requirement, priorities and the weighted alignment %."},
    {"name": "GITHUB", "description": "Connect GitHub with OAuth, list repositories and analyse them as evidence."},
    {"name": "ROADMAP", "description": "Personal learning roadmap built from the gaps: order, prerequisites, "
                                       "time budget, versions and per-item progress."},
    {"name": "PROGRESS", "description": "Career readiness score, history and comparison, plus skill evidence "
                                        "(GitHub repositories and project links) and its verification."},
    {"name": "CAREER", "description": "Career intelligence: prioritised next actions, project ideas, interview "
                                      "preparation and matching against opportunities."},
    {"name": "SYSTEM", "description": "Health check used by the hosting platform."},
]

# (METHOD, path) -> summary
SUMMARIES = {
    ("POST", "/auth/register"): "Create an account",
    ("POST", "/auth/login"): "Log in and get an access token (5 wrong tries = 15-minute wait)",
    ("POST", "/auth/forgot-password"): "Email a single-use password reset link (same answer for unknown emails)",
    ("POST", "/auth/reset-password"): "Set a new password with a valid reset link token",

    ("GET", "/users/me"): "Get my account",
    ("PUT", "/users/me"): "Update my name or target role",
    ("PUT", "/users/me/password"): "Change my password (needs the current password)",

    ("POST", "/skills"): "Add a skill",
    ("GET", "/skills"): "List my skills",
    ("PUT", "/skills/{skill_id}"): "Edit a skill",
    ("DELETE", "/skills/{skill_id}"): "Delete a skill",
    ("GET", "/profile/skills"): "My skill profile (skills grouped with their sources)",

    ("GET", "/github/connect"): "Start GitHub connection (returns the GitHub authorise URL)",
    ("GET", "/github/callback"): "GitHub OAuth callback (redirects back to the website)",
    ("GET", "/github/status"): "Is my GitHub account connected?",
    ("GET", "/github/repositories"): "List my GitHub repositories",
    ("POST", "/github/analyze"): "Detect skills from my GitHub repositories",

    ("POST", "/jobs"): "Save a job description",
    ("GET", "/jobs"): "List my job descriptions",
    ("GET", "/jobs/{job_id}"): "Get a job description with its requirements",
    ("DELETE", "/jobs/{job_id}"): "Delete a job description",
    ("POST", "/jobs/{job_id}/analyze"): "Extract (or re-extract) the job's requirements",
    ("GET", "/jobs/{job_id}/requirements"): "List the job's requirements",

    ("POST", "/gap-analysis/{job_id}"): "Run a skill gap analysis against a job",
    ("GET", "/gap-analysis"): "List my analyses",
    ("GET", "/gap-analysis/{analysis_id}"): "Analysis summary (alignment %, counts)",
    ("GET", "/gap-analysis/{analysis_id}/results"): "Per-requirement results with explanations",

    ("POST", "/roadmaps"): "Create a roadmap from an analysis",
    ("POST", "/roadmaps/{roadmap_id}/regenerate"): "Rebuild the roadmap from the latest analysis",
    ("POST", "/roadmaps/{roadmap_id}/improve"): "Improve the study-plan wording with AI",
    ("GET", "/roadmaps"): "List my roadmaps",
    ("GET", "/roadmaps/{roadmap_id}"): "Get a roadmap with its items",
    ("GET", "/roadmaps/{roadmap_id}/progress"): "Roadmap progress summary",
    ("PATCH", "/roadmaps/{roadmap_id}/items/{item_id}"): "Update an item's status",
    ("PATCH", "/roadmaps/{roadmap_id}/items/{item_id}/progress"): "Update an item's status (alias used by Progress)",
    ("DELETE", "/roadmaps/{roadmap_id}"): "Delete a roadmap",

    ("POST", "/evidence"): "Add evidence for a skill (GitHub repository or project link)",
    ("GET", "/evidence"): "List my evidence",
    ("GET", "/evidence/{evidence_id}"): "Get one piece of evidence",
    ("POST", "/evidence/{evidence_id}/verify"): "Verify evidence again",
    ("DELETE", "/evidence/{evidence_id}"): "Delete evidence",

    ("GET", "/readiness/compare"): "Compare two analyses (before vs after)",
    ("GET", "/readiness/jobs/{job_id}/history"): "Readiness history for a job",
    ("GET", "/readiness/jobs/{job_id}/latest"): "Latest readiness for a job",
    ("POST", "/readiness/{analysis_id}/calculate"): "Calculate career readiness",
    ("GET", "/readiness/{analysis_id}"): "Get career readiness for an analysis",

    ("GET", "/career/actions"): "List my career actions",
    ("PATCH", "/career/actions/{action_id}"): "Update an action (completing it with a link adds evidence)",
    ("GET", "/career/{analysis_id}/plan"): "Get the career action plan",
    ("POST", "/career/{analysis_id}/plan/generate"): "Generate or rebuild the career action plan",
    ("PATCH", "/career/interview-prep/{item_id}"): "Update an interview-prep item",
    ("GET", "/career/{analysis_id}/interview-prep"): "Get interview preparation",
    ("POST", "/career/{analysis_id}/interview-prep/generate"): "Generate interview preparation",
    ("GET", "/career/opportunities/source-status"): "Which opportunity sources are available",
    ("GET", "/career/opportunities/saved-jobs"): "Match me against my saved jobs",
    ("POST", "/career/opportunities/match"): "Match me against a pasted job description",
    ("GET", "/career/opportunities"): "My opportunity match history",
    ("DELETE", "/career/opportunities/{match_id}"): "Delete an opportunity match",

    ("GET", "/health"): "Health check",
}


def apply_documentation(*routers: APIRouter) -> None:
    """Attach the summaries to each router's routes (documentation only).

    Call this BEFORE app.include_router(): newer FastAPI versions keep included routers nested,
    so walking app.routes afterwards would miss them. A router built with a prefix already
    stores full paths ("/jobs/{job_id}"), which is what SUMMARIES uses.
    """
    for router in routers:
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            prefix = router.prefix or ""
            full_path = route.path if route.path.startswith(prefix) and prefix else prefix + route.path
            for method in route.methods:
                summary = SUMMARIES.get((method, full_path)) or SUMMARIES.get((method, route.path))
                if summary:
                    route.summary = summary
                    break
