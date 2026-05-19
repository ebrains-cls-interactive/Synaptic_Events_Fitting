import os
import shutil
from pathlib import Path
import pandas
import subprocess
import importlib
import plotly.graph_objs as go

def build_results_column_names(param_names):
    names = ["trace", "fitnr", "error"]
    names.extend(param_names)
    names.append("thresh")
    names.append("min")

    return names


def find_analysis_files(results_dir):
    """
    Find necessary files for best-fit analysis.
    """
    results_dir = Path(results_dir)

    config_file = None
    csv_file = None
    mod_file = None

    for file_path in results_dir.iterdir():
        if not file_path.is_file():
            continue

        if file_path.name.startswith("config") and file_path.suffix == ".txt":
            config_file = file_path
        elif file_path.suffix == ".csv":
            csv_file = file_path
        elif file_path.suffix == ".mod" and not file_path.name.startswith("netstims"):
            mod_file = file_path

    return {
        "config_file": config_file,
        "csv_file": csv_file,
        "mod_file": mod_file,
    }


def load_fit_results(results_dir):
    """
    Load configuration and fitting results form local results folder.
    """
    from synapticwidgets.data.model_support import readconffile

    files = find_analysis_files(results_dir)

    config_file = files["config_file"]
    csv_file = files["csv_file"]

    if config_file is None:
        raise FileNotFoundError("No config file was found in the selected results folder.")

    if csv_file is None:
        raise FileNotFoundError("No results CSV file was found in the selected results folder.")

    readconffile.filename = str(config_file)
    [inputfilename, modfilename, parametersfilename, flagdata, flagcut, nrtraces, Vrestf, esynf,
     nrparamsfit, paramnr, paramname, paraminitval, paramsconstraints, nrdepnotfit, depnotfit, nrdepfit,
     depfit, seedinitvaluef] = readconffile.readconffile()

    exp_file = None
    exp_candidate = results_dir / inputfilename.rstrip()
    if exp_candidate.exists():
        exp_file = exp_candidate

    names = build_results_column_names(paramname)

    cols = range(0, len(names))
    data = pandas.read_csv(csv_file, sep="\t", usecols=cols, names=names)

    files["exp_file"] = exp_file

    return {
        "files": files,
        "data": data,
        "names": names,
        "inputfilename": inputfilename,
        "modfilename": modfilename,
        "parametersfilename": parametersfilename,
        "flagdata": flagdata,
        "flagcut": flagcut,
        "nrtraces": nrtraces,
        "Vrestf": Vrestf,
        "esynf": esynf,
        "nrparamsfit": nrparamsfit,
        "paramnr": paramnr,
        "paramname": paramname,
        "paraminitval": paraminitval,
        "paramsconstraints": paramsconstraints,
        "nrdepnotfit": nrdepnotfit,
        "depnotfit": depnotfit,
        "nrdepfit": nrdepfit,
        "depfit": depfit,
        "seedinitvaluef": seedinitvaluef,
    }

def extract_best_fit_parameters(data, names, param_name):
    """
    Extract the best-fit row and fitted parameter values from the results dataframe.
    """
    if data.empty:
        raise ValueError("Results file is empty. No best fit can be extracted.")

    error_col = names[2]  # "error"
    index_plot = [n for n, i in enumerate(data[error_col]) if i == min(data[error_col])][0]

    vec_params_f = []
    for k in range(len(param_name)):
        vec_params_f.append(data[names[k + 3]][index_plot])

    return {
        "index": index_plot,
        "trace_number": data[names[0]][index_plot],
        "error": data[error_col][index_plot],
        "parameters": vec_params_f,
    }

def prepare_best_fit_workspace(results_dir, transfer_path):
    """
    Prepare the transfer folder workspace for NEURON best-fit replay using the files from one selected local results
     folder.
    """
    results_dir = Path(results_dir)
    transfer_path = Path(transfer_path)

    removable_names = {"start.py", "init.py"}
    removable_suffixes = {".txt", ".mod", ".csv", ".cpp", ".o", ".obj", ".tmp", ".dll", ".so"}
    removable_dirs = {"x86_64", "aarch64", "amd64"}

    # remove old job-specific files
    for file_path in transfer_path.iterdir():
        if file_path.is_dir():
            if file_path.name in removable_dirs:
                shutil.rmtree(file_path, ignore_errors=True)
            continue

        if file_path.name in removable_names:
            file_path.unlink()
        elif file_path.suffix in removable_suffixes and file_path.name != "netstims.mod":
            file_path.unlink()

    copied = []

    for file_path in results_dir.iterdir():
        if not file_path.is_file():
            continue

        keep = (
            file_path.suffix == ".txt"
            or (file_path.suffix == ".mod" and file_path.name != "netstims.mod")
            or file_path.name in {"test.csv", "start.py", "init.py"}
        )

        if keep:
            dest = transfer_path / file_path.name
            shutil.copy2(file_path, dest)
            copied.append(dest)

    return copied

def run_best_fit_simulation(transfer_path, data, names, best_fit, esynf, Vrestf, nrparamsfit, nrdepnotfit, modfilename,
                            paramname, depnotfit, nrdepfit, depfit, paramsconstraints, inputfilename):
    """
    Replay the best-fit result locally in NEURON and return the original and fitted traces.
    """
    transfer_path = Path(transfer_path)

    if not transfer_path.exists():
        raise FileNotFoundError(f"Transfer path does not exist: {transfer_path}")

    old_cwd = Path.cwd()

    try:
        os.chdir(transfer_path)

        compile_cmd = ["nrnivmodl"] if os.name != "nt" else ["cmd.exe", "/c", "nrnivmodl"]

        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            raise RuntimeError(
                f"nrnivmodl failed.\nSTDOUT:\n{compile_result.stdout}\nSTDERR:\n{compile_result.stderr}"
            )

        import neuron

        from synapticwidgets.data.model_support import readconffile, readexpfile

        config_file = next(transfer_path.glob("config*.txt"), None)
        if config_file is None:
            raise FileNotFoundError("No config file found in best-fit workspace.")

        readconffile.filename = str(config_file)
        readexpfile.filename2 = inputfilename.rstrip()

        from synapticwidgets.data.model_support import fitness, cellprop
        importlib.reload(fitness)
        importlib.reload(cellprop)

        fitness.filename3 = modfilename.rstrip()

        trace_number = data[names[0]][best_fit["index"]]
        vecparamsf = best_fit["parameters"]

        [sizeofsw, maxofsw, vec5, timevecS, cutsin] = fitness.finaltrace(trace_number=trace_number)
        parameters = vecparamsf
        print("Best-fit parameters:")
        for name, value in zip(paramname, parameters):
            print(name, value)

        tstop = 100
        e_syn = esynf
        Vrest = Vrestf

        netstim = neuron.h.NetStims(0.5, sec=cellprop.soma)
        netstim.freqhz = 18.0
        netstim.q = 0.0
        netstim.prob = 2.0
        netstim.noise = 1.0
        netstim.number = 1.0

        vclamp = neuron.h.VClamp(0.5, sec=cellprop.soma)
        vclamp.dur[0] = tstop
        vclamp.amp[0] = Vrest

        vclamp_i = neuron.h.Vector()
        timevec = neuron.h.Vector()
        timevec.from_python(timevecS)
        print("First 10 time values:", list(timevecS)[:10])

        with open(fitness.filename3) as ff:
            search_lines = ff.readlines()

        point_process_name = None
        for line in search_lines:
            if "POINT_PROCESS" in line:
                point_process_name = line.split()[1]
                break

        if point_process_name is None:
            raise RuntimeError(f"Could not find POINT_PROCESS in {fitness.filename3}")

        synapse = neuron.h.__getattribute__(point_process_name)(0.5)

        if fitness.filename3 == "ProbGABAAB_EMS_GEPH_g.mod":
            synapse.verboseLevel = 0
            synapse.Use = 1.0
            synapse.u0 = 1.0
            synapse.e_GABAA = e_syn
            synapse.setRNG(cellprop.synapse_rng)

        netcon = neuron.h.NetCon(netstim, synapse)
        netcon.delay = 0.0
        netcon.threshold = 0.0

        neuron.h("""nrparamsfit=0""")
        neuron.h.nrparamsfit = nrparamsfit
        neuron.h("""objref paramnamenrn[nrparamsfit]""")
        for i in range(nrparamsfit):
            neuron.h.paramnamenrn[i] = neuron.h.String()
            neuron.h.paramnamenrn[i].s = paramname[i]

        neuron.h("""objref parametersnrn""")
        neuron.h("""parametersnrn = new Vector()""")
        neuron.h.parametersnrn.from_python(parameters)

        for i in range(nrparamsfit):
            neuron.h("""strdef cmdstr""")
            neuron.h("""a=0""")
            neuron.h.a = i
            neuron.h.execute("""sprint(cmdstr,"%s = %g", paramnamenrn[a].s, parametersnrn.x[a])""")
            exec(neuron.h.cmdstr)

        for i in range(nrdepnotfit):
            cmd = depnotfit[i]
            exec(cmd)

        neuron.h.tstop = tstop

        exc = 0
        for i in range(nrdepfit):
            cmd = depfit[i]
            if eval(cmd):
                exc = exc or 1

        paramnr = 0
        for row in paramsconstraints:
            low = row[0]
            high = row[1]
            if parameters[paramnr] < low or parameters[paramnr] > high:
                exc = exc or 1
            paramnr += 1

        vclamp_i.record(synapse._ref_i, timevec)

        neuron.h.run()

        vclamp_i.mul(1000.0)

        model_current = vclamp_i.to_python()

        errorverif = 0
        for k in range(len(timevec)):
            errorverif += (model_current[k] - vec5[k]) * (model_current[k] - vec5[k])
        errorverif = errorverif / len(vec5)

        return {
            "time": list(timevecS),
            "original_trace": list(vec5),
            "fitted_trace": list(model_current),
            "error_verification": errorverif,
            "constraint_violation": bool(exc),
            "trace_number": trace_number,
        }

    finally:
        os.chdir(old_cwd)

def plot_best_fit(simulation_result):
    """
    Plot the original experimental trace and the locally replayed fitted trace.
    """
    time_values = simulation_result["time"]
    original_trace = simulation_result["original_trace"]
    fitted_trace = simulation_result["fitted_trace"]

    layout = go.Layout(
        xaxis=dict(
            title="time (ms)",
        ),
        yaxis=dict(
            title="current (pA)",
            hoverformat=".2f",
        ),
        width=1200,
        height=700,
    )

    trace1 = go.Scatter(x=time_values, y=original_trace, mode="lines", name="original")
    trace2 = go.Scatter(x=time_values, y=fitted_trace, mode="lines", name="fitted")

    return go.FigureWidget(data=[trace1, trace2], layout=layout)



