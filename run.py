import os
import subprocess
import argparse
import shutil
import json
import difflib
from datetime import datetime
from collections import OrderedDict
from io import StringIO

import bundles
from utils import files, gitwrap, color
from config import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=["bundle", "diff"])
    args = parser.parse_args()
    if args.action == "bundle":
        fill_and_bundle()
    else:
        generate_diffs(10)


def fill_and_bundle():
    repo = update_repo()
    # TODO: check last_run
    set_env_vars()
    # convert bundle definitions into filesystem paths
    paths = bundles.paths()
    # get the minimal set of tests to fill
    tests = bundles.tests(paths)
    tests = {(suite, "") for (suite, singletest) in tests}
    # fill the tests
    fill_tests(tests)
    hexsha = repo.commit().hexsha
    # and finally, create bundle zips
    bundles_dir = config['output_dir'] + "/bundles"
    out_dir = bundles_dir + "/" + hexsha
    out_dir = files.get_dir(out_dir, allow_create=True)

    for (name, test_paths) in paths.items():
        bundle_zip = out_dir + "/" + name + ".zip"
        latest_zip = bundles_dir + "/" + name + ".zip"
        for path in test_paths:
            files.add_to_zip(bundle_zip, path)
        shutil.copy2(bundle_zip, latest_zip)

    write_bundle_html(paths, repo.commit().hexsha)
    # TODO: update last_run


def generate_diffs(n):
    repo = update_repo()
    commits = list(repo.iter_commits())[n::-1] # [HEAD^n to HEAD]
    # TODO: check last_run
    # [1, 2, 3, 4...] => [(2, 1), (3, 2), (4, 3)...]
    for (older, newer) in zip(commits[:-1], commits[1:]):
        fill_changed(older, newer)
        write_diffs(older, newer)
    # TODO: update last_run

def write_diffs(older, newer):
    changed_srcs = _changed_files(older, newer)
    artefacts = [_artefact_path(src) for src in changed_srcs]
    # remove invalid artefacts (returned as None) and duplicates
    artefacts = set(filter(None, artefacts))
    if not artefacts:
        return
    old_dir = files.get_dir(config['output_dir']+
                           "/commits/"+
                           older.hexsha)
    new_dir = files.get_dir(config['output_dir']+
                           "/commits/"+
                           newer.hexsha)
    diff_tables = ""
    diff_count = 0
    print("Diffing tests...")
    # generate diff <table> for all changed artefacts
    for artefact in artefacts:
        old_fn = old_dir + "/" + artefact
        new_fn = new_dir + "/" + artefact
        old_test = _load_test(old_fn)
        new_test = _load_test(new_fn)
        # count artefacts that have changed
        if old_test != new_test:
            diff_count += 1
        # html diff between older and newer artefacts
        diff_table = difflib.HtmlDiff().make_table(old_test.split(),
                                                   new_test.split(),
                                                   older.hexsha+"<br>"+artefact,
                                                   newer.hexsha+"<br>"+artefact,
                                                   True,
                                                   5)
        # hack to fix column widths and text wrapping for output table
        diff_table = diff_table.replace(" nowrap=\"nowrap\"", "")
        diff_table = diff_table.replace("<th ", "<td ")
        diff_table = diff_table.replace("</th>", "</td>")
        diff_table = diff_table.replace("""<td colspan="2" class="diff_header">""", """<td class="diff_header"></td><td class="diff_title">""")

        diff_tables = diff_tables + diff_table + "<br>"
    # write diff html to file
    with open(config['script_dir']+"/templates/diff.html", 'r') as f:
        diff_template = f.read()
    diff_html = diff_template.replace("%diff_table%", diff_tables)
    with open(new_dir+"/index.html", 'w') as out:
        out.write(diff_html)

    # add commit details to index file
    with open(config['script_dir']+"/templates/commit.html") as f:
        commit_template = f.read()
    commit_html = commit_template.replace("%commithex%", newer.hexsha)
    commit_html = commit_html.replace("%nsrc%", str(len(changed_srcs)))
    commit_html = commit_html.replace("%nart%", str(diff_count))
    commit_github = config['repo_url'] + "/commit/" + newer.hexsha
    commit_html = commit_html.replace("%srcdiff%", commit_github)
    commit_html = commit_html.replace("%artdiff%", "commits/"+newer.hexsha+"/index.html")
    # read existing index file
    try:
        f = open(config['output_dir']+"/index.html", "r")
        index_html = f.read()
        f.close()
    except FileNotFoundError:
        index_html = ""
    # prepend and write
    index_html = commit_html + index_html
    with open(config['output_dir']+"/index.html", 'w') as out:
        out.write(index_html)


def _copy_changed(older, newer):
    changed_files = _changed_files(older, newer)
    for commit in (older, newer):
        # checkout the commit
        repo = commit.repo
        repo.head.reference = commit
        repo.head.reset(index=True, working_tree=True)
        for fn in changed_files:
            src_path = config['tests_dir'] + "/" + fn
            if os.path.exists(src_path):
                dest_dir = config['output_dir'] + "/commits/" + commit.hexsha
                dest_dir = files.get_dir(dest_dir, allow_create=True)
                dest_path = dest_dir + "/" + fn
                files.get_dir(os.path.dirname(dest_path),
                              allow_create=True)
                shutil.copy2(src_path, dest_path)
    return changed_files


def _changed_files(older, newer):
    changed = set()
    for diff in older.diff(newer):
        changed.update({diff.a_path, diff.b_path})
    return changed


def fill_changed(older, newer):
    changed_files = _copy_changed(older, newer)
    changed_files = {f.replace("src/", "") for f in changed_files if f.startswith("src/")}
    changed_tests = bundles.tests({'Changed': changed_files})
    if not changed_tests:
        return
    # Fill entire suites because they only contain changed tests
    changed_tests = {(suite.split("/")[0], "") for (suite, singletest) in changed_tests}
    for commit in (older, newer):
        commit_dir = files.get_dir(config['output_dir']+
                                   "/commits/"+commit.hexsha,
                                   allow_create=True)
        set_env_vars(commit_dir)
        fill_tests(changed_tests)


def _artefact_path(path):
    if not (path.endswith(".json") or
            path.endswith(".yml")):
        return
    if path.startswith("src/"):
       path = path.replace("src/", "", 1)
    path = path.replace("Filler/", "/").replace("Filler.", ".")
    return path


def fill_tests(tests):
    ct = 0
    for (suite, singletest) in tests:
        ct += 1
        # ordering of arguments matters here!
        cmd = ["testeth"]
        if suite:
            cmd.extend(["-t", suite])
        cmd.extend(["--", "--filltests"])
        if singletest:
            cmd.extend(["--singletest", singletest])
        print("Executing [%d of %d]: " % (ct, len(tests)) +
              " ".join(cmd))
        subprocess.call(cmd)


def update_repo():
    # get (or create) the local tests repo
    repo = gitwrap.get_repo(config['tests_dir'],
                            config['repo_url'],
                            allow_create=True)
    # pull from the configured branch
    gitwrap.pull_remote_branch(repo, config['repo_branch'])
    return repo


def set_env_vars(test_path=""):
    if not test_path:
        test_path = config['tests_dir']
    os.environ['ETHEREUM_TEST_PATH'] = test_path

    lllc_dir = os.path.dirname(config['lllc_path'])
    if not lllc_dir in os.environ['PATH'].split(":"):
        os.environ['PATH'] = os.environ['PATH'] + ":" + lllc_dir

    testeth_dir = os.path.dirname(config['testeth_path'])
    if not testeth_dir in os.environ['PATH'].split(":"):
        os.environ['PATH'] = os.environ['PATH'] + ":" + testeth_dir


def _load_test(filename):
    if not os.path.isfile(filename):
        return "{}"
    with open(filename, 'r') as fp:
        json_test = fp.read()
    test = json.loads(json_test)
    fp.close()
    test = _sort_dict(_exclude_keys(test, config['ignored_fields']))
    return json.dumps(test)


def _exclude_keys(d, keys):
    if type(d) is not dict:
        return d
    # copy the dict to prevent side-effects
    out = dict(d)
    for key in keys:
        if key in out:
            del out[key]
    out = dict((key, _exclude_keys(value, keys)) for (key, value) in out.items())
    return out


def _sort_dict(d):
    if type(d) is not dict:
        return d
    out = OrderedDict(sorted(d.items()))
    for (key, value) in out.items():
        out[key] = _sort_dict(value)
    return out


def write_bundle_html(paths, hexsha):
    # generate html
    with open(config['script_dir']+"/templates/bundles.html", 'r') as f:
        bundle_template = f.read()
    bundle_html = bundle_template
    commit_stamp = "%s (Generated at %s)" % (hexsha,
                                           datetime.utcnow().replace(microsecond=0))
    bundle_html = bundle_html.replace("%commit%", commit_stamp)
    link_template = """%bundlename%: <a href="%bundlelink%">download .zip</a><br />\n"""
    bundle_links = ""
    for name in paths:
        link_html = link_template
        link_html = link_html.replace("%bundlename%", name)
        link_html = link_html.replace("%bundlelink%", name+".zip")
        bundle_links += link_html
    bundle_html = bundle_html.replace("%bundles%", bundle_links)
    # read existing bundles file
    bundles_file = config['output_dir'] + "/bundles/index.html"
    try:
        f = open(bundles_file, "r")
        prev = f.read()
        f.close()
    except FileNotFoundError:
        prev = ""
    # prepend and write
    bundles_html = bundle_html + prev
    with open(bundles_file, 'w') as out:
        out.write(bundles_html)


if __name__ == "__main__":
    main()
