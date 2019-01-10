import os
import re

import yaml

from utils import files
from config import config


def paths():
    """
    Processes bundles.yaml and generates a dict like {bundlename: [paths]}
    [paths] contains relative paths to artefacts (i.e. filled .json test files)
    Applies includes/excludes and ensures that source files exist
    """
    bundles_raw = yaml.safe_load(open("bundles.yaml"))
    _check_config(bundles_raw)
    # Split into includes and excludes
    includes = dict((name, []) for name in bundles_raw)
    excludes = dict((name, []) for name in bundles_raw)
    ## bundles_raw looks like {'name': ['path1', '^path2', ..], ..}
    for (name, paths) in bundles_raw.items():
        for path in paths:
            # Remove blank lines etc.
            if not path.strip():
                continue
            # Remove trailing slashes for consistency
            path = path.rstrip("/")
            if not path.startswith("^"):
                includes[name].append(path)
            else:
                excludes[name].append(path.lstrip("^"))
    # Generate dict of test paths after removing excludes
    test_paths = {}
    for (name, paths) in includes.items():
        test_paths[name] = set()
        # If there are no excludes, add everything
        if not excludes[name]:
            test_paths[name].update(paths)
        else:
            # Traverse included dirs and filter out excludes
            for path in paths:
                test_paths[name].update(_exclude(path, excludes[name]))
    for name in test_paths:
        # Convert source (Filler) filesystem paths into artefact (test) paths
        test_paths[name] = [_artefact_name(s) for s in test_paths[name]]
        # Remove children if parents have already been included
        test_paths[name] = _remove_children(test_paths[name])
    return test_paths


def tests(paths_dict):
    """
    Takes a bundles dict and flattens into unique tests.
    Removes unnecessary subdirectories so that all tests are run only once.
    Returns: [(Suite1, SingleTestIfAny), (Suite2, SingleTestIfAny),.. ]
    """
    tests_set = {path for paths in paths_dict.values() for path in paths}
    tests_set = _remove_children(tests_set)
    out = []
    for item in tests_set:
        test = _test_tuple(item)
        if test:
            out.append(test)
    return out


def _exclude(path, excludes):
    # Get filler dirs for path/excludes
    # e.g. "BlockchainTests/TransitionTests" => "/blah/../blah/src/BlockchainTestsFiller/TransitionTests"
    filler = _filler_path(path)
    excludes = [_filler_path(s) for s in excludes]
    # If this is a file, there are no subdirectories to exclude
    if os.path.isfile(filler):
        yield path
    # Traverse test dirs under path
    for (dirpath, dirnames, filenames) in os.walk(filler):
        ## Skip if we're in an excluded (sub)directory
        if any(dirpath.startswith(x) for x in excludes):
            dirnames.clear()
            continue
        # convert dirpath into testeth-usable test path
        if path:
            rel_path = path + dirpath.replace(filler, "")
        else:
            # We're at the src/ directory itself
            # Folders in here often start with "Filler"
            rel_path = dirpath.replace(filler, "").replace("Filler", "", 1).strip("/")
        ## If no excludes are inside this dir, add it and skip subdirectories
        if not any(x.startswith(dirpath) for x in excludes):
            yield rel_path
            dirnames.clear()
            continue
        ## Process all "final" subdirectories that contain tests
        if len(dirnames) == 0 and len(filenames) > 0:
            # No excluded path starts with this dirname.
            # And nothing excluded is inside this dir either.
            # So why are we still here? A file in here must be excluded.
            for filename in filenames:
                filepath = dirpath + "/" + filename
                if not any(filepath in s for s in excludes):
                    yield rel_path + "/" + filename


def _filler_path(path):
    if path:
        path = path + "/"
        path = path.replace("/", "Filler/", 1)
        path = path.rstrip("/")
        # Assuming that bundles.yaml can contain both source and artefact files
        # So first remove "Filler" from the filename if it exists, and then add it
        path = path.replace("Filler.json", ".json").replace(".json", "Filler.json")
        path = path.replace("Filler.yml", ".yml").replace(".yml", "Filler.yml")
    path = config['tests_dir'] + "/src/" + path
    return path


def _check_config(bundles):
    for paths in bundles.values():
        # Remove blanks
        for path in filter(None, paths):
            if path == "/" or path.startswith("^"):
                continue
            src_path = _filler_path(path)
            artefact_path = config['tests_dir'] + "/" + path
            if not (os.path.exists(src_path) or os.path.exists(artefact_path)):
                raise FileNotFoundError(path)


def _remove_children(paths):
    # Sort by length so we only have to check subdirectories in one direction
    paths = sorted(paths, key=len)
    # Find all subdirectories
    subdirs = set()
    for (i, path) in enumerate(paths):
        for s in paths[i+1:]:
            if s.startswith(path):
                subdirs.add(s)
    # Remove subdirectories
    paths = set(paths)
    paths.difference_update(subdirs)
    return paths


def _artefact_name(path):
    return path.replace("Filler/", "/").replace("Filler.", ".")


def _test_tuple(path):
    if "." in path:
        if not (path.endswith(".json") or path.endswith(".yml")):
            return
    test = _artefact_name(path)
    test = test.replace(".json", "").replace(".yml", "")
    suites = {
        "BlockchainTests/GeneralStateTests": "BCGeneralStateTests",
    }
    for (key, value) in suites.items():
        test = test.replace(key, value)
    if "." in path:
        return tuple(test.rsplit("/", 1))
    else:
        return (test, "")
