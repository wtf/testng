import os

import yaml

config = yaml.safe_load(open("config.yaml"))

# Set default branch
if not 'repo_branch' in config or not config['repo_branch']:
    config['repo_branch'] = 'master'

# Set default lllc path
if not 'lllc_path' in config or not config['lllc_path']:
    config['lllc_path'] = 'lllc'

# Set default testeth path
if not 'testeth_path' in config or not config['testeth_path']:
    config['testeth_path'] = 'testeth'

# Ensure that lllc can found
if not os.path.exists(config['lllc_path']):
    print('lllc could not be found! Please check that lllc exists at config.yaml::lllc_path')
    raise FileNotFoundError(404, 'lllc', 'Please make sure that "lllc_path" in config.yaml points to lllc executable')

# Ensure that testeth can found
if not os.path.exists(config['testeth_path']):
    print('testeth could not be found! Please check that testeth exists at config.yaml::testeth_path')
    raise FileNotFoundError(404, 'testeth', 'Please make sure that "testeth_path" in config.yaml points to testeth executable')

# Removing trailing slashes is a way of life
config['tests_dir'] = config['tests_dir'].rstrip("/")
