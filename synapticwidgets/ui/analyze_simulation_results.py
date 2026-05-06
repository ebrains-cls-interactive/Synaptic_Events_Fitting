from pathlib import Path
import ipywidgets
from synapticwidgets.ui.base_widget import BaseWidget


class AnalyzeSimulationResults(ipywidgets.VBox, BaseWidget):
    """
    Widget for analyzing locally downloaded simulation results
    """

    def __init__(self, results_path, **kwargs):
        self.results_path = Path(results_path)

        self.title = ipywidgets.HTML("<h3>Analyze local simulation results</h3>")

        self.help_text = ipywidgets.HTML(
            "<span style='font-size:12px; color:#666;'>"
            "Select one locally downloaded results folder to inspect fitting outputs."
            "</span>"
        )

        self.folder_dropdown = ipywidgets.Dropdown(
            description="Results folder:",
            options=[],
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="750px"),
        )

        self.results_table_button = ipywidgets.Button(
            description="Results table"
        )

        self.boxplot_button = ipywidgets.Button(
            description="Boxplot results"
        )

        self.best_fit_button = ipywidgets.Button(
            description="Best fit"
        )

        self.status_message = ipywidgets.HTML("")
        self.plot_box = ipywidgets.VBox()

        self.output = ipywidgets.Output()

        self.results_table_button.on_click(self._show_results_table)
        self.boxplot_button.on_click(self._show_boxplot)
        self.best_fit_button.on_click(self._show_best_fit)

        actions_box = ipywidgets.HBox(
            [self.results_table_button, self.boxplot_button, self.best_fit_button],
            layout=ipywidgets.Layout(gap="10px")
        )

        super().__init__([self.title, self.help_text, self.folder_dropdown, actions_box, self.status_message,
                          self.plot_box, self.output], layout=self.DEFAULT_BORDER)

        self._populate_result_folders()

    def _show_success(self, message):
        self.status_message.value = f"<span style='color: green;'>{message}</span>"

    def _show_error(self, message):
        self.status_message.value = f"<span style='color: red;'>{message}</span>"

    def _populate_result_folders(self):
        options = []

        if self.results_path.exists():
            for backend_dir in sorted(self.results_path.iterdir()):
                if not backend_dir.is_dir():
                    continue

                for result_dir in sorted(backend_dir.iterdir()):
                    if not result_dir.is_dir():
                        continue

                    label = f"{backend_dir.name} / {result_dir.name}"
                    options.append((label, str(result_dir)))

        self.folder_dropdown.options = options

        has_results = bool(options)
        self.results_table_button.disabled = not has_results
        self.boxplot_button.disabled = not has_results
        self.best_fit_button.disabled = not has_results

        if has_results:
            self._show_success("Local results folders loaded.")
        else:
            self._show_error("No local results folders were found.")

    def _get_selected_folder(self):
        value = self.folder_dropdown.value
        if not value:
            return None
        return Path(value)

    def _show_results_table(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            folder = self._get_selected_folder()
            if folder is None:
                self._show_error("No results folder selected.")
                return

            try:
                from IPython.display import HTML, display

                data, names, param_name = self._load_analysis_data(folder)

                if data.empty:
                    self._show_error("Results file is empty. No fitting result is available.")
                    return

                data_sorted = data.sort_values(["error"], ascending=True)
                preview = data_sorted.head(20)

                self._show_success(f"Loaded results table from {folder.name}. Showing top 20 rows out of "
                                   f"{len(data_sorted)} sorted by error.")
                display(HTML(preview.to_html(index=False)))

            except Exception as exc:
                self._show_error(f"Could not load results table: {exc}")

    def _show_boxplot(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            folder = self._get_selected_folder()
            if folder is None:
                self._show_error("No results folder selected.")
                return
        try:
            import numpy
            import plotly.graph_objs as go
            from IPython.display import display

            data, names, param_name = self._load_analysis_data(folder)

            if data.empty:
                self._show_error("Results file is empty. No fitting result is available.")
                return

            box_traces = []
            data_norm = data.copy()

            for param in param_name:
                std = numpy.std(data_norm[param])
                mean = numpy.mean(data_norm[param])

                if std == 0:
                    normalized = data_norm[param] - mean
                else:
                    normalized = (data_norm[param] - mean) / std

                box_traces.append(go.Box(y=normalized, name=param, showlegend=False))

            self.output.clear_output()
            self.plot_box.children = []

            fig = go.FigureWidget(data=box_traces, layout=go.Layout(yaxis=dict(hoverformat=".2f"), width=1200,
                                                                    height=700,))

            self._show_success(f"Loaded parameter boxplots from {folder.name}.")
            self.plot_box.children = [fig]

        except Exception as exc:
            self._show_error(f"Could not build boxplot results: {exc}")

    def _show_best_fit(self, _):
        #TODO: pass for now
        pass

    @staticmethod
    def _find_analysis_files(folder_path):
        folder_path = Path(folder_path)

        config_file = None
        csv_file = None

        for file_path in folder_path.iterdir():
            if file_path.is_file():
                if file_path.name.startswith("config") and file_path.suffix == ".txt":
                    config_file = file_path
                elif file_path.suffix == ".csv":
                    csv_file = file_path

        return config_file, csv_file

    def _load_analysis_data(self, folder):
        config_file, csv_file = self._find_analysis_files(folder)

        if config_file is None:
            raise FileNotFoundError("No config file was found in the selected folder.")

        if csv_file is None:
            raise FileNotFoundError("No results CSV file was found in the selected folder.")

        import pandas
        from synapticwidgets.data.model_support import readconffile

        readconffile.filename = str(config_file)

        [inputfilename, modfilename, parametersfilename, flagdata, flagcut, nrtraces, Vrestf, esynf,
         nrparamsfit, paramnr, paramname, paraminitval, paramsconstraints, nrdepnotfit, depnotfit, nrdepfit,
         depfit, seedinitvaluef] = readconffile.readconffile()

        names = ["trace", "fitnr", "error"]
        for k in range(len(paramname)):
            names.append(paramname[k])
        names.append("thresh")
        names.append("min")

        cols = range(0, len(names))
        data = pandas.read_csv(csv_file, sep="\t", usecols=cols, names=names)

        return data, names, paramname