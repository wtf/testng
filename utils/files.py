import os

import zipfile

from config import config

def get_dir(path, get_or_create=False):
    dir_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(dir_path):
        if get_or_create:
            os.makedirs(dir_path)
        else:
            raise FileNotFoundError(dir_path)
    return dir_path

def add_to_zip(dest, src, root=""):
    # default to tests_dir from config
    if not root:
        root = config['tests_dir']
    # get absolute path of root
    root = get_dir(root)

    dest = os.path.join(root, dest)
    dest = os.path.abspath(dest)
    src_abs = os.path.join(root, src)

    if not os.path.exists(src_abs):
        raise FileNotFoundError(src_abs)

    zf = zipfile.ZipFile(dest, "a")
    if os.path.isfile(src_abs):
        zf.write(src_abs, arcname = src)
    else:
        for (dirpath, dirnames, filenames) in os.walk(src_abs):
            for filename in filenames:
                abspath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(abspath, root)
                zf.write(abspath, arcname = relpath)
    zf.close()
