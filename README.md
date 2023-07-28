# test-suite
A portable test suite for software installations, using ReFrame

## Getting started

- install ReFrame >=4.0

- install the test suite using 

```bash
pip install git+https://github.com/EESSI/test-suite.git
```

Alternatively, you can clone the repository

```bash
git clone git@github.com:EESSI/test-suite.git
```

- add the path of the `test-suite` directory to your ``$PYTHONPATH``

- create a site configuration file

    - should look similar to `test-suite/config/settings_example.py`

- run the tests

    The example below runs a gromacs simulation using GROMACS modules available
    in the system, in combination with all available system:partitions as
    defined in the site config file, using 1 full node (`--tag 1_node`, see `SCALES`
    in `constants.py`).  This example assumes that you have cloned the
    repository at `/path/to/EESSI/test-suite`.

```
cd /path/to/EESSI/test-suite

module load ReFrame/4.2.0

export PYTHONPATH=$PWD:$PYTHONPATH

reframe \
    --config-file <path_to_site_config_file> \
    --checkpath eessi/testsuite/tests/apps \
    --tag CI --tag 1_node \
    --run --performance-report
```

## Configuring GPU/non-GPU partitions in your site config file:

- running GPU jobs in GPU nodes
    - add `'features': [FEATURES[GPU]]` to the GPU partitions
    - add `'extras': {GPU_VENDOR: GPU_VENDORS[NVIDIA]}` to the GPU partitions (or
      `INTEL` or `AMD`, see `GPU_VENDORS` in `constants.py`)

- running non-GPU jobs in non-GPU nodes
    - add `'features': [FEATURES[CPU]]` to the non-GPU partitions

- running both GPU jobs and non-GPU jobs in GPU nodes
    - add `'features': [FEATURES[CPU], FEATURES[GPU]]` to the GPU partitions

- setting the number of GPUS per node <x> for a partition:
    ```
    'access': ['-p <partition_name>'],
    'devices': [
        {'type': DEVICE_TYPES[GPU], 'num_devices': <x>}
    ],
    ```
- requesting GPUs per node for a partition:
    ```
    'resources': [
        {
            'name': '_rfm_gpu',
            'options': ['--gpus-per-node={num_gpus_per_node}'],
        }
    ],
    ```

## Changing the default test behavior on the cmd line

- specifying modules
    - `--setvar modules=<modulename>`

- specifying valid systems:partitions
    - `--setvar valid_systems=<comma-separated-list>`

      Note that setting `valid_systems` on the cmd line disables filtering of
      valid systems:partitions in the hooks, so you have to do the filtering
      yourself.

- overriding tasks, cpus, gpus
    - `--setvar num_tasks_per_node=<x>`
    - `--setvar num_cpus_per_task=<y>`
    - `--setvar num_gpus_per_node=<x>`

- setting additional environment variables
    - `--setvar env_vars=<envar>:<value>`

Note that these override the variables for _all_ tests in the test suite that
respect those variables. To override a variable only for specific tests, one
can use the `TEST.VAR` syntax. For example, to run the `GROMACS_EESSI` test with the
module `GROMACS/2021.6-foss-2022a`:

- `--setvar GROMACS_EESSI.modules=GROMACS/2021.6-foss-2022a`

## Developers
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
We'll assume you already have a local clone of the official test-suite
repository, called 'origin'. In that case, executing `git remote -v`, you
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
origin  git@github.com:EESSI/test-suite.git (fetch)
origin  git@github.com:EESSI/test-suite.git (push)
casparvl        git@github.com:casparvl/test-suite.git (fetch)
casparvl        git@github.com:casparvl/test-suite.git (push)
```

Next, we'll fetch the branches that `casparvl` has in his fork:

```bash
$ git fetch casparvl
```

We can check the remote branches using
```bash
$ git branch --list --remotes
  casparvl/gromacs_cscs
  casparvl/main
  casparvl/setuppy
  casparvl/updated_defaults_pr11
  origin/HEAD -> origin/main
  origin/main
```

(remember to re-run `git fetch <remote>` if new branches don't show up with
this command).

Finally, we can create a new local branch (`-c`) and checkout one of these
feature branches (e.g. `setuppy` from the remote `casparvl`). Here, we've
picked `local_setuppy_branch` as the local branch name:
```bash
$ git switch -c local_setuppy_branch casparvl/setuppy
```

While the initial setup is a bit more involved, the advantage of this approach
is that it is easy to pull in updates from a feature branch using `git pull`.
You can also push back changes to the feature branch directly, but note that
you are pushing to the Github fork of another Github user, so _make sure they
are ok with that_ before doing so!
