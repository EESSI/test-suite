# test-suite

A portable test suite for software installations, using ReFrame.

## Documentation

For documentation on installing, configuring, and using the EESSI test suite, see https://eessi.io/docs/test-suite/.

## Development

If you want to install the EESSI test suite from a branch, you can either
install the feature branch with `pip`, or clone the Github repository and check
out the feature branch.

### Install from branch with pip

To install from one of the branches of the main repository, use:

```bash
pip install git+https://github.com/EESSI/test-suite.git@branchname
```

Generally, you'll want to do this from a forked repository though, where
someone worked on a feature. E.g.

```bash
pip install git+https://github.com/<someuser>/test-suite.git@branchname
```

### Check out a feature branch from a fork

We'll assume you already have a local clone of the official `test-suite`
repository, called '`origin`'. In that case, executing `git remote -v`, you
should see:

```bash
$ git remote -v
origin  git@github.com:EESSI/test-suite.git (fetch)
origin  git@github.com:EESSI/test-suite.git (push)
```

You can add a fork to your local clone by adding a new remote. Pick a name for
the remote that you find easy to recognize. E.g. to add the fork
https://github.com/casparvl/test-suite and give it the (local) name `casparvl`,
run:

```bash
git remote add casparvl git@github.com:casparvl/test-suite.git
```

With `git remote -v` you should now see the new remote:

```bash
$ git remote -v
origin    git@github.com:EESSI/test-suite.git (fetch)
origin    git@github.com:EESSI/test-suite.git (push)
casparvl  git@github.com:casparvl/test-suite.git (fetch)
casparvl  git@github.com:casparvl/test-suite.git (push)
```

Next, we'll fetch the branches that `casparvl` has in his fork:

```bash
$ git fetch casparvl
```

We can check the remote branches using
```bash
$ git branch --list --remotes
  casparvl/example_branch
  casparvl/main
  origin/HEAD -> origin/main
  origin/main
```

(remember to re-run `git fetch <remote>` if new branches don't show up with
this command).

Finally, we can create a new local branch (`-c`) and checkout one of these
feature branches (e.g. `example_branch` from the remote `casparvl`). Here, we've
picked `my_own_example_branch` as the local branch name:
```bash
$ git switch -c my_own_example_branch casparvl/example_branch
```

While the initial setup is a bit more involved, the advantage of this approach
is that it is easy to pull in updates from a feature branch using `git pull`.

You can also push back changes to the feature branch directly, but note that
you are pushing to the Github fork of another Github user, so _make sure they
are ok with that_ before doing so!
