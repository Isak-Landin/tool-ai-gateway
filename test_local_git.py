from git.utils import GitHub, PersistentShell
import subprocess
"""
    def __init__(self, remote_repo_url, local_key_path, local_repo_path, branch="main"):
        # self.remote_repo = remote_repo_url
        self.local_repo_path = local_repo_path
        self.key_path = local_key_path
        self.branch = branch
        self.shell = PersistentShell()
"""

remote_repo_url = "git@github.com:Isak-Landin/tool-ai-gateway.git"
local_user_repo_path = "~/tool-ai-gateway"
key_user = "~/.ssh/id_ed25519"

key_static = "/home/isakadmin/.ssh/id_ed25519"
local_static_repo_path = "/home/isakadmin/tool-ai-gateway"


Git = GitHub(
    remote_repo_url=remote_repo_url,
    local_key_path=key_static,
    local_repo_path=local_static_repo_path
)

print(Git.git_add(["ui/", "db/"]))
