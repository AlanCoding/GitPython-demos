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
