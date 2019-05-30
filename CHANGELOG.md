### Changelog

 - Added script that does basic two-step process of
   clone from remote, and then clone specific branch to another folder
 - Changed the remote clone from a bare clone to a mirror clone
   this was probably needed in order to do a PR local clone
 - Added parameterizations for scenarios for the local clone
   - cloning a branch
   - cloning a commit
   - cloning a PR
 - Confirmed that doing a bare clone will not allow a subsequent local clone
   for the PR scenario
 - Changed from mirror cloning back to simple bare cloning
   - added logic to PR checkout that will pull from remote remote, not "local remote"
 - Investigated performance of options for obtaining a checkout of a PR reference
   it was found that a local clone from the bare repo as a pre-step provided
   a meaningful performance improvement
 - Replace the cloning actions with a subprocess call to a playbook
   using the git module
 - added refspec as parameter to git module bare cloning
 - investigate timing of making a new head, and then cloning
 - Add a step that tests whether or not arbitrary ref or commit is present
   - tests refs, then tests commits
     note: in actual implementation we will know in advance whether the
     ref should be expected to exist, so that makes it a little different
     from this, but commit check is still needed
   - if not, then try fetching (for PR refs)

### Pending

 - add a case for tags

### Abandoned

 - (subpoints that were abandoned, the larger thing was implemented)
    - if not present, the default branch is cloned into the tmp dir
      THIS IS HIGHLY CONTROVERSIAL
    - perform a git clone from the remote into that repo in the tmp dir
      reasoning is because this is more performant than cloning
      straight from the remote with the prior local clone
      THIS IS ALSO VERY CONTROVERSIAL AND MAY NOT WORK RIGHT

(all of the stuff about a specific commit was too complex and too far off
  the type of scripting that is done here)

- Add a 3rd step for the case of the PR
  - Do a fetch of the ref in the bare repo
    then move to the tmp dir by a local clone after it is fetched
    THIS HAS A LOT OF PROBLEMS AND IS TOTALLY ABANDONED

- detect whether an input is SHA1 or a ref like a branch / tag / PR
- have no logic switches specific to the scenarios, detect it implicitly
- Possibly look into a 4th scenario of a corner case, where someone tries
  to clone a commit of a PR. This will probably not be supported,
  although we could check to see if the mirror clone would allow this.
- Handle cases of deleted branches as well

