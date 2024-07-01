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

#### Option 1: Creating a branch from the PR directly

```bash
git fetch origin pull/ID/head:BRANCH_NAME
```
where `ID` is the number of the pull request, and `BRANCH_NAME` is the name of the local branch (you can pick this yourself).

#### Option 2: Creating a branch tracking the feature branch

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

## Release management

When a release of the EESSI test suite is made, the following things must be taken care of:

- Version bump: in both `pyproject.toml` and `setup.cfg`;
- Version bump the default `EESSI_TESTSUITE_BRANCH` in `CI/run_reframe.sh`;
- Release notes: in `RELEASE_NOTES` + in GitHub release (cfr. https://github.com/EESSI/test-suite/releases/tag/v0.2.0);
- Tag release on GitHub + publish release (incl. release notes);
- Publishing release to PyPI:
  ```
  # example for version 0.2.0
  python setup.py sdist
  twine upload dist/eessi_testsuite-0.2.0.tar.gz
  ```
