from git import Repo

import time
import sys
import os
from contextlib import contextmanager
import shutil
import json
import subprocess
from uuid import uuid4


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
        # from 2.3, in all branches: 5400a06ac45fdd165c195a9369e93acece4b4c96
        # has 33 top level files
        # stable-2.8 head f511bec4ff2d0371e5a90e5da2ea8887f5ff1ac2
        # as 27 top level files
        'hash': 'f511bec4ff2d0371e5a90e5da2ea8887f5ff1ac2',
        # 2.9: pull/56903/head
        # 2.3: pull/50671/head, expect 33 top level files
        'PR': 'pull/50671/head'
    },
}


inputs = CASES[case]
print('***** Analyizing {} ******'.format(case))


track_all_refs = True  # works for bare clones, not mirror clones
reclone_original = bool('--reclone' in sys.argv)
full_mirror = bool('--mirror' in sys.argv)
use_playbook = bool('--python' not in sys.argv)
clone_in_tmp = bool('--clone-in-tmp' in sys.argv)


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
    sha_dict = {}

    if all_refs:
        display_mode = 'all_local_refs'
    else:
        display_mode = 'branches_only'

    with time_this('list_references_{}'.format(display_mode)):

        if all_refs:
            main_iterable = repo.refs
        else:
            main_iterable = repo.branches

        name_list = []
        # ref_list_paths = []
        watchout_time = time.time()
        for i, this_ref in enumerate(main_iterable):
            name_list.append(this_ref.name)
            # ref_list_paths.append(this_ref.path)
            sha_dict[this_ref.name] = this_ref.commit.hexsha
            passed_time = time.time() - watchout_time
            if passed_time > 60.0:
                print('Processed {} in time of {}'.format(i, passed_time))
                print('  average time per item of {}'.format(passed_time/i))
                raise Exception('Fetching list of {} is taking too long.'.format(display_mode))


    # using commit.hexsha this is the most accepted standard, example:
    # https://github.com/ansible/ansible/commit/fca2a4c68b1173ec88a9e0e27e4151378aa56b10

    print('length of {}: {}'.format(display_mode, len(name_list)))

    return sha_dict


mirror_path = os.path.join(mirrors_dir, case.replace('-', '_'))
orig_branch_shas, orig_ref_shas = (None, None)


def playbook_update(path, url, bare=None, branch=None, refspec=None):
    extra_vars = {
        'project_path': path,
        'scm_url': url,
        'force': 'False',
        'scm_clean': 'False'
    }
    if bare is not None:
        extra_vars['bare'] = str(bare)
    if branch is not None:
        extra_vars['scm_branch'] = branch
    if refspec is not None:
        extra_vars['refspec'] = refspec
    args = ['ansible-playbook', 'checkout.yml', '--connection', 'local', '-i', 'localhost,']
    for k, v in extra_vars.items():
        args.extend(['-e', '{}={}'.format(k, v)])
    print('')
    print(' '.join(args))
    subprocess.run(' '.join(args), shell=True)


if reclone_original or not os.path.exists(mirror_path):
    if os.path.exists(mirror_path):
        shutil.rmtree(mirror_path)
    with time_this('bare_clone_from_github'):
        if full_mirror:
            # using the mirror option will pick up pull requests
            # but is this a good idea?
            repo = Repo.clone_from(inputs['url'], mirror_path, mirror=True, bare=True)
        else:
            if use_playbook:
                playbook_update(mirror_path, inputs['url'], bare=True, refspec='+refs/heads/*:refs/heads/*')
                repo = Repo(mirror_path)
            else:
                repo = Repo.clone_from(inputs['url'], mirror_path, bare=True)
else:
    with time_this('create_repo_object'):
        repo = Repo(mirror_path)
        orig_branch_shas = get_hash_dict(repo, all_refs=track_all_refs)
    with time_this('fetching_origin'):
        if use_playbook:
            # TODO: this does not take a prune option, that's a problem
            # filed: https://github.com/ansible/ansible/issues/57143
            playbook_update(mirror_path, inputs['url'], bare=True, refspec='+refs/heads/*:refs/heads/*')
            repo = Repo(mirror_path)  # not sure if this is needed
        else:
            # This is the refmap needed for the bare clones, in other words, always
            repo.remotes.origin.fetch('+refs/heads/*:refs/heads/*', prune=True)
            # This is the refmap needed for the mirror clones
            # using this is dangerously slow
            # repo.remotes.origin.fetch('+refs/*:refs/*', prune=True)


branch_shas = get_hash_dict(repo, all_refs=track_all_refs)

print('branch names')
print(list(branch_shas.keys()))


# compare the new SHAs to the old to verify that the mirrored fetch is working
def diff_dicts(first, second):
    ret = {}
    for key, value in second.items():
        if key not in first:
            ret[key] = value
        elif first[key] != value:
            ret[key] = (first[key], value)
    for key in first.keys():
        if key not in second:
            # a branch was pruned!
            ret[key] = '-{}'.format(first[key])
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


# NOTE: this is purely a local action, would need no git module action
# NOTE: in final implementation, we will have to check out a specific
# commit for that branch, because of reference tracking
with time_this('make_branch_clone'):
    cloned_repo = repo.clone(clone_path, branch=inputs['branch'], depth=1, single_branch=True)


# We print top-level file count so that we can demonstrate that the
# trees are, in fact, checked out, and they differ from each other
# according to the different data in the scenario
print('Number of top-level files: {}'.format(len(os.listdir(clone_path))))


# NOTE: this is purely a local action, would need no git module action
with time_this('make_hash_checkout'):
    use_hash = inputs['hash']
    # use the short version of the commit instead
    # use_hash = use_hash[:8]
    if not clone_in_tmp:
        commit = repo.commit(use_hash)
        tmp_branch_name = 'awx_internal/{}'.format(uuid4())
        tmp_branch = repo.create_head(tmp_branch_name, commit)
        hash_repo = repo.clone(hash_path, branch=tmp_branch, depth=1, single_branch=True)
        repo.delete_head(tmp_branch, force=True)
    else:
        hash_repo = repo.clone(hash_path)
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
    if not clone_in_tmp:
        tmp_branch_name = 'awx_internal/{}'.format(uuid4())

        if use_playbook:
            with time_this('make_pr_checkout_fetch_time'):
                playbook_update(
                    mirror_path, inputs['url'],
                    bare=True,
                    refspec='refs/{}:{}'.format(inputs['PR'], tmp_branch_name),
                )

            with time_this('make_pr_checkout_checkout_time'):
                tmp_branch = getattr(repo.branches, tmp_branch_name)
                pr_repo = repo.clone(pr_path, branch=tmp_branch, depth=1, single_branch=True)
                repo.delete_head(tmp_branch, force=True)

        else:
            raise Exception('logic for this is not written.')
    else:
        # Start by making a super dumb clone, just dont ask any questions
        with time_this('make_pr_checkout_clone_time'):
            pr_repo = repo.clone(pr_path)

        if use_playbook:
            with time_this('make_pr_checkout_fetch_time'):
                playbook_update(
                    pr_path, inputs['url'],
                    refspec='refs/{}:branch_for_job_run'.format(inputs['PR']),
                    branch='branch_for_job_run'
                )
        else:
            # old method
            with time_this('make_pr_checkout_fetch_time'):
                upstream = pr_repo.create_remote('upstream', inputs['url'])
                upstream.fetch('refs/{}:branch_for_job_run'.format(inputs['PR']))

            # a second part of the old method
            with time_this('make_pr_checkout_checkout_time'):
                pr_repo.branches.branch_for_job_run.checkout()

print('Number of top-level files: {}'.format(len(os.listdir(pr_path))))


print('')

