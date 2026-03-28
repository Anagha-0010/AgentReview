from dataclasses import dataclass
from loguru import logger

@dataclass
class PRData:
    pr_number: int
    title: str
    author: str
    repo_full_name: str
    diff: str
    base_branch: str
    head_branch: str

class PRParser:
    def extract_diff(self, files: list) -> str:
        diff_parts = []
        for f in files:
            filename = f.filename
            patch = getattr(f, "patch", None)
            if patch:
                diff_parts.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
        diff = "\n\n".join(diff_parts)
        logger.debug(f"Extracted diff: {len(diff)} chars from {len(files)} files")
        return diff

    def parse_pr(self, pr, files: list) -> PRData:
        return PRData(
            pr_number=pr.number,
            title=pr.title,
            author=pr.user.login,
            repo_full_name=pr.base.repo.full_name,
            diff=self.extract_diff(files),
            base_branch=pr.base.ref,
            head_branch=pr.head.ref
        )