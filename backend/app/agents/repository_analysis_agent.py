"""
Repository Analysis Agent — Agent 1 (Phase 1) — T-030-T-037.

Deterministic parsers extract factual repository metadata.
The LLM interprets metadata into higher-level architectural understanding.
The LLM does NOT generate the raw metadata — parsers do.
"""

import os
import json
import subprocess
from collections import Counter
from pathlib import Path
import git
import structlog

logger = structlog.get_logger()


# ── T-030: Clone repository ──────────────────────────────────────────────────

def clone_repository(repo_url: str, token: str, target_dir: str) -> str:
    """T-030: Clone a GitHub repository to target_dir using the authenticated URL."""
    auth_url = repo_url.replace("https://", f"https://oauth2:{token}@")
    if os.path.exists(target_dir) and os.listdir(target_dir):
        logger.info("Repository already cloned", target=target_dir)
        return target_dir
    os.makedirs(target_dir, exist_ok=True)
    git.Repo.clone_from(auth_url, target_dir, depth=50)
    logger.info("Repository cloned", target=target_dir)
    return target_dir


# ── T-031: Build file tree ────────────────────────────────────────────────────

def build_file_tree(root_dir: str, max_depth: int = 5) -> dict:
    """T-031: Return directory/file structure as a JSON-serializable dict."""
    result = {"name": os.path.basename(root_dir), "type": "directory", "children": []}

    def _walk(path: str, node: dict, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return
        for entry in entries:
            if entry.name.startswith(".") and entry.name not in (".env.example",):
                continue
            if entry.name in ("node_modules", "__pycache__", ".git", ".next", "dist", "build"):
                continue
            if entry.is_dir():
                child = {"name": entry.name, "type": "directory", "children": []}
                node["children"].append(child)
                _walk(entry.path, child, depth + 1)
            else:
                node["children"].append({"name": entry.name, "type": "file"})

    _walk(root_dir, result, 1)
    return result


# ── T-032: Language detection ─────────────────────────────────────────────────

LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "JavaScript",
    ".tsx": "TypeScript", ".java": "Java", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".cpp": "C++", ".c": "C", ".rs": "Rust", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell", ".yml": "YAML", ".yaml": "YAML",
    ".json": "JSON", ".html": "HTML", ".css": "CSS", ".sql": "SQL",
}


def detect_languages(root_dir: str) -> list[str]:
    """T-032: Count file extensions and return ranked list of programming languages."""
    counts: Counter = Counter()
    for path in Path(root_dir).rglob("*"):
        if path.is_file() and not any(
            p in path.parts for p in ("node_modules", "__pycache__", ".git", "dist", "build")
        ):
            lang = LANG_MAP.get(path.suffix.lower())
            if lang and lang not in ("YAML", "JSON", "HTML", "CSS", "Shell", "SQL"):
                counts[lang] += 1
    return [lang for lang, _ in counts.most_common()]


# ── T-033: Framework detection ────────────────────────────────────────────────

def detect_frameworks(root_dir: str) -> list[str]:
    """T-033: Detect frameworks from dependency manifests."""
    frameworks = []

    # package.json (Node/JS)
    pkg_json = os.path.join(root_dir, "package.json")
    if os.path.exists(pkg_json):
        with open(pkg_json, "r", encoding="utf-8", errors="ignore") as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" in deps:
            frameworks.append("Next.js")
        if "react" in deps:
            frameworks.append("React")
        if "express" in deps:
            frameworks.append("Express")
        if "fastify" in deps:
            frameworks.append("Fastify")
        if "vue" in deps:
            frameworks.append("Vue.js")
        if "angular" in deps:
            frameworks.append("Angular")

    # requirements.txt (Python)
    reqs = os.path.join(root_dir, "requirements.txt")
    if os.path.exists(reqs):
        with open(reqs, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
        if "fastapi" in content:
            frameworks.append("FastAPI")
        if "django" in content:
            frameworks.append("Django")
        if "flask" in content:
            frameworks.append("Flask")

    # pyproject.toml
    pyproject = os.path.join(root_dir, "pyproject.toml")
    if os.path.exists(pyproject):
        with open(pyproject, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
        if "fastapi" in content:
            frameworks.append("FastAPI")

    return list(dict.fromkeys(frameworks))  # deduplicate, preserve order


# ── T-034: Dependency detection ───────────────────────────────────────────────

def detect_dependencies(root_dir: str) -> dict[str, list[dict]]:
    """T-034: Extract dependency manifests from discovered dependency files."""
    result: dict[str, list[dict]] = {}

    pkg_json = os.path.join(root_dir, "package.json")
    if os.path.exists(pkg_json):
        with open(pkg_json, "r", encoding="utf-8", errors="ignore") as f:
            pkg = json.load(f)
        result["npm"] = [
            {"name": k, "version": v, "dev": is_dev}
            for is_dev, section in [(False, "dependencies"), (True, "devDependencies")]
            for k, v in pkg.get(section, {}).items()
        ]

    reqs = os.path.join(root_dir, "requirements.txt")
    if os.path.exists(reqs):
        with open(reqs, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        result["pip"] = [{"name": l.split("==")[0].split(">=")[0].split("~=")[0], "spec": l} for l in lines]

    return result


# ── Repository Analysis Agent node ────────────────────────────────────────────

def run_repository_analysis_agent(repo_dir: str, llm_client, scan_id: str) -> dict:
    """
    T-035: Full Repository Analysis Agent.
    1. Deterministic parsers extract metadata.
    2. LLM interprets metadata into architectural understanding.
    Returns a RepositoryContext dict.
    """
    logger.info("Agent 1: Repository Analysis starting", scan_id=scan_id)

    file_tree = build_file_tree(repo_dir)
    languages = detect_languages(repo_dir)
    frameworks = detect_frameworks(repo_dir)
    dependencies = detect_dependencies(repo_dir)

    # Detect databases and auth from dependency names
    databases = []
    authentication = []
    all_dep_names = []
    for pkg_list in dependencies.values():
        for pkg in pkg_list:
            all_dep_names.append(pkg.get("name", "").lower())

    db_indicators = {"psycopg2": "PostgreSQL", "asyncpg": "PostgreSQL", "mysql": "MySQL",
                     "pymongo": "MongoDB", "redis": "Redis", "sqlite": "SQLite", "pg": "PostgreSQL"}
    auth_indicators = {"passport": "OAuth", "jsonwebtoken": "JWT", "jwt": "JWT",
                       "bcrypt": "bcrypt", "pyjwt": "JWT", "authlib": "OAuth"}

    for dep_name in all_dep_names:
        for indicator, label in db_indicators.items():
            if indicator in dep_name and label not in databases:
                databases.append(label)
        for indicator, label in auth_indicators.items():
            if indicator in dep_name and label not in authentication:
                authentication.append(label)

    repo_context = {
        "languages": languages,
        "frameworks": frameworks,
        "databases": databases,
        "authentication": authentication,
        "file_tree_summary": json.dumps(file_tree, indent=2)[:3000],
        "raw_context": {
            "file_tree": file_tree,
            "dependencies": dependencies,
        },
    }

    # LLM architectural summary
    try:
        prompt = f"""You are analyzing a software repository for security assessment purposes.

Repository metadata extracted by deterministic parsers:
- Languages: {languages}
- Frameworks: {frameworks}  
- Databases: {databases}
- Authentication: {authentication}
- Total top-level items: {len(file_tree.get('children', []))}

Provide a concise (3-5 sentences) architectural summary covering:
1. What kind of application this is
2. The technology stack
3. Key security-relevant architectural patterns (auth, data access, API exposure)

Be factual and grounded in the metadata above. Do not invent information not present in the data."""

        response = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )
        repo_context["architecture_summary"] = response.choices[0].message.content
    except Exception as e:
        logger.warning("LLM architectural summary failed", error=str(e))
        repo_context["architecture_summary"] = f"Languages: {', '.join(languages)}. Frameworks: {', '.join(frameworks)}."

    logger.info("Agent 1: Repository Analysis complete", languages=languages, frameworks=frameworks)
    return repo_context
