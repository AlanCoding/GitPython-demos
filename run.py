from git import Repo
from gitdb.exc import BadName as BadGitName

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


if not os.path.exists(mirrors_dir):
    print('making root folder path {}'.format(mirrors_dir))
    os.mkdir(mirrors_dir)


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
                print('  average time per item of {}'.format(passed_time / i))
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


# NOTE: this is congruent to AWX project update logic
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


def could_be_commit(some_ref):
    # git short commit is first 8 characters
    if len(some_ref) not in (40, 8):
        return False
    try:
        int(some_ref, 16)
        return True
    except ValueError:
        return False


# NOTE: this is loosely congruent to AWX project sync logic
def make_tmp_dir(case, name, some_ref):

    # some mundane groundwork stuff
    print('')
    print('')
    print('Starting case: {}'.format(name))
    scenario_dir = os.path.join('/tmp', name)

    if not os.path.exists(scenario_dir):
        print('making root folder path {}'.format(scenario_dir))
        os.mkdir(scenario_dir)

    project_folder = case.replace('-', '_')

    this_path = os.path.join(scenario_dir, project_folder)

    if os.path.exists(this_path):
        shutil.rmtree(this_path)
        print(' pre-run removed {}'.format(this_path))

    with time_this('make_{}_checkout'.format(name)):

        with time_this(' check_{}_existence'.format(name)):
            # First check, does it look like a commit, is it really a commit?
            concrete_commit = None
            delete_branch = True
            ref_type = 'unknown'
            if could_be_commit(some_ref):
                try:
                    concrete_commit = repo.commit(some_ref)
                    ref_type = 'commit'
                except BadGitName:
                    pass

            concrete_branch = None
            concrete_branch_name = 'awx_internal/{}'.format(uuid4())
            if concrete_commit:
                concrete_branch = repo.create_head(concrete_branch_name, concrete_commit)
            else:
                # Second check, does this reference tag which exists locally?
                try:
                    # NOTE: in final implementation, we will have to check out a specific
                    # commit for that branch, because of reference tracking
                    # so that'll make this case go away and get replaced with commit case
                    # but that will only happen when we have model attributes to deal with
                    concrete_branch = getattr(repo.refs, some_ref)
                    concrete_branch_name = some_ref
                    # don't want to delete user's branch, that'd be a whoopsie
                    delete_branch = False
                    ref_type = 'ref'
                except AttributeError:
                    pass

        refspec_conversion = 'refs/{}:{}'.format(inputs['PR'], concrete_branch_name)
        if not clone_in_tmp or ref_type == 'ref':

            if concrete_branch is None:
                # last ditch effort to get specifier, see if we can pull it from remote!
                with time_this('make_pr_checkout_fetch_time'):
                    if use_playbook:
                        playbook_update(
                            mirror_path, inputs['url'], bare=True,
                            refspec=refspec_conversion,
                        )
                    else:
                        # maybe this works, not really sure
                        # NOTE: this talks to remote (or it will, if it works)
                        repo.remotes.origin.fetch(refspec_conversion)

                    concrete_branch = getattr(repo.branches, concrete_branch_name)

            with time_this('make_{}_checkout_checkout_time'.format(name)):
                this_repo = repo.clone(this_path, branch=concrete_branch, depth=1, single_branch=True)

            if delete_branch:
                with time_this(' delete_{}_tmp_branch'.format(name)):
                    repo.delete_head(concrete_branch, force=True)

        else:
            # NOTE: this is the git-flow where the checkout is done in the tmp dir
            # this is generally the non-preferred method moving forward
            # Start by making a super dumb clone, just dont ask any questions
            with time_this('make_{}_checkout_clone_time'.format(name)):
                this_repo = repo.clone(this_path)

            if ref_type == 'unknown':
                if use_playbook:
                    with time_this('make_{}_checkout_fetch_time'.format(name)):
                        # well this is weird, we are both fetching to the branch and
                        # checking out that branch in the same command...
                        playbook_update(
                            this_path, inputs['url'],
                            refspec=refspec_conversion,
                            branch=concrete_branch_name
                        )
                else:
                    # this worked at least at some point in the past
                    with time_this('make_{}_checkout_fetch_time'.format(name)):
                        # NOTE: this talks to the remote
                        # also note, we're talking to remote in python code
                        upstream = this_repo.create_remote('upstream', inputs['url'])
                        upstream.fetch(refspec_conversion)

                concrete_branch = getattr(this_repo.branches, concrete_branch_name)

            elif ref_type == 'commit':
                concrete_branch = this_repo.create_head(concrete_branch_name, some_ref)

            with time_this('make_{}_checkout_checkout_time'.format(name)):
                concrete_branch.checkout()

    print('Number of top-level files for {}: {}'.format(name, len(os.listdir(this_path))))
    print(' head is detached: {}'.format(this_repo.head.is_detached))


for key in ('branch', 'hash', 'PR'):
    make_tmp_dir(case, key, inputs[key])


print('')

