from pathlib import Path
import ipywidgets
from clsiwidgets.ui.base_widget import BaseWidget
from clsiwidgets.core.best_fit_analysis import (load_fit_results, extract_best_fit_parameters,
                                                prepare_best_fit_workspace, run_best_fit_simulation, plot_best_fit)


class AnalyzeSimulationResults(ipywidgets.VBox, BaseWidget):
    """
    Widget for analyzing locally downloaded simulation results
    """

    def __init__(self, results_path, best_fit_workspace_path, **kwargs):
        self.results_path = Path(results_path)
        self.best_fit_workspace_path = Path(best_fit_workspace_path)

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
            self.plot_box.children = []

            folder = self._get_selected_folder()
            if folder is None:
                self._show_error("No results folder selected.")
                return

            try:
                from IPython.display import HTML, display

                analysis = load_fit_results(folder)
                data = analysis["data"]

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

            analysis = load_fit_results(folder)
            data = analysis["data"]
            param_name = analysis["paramname"]

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
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""
            self.plot_box.children = []

            folder = self._get_selected_folder()
            if folder is None:
                self._show_error("No results folder selected.")
                return
            try:
                analysis = load_fit_results(folder)

                prepare_best_fit_workspace(folder, self.best_fit_workspace_path)

                best_fit = extract_best_fit_parameters(analysis["data"], analysis["names"], analysis["paramname"])

                simulation_result = run_best_fit_simulation(
                    transfer_path=self.best_fit_workspace_path, data=analysis["data"], names=analysis["names"],
                    best_fit=best_fit, esynf=analysis["esynf"], Vrestf=analysis["Vrestf"],
                    nrparamsfit=analysis["nrparamsfit"], nrdepnotfit=analysis["nrdepnotfit"],
                    modfilename=analysis["modfilename"], paramname=analysis["paramname"],
                    depnotfit=analysis["depnotfit"], nrdepfit=analysis["nrdepfit"], depfit=analysis["depfit"],
                    paramsconstraints=analysis["paramsconstraints"], inputfilename=analysis["inputfilename"])

                fig = plot_best_fit(simulation_result)

                self.plot_box.children = [fig]

                self._show_success(
                    f"Best fit loaded from {folder.name}: "
                    f"trace {simulation_result['trace_number']}, "
                    f"CSV error {best_fit['error']:.6f}, "
                    f"replay error {simulation_result['error_verification']:.6f}"
                )
            except Exception as exc:
                message = str(exc)
                if "WinError 5" in message and "nrnmech.dll" in message:
                    self._show_error("NEURON cannot reload the compiled DLL in the current session. "
                                     "Please restart the kernel and try Best fit again.")
                else:
                    self._show_error(f"Could not load best fit: {exc}")
