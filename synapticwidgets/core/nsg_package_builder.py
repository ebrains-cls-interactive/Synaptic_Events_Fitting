import shutil
# import subprocess
from pathlib import Path
import zipfile

class NSGPackageBuilder:
    DEFAULT_MOD_NAME = "ProbGABAAB_EMS_GEPH_g.mod"

    def __init__(self, data_path, transfer_path):
        self.data_path = Path(data_path)
        self.transfer_path = Path(transfer_path)

    def detect_exp_file(self):
        exp_files = list(self.transfer_path.glob("exp*.txt"))
        if not exp_files:
            raise FileNotFoundError("No experimental file found in transfer folder.")
        return exp_files[0]

    def detect_mod_file(self):
        mod_files = [path for path in self.transfer_path.glob("*.mod") if path.name != "netstims.mod"]
        if not mod_files:
            raise FileNotFoundError("No model .mod file found in transfer folder.")
        return mod_files[0]

    def detect_config_file(self, exp_file, mod_file):
        if mod_file.name == self.DEFAULT_MOD_NAME:
            config_name = exp_file.name.replace("exp", "config")
            config_path = self.transfer_path / config_name

            if not config_path.exists():
                source = self.data_path / "config_files" / config_name
                if source.exists():
                    shutil.copy2(source, config_path)

            return config_path

        return self.transfer_path / "config.txt"

    def write_start_file(self, trace_mode, trace_value=None):
        exp_file = self.detect_exp_file()
        mod_file = self.detect_mod_file()
        config_file = self.detect_config_file(exp_file, mod_file)

        all_traces = trace_mode == "all_traces"
        single_trace = trace_mode == "singletrace"
        demo = trace_mode == "demo"

        trace_arg = trace_value if trace_value is not None else "3"

        start_path = self.transfer_path / "start.py"

        with start_path.open("w", encoding="utf-8") as f:
            f.write("import fitting\n")
            f.write(
                "fitting.fitting("
                f"'{config_file.name}', "
                f"'{exp_file.name}', "
                f"'{mod_file.name}', "
                f"'{all_traces}', "
                f"'{single_trace}', "
                f"'{demo}', "
                f"'{trace_arg}'"
                ")\n"
            )

        if not (self.transfer_path / self.DEFAULT_MOD_NAME).exists():
            self._patch_fitness_for_local_mod()

        return start_path

    def _patch_fitness_for_local_mod(self):
        fitness_path = self.transfer_path / "fitness.py"
        if not fitness_path.exists():
            raise FileNotFoundError(f"fitness.py not found in transfer folder: {fitness_path}")

        lines = fitness_path.read_text(encoding="utf-8").splitlines(keepends=True)
        for idx in range(242, 246):
            if idx < len(lines):
                lines[idx] = "\n"
        fitness_path.write_text("".join(lines), encoding="utf-8")

        return fitness_path

    def create_zip(self, zip_name="nsg_input.zip"):
        zip_path = self.transfer_path.parent / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in self.transfer_path.rglob("*"):
                if path.is_file():
                    arcname = Path(self.transfer_path.name) / path.relative_to(self.transfer_path)
                    zf.write(path, arcname=arcname)

        return zip_path

    # def compile_mod_files(self):
    #     transfer_path = Path(self.transfer_path)
    #
    #     result = subprocess.run(
    #         ["nrnivmodl"],
    #         cwd=transfer_path,
    #         capture_output=True,
    #         text=True,
    #         check=True,
    #     )
    #
    #     return result
