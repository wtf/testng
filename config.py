import os

import yaml

from utils.files import get_dir

config = yaml.safe_load(open("config.yaml"))

# Set default branch
config['repo_branch'] = config.get('repo_branch', "master")
if not config.get('repo_branch'):
    config['repo_branch'] = "master"

# Set default lllc path
if not config.get('lllc_path'):
    config['lllc_path'] = "lllc"

# Set default testeth path
if not config.get('testeth_path'):
    config['testeth_path'] = "testeth"

# Ensure that lllc can found
if not os.path.isfile(config['lllc_path']):
    print("lllc could not be found! Please check that config.yaml::lllc_path points to lllc binary")
    raise FileNotFoundError(404, "lllc", "Please make sure that \"lllc_path\" in config.yaml points to lllc binary")

# Ensure that testeth can found
if not os.path.isfile(config['testeth_path']):
    print("testeth could not be found! Please check that config.yaml::testeth_path points to testeth binary")
    raise FileNotFoundError(404, "testeth", "Please make sure that \"testeth_path\" in config.yaml points to testeth binary")

# Removing trailing slashes is a way of life
config['tests_dir'] = get_dir(config.get('tests_dir'))

# Useful variable for reading/writing files in this dir
config['script_dir'] = os.path.dirname(os.path.realpath(__file__))

# Output dir (for bundles, diffs, etc.)
if not config.get('output_dir'):
    config['output_dir'] = config['script_dir']

if not config.get('ignored_fields'):
    config['ignored_fields'] = []
