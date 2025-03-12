import os

import reframe.core.logging as rflog

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
    return common configuration for the 'general' section of the ReFrame configuration file
    :param: prefix: prefix for the report_file
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
        rflog.getlogger().warning(' '.join([
            "Environment variable 'EESSI_CVMFS_REPO' is not defined.",
            "If you do not intend to use the EESSI software stack, this is perfectly fine.",
            "To use EESSI, initialize the EESSI environment before running the test suite.",
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
