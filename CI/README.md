# Setting up EESSI test suite CI

To set up regular runs for the EESSI test suite on a system, four things are needed:

1. The variable `EESSI_CI_SYSTEM_NAME` needs to be set in the environment
2. A local checkout of the `CI` subdirectory of the EESSI test suite repository needs to be present
3. The EESSI test suite repository needs to contain a file `CI/${EESSI_CI_SYSTEM_NAME}/ci_config.sh` with the configuration for the CI on that system
4. Add running the `run_reframe_wrapper.sh` to your `crontab`

## Checking out the CI folder from the EESSI test-suite
You can clone the full EESSI test suite
```
git clone https://github.com/EESSI/test-suite.git
```
Or do a sparse checkout
```
git clone -n --depth=1 --filter=tree:0 https://github.com/EESSI/test-suite.git
cd test-suite
git sparse-checkout set --no-cone CI
git checkout
```

## Creating a CI configuration file
If you are adding CI on a new system, first, pick a name for that system (we'll refer to this as `EESSI_CI_SYSTEM_NAME`). Using the example in `CI/aws_citc/ci_config.sh`, you can adapt the config to your needs.
It should define:
- `TEMPDIR` (mandatory): the temporary directory in which the CI pipeline can check out repositories and install ReFrame.
- `REFRAME_VERSION` (mandatory): the version of ReFrame you'd like to use to drive the EESSI test suite in the CI pipeline.
- `EESSI_VERSION` (mandatory): the version of the EESSI software stack you would like to be loaded & tested in the CI pipeline.
- `EESSI_CI_TESTSUITE_VERSION` (mandatory): the version of the EESSI test-suite repository you want to use in the CI pipeline.
- `RFM_CONFIG_FILES` (mandatory): the location of the ReFrame configuration file to be used for this system.
- `RFM_CHECK_SEARCH_PATH` (mandatory): the search path where ReFrame should search for tests to run in this CI pipeline.
- `RFM_CHECK_SEARCH_RECURSIVE` (mandatory): whether ReFrame should search `RFM_CHECK_SEARCH_PATH` recursively.
- `RFM_PREFIX`: the prefix in which ReFrame stores all the files.

## Creating the `crontab` entry and specifying `EESSI_CI_SYSTEM_NAME`
This line depends on how often you want to run the tests, and where the `run_reframe_wrapper.sh` is located exactly. We also define the EESSI_CI_SYSTEM_NAME in this entry, as cronjobs don't normally read your `.bashrc` (and thus we need a different way of specifying this environment variable).
 Assuming you checked out the EESSI test suite repository in your home dir:
```
echo "0 0 * * SUN EESSI_CI_SYSTEM_NAME=aws_citc ${HOME}/test-suite/CI/run_reframe_wrapper.sh" | crontab -
```
Would create a cronjob running weekly on Sundays. See the crontab manual for other schedules.

## Output of the CI pipeline
The whole point of the `run_reframe_wrapper.sh` script is to easily get the stdout and stderr from your `run_reframe.sh` in a time-stamped logfile. By default, these are stored in `${HOME}/EESSI_CI_LOGS`. This can be changed by setting the environment variable `EESSI_CI_LOGDIR`. Again, you'd have to set this when creating your `crontab` file, e.g.
```
echo "0 0 * * SUN EESSI_CI_SYSTEM_NAME=aws_citc EESSI_CI_LOGDIR=${HOME}/my_custom_logdir ${HOME}/test-suite/CI/run_reframe_wrapper.sh" | crontab -
```
