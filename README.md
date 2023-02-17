# test-suite
A portable test suite for software installations, using ReFrame

## Getting started (@casparvl, commited 2022-12-06)

- install ReFrame >=3.11, <4

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
    in combination with all available system:partitions as defined in the site config file,
    but skips CUDA modules in non-GPU nodes, and skips non-CUDA modules in GPU nodes

```
module load ReFrame/3.12.0

eessiroot=<path_to_test-suite>
eessihome=$eessiroot/eessi/reframe

PYTHONPATH=$PYTHONPATH:$EBROOTREFRAME:$eessihome reframe \
    -C <path_to_site_config_file> \
    -c $eessihome/eessi-checks/applications/ \
    -t CI -t singlenode \
    -r --performance-report
```

## Improvements in PR #11 (2022-12-14)

- features to filter out CUDA modules in non-GPU nodes and non-CUDA modules in GPU nodes
    - requires adding `features` `cpu` and/or `gpu` to the partitions in the site config file
- support for specifying modules
    - via `--setvar modules=<modulename>`
- support for specifying systems:partitions
    - via `--setvar valid_systems=<comma-separated-list>`
- support for overriding tasks, cpus
    - via `--setvar num_tasks_per_node=<x>` and/or `--setvar num_cpus_per_task=<y>`
- support for setting additional environment variables
    - via `--setvar variables=<envar>:<value>`

