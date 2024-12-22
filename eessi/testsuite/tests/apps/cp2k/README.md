# Input files for the CP2K test in src/QS

The following input files have been copied from the v2024.1 sources under benchmarks/QS,
but with `&SCF` option `IGNORE_CONVERGENCE_FAILURE` commented out as this option is only supported in versions >= 2023.1

```
$ find . -name "*.inp" |xargs sha256sum
fd7b90aafa5918ec8eb1b0c1c239332dca9981b9752e7ec3cf4b5e94724ee095  ./QS/H2O-32.inp
84ea9118535718df8604ff5b02e5805941cc76a4ddb2dad18b1a473b0a352b1e  ./QS/H2O-512.inp
218003ac4b23ed47caaa7717e988df0d52e5db9de90a65406273a6a44ccbf7d2  ./QS/H2O-128.inp
```
