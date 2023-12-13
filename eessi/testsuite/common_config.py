import os

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

def common_eessi_init(eessi_version=None):
    """
    Returns the full path that should be sourced to initialize the EESSI environment for a given version of EESSI.
    If no eessi_version is passed, the EESSI_VERSION environment variable is read. If that is also not defined, default behaviour is to use `latest`.
    :param eessi_version: version of EESSI that should be sourced (e.g. '2023.06' or 'latest') [optional]
    """
    if eessi_version == None:
        eessi_version = os.getenv('EESSI_VERSION', 'latest')
    if eessi_version == 'latest':
        return '/cvmfs/pilot.eessi-hpc.org/latest/init/bash'
    else:
        return '/cvmfs/pilot.eessi-hpc.org/versions/%s/init/bash' % eessi_version
