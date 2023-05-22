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

and set your `PYTHONPATH` so that it includes the `eessi/reframe` directory from the repository.

- create a site configuration file

    - should look similar to `test-suite/eessi/reframe/config/settings_example.py`

- run the tests

    the example below runs a gromacs simulation using GROMACS modules available in the system,
    in combination with all available system:partitions as defined in the site config file

```
module load ReFrame/4.0.1

eessiroot=<path_to_test-suite>
eessihome=$eessiroot/eessi/reframe

PYTHONPATH=$PYTHONPATH:$EBROOTREFRAME:$eessihome reframe \
    -C <path_to_site_config_file> \
    -c $eessihome/eessi_checks/applications/ \
    -t CI -t 1_node \
    -r --performance-report
```

## Configuring GPU/non-GPU partitions in your site config file:

- running GPU jobs in GPU nodes
    - add feature `gpu` to the GPU partitions

- running non-GPU jobs in non-GPU nodes
    - add feature `cpu` to the non-GPU partitions

- running GPU jobs and non-GPU jobs on gpu nodes
    - add both features `cpu` and `gpu` to the GPU partitions
    ```
    'features': ['cpu', 'gpu'],
    ```

- setting the number of GPUS per node <x> for a partition:
    ```
    'access': ['-p <partition_name>'],
    'devices': [
        {'type': 'gpu', 'num_devices': <x>}
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

- specifying systems:partitions
    - `--setvar valid_systems=<comma-separated-list>`

- overriding tasks, cpus, gpus
    - `--setvar num_tasks_per_node=<x>`
    - `--setvar num_cpus_per_task=<y>`
    - `--setvar num_gpus_per_node=<x>`

- setting additional environment variables
    - `--setvar env_vars=<envar>:<value>`

## Developers
If you want to install the EESSI test suite from a branch, you can either install the feature branch with pip, or clone the github repo and check out the feature branch.

### Install from branch with pip

To install from one of the branches of the main repository, use:

```bash
pip install git+https://github.com/EESSI/test-suite.git@branchname
```

Generally, you'll want to do this from a forked repository though, where someone worked on a feature. E.g.

```bash
pip install git+https://github.com/<someuser>/test-suite.git@branchname
```

### Check out a feature branch from a fork
We'll assume you already a local clone of the official test-suite repository, called 'origin'. In that case, executing `git remote -v`, you should see:

```bash
$ git remote -v
origin  git@github.com:EESSI/test-suite.git (fetch)
origin  git@github.com:EESSI/test-suite.git (push)
```

You can add a fork to your local clone by adding a new remote. Pick a name for the remote that you find easy to recognize. E.g. to add the fork https://github.com/casparvl/test-suite

```bash
git remote add casparvl git@github.com:casparvl/test-suite.git
```

With `git remote -v` you should now see:

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

(remember to re-run `git fetch <remote>` if new branches don't show up with this command).

Finally, we can create a new local branch (-c) and checkout one of these feature branches (e.g. `setuppy` from the remote `casparvl`):
```bash
$ git switch -c local_setuppy_branch casparvl/setuppy
```

While the initial setup is a bit more involved, the advantage of this approach is that it is easy to pull in updates from a feature branch using `git pull`. You can also push back changes to the feature branch directly, but note that you are pushing to the Github fork of another Github user, so _make sure they are ok with that_!
