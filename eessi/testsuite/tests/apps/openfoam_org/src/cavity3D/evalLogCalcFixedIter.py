import re
import numpy as np
import pandas as pd
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("logfile", metavar="logFile", type=str,
                        help="an integer for the accumulator")
    parser.add_argument("-t", "--timeEnd", metavar="timeEnd", type=float,
                        help="provide runTime up to which the evaluation is performed")
    parser.add_argument("-s", "--saveEval", action='store_true',
                        help="save evaluation to a CSV file")
    args = parser.parse_args()

    customSolver, df = read_logfile(args.logfile)

    if args.timeEnd:
        df = df[df.runTimes <= args.timeEnd]

    # Extrapolation factor for the iteration number determined empirically
    fac = 2.3
    iter_start = int(round(np.mean(df.nPIter) / 2))
    iter_run = int(round(iter_start / fac))

    nTimes = len(df.nPIter)
    if nTimes != 15:
        print("\nWARNING: the extrapolation factor for the iteration number is "
              "legit only for the evaluation invterval of 15 time steps, but",
              nTimes, "has been evaluated from the logfile\n")
    print("Assumption: the linear solver is executed twice for the p eq.",
          "(nCorrectors 2)")
    print("nMeanUIter =", int(round(np.mean(df.nUIter) / 3)),
          "evaluated from", len(df.nUIter), "time steps")
    print("iter_start =", iter_start,
          "evaluated from", len(df.nPIter), "time steps")
    print("iter_run =", iter_run,
          "(supply this to maxIter entry in fixedIter/system/fvSolution)")

    if args.saveEval:
        df.to_csv(args.logfile + '.csv')


def addMatch(nIterArr, match):
    nIterArr[-1] += float(match.groups()[0])


def read_logfile(log):
    # String dict for matches
    regexFloat = r"[+-]?(\d+([.]\d*)?(e[+-]?\d+)?|[.]\d+(e[+-]?\d+)?)"
    matches = {
        "Ux": r".+Ux.+No Iterations ([\w.]+)",
        "Uy": r".+Uy.+No Iterations ([\w.]+)",
        "Uz": r".+Uz.+No Iterations ([\w.]+)",
        "p": r".+p.+No Iterations ([\w.]+)",
        "clockDiff": r"^Wall clock time.+ = ([\w.]+)",
        "execTime": r"^ExecutionTime = ([\w.]+)",
        "runTime": r"^Time = ([\w.]+)",
    }

    # Get the endTime from system/controlDict
    runTimes = []
    nUIter = []
    nPIter = []
    pResiduals = []
    times = []
    clockDiffs = []
    customSolver = False
    with open(log) as f:
        for line in f:
            for key, value in matches.items():
                match = re.match(value, line)
                if match:
                    if (key == "runTime"):
                        runTimes.append(0)
                        nUIter.append(0)
                        nPIter.append(0)
                        pResiduals.append(0)
                        times.append(0)
                        clockDiffs.append(0)
                        addMatch(runTimes, match)
                        continue
                    elif (key == "Ux"
                          or key == "Uy"
                          or key == "Uz"):
                        addMatch(nUIter, match)
                        continue
                    elif (key == "p"):
                        addMatch(nPIter, match)
                        match =\
                            re.match(".+Initial residual = " + regexFloat, line)
                        pResiduals[-1] = float(match.groups()[0])
                        continue
                    elif (key == "clockDiff"):
                        addMatch(clockDiffs, match)
                        customSolver = True
                    elif (key == "execTime"):
                        addMatch(times, match)
                        continue

    return customSolver, pd.DataFrame({'runTimes': runTimes, 'nUIter': nUIter,
                                       'nPIter': nPIter, 'pResiduals': pResiduals, 'times': times,
                                       'clockDiffs': clockDiffs})


if (__name__ == "__main__"):
    main()
