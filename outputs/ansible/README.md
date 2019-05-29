### Output discoveries

Why am I sharing these? Because they all illuminate some important information.
I will try to go through a few here.

#### landed_commits

```
Changes detected in branches:
{
  "devel": [
    "fca2a4c68b1173ec88a9e0e27e4151378aa56b10",
    "6e66ea9f78ea05bb6cf500fa7b910e74e8997618"
  ],
  "stable-2.8": [
    "73484808c8d4cbd47a84cfa9371b047a3ca68404",
    "20d17fe0eae528ea79235be6ded8c9ec454ae1ee"
  ]
}
```

This corresponds to real changes that happened.


#### ref_commits

in ref_commits file, we have:

```
Starting timing for get_SHA1_for_refs
  timing for get_SHA1_for_refs: 78.12333250045776
  timing for create_repo_object: 84.63474178314209
```

This was with an artificial limitation on the number of references
to 100. That means that these ran at a rate of about 1 commit
processed per second.

Something is not right there.

Also, we have a count for the total expected, which is 44086.
That means that saving the commit for all references would take 12 hours.

#### PR checkout options

There seems to be no direct cloning option for obtaining a PR ref. See:

https://stackoverflow.com/a/14969986/1092940

This seems like a notable absence.

Anyway, a PR ref is not grabbed as a part of the bare clone. So... that
raise the obvious question - do we need to do anything form the bare
clone when trying to get a checkout of a PR ref?

Yes.

From the output:

```
Starting timing for make_pr_checkout0

Starting timing for make_pr_checkout0_clone_time
  timing for make_pr_checkout0_clone_time: 4.158077955245972

Starting timing for make_pr_checkout0_fetch_time
  timing for make_pr_checkout0_fetch_time: 2.0287258625030518

Starting timing for make_pr_checkout0_checkout_time
  timing for make_pr_checkout0_checkout_time: 0.29522275924682617
  timing for make_pr_checkout0: 6.483470678329468
Number of top-level files: 27

Starting timing for make_pr_checkout1

Starting timing for make_pr_checkout1_clone_time
  timing for make_pr_checkout1_clone_time: 4.613970756530762

Starting timing for make_pr_checkout1_fetch_time
  timing for make_pr_checkout1_fetch_time: 2.2071762084960938

Starting timing for make_pr_checkout1_checkout_time
  timing for make_pr_checkout1_checkout_time: 0.3582789897918701
  timing for make_pr_checkout1: 7.180121183395386
Number of top-level files: 27

Starting timing for make_pr_checkout2

Starting timing for make_pr_checkout2_clone_time
  timing for make_pr_checkout2_clone_time: 4.996077060699463

Starting timing for make_pr_checkout2_fetch_time
  timing for make_pr_checkout2_fetch_time: 3.5560176372528076

Starting timing for make_pr_checkout2_checkout_time
  timing for make_pr_checkout2_checkout_time: 0.29170870780944824
  timing for make_pr_checkout2: 8.844265937805176
Number of top-level files: 27

Starting timing for make_pr_checkout3

Starting timing for make_pr_checkout3_clone_time
  timing for make_pr_checkout3_clone_time: 4.449956655502319

Starting timing for make_pr_checkout3_fetch_time
  timing for make_pr_checkout3_fetch_time: 2.3648977279663086

Starting timing for make_pr_checkout3_checkout_time
  timing for make_pr_checkout3_checkout_time: 0.3452773094177246
  timing for make_pr_checkout3: 7.160769939422607
Number of top-level files: 27

Starting timing for make_pr_checkout4
  timing for make_pr_checkout4: 23.417669534683228
```

This was an investigation of the multiple methods of cloning a PR ref.
You the approaches 0 through 3 were all different variations of
parameters added to the fetch/checkout process after cloning the default
branch from the bare repo. The approach 4 clones the repo anew.

You can see that the parameters don't matter a whole lot:

 - 0 - 'depth': 1, 'single_branch': True - 6.48
 - 1 - 'depth': 1 - 7.18
 - 2 - 'single_branch': True - 8.844
 - 3 - nothing: - 7.16

However, all of these are much better than cloning anew, which took 23.41 seconds.
So the bottom line is that we shouldn't worry too much about what parameters
are fed into the local clone (which favors option 3 for simplicity's sake),
BUT it is very important that we first perform the local clone to provide
a reference before fetching from remote and checking out the reference.
