# GitPython-demos
Demonstrations and timings of using GitPython with github and a
local proxy cloning repo

How to use:

```
python run.py test-playbooks
```

What this does:

This runs the demo for the ansible/test-playbooks repo in github.
The argument you give must be one of the data sets which are defined
in the code in `run.py`.

The demo will first either clone (anew) or fetch the remote repo.
To delete the repo and force it to clone again do:

```
python run.py test-playbooks --reclone
```

Then it will investigate the process of cloning for ref-cases.

ref-cases:
 - non-default branch
 - SHA1 reference
 - PR reference

### Repo cases

Several github repositories are selected to illustrate a boundary case
in computation, or for some connection to this project, or for some
other accolade.

These are defined in a dictionary in the `run.py` script and passed
as an argument on the CLI.

https://github.com/ansible/test-playbooks

The intended use case of AWX involves users maintaining their playbooks
in source control, and this is a repo of playbooks maintained to
test AWX. Since it has years of history, it becomes a fairly typical
example in terms of features used and contribution depth.

https://github.com/ansible/ansible

In addition to containing an epic quantity of playbooks (used for
integration testing), Ansible is one of the top open source projects
in the world, meaning that it has a contribution depth and tag history
which is substantial by any standard of "large project".
Issue count goes to 56k, and commits goes to 44k.

https://github.com/Microsoft/vscode

github gave this #1 place in "Top open source projects", but that is
measured by contributor count. Its 50k commit count is extremely large,
although not the largest. Issue count goes to 75k.

https://github.com/cirosantilli/test-many-commits-1m/

Has 100 million commits. This feels like a bad idea.

https://github.com/torvalds/linux

Has 840k commits, but they are not all garbage.

Somewhat deficient testing:

 - need a large branch/tag count repo
 - subrepos

### Findings

In the Ansible test case, checking out a SHA-1 in a non-default branch
was verified. f511bec4ff2d0371e5a90e5da2ea8887f5ff1ac2 is present in
stable-2.8, but not in devel.

timing was 6.47, as opposed to older commit which took 4.11

Also, behavior if commit does not exist verified:

```
print('commit that does not exist')
import traceback
try:
    # commit is from this repo, so not in any target repo
    repo.commit('dc587989c3c36560148429238bd19ac51163f6c6')
except Exception:
    traceback.print_exc()
```

gives

> ValueError: SHA b'dc587989c3c36560148429238bd19ac51163f6c6' could not be resolved, git returned: b'dc587989c3c36560148429238bd19ac51163f6c6 missing'

This is perfectly fine.

#### CLI options use

We can get the differential impact of certain decisions by using some of the CLI
flags. For instance, here's the timing of running `time python run.py ansible --clone-in-tmp`
with a pre-existing repo:

```
real	0m28.274s
user	0m16.730s
sys	0m8.070s
```

Now the timings for just `time python run.py ansible`:

```
real	0m18.329s
user	0m10.920s
sys	0m5.120s
```

You can see that one method is simply faster (due to reducing the number
of index items that need to be copied).

Likewise, for `time python run.py ansible --python`

```
real	0m12.167s
user	0m7.460s
sys	0m2.320s
```

This effectively demonstrates the amount of overhead we add by running
through the Ansible subprocess.
