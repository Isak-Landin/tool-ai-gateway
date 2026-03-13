import subprocess
from errors import GitHubError


class GitHub:
    def __init__(self, remote_repo, key, user, ):
        self.remote_repo = remote_repo
        self.key = key

    def git_pull(self, repo_path):
        return self.run_git(["pull"], repo_path)

    def git_push(self, repo_path):
        return self.run_git(["push"], repo_path)

    def git_add(self, repo_path, files):
        return self.run_git(["add", *files], repo_path)

    def git_commit(self, repo_path, message):
        return self.run_git(["commit", "-m", message], repo_path)

    def attempt_pull(self, repo_path):
        return self.git_pull(repo_path)

    def clone_repo(self, repo_path):
        return self.run_git(["clone", repo_path], repo_path)

    def run_git(self, args, cwd):
        try:

            result = subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise GitHubError(message=result.stderr.strip())

            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitHubError(message=e.stderr.strip())
        except Exception as e:
            raise GitHubError(message=str(e))