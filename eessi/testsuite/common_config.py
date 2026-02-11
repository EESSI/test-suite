import json
import os

from reframe.core.logging import getlogger

from eessi.testsuite.constants import FEATURES

perflog_format = '|'.join([
    '%(check_job_completion_time)s',
    '%(osuser)s',
    '%(version)s',
    '%(check_unique_name)s',
    '%(check_info)s',
    '%(check_system)s',
    '%(check_partition)s',
    '%(check_environ)s',
    '%(check_exclusive_access)s',
    '%(check_num_tasks)s',
    '%(check_num_cpus_per_task)s',
    '%(check_num_tasks_per_node)s',
    '%(check_num_gpus_per_node)s',
    '%(check_use_multithreading)s',
    '%(check_modules)s',
    '%(check_jobid)s',
    '%(check_perfvalues)s',
])

format_perfvars = '|'.join([
    '%(check_perf_var)s',
    '%(check_perf_value)s',
    '%(check_perf_lower_thres)s',
    '%(check_perf_upper_thres)s',
    '%(check_perf_unit)s',
    ''  # final delimiter required
])


def set_common_required_config(site_configuration: dict, set_memory: bool = True):
    """
    Update ReFrame configuration file: set common required config options.
    Must be called at the end of the site configuration file (below the `site_configuration` dict).
    :param site_configuration: site configuration dictionary
    :param set_memory: whether to set memory resources
    """
    environments = [{'name': 'default'}]
    environs = ['default']
    use_nodes_option = True
    if set_memory:
        resources_memory = [{
            'name': 'memory',
            'options': ['--mem={size}'],
        }]
    else:
        resources_memory = []
    resources_gpu = [{
        'name': '_rfm_gpu',
        'options': ['--gpus-per-node={num_gpus_per_node}'],
    }]

    if 'environments' in site_configuration and site_configuration['environments'] != environments:
        getlogger().info(f"Changing environments in site config to {environments}")
    site_configuration['environments'] = environments

    for system in site_configuration.get('systems', []):
        for partition in system.get('partitions', []):
            # Set or overwrite the partition environment
            if 'environs' in partition and partition['environs'] != environs:
                getlogger().info(
                    f"Changing environs in site config to {environs} for {system['name']}:{partition['name']}")
            partition['environs'] = environs

            # Set or overwrite the 'use_nodes_option' scheduler option, if this is a SLURM-like scheduler
            if partition['scheduler'] in ['slurm', 'squeue']:
                # use --nodes option to ensure the exact number of nodes is requested
                if (
                    'sched_options' in partition
                    and 'use_nodes_option' in partition['sched_options']
                    and partition['sched_options']['use_nodes_option'] is not use_nodes_option
                ):
                    getlogger().info(' '.join([
                        "Changing sched_options['use_nodes_option'] in site config to",
                        f"{use_nodes_option} for {system['name']}:{partition['name']}",
                    ]))
                if 'sched_options' in partition:
                    partition['sched_options']['use_nodes_option'] = use_nodes_option
                else:
                    partition['sched_options'] = {'use_nodes_option': use_nodes_option}

            # Set or overwrite the partition resources
            if 'features' in partition and FEATURES.GPU in partition['features']:
                resources = resources_memory + resources_gpu
            else:
                resources = resources_memory
            if 'resources' in partition:
                orig = {json.dumps(x, sort_keys=True) for x in partition['resources']}
                new = {json.dumps(x, sort_keys=True) for x in resources}
                if orig != new:
                    getlogger().info(' '.join([
                        f"Changing resources in site config to {resources}",
                        f"for {system['name']}:{partition['name']}",
                    ]))
            partition['resources'] = resources


def common_logging_config(prefix=None):
    """
    return default logging configuration as a list: stdout, file log, perflog
    :param prefix: file log prefix
    """
    prefix = os.getenv('RFM_PREFIX', prefix if prefix else '.')
    logdir = os.path.join(prefix, 'logs')
    os.makedirs(logdir, exist_ok=True)

    return [{
        'level': 'debug',
        'handlers': [
            {
                'type': 'stream',
                'name': 'stdout',
                'level': 'info',
                'format': '%(message)s',
            },
            {
                'type': 'file',
                'name': os.path.join(logdir, 'reframe.log'),
                'level': 'debug',
                'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',
                'append': True,
                'timestamp': "%Y%m%d_%H%M%S",  # add a timestamp to the filename (reframe_<timestamp>.log)
            },
        ],
        'handlers_perflog': [
            {
                'type': 'filelog',
                'prefix': '%(check_system)s/%(check_partition)s',
                'level': 'info',
                'format': perflog_format,
                'format_perfvars': format_perfvars,
                'append': True,  # avoid overwriting
            },
        ],
    }]


def common_general_config(prefix=None):
    """
    Return common configuration for the 'general' section of the ReFrame configuration file
    :param prefix: prefix for the report_file
    """
    prefix = os.getenv('RFM_PREFIX', prefix if prefix else '.')
    reportdir = os.path.join(prefix, 'report_files')
    os.makedirs(reportdir, exist_ok=True)

    return {
        'check_search_recursive': True,
        'report_file': os.path.join(reportdir, 'run-report-{sessionid}.json')
    }


def common_eessi_init(eessi_version=None):
    """
    Returns the full path that should be sourced to initialize the EESSI environment for a given version of EESSI.
    If no eessi_version is passed, the EESSI_VERSION environment variable is read.
    If that is also not defined, default behaviour is to use `latest`.
    :param eessi_version: version of EESSI that should be sourced (e.g. '2023.06' or 'latest') [optional]
    """
    # Check which EESSI_CVMFS_REPO we are running under
    eessi_cvmfs_repo = os.getenv('EESSI_CVMFS_REPO', None)

    if eessi_cvmfs_repo is None:
        getlogger().warning(' '.join([
            "Environment variable 'EESSI_CVMFS_REPO' is not defined.",
            "If you plan to use the EESSI software stack,",
            "make sure to initialize the EESSI environment before running the test suite.",
        ]))
        return ''

    eessi_init = []
    pilot_repo = '/cvmfs/pilot.eessi-hpc.org'

    if eessi_cvmfs_repo == pilot_repo:
        eessi_init.append('export EESSI_FORCE_PILOT=1')
        if eessi_version is None:
            # Try also EESSI_VERSION for backwards compatibility with previous common_eessi_init implementation
            eessi_version = os.getenv('EESSI_PILOT_VERSION', os.getenv('EESSI_VERSION', 'latest'))
    else:
        # software.eessi.io, or another where we assume the same variable names to be used
        if eessi_version is None:
            eessi_version = os.getenv('EESSI_VERSION', None)
        # Without EESSI_VERSION, we don't know what to do. There is no default/latest version
        # So, report error
        if eessi_version is None:
            err_msg = "Environment variable 'EESSI_VERSION' was not found."
            err_msg += " Did you initialize the EESSI environment before running the test suite?"
            raise ValueError(err_msg)

    if eessi_cvmfs_repo == pilot_repo and eessi_version == 'latest':
        version_string = eessi_version
    else:
        version_string = f'versions/{eessi_version}'

    eessi_init.append(f'source {eessi_cvmfs_repo}/{version_string}/init/bash')
    return ' && '.join(eessi_init)


def get_sbatch_account():
    """
    return SBATCH_ACCOUNT as a string
    """
    sbatch_account = os.getenv('SBATCH_ACCOUNT', None)
    if sbatch_account is None:
        err_msg = "Environment variable 'SBATCH_ACCOUNT' was not found."
        err_msg += " It is required to set `SBATCH_ACCOUNT` to run on this system."
        raise ValueError(err_msg)
    return sbatch_account
