"""
This test is adapted from the BLAS test included in the BLIS v1.1 sources at
https://github.com/flame/blis/tree/1.1/test/3 .

Customizations to the original BLAS test:
- adapted and simplified Makefile for FlexiBLAS support
- custom simplified run.sh script

Supported tags in this ReFrame test (in addition to the common tags):
- threading: `st`, `mt`
- BLAS implementation: `openblas`, `blis`, `aocl-blas`, `mkl`
- toolchain: `2023a`, `2023b`, `2024a`, ...
- `CI` tag: runs only openblas st + mt
"""


import reframe as rfm
from reframe.core.backends import getlauncher
from reframe.core.builtins import parameter, run_after, run_before, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import check_modules_avail, log

BLAS_MODULES = {
    '2023a': {
        'FlexiBLAS': 'FlexiBLAS/3.3.1-GCC-12.3.0',
        'BLIS': 'BLIS/0.9.0-GCC-12.3.0',
        'imkl': 'imkl/2023.1.0',
    },
    '2023b': {
        'FlexiBLAS': 'FlexiBLAS/3.3.1-GCC-13.2.0',
        'BLIS': 'BLIS/1.0-GCC-13.2.0',
        'imkl': 'imkl/2023.2.0',
    },
    '2024a': {
        'FlexiBLAS': 'FlexiBLAS/3.4.4-GCC-13.3.0',
        'BLIS': 'BLIS/1.0-GCC-13.3.0',
        'AOCL-BLAS': 'AOCL-BLAS/5.0-GCC-13.3.0',
        'imkl': 'imkl/2024.2.0',
    },
    '2025a': {
        'FlexiBLAS': 'FlexiBLAS/3.4.5-GCC-14.2.0',
        'BLIS': 'BLIS/1.1-GCC-14.2.0',
        'AOCL-BLAS': 'AOCL-BLAS/5.0-GCC-14.2.0',
        'imkl': 'imkl/2025.1.0',
    },
}

# FlexiBLAS and BLIS must always be loaded, even if BLIS is not used
BASE_BLAS_MODULES = {'FlexiBLAS', 'BLIS'}


def single_thread_scales():
    """Scales for the single-threaded tests"""
    return parameter(['1_core', '1_node'])


def multi_thread_scales():
    """Scales for the multi-threaded tests"""
    return parameter([
        k for (k, v) in SCALES.items()
        if v['num_nodes'] == 1
    ])


def get_module_lists(req_modules):
    module_lists = [
        [x[y] for y in req_modules]
        for x in BLAS_MODULES.values()
        if req_modules.issubset(x.keys())
    ]
    return [x for x in module_lists if check_modules_avail(x)]


class EESSI_BLAS_base(rfm.RunOnlyRegressionTest):
    "base BLAS test"
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.NODE
    time_limit = '10m'
    readonly_files = ['Makefile', 'run.sh', 'test_gemm.c', 'test_hemm.c', 'test_herk.c', 'test_trmm.c', 'test_trsm.c',
                      'test_utils.c', 'test_utils.h']
    env_vars = {
        'CFLAGS': '"-O2 -ftree-vectorize -march=native -fno-math-errno -g"',  # default EB CFLAGS
    }
    executable = './run.sh'
    nrepeats = '3'
    dts = ['s', 'd', 'c', 'z']
    ops = ['gemm_nn', 'hemm_ll', 'herk_ln', 'trmm_llnn', 'trsm_runn']
    sizes = {
        'st': ['100', '1000', '100'],
        'mt': ['200', '2000', '200'],
    }

    def required_mem_per_node(self):
        return self.num_cpus_per_task * 100 + 250

    @run_after('init')
    def set_prerun_cmds(self):
        """Set prerun_cmds"""
        self.prerun_cmds = [f'make flexiblas-{self.threading}']

    @run_after('init')
    def _tags(self):
        """Add tags for toolchain (e.g. 2024a) and threading (st or mt)"""
        blas_modules = {x: set(y.values()) for x, y in BLAS_MODULES.items()}
        module_names = set(self.module_name)
        toolchain = [x for x, y in blas_modules.items() if (module_names & y == module_names)][0]
        self.tags.add(toolchain)

        self.tags.add(self.threading)
        log(f'tags set to {self.tags}')

    @run_after('init')
    def set_executable_opts(self):
        """Set executable_opts"""
        self.size = self.sizes[self.threading]
        self.executable_opts = [
            self.threading,
            self.nrepeats,
            f'''"{' '.join(self.size)}"''',
            f'''"{' '.join(self.dts)}"''',
            f'''"{' '.join(self.ops)}"''',
        ]

    @run_after('init')
    def set_blas_lib(self):
        """Set FLEXIBLAS environment variable to selected BLAS lib"""
        self.env_vars.update({
            'FLEXIBLAS': self.blas_lib,
        })

    @run_after('setup')
    def set_launcher(self):
        """Select local launcher"""
        self.job.launcher = getlauncher('local')()

    @sanity_function
    def assert_result(self):
        return sn.all([
            sn.assert_found(r"data\S+_flexiblas", f'output/{x}{y}_flexiblas.m', f'output/{x}{y}_flexiblas.m')
            for x in self.dts for y in self.ops
        ])

    def _extract_perf(self, dt, op):
        return sn.extractsingle(
            rf'^data\S+_flexiblas.*{self.size[1]}\s+(?P<perf>\S+)\s+\];',
            f'output/{dt}{op}_flexiblas.m',
            1, float
        )

    @run_before('performance')
    def set_perf_vars(self):
        """Set performance variables"""
        self.perf_variables.update({
            f'{x}{y.split("_")[0]}': sn.make_performance_function(self._extract_perf(x, y), 'GFLOPS')
            for x in self.dts for y in self.ops
        })


class EESSI_BLAS_OpenBLAS_base(EESSI_BLAS_base):
    "base OpenBLAS test"

    module_lists = get_module_lists(BASE_BLAS_MODULES)
    module_name = parameter(module_lists)

    blas_lib = 'openblas'
    tags = {'openblas'}


@rfm.simple_test
class EESSI_BLAS_OpenBLAS_st(EESSI_BLAS_OpenBLAS_base, EESSI_Mixin):
    "single-threaded OpenBLAS test"

    scale = single_thread_scales()

    bench_name = bench_name_ci = 'OpenBLAS_st'
    threading = 'st'


@rfm.simple_test
class EESSI_BLAS_OpenBLAS_mt(EESSI_BLAS_OpenBLAS_base, EESSI_Mixin):
    "multi-threaded OpenBLAS test"

    scale = multi_thread_scales()

    bench_name = bench_name_ci = 'OpenBLAS_mt'
    threading = 'mt'


class EESSI_BLAS_AOCLBLAS_base(EESSI_BLAS_base):
    "base AOCL-BLAS test"

    module_lists = get_module_lists(BASE_BLAS_MODULES.union({'AOCL-BLAS'}))
    module_name = parameter(module_lists)

    blas_lib = 'aocl_mt'
    tags = {'aocl-blas'}


@rfm.simple_test
class EESSI_BLAS_AOCLBLAS_st(EESSI_BLAS_AOCLBLAS_base, EESSI_Mixin):
    "single-threaded AOCL-BLAS test"

    scale = single_thread_scales()
    threading = 'st'


@rfm.simple_test
class EESSI_BLAS_AOCLBLAS_mt(EESSI_BLAS_AOCLBLAS_base, EESSI_Mixin):
    "multi-threaded AOCL-BLAS test"

    scale = multi_thread_scales()
    threading = 'mt'


class EESSI_BLAS_MKL_base(EESSI_BLAS_base):
    "base MKL test"

    module_lists = get_module_lists(BASE_BLAS_MODULES.union({'imkl'}))
    module_name = parameter(module_lists)

    blas_lib = 'imkl'
    tags = {'mkl'}


@rfm.simple_test
class EESSI_BLAS_MKL_st(EESSI_BLAS_MKL_base, EESSI_Mixin):
    "single-threaded MKL test"

    scale = single_thread_scales()
    threading = 'st'


@rfm.simple_test
class EESSI_BLAS_MKL_mt(EESSI_BLAS_MKL_base, EESSI_Mixin):
    "multi-threaded MKL test"

    scale = multi_thread_scales()
    threading = 'mt'


class EESSI_BLAS_BLIS_base(EESSI_BLAS_OpenBLAS_base):
    "base BLIS test"

    blas_lib = 'blis'
    tags = {'blis'}


@rfm.simple_test
class EESSI_BLAS_BLIS_st(EESSI_BLAS_BLIS_base, EESSI_Mixin):
    "single-threaded BLIS test"

    scale = single_thread_scales()
    threading = 'st'


@rfm.simple_test
class EESSI_BLAS_BLIS_mt(EESSI_BLAS_BLIS_base, EESSI_Mixin):
    "multi-threaded BLIS test"

    scale = multi_thread_scales()
    threading = 'mt'
