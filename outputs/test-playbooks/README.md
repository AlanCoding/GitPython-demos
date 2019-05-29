### Output discoveries

#### ref_commits

Since the time needed to get the head commit of all refs with ansible
was too burdensome, we can only get complete numbers with small
repos. See from output:

```
length of branches: 4, length of references: 71

Starting timing for get_SHA1_for_branches
  timing for get_SHA1_for_branches: 0.001798868179321289

Starting timing for get_SHA1_for_refs
  timing for get_SHA1_for_refs: 0.10355138778686523
```

Time per thing:

 - 0.001798868179321289/4 = 0.5ms for branches
 - 0.10355138778686523/71 = 1.4ms for refs

Compare to Ansible where it took a full second to get the SHA1 for a ref.
This weakly suggests some O(N^2) scaling for the task of getting all
commit hashes for some reference.

This was later sped up by avoiding a `getattr` for getting the references
for every item in the loop. This reduced the time from about 1 second per
item to about 0.01 seconds per item. That still is too long.
While the incorrectly implemented method would take 12 hours for
all references in the Ansible repo, the improved logic would still take
over 6 minutes.
