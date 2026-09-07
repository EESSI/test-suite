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


def set_common_required_config(site_configuration: dict, set_memory: bool = True, eessi_prepare_cmds=None):
    """
    Update ReFrame configuration file: set common required config options.
    Must be called at the end of the site configuration file (below the `site_configuration` dict).
    :param site_configuration: site configuration dictionary
    :param set_memory: whether to set memory resources
    """
    if not eessi_prepare_cmds:
        eessi_prepare_cmds = []

    environments = [
        {'name': 'EESSI-2023.06', 'modules': ['EESSI/2023.06'], 'prepare_cmds': eessi_prepare_cmds},
        {'name': 'EESSI-2025.06', 'modules': ['EESSI/2025.06'], 'prepare_cmds': eessi_prepare_cmds},
    ]
    environs = ['EESSI-2023.06', 'EESSI-2025.06']
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
        msg = f"Appending environments {environments} to the environments already present in the site_configuration"
        msg += f" ({site_configuration['environments']})"
        getlogger().info(msg)
        site_configuration['environments'].extend(environments)
    else:
        site_configuration['environments'] = environments

    for system in site_configuration.get('systems', []):
        for partition in system.get('partitions', []):
            # Set or overwrite the partition environment
            if 'environs' in partition and partition['environs'] != environs:
                msg = f"Appending environs {environs} to the existing environs ({partition['environs']})"
                msg += f" for {system['name']}:{partition['name']}"
                getlogger().info(msg)
                partition['environs'].extend(environs)
            else:
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
    Deprecated - print warning with suggested change.
    """
    getlogger().warning(' '.join([
        'common_eessi_init() is deprecated, you should replace the prepare_cmds in your ReFrame configuration.'
        ' On systems that have a module command available, you should no longer need any prepare_cmds.'
        " On systems that don't have a module command available, you need something like"
        " 'prepare_cmds' : ['source /cvfms/software.eessi.io/2025.06/init/lmod/bash && module unload EESSI']"
        " in order to use the Lmod from the EESSI compatibility layer (but not yet have an EESSI version loaded)"
    ]))
    return 'source /cvfms/software.eessi.io/2025.06/init/lmod/bash && module unload EESSI'


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
