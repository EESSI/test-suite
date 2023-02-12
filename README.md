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
    in combination with all available system:partitions as defined in the site config file,
    but skips CUDA modules in non-GPU nodes, and skips non-CUDA modules in GPU nodes

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

