# test-suite
A portable test suite for software installations, using ReFrame

## Getting started

- install ReFrame >=4.0

- clone the test suite

```bash
git clone git@github.com:EESSI/test-suite.git
```

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
    -c $eessihome/eessi-checks/applications/ \
    -t CI -t singlenode \
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

