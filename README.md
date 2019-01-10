# Installing
```
pip install -r requirements.txt
```
# Running
To diff artefacts between commits:
```
python run.py diff
```
To fill tests and create bundles:
```
python run.py fill
```# Configuration
## Generator settings
The `config.yaml` file contains the following variables:
 - `repo_url`: Github URL for repository containing test sources
 - `tests_dir`: Path to tests directory which contains the remote repo (created and updated if it doesn't exist)
 - `testeth_path`: Path to the testeth executable (unless already found in system `$PATH`)
 - `lllc_path`: Path to the lllc executable (unless already found in system `$PATH`)
 - `repo_branch`: Name of the remote branch containing desired tests
 - `output_dir`: Directory where bundles and diffs (but not artefacts) are created. Artefacts are created by testeth by inside the repo itself.
 - `ignored_fields`: List of JSON fields to be ignored while `diff`ing artefacts.

## Bundles
Test "bundles" can be defined inside `bundles.yaml`:
 - For each folder, all json/yml files inside all subfolders are included, minus the ones explicitly excluded.
 - Folders starting with `^` will be excluded (along with their subfolders)
 - Individual JSON files can be (in|ex)cluded in the same way
 - For the sake of simplicity, bundles or file path definitions cannot be nested

## Notes
 - The script loads tests fillers from an `src/` folder inside the `tests_dir`. This behavior is hard coded inside testeth.
