import git

from .files import get_dir


class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        # print('update(%s, %s, %s, %s)'%(op_code, cur_count, max_count, message))
        if not cur_count % 20:
            print(self._cur_line)


def get_repo(path, remote_url="", allow_create=False):
    dir_path = get_dir(path, allow_create)
    try:
        repo = git.Repo(dir_path)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError) as e:
        if allow_create:
            if remote_url:
                repo = clone_repo(remote_url, dir_path)
            else:
                raise ValueError("Please provide a remote repository URL")
        else:
            raise e
    else:
        print("Repository found:", dir_path)
    return repo


def clone_repo(url, path):
    print("Cloning %s into %s:" % (url, path))
    return git.Repo.clone_from(url, path, progress=Progress())


def pull_remote_branch(repo, branch):
    # discard changes in the working directory
    repo.head.reset(index=True, working_tree=True)
    # pull the remote branch
    repo.remotes.origin.pull(':'.join([branch]*2))
    # checkout to the branch
    repo.heads.__getitem__(branch).checkout()
