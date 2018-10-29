# Installing
```
pip install -r requirements.txt
```
# Running
```
python run.py
```
# Configuration
## Generator settings
The `config.yaml` file contains the following variables:
 - `repo_url`: Github URL for repository containing test sources
 - `tests_dir`: Path to tests directory which will contain the remote repo (will be created and pulled automatically)
 - `testeth_path`: Path to the testeth executable (unless already found in system `$PATH`)
 - `lllc_path`: Path to the lllc executable (unless already found in system `$PATH`)
 - `repo_branch`: Name of the remote branch containing desired tests
 - `ignored_fields`: List of JSON fields in test artefacts which will be ignored while `diff`ing.

## Bundles
Test "bundles" can be defined inside `bundles.yaml`:
 - For each folder, all JSON files inside all subfolders are included
 - Folders starting with `^` will be excluded (along with their subfolders)
 - Individual JSON files can be (in|ex)cluded in the some way
 - For the sake of simplicity, bundles or file paths cannot be nested

## Notes
 - The script loads tests fillers from an `src/` folder inside the `tests_dir`. This is hard coded inside testeth.
