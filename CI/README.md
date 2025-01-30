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
If you are adding CI on a new system, first, pick a name for that system (we'll refer to this as `EESSI_CI_SYSTEM_NAME`). The CI config should then be in `CI/${EESSI_CI_SYSTEM_NAME}/ci_config.sh`. You can use the example in `CI/aws_mc/ci_config.sh`, and adapt it to your needs.
It should define:
- `TEMPDIR` (optional): the temporary directory in which the CI pipeline can check out repositories and install ReFrame. Default: `$(mktemp --directory --tmpdir=/tmp  -t rfm.XXXXXXXXXX)`.
- `REFRAME_ARGS` (optional): additional arguments to pass to the `reframe` command. Typically, you'll use this to specify `--tag` arguments to run a subset of tests. Default: `"--tag CI --tag 1_node"`.
- `REFRAME_VERSION` (mandatory): the version of ReFrame you'd like to use to drive the EESSI test suite in the CI pipeline.
- `REFRAME_URL` (optional): the URL that will be used to `git clone` the ReFrame repository (in order to provide the `hpctestlib`). Typically this points to the official repository, but you may want to use another URL from a fork for development purposes. Default: `https://github.com/reframe-hpc/reframe.git`.
- `REFRAME_BRANCH` (optional): the branch name to be cloned for the ReFrame repository (in order to provide the `hpctestlib`). Typically this points to the branch corresponding with `${REFRAME_VERSION}`, unless you want to run from a feature branch for development purposes. Default: `v${REFRAME_VERSION}`.
- `EESSI_CVMFS_REPO` (optional): the prefix for the CVMFS repository to use, e.g. `/cvmfs/software.eessi.io`
- `EESSI_VERSION` (optional): the version of the EESSI software stack you would like to be loaded & tested in the CI pipeline.
- `EESSI_TESTSUITE_URL` (optional): the URL that will be used to `git clone` the `EESSI/test-suite` repository. Typically this points to the official repository, but you may want to use another URL from a fork for development purposes. Default: `https://github.com/EESSI/test-suite.git`.
- `EESSI_TESTSUITE_VERSION` (optional): the version of the EESSI test-suite repository you want to use in the CI pipeline. Default: latest release.
- `EESSI_CONFIGS_TESTSUITE_URL` (optional): the URL that will be used to `git clone` the `test-suite/config` directory. Allows e.g. to use the tests from the latest release, but the configs from a feature branch in a different repository. Default: `EESSI_TESTSUITE_URL`.
- `EESSI_CONFIGS_TESTSUITE_BRANCH` (optional): the branch that will be checked out when cloning the `test-suite/config` directory. Allows e.g. to use the tests from the latest release, but the configs from the main branch. Default: `EESSI_TESTSUITE_VERSION`.
- `RFM_CONFIG_FILES` (optional): the location of the ReFrame configuration file to be used for this system. Default: `${TEMPDIR}/test-suite/config/${EESSI_CI_SYSTEM_NAME}.py`.
- `RFM_CHECK_SEARCH_PATH` (optional): the search path where ReFrame should search for tests to run in this CI pipeline. Default: `${TEMPDIR}/test-suite/eessi/testsuite/tests/`.
- `RFM_CHECK_SEARCH_RECURSIVE` (optional): whether ReFrame should search `RFM_CHECK_SEARCH_PATH` recursively. Default: `1`.
- `RFM_PREFIX` (optional): the prefix in which ReFrame stores all the files. Default: `${HOME}/reframe_CI_runs`.
- `REFRAME_TIMEOUT` (optional): DURATION as passed to the `timeout` command in Unix. If the `reframe` commands runs for longer than this, it will be killed by SIGTERM. The ReFrame runtime will then cancel all scheduled (and running) jobs. Can be used to make sure jobs don't pile up, e.g. if the test suite runs daily, but it takes longer than one day to process all jobs.

## Creating the `crontab` entry and specifying `EESSI_CI_SYSTEM_NAME`
This line depends on how often you want to run the tests, and where the `run_reframe_wrapper.sh` is located exactly. We also define the EESSI_CI_SYSTEM_NAME in this entry, as cronjobs don't normally read your `.bashrc` (and thus we need a different way of specifying this environment variable).
 Assuming you checked out the EESSI test suite repository in your home dir:
```
echo "0 0 * * SUN EESSI_CI_SYSTEM_NAME=aws_citc ${HOME}/test-suite/CI/run_reframe_wrapper.sh" | crontab -
```
Would create a cronjob running weekly on Sundays. See the crontab manual for other schedules.

Note that you can overwrite the settings in the ci_config.sh by setting environment variables in the crontab. E.g. the following crontab file would run single node and 2-node tests daily, and 1, 2, 4, 8, and 16-node tests weekly (on Sundays):
```
# crontab file
0 0 * * * EESSI_CI_SYSTEM_NAME=aws_mc REFRAME_ARGS="--tag CI --tag 1_node|2_nodes" ${HOME}/test-suite/CI/run_reframe_wrapper.sh
0 0 * * SUN EESSI_CI_SYSTEM_NAME=aws_mc REFRAME_ARGS="--tag CI --tag 1_node|2_nodes|4_nodes|8_nodes|16_nodes" ${HOME}/test-suite/CI/run_reframe_wrapper.sh
```

## Output of the CI pipeline
The whole point of the `run_reframe_wrapper.sh` script is to easily get the stdout and stderr from your `run_reframe.sh` in a time-stamped logfile. By default, these are stored in `${HOME}/EESSI_CI_LOGS`. This can be changed by setting the environment variable `EESSI_CI_LOGDIR`. Again, you'd have to set this when creating your `crontab` file, e.g.
```
echo "0 0 * * SUN EESSI_CI_SYSTEM_NAME=aws_citc EESSI_CI_LOGDIR=${HOME}/my_custom_logdir ${HOME}/test-suite/CI/run_reframe_wrapper.sh" | crontab -
```
