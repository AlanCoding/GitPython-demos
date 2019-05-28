### Changelog

 - Added script that does basic two-step process of
   clone from remote, and then clone specific branch to another folder
 - Changed the remote clone from a bare clone to a mirror clone
   this was probably needed in order to do a PR local clone
 - Added parameterizations for scenarios for the local clone
   - cloning a branch
   - cloning a commit
   - cloning a PR

### Roadmap

 - Confirm that doing a bare clone will not allow a subsequent local clone
   for the PR scenario
 - Add a step that tests whether or not the ref (arbitrary ref) is present
 - Add a 3rd step for the case of the PR
   - Do a fetch of the ref
 - Possibly look into a 4th scenario of a corner case, where someone tries
   to clone a commit of a PR. This will probably not be supported,
   although we could check to see if the mirror clone would allow this.

 - detect whether an input is SHA1 or a ref like a branch / tag / PR
 - have no logic switches specific to the scenarios, detect it implicitly

