"""
This test is adapted from the BLAS test included in the BLIS v1.1 sources at
https://github.com/flame/blis/tree/1.1/test/3

Customizations to the original BLAS test:
- adapted and simplified Makefile for FlexiBLAS support
- custom simplified run.sh script

Note: a FlexiBLAS and BLIS module must always be loaded to run the test, even if BLIS or OpenBLAS are not used

Supported tags in this ReFrame test (in addition to the common tags):
- threading: `st`, `mt`
- BLAS implementation: `openblas`, `blis`, `aocl-blas`, `imkl`
- `CI` tag: runs only openblas st + mt
"""


import reframe as rfm
from reframe.core.backends import getlauncher
from reframe.core.builtins import parameter, run_after, run_before, sanity_function
import reframe.utility.sanity as sn

from eessi.testsuite.constants import COMPUTE_UNITS, DEVICE_TYPES, SCALES
from eessi.testsuite.eessi_mixin import EESSI_Mixin
from eessi.testsuite.utils import find_modules, find_modules_in_toolchain, split_module, log


def single_thread_scales():
    """Scales for the single-threaded tests"""
    return parameter(['1_core', '1_node'])


def multi_thread_scales():
    """Scales for the multi-threaded tests"""
    return parameter([
        k for (k, v) in SCALES.items()
        if v['num_nodes'] == 1
    ])


def get_blis_modules():
    """Return available BLIS modules + matching Flexiblas modules as a list of lists"""
    ml_lists = []

    blises = list(find_modules(r'BLIS$'))
    for blis in blises:
        _, _, toolchain, _ = split_module(blis)
        flexiblases = find_modules_in_toolchain('FlexiBLAS', toolchain)
        if flexiblases:
            ml_lists.append([flexiblases[-1], blis])
        else:
            log(f'no matching FlexiBLAS module found for module {blis}')

    return ml_lists


def get_openblas_modules():
    """
    Return available FlexiBLAS modules + matching BLIS modules as a list of lists
    Assume OpenBLAS is included in FlexiBLAS as a dependency
    """
    ml_lists = []

    flexiblases = list(find_modules(r'FlexiBLAS$'))
    for flexiblas in flexiblases:
        _, _, toolchain, _ = split_module(flexiblas)
        blises = find_modules_in_toolchain('BLIS', toolchain)
        if blises:
            ml_lists.append([flexiblas, blises[-1]])
        else:
            log(f'no matching BLIS module found for module {flexiblas}')

    return ml_lists


def get_aoclblas_modules():
    """Return available AOCL-BLAS modules + matching Flexiblas and BLIS modules as a list of lists"""
    ml_lists = []

    aoclblases = list(find_modules(r'AOCL-BLAS$'))
    for aoclblas in aoclblases:
        _, _, toolchain, _ = split_module(aoclblas)
        flexiblases = find_modules_in_toolchain('FlexiBLAS', toolchain)
        blises = find_modules_in_toolchain('BLIS', toolchain)
        if flexiblases and blises:
            ml_lists.append([flexiblases[-1], blises[-1], aoclblas])
        else:
            log(f'no matching FlexiBLAS and/or BLIS module found for module {aoclblas}')

    return ml_lists


def get_imkl_modules():
    """
    Return available imkl modules + matching Flexiblas and BLIS modules as a list of lists
    Only select imkl modules with SYSTEM toolchain
    """
    ml_lists = []

    flexiblases = sorted(find_modules(r'FlexiBLAS$'))
    if flexiblases:
        flexiblas = flexiblases[-1]
    else:
        log('no FlexiBLAS module found')
        return ml_lists

    _, _, toolchain, _ = split_module(flexiblas)

    blises = find_modules_in_toolchain('BLIS', toolchain)
    if blises:
        blis = blises[-1]
    else:
        log(f'no matching BLIS module found for module {flexiblas}')
        return ml_lists

    imkls = list(find_modules(r'imkl/[^-]*$', name_only=False))
    for imkl in imkls:
        ml_lists.append([flexiblas, blis, imkl])

    return ml_lists


class EESSI_BLAS_base(rfm.RunOnlyRegressionTest):
    "base BLAS test"
    device_type = DEVICE_TYPES.CPU
    compute_unit = COMPUTE_UNITS.NODE
    time_limit = '10m'
    readonly_files = ['Makefile', 'run.sh', 'test_gemm.c', 'test_hemm.c', 'test_herk.c', 'test_trmm.c', 'test_trsm.c',
                      'test_utils.c', 'test_utils.h']
    env_vars = {
        'CFLAGS': '"-O2 -ftree-vectorize -march=native -fno-math-errno -g"',  # default CFLAGS set by EasyBuild
    }
    executable = './run.sh'
    nrepeats = '5'
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
        """Add threading tag (st or mt)"""
        self.tags.add(self.threading)
        log(f'tags set to {self.tags}')

    @run_after('init')
    def set_executable_opts(self):
        """Set executable_opts"""
        self.size = self.sizes[self.threading]
        self.executable_opts = [
            self.threading,
            self.nrepeats,
            '"{}"'.format(' '.join(self.size)),
            '"{}"'.format(' '.join(self.dts)),
            '"{}"'.format(' '.join(self.ops)),
        ]

    @run_after('init')
    def set_flexiblas_blas_lib(self):
        """Set FLEXIBLAS environment variable to selected BLAS lib"""
        self.env_vars.update({
            'FLEXIBLAS': self.flexiblas_blas_lib,
        })

    @run_after('setup')
    def set_launcher(self):
        """Select local launcher"""
        self.job.launcher = getlauncher('local')()

    @sanity_function
    def assert_sanity(self):
        assert_backend = sn.assert_not_found(
            r'BLAS backend\s+\S+\s+not found',
            self.stderr,
            f'FlexiBLAS BLAS backend not found ({self.flexiblas_blas_lib})'
        )
        asserts_result = [
            sn.assert_found(r"data\S+_flexiblas", f'output/{x}{y}_flexiblas.m', f'output/{x}{y}_flexiblas.m')
            for x in self.dts for y in self.ops
        ]
        return sn.all([assert_backend] + asserts_result)

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

    module_name = parameter(get_openblas_modules())
    flexiblas_blas_lib = 'openblas'
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

    module_name = parameter(get_aoclblas_modules())
    flexiblas_blas_lib = 'aocl_mt'
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


class EESSI_BLAS_imkl_base(EESSI_BLAS_base):
    "base imkl test"

    module_name = parameter(get_imkl_modules())
    flexiblas_blas_lib = 'imkl'
    tags = {'imkl'}


@rfm.simple_test
class EESSI_BLAS_imkl_st(EESSI_BLAS_imkl_base, EESSI_Mixin):
    "single-threaded imkl test"

    scale = single_thread_scales()
    threading = 'st'


@rfm.simple_test
class EESSI_BLAS_imkl_mt(EESSI_BLAS_imkl_base, EESSI_Mixin):
    "multi-threaded imkl test"

    scale = multi_thread_scales()
    threading = 'mt'


class EESSI_BLAS_BLIS_base(EESSI_BLAS_base):
    "base BLIS test"

    module_name = parameter(get_blis_modules())
    flexiblas_blas_lib = 'blis'
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
