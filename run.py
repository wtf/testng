import os
import subprocess

import shutil # for creating zip files

import utils.files
import utils.git
import bundles
from config import config


def main():
    # get (or create) the local tests repo
    tests_dir = utils.files.get_dir(config['tests_dir'])
    repo = utils.git.get_repo(config['tests_dir'], config['repo_url'])
    # pull from the configured branch
    utils.git.get_remote_branch(repo, config['repo_branch'])

    # set up the environment
    os.environ['ETHEREUM_TEST_PATH'] = tests_dir
    lllc_dir = config['lllc_path'].rsplit("/", 1)[0]
    if not lllc_dir in os.environ['PATH'].split(":"):
        os.environ['PATH'] = ":".join([os.environ['PATH'], lllc_dir])

    # expand paths inside bundles.yaml
    bundle_paths = bundles.paths()
    # get tests to fill
    tests = bundles.tests(bundle_paths)

    # fill the tests!
    ct = 0
    for (bundle, singletest) in tests:
        ct += 1
        testeth_params = [config['testeth_path']]
        if bundle:
            testeth_params.extend(["-t", bundle])
        testeth_params.extend(["--", "--filltests"])
        if singletest:
            testeth_params.extend(["--singletest", singletest])
        print("Executing [%d of %d] " % (ct, len(tests)) + " ".join(testeth_params))
        subprocess.call(testeth_params)

    bundles_dir = utils.files.get_dir(tests_dir + "/bundles", get_or_create=True)
    for (bundle_name, paths) in bundle_paths.items():
        bundle_name = bundles_dir + "/" + bundle_name + ".zip"
        for path in paths:
            utils.files.add_to_zip(bundle_name, path)
    # and zip 'em up
    # shutil.make_archive(tests_dir + '/GeneralStateTests', 'zip', tests_dir)


if __name__ == "__main__":
    main()
