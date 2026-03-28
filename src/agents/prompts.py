RETRIEVAL_PROMPT = """You are a code retrieval specialist. Given a PR diff, 
identify the most important functions, classes, and patterns to search for 
in the codebase to provide relevant context for the review.

PR Diff:
{diff}

List 3-5 specific search queries to find relevant context. 
Return as a simple numbered list, one query per line."""

ANALYSIS_PROMPT = """You are a senior software engineer performing a code review.

PR Diff to review:
{diff}

Relevant codebase context:
{context}

Analyze this code change for:
1. Bugs and logical errors
2. Security vulnerabilities  
3. Performance issues
4. Code style and maintainability

Be specific and reference exact line numbers where possible.
Format your response as JSON with this structure:
{{
    "bugs": ["list of bugs found"],
    "security": ["list of security issues"],
    "performance": ["list of performance issues"],
    "style": ["list of style issues"],
    "summary": "one paragraph overall assessment"
}}"""

SYNTHESIS_PROMPT = """You are writing a GitHub PR review comment.

Analysis results:
{analysis}

Write a clear, constructive, developer-friendly review comment in markdown.
- Start with a brief overall assessment
- Use sections for Bugs, Security, Performance, Style
- Use bullet points
- Be specific and actionable
- End with an overall recommendation: APPROVE, REQUEST_CHANGES, or COMMENT"""