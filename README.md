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

