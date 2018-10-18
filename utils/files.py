import os


def get_dir(path, create_if_not_exists=False):
    dir_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(dir_path):
        if create_if_not_exists:
            os.makedirs(dir_path)
        else:
            raise FileNotFoundError
    return dir_path
