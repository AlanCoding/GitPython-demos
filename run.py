from git import Repo

import time
import sys
import os
from contextlib import contextmanager
import shutil
import json


assert len(sys.argv) >= 2, 'You need to pass the case name to investigate'
case = sys.argv[1]


CASES = {
    'test-playbooks': {
        'url': 'https://github.com/ansible/test-playbooks.git',
        'branch': 'with_requirements',
        'hash': '8e84f973fc711aee74bd8bc37e42b780d38ed884',
        'PR': 'pull/62/head'
    },
    'ansible': {
        'url': 'https://github.com/ansible/ansible.git',
        'branch': 'stable-2.5',
        'hash': '5400a06ac45fdd165c195a9369e93acece4b4c96',
        'PR': 'pull/56903/head'
    },
}


inputs = CASES[case]
print('***** Analyizing {} ******'.format(case))


track_all_refs = bool('--all-refs' in sys.argv)
reclone_original = bool('--reclone' in sys.argv)
full_mirror = bool('--mirror' in sys.argv)


mirrors_dir = os.path.join('/tmp', 'mirrors')
clones_dir = os.path.join('/tmp', 'clones')
hashes_dir = os.path.join('/tmp', 'hashes')
pr_dir = os.path.join('/tmp', 'pr')


for path in [mirrors_dir, clones_dir, hashes_dir]:
    if not os.path.exists(path):
        print('making root folder path {}'.format(path))
        os.mkdir(path)


@contextmanager
def time_this(name=''):
    print('')
    if name:
        print('Starting timing for {}'.format(name))
    start_time = time.time()
    yield start_time
    print('  timing for {}: {}'.format(name, time.time() - start_time))


def get_hash_dict(repo, all_refs=False):
    """Return a dictionary of commit hashes of branches, indexed by the branch name
    if all_refs is True, then a dictionary containing all references,
    not only the branches and tags, will be returned instead
    """
    if all_refs:
        display_mode = 'branches_and_tags'
        main_iterable = repo.refs
        with time_this('list_references_refs'):
            name_list = []
            ref_list_paths = []
            for this_ref in repo.refs:
                name_list.append(this_ref.name)
                ref_list_paths.append(this_ref.path)
    else:
        display_mode = 'all_refs'
        main_iterable = repo.branches
        with time_this('list_references_branches'):
            name_list = [b.name for b in main_iterable]

    # using commit.hexsha this is the most accepted standard, example:
    # https://github.com/ansible/ansible/commit/fca2a4c68b1173ec88a9e0e27e4151378aa56b10

    print('length of {}: {}'.format(display_mode, len(name_list)))

    sha_dict = {}
    watchout_time = time.time()
    with time_this('get_SHA1_for_{}'.format(display_mode)):
        for i, branch_name in enumerate(name_list):
            sha_dict[branch_name] = getattr(main_iterable, branch_name).commit.hexsha
            passed_time = time.time() - watchout_time
            if passed_time > 60.0:
                print('Processed {} in time of {}'.format(i, passed_time))
                print('  average time per item of {}'.format(passed_time/i))
                raise Exception('Fetching list of {} is taking too long.'.format(display_mode))

    return sha_dict


mirror_path = os.path.join(mirrors_dir, case.replace('-', '_'))
orig_branch_shas, orig_ref_shas = (None, None)


if reclone_original or not os.path.exists(mirror_path):
    if os.path.exists(mirror_path):
        shutil.rmtree(mirror_path)
    with time_this('bare_clone_from_github'):
        if full_mirror:
            # using the mirror option will pick up pull requests
            # but is this a good idea?
            repo = Repo.clone_from(inputs['url'], mirror_path, mirror=True, bare=True)
        else:
            repo = Repo.clone_from(inputs['url'], mirror_path, bare=True)
else:
    with time_this('create_repo_object'):
        repo = Repo(mirror_path)
        orig_branch_shas = get_hash_dict(repo, all_refs=track_all_refs)
    with time_this('fetching_origin'):
        # repo.remotes.origin.fetch('+refs/heads/*:refs/heads/*')
        repo.remotes.origin.fetch('+refs/*:refs/*')


branch_shas = get_hash_dict(repo, all_refs=track_all_refs)
# not the right time to gather this information, redundant with prints in method
# print('')
# print('length of branches: {}, length of references: {}'.format(len(branch_shas), len(ref_shas)))
# if orig_branch_shas is not None:
#     print('[original] length of branches: {}, length of references: {}'.format(len(orig_branch_shas), len(orig_ref_shas)))


# compare the new SHAs to the old to verify that the mirrored fetch is working
def diff_dicts(first, second):
    ret = {}
    for key, value in second.items():
        if key not in first:
            ret[key] = value
        elif first[key] != value:
            ret[key] = (first[key], value)
    return ret


print('')

if orig_branch_shas is not None:
    branch_diff = diff_dicts(orig_branch_shas, branch_shas)

    if branch_diff:
        print('Changes detected in refs/tags/branches:')
        print(json.dumps(branch_diff, indent=2))
    else:
        print('No differences detected in branch SHAs')

else:
    print('This is a first clone, so state comparisions are not done')


project_folder = case.replace('-', '_')

clone_path = os.path.join(clones_dir, project_folder)
hash_path = os.path.join(hashes_dir, project_folder)
pr_path = os.path.join(pr_dir, project_folder)


removed = []
for path in [clone_path, hash_path, pr_path]:
    if os.path.exists(path):
        shutil.rmtree(path)
        removed.append(path)

if removed:
    print('')
    print('Removed directories {}'.format(removed))


with time_this('make_branch_clone'):
    cloned_repo = repo.clone(clone_path, branch=inputs['branch'], depth=1, single_branch=True)


# We print top-level file count so that we can demonstrate that the
# trees are, in fact, checked out, and they differ from each other
# according to the different data in the scenario
print('Number of top-level files: {}'.format(len(os.listdir(clone_path))))


with time_this('make_hash_checkout'):
    hash_repo = repo.clone(hash_path, branch=inputs['branch'], single_branch=True)
    # verify that clone is clean-ish: hash_repo.head.is_detached
    # tends to work pretty reliably, so I stopped testing that
    head_for_hash = hash_repo.create_head('branch_for_job_run', inputs['hash'])
    head_for_hash.checkout()

    # this does not work
    # print(hash_repo.head.is_detached)
    # head_for_hash = hash_repo.create_head('branch_for_job_run', inputs['hash'])
    # hash_repo.head.reference = head_for_hash
    # print(hash_repo.head.is_detached)

    # this does not work
    # print(hash_repo.head.is_detached)
    # hash_repo.head.reference = repo.commit(inputs['hash'])
    # print(hash_repo.head.is_detached)


print('Number of top-level files: {}'.format(len(os.listdir(hash_path))))


with time_this('make_pr_checkout'):
    # Start by making a super dumb clone, just dont ask any questions
    # TODO: do the depth and single_branch arguments help or hurt??????
    pr_repo = repo.clone(pr_path, single_branch=True)
    # depth=1, single_branch=True: 0.3691997528076172
    # depth=1: 0.34058356285095215
    # single_branch=True: 0.38864684104919434
    # 0.6973230838775635

    upstream = pr_repo.create_remote('upstream', inputs['url'])
    upstream.fetch('refs/{}:branch_for_job_run'.format(inputs['PR']))

    pr_repo.branches.branch_for_job_run.checkout()


print('Number of top-level files: {}'.format(len(os.listdir(pr_path))))

print('')

