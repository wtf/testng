import utils.files
import utils.git
import os
import subprocess
import shutil # for creating zip files

from config import config

def main():
    # get (or create) the local tests repo
    tests_dir = utils.files.get_dir(config["tests_dir"])
    repo = utils.git.get_repo(config["tests_dir"], config["repo_url"])
    utils.git.get_remote_branch(repo, config['repo_branch'])

    # set up the environment
    os.environ["ETHEREUM_TEST_PATH"] = tests_dir
    lllc_dir = config["lllc_path"].rsplit("/", 1)[0]
    if not lllc_dir in os.environ["PATH"].split(":"):
        os.environ["PATH"] = os.environ["PATH"] + ":" + lllc_dir

    # fill the tests!
    subprocess.call([config["testeth_path"], "-t", "GeneralStateTests", "--", "--filltests"])

    # and zip 'em up
    shutil.make_archive(tests_dir + '/GeneralStateTests', 'zip', tests_dir)


if __name__ == "__main__":
    main()
