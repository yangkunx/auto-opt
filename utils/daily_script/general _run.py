import git
from git import RemoteProgress

class Git_progress(RemoteProgress):
    """
    #打印git clone的进度条
    """
    def update(self, *args):
        print(self._cur_line)

class WsfCode():
    def __init__(self, llm_dir, repo_url, repo_dir_name, branch=None):
        self.llm_dir = llm_dir
        self.repo_url = repo_url
        self.repo_dir_name = repo_dir_name
        try:
            self.repo = git.Repo(repo_dir_name)
        except git.exc.InvalidGitRepositoryError:
            print("Check-git-dir: The {} directory is not a git repository ".format(repo_dir_name))
        except git.exc.NoSuchPathError:
           print("Check-git-dir: The {} directory is not found".format(repo_dir_name)) 
        # self.branch = branch
        self.process = Git_progress()
    
    def clone_code(self, branch):
        """
        clone code
        """
        git.Repo.clone_from(self.repo_url, self.repo_dir_name, branch=branch, progress=self.process)
        active_branch = git.Repo(self.repo_dir_name).active_branch.name
        print("Aurrent_branch: {}".format(active_branch) )
    
    def check_branch(self):
        """
        检查指定目录是否是git repo
        """
        try:
            repo = git.Repo(check_git_dir)
            git_dir = repo.git_dir
            active_branch = repo.active_branch.name
            print("Check-git-dir: The {} directory is a git repository ".format(git_dir) )
            print("Aurrent_branch: {}".format(active_branch) )
            return True
        except git.exc.InvalidGitRepositoryError:
            print("Check-git-dir: The {} directory is not a git repository ".format(check_git_dir))
            return False
        except git.exc.NoSuchPathError:
            print("Check-git-dir: The {} directory is not exsit".format(check_git_dir))
            return False
    
    def checkout_branch(self):
        """
        checkout branch
        """
        print("Checkout: checkout the branch")
        if self.branch:
            self.repo.git.checkout("develop")
        else:
            self.repo.git.checkout(self.branch)

    def pull_code(self):
        """
        pull code
        """
        active_branch = git.Repo(self.repo_dir_name).active_branch.name
        print("Aurrent_branch: {}".format(active_branch) )
        print("Pull: pull the latest code")
        origin = self.repo.remotes.origin
        origin.pull()
        print("Pull: over to pull the latest code")

class PrepareEnv():
    pass

class AutomatedTest():
    pass



wsf_code = WsfCode()