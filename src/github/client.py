from github import Github
from loguru import logger
from src.core.config import settings
from src.github.parser import PRParser, PRData

class GitHubClient:
    def __init__(self):
        self.client = Github(settings.github_token)
        self.parser = PRParser()
        logger.info("GitHub client ready")

    def get_pr_data(self, repo_full_name: str, pr_number: int) -> PRData:
        logger.info(f"Fetching PR #{pr_number} from {repo_full_name}")
        repo = self.client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        files = list(pr.get_files())
        return self.parser.parse_pr(pr, files)

    def post_review_comment(self, repo_full_name: str, pr_number: int, comment: str):
        logger.info(f"Posting review to PR #{pr_number}")
        repo = self.client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(f"## 🤖 AgentReview\n\n{comment}")
        logger.info("Review posted successfully")