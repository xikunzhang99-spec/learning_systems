def detect_language(code: str) -> str:
    code_lower = code.lower()

    if "import " in code or "def " in code or "print(" in code:
        return "Python"

    if "const " in code or "let " in code or "await " in code or "=>" in code:
        return "JavaScript"

    if "select " in code_lower and "from " in code_lower:
        return "SQL"

    if "<html" in code_lower or "<div" in code_lower:
        return "HTML"

    if "<style" in code_lower or "{" in code and ":" in code and ";" in code:
        return "CSS"

    if any(kw in code_lower for kw in ["cd ", "pip ", "npm ", "git ", "ls ", "mkdir ", "echo "]):
        return "Shell"

    return "其他"
