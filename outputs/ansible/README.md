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

