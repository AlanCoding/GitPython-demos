from git import Repo

import time
import sys
import os
from contextlib import contextmanager
import shutil


assert len(sys.argv) >=2, 'You need to pass the case name to investigate'
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
        'PR': 'pull/56903/head'
    },
}


inputs = CASES[case]
print('***** Analyizing {} ******'.format(case))
print('')


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
    if name:
        print('Starting timing for {}'.format(name))
    start_time = time.time()
    yield start_time
    print('Timing for {}: {}'.format(name, time.time() - start_time))
    print('')


mirror_path = os.path.join(mirrors_dir, case.replace('-', '_'))

if '--reclone' in sys.argv:
    if os.path.exists(mirror_path):
        shutil.rmtree(mirror_path)
    with time_this('bare_clone_from_github'):
        # using the mirror option will pick up pull requests
        # but is this a good idea?
        repo = Repo.clone_from(inputs['url'], mirror_path, mirror=True, bare=True)
else:
    with time_this('create_repo_object'):
        repo = Repo(mirror_path)
    with time_this('fetching_origin'):
        # repo.remotes.origin.fetch('+refs/heads/*:refs/heads/*')
        repo.remotes.origin.fetch('+refs/*:refs/*')


with time_this('list_references'):
    branch_list = [b.name for b in repo.branches]
    ref_list = [r.path for r in repo.refs]
    print(branch_list)
    print(ref_list)


with time_this('get_SHA1_for_refs'):
    branch_shas = [getattr(repo.branches, branch_name).commit.tree.hexsha for branch_name in branch_list]
    print(branch_shas)
    branch_shas = [getattr(repo.branches, branch_name).commit.hexsha for branch_name in branch_list]
    print(branch_shas)


project_folder = case.replace('-', '_')

clone_path = os.path.join(clones_dir, project_folder)
hash_path = os.path.join(hashes_dir, project_folder)
pr_path = os.path.join(pr_dir, project_folder)


for path in [clone_path, hash_path, pr_path]:
    if os.path.exists(path):
        print('removing directory {}'.format(path))
        shutil.rmtree(path)


with time_this('make_branch_clone'):
    cloned_repo = repo.clone(clone_path, branch=inputs['branch'], depth=1, single_branch=True)


print('Number of top-level files: {}'.format(len(os.listdir(clone_path))))


# import pdb; pdb.set_trace()

with time_this('make_hash_checkout'):
    hash_repo = repo.clone(hash_path, branch=inputs['branch'], single_branch=True)
    print(hash_repo.head.is_detached)
    head_for_hash = hash_repo.create_head('branch_for_job_run', inputs['hash'])
    head_for_hash.checkout()
    # hash_repo.head.reference = head_for_hash
    print(hash_repo.head.is_detached)

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
    pr_repo = repo.clone(pr_path, depth=1)
    pr_repo.remotes.origin.fetch('refs/{}:branch_for_job_run'.format(inputs['PR']))
    pr_repo.branches.branch_for_job_run.checkout()


print('Number of top-level files: {}'.format(len(os.listdir(clone_path))))


