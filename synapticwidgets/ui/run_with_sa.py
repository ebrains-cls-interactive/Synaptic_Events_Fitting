from pathlib import Path
import ipywidgets
from synapticwidgets.core.results_handler import ResultsHandler
from synapticwidgets.core.sa_submitter import SASubmitter
from synapticwidgets.ui.base_widget import BaseWidget
from synapticwidgets.core.nsg_package_builder import NSGPackageBuilder
from synapticwidgets.ui.sa_context_widget import SAContextWidget
from synapticwidgets.ui.nsg_job_settings_widget import NSGJobSettingsWidget
from synapticwidgets.ui.sa_monitor_widget import ServiceAccountMonitorWidget


class RunWithSA(ipywidgets.VBox, BaseWidget):
    """
    Widget for submitting a NEURON simulation using Service Account.
    """

    def __init__(self, data_path, transfer_path, results_path, **kwargs):
        self.data_path = Path(data_path)
        self.transfer_path = Path(transfer_path)
        self.results_path = Path(results_path)
        self.results_sa_path = self.results_path / "results_SA"
        self.results_sa_path.mkdir(parents=True, exist_ok=True)

        self.package_builder = NSGPackageBuilder(self.data_path, self.transfer_path)

        self.current_job_id = None
        self.current_job_status = None

        self.title = ipywidgets.HTML("<h3>Run a simulation on NSG using Service Account</h3>")

        self.context_widget = SAContextWidget()
        self.job_settings_widget = NSGJobSettingsWidget()

        self.submit_button = ipywidgets.Button(description="Submit job", button_style="primary", icon="play",
                                               disabled=True)

        self.check_sim_button = ipywidgets.Button(description="Check simulation", icon="refresh", disabled=True)

        self.retrieve_results_button = ipywidgets.Button(description="Retrieve results", icon="download",
                                                         layout=ipywidgets.Layout(display="none"))

        self.sim_status = ipywidgets.HTML("")

        submit_buttons = ipywidgets.HBox(
            [self.submit_button, self.check_sim_button, self.retrieve_results_button],
            layout=ipywidgets.Layout(gap="10px")
        )

        self.monitor_widget = ServiceAccountMonitorWidget()

        submit_box = ipywidgets.VBox([ipywidgets.HTML("<b>Submit simulation</b>"),
                                      ipywidgets.HTML(
                                          "<span style='font-size:12px; color:#666;'>"
                                          "Create the Service Account from the prepared transfer folder and submit the "
                                          "simulation.</span>"
                                      ),
                                      submit_buttons, self.sim_status], layout=ipywidgets.Layout(padding="4px 16px 12px 16px",
                                                                                     margin="0 20px 0 0", width="420px",
                                                                                     gap="10px",))

        actions_box = ipywidgets.HBox(
            [submit_box, self.monitor_widget],
            layout=ipywidgets.Layout(align_items="flex-start", gap="40px")
        )

        info_box = ipywidgets.HBox(
            [self.context_widget, self.job_settings_widget],
            layout=ipywidgets.Layout(align_items="flex-start", gap="40px")
        )

        self.status_message = ipywidgets.HTML("")
        self.output = ipywidgets.Output()

        self.context_widget.load_projects_button.on_click(self._load_projects)
        self.context_widget.project.observe(self._update_actions_state, names="value")

        self.submit_button.on_click(self._submit_job)
        self.check_sim_button.on_click(self._check_simulation)
        self.retrieve_results_button.on_click(self._retrieve_results)
        self.monitor_widget.retrieve_jobs_button.on_click(self._retrieve_jobs)

        self._update_actions_state()
        super().__init__([self.title, info_box, actions_box, self.status_message, self.output], layout=self.DEFAULT_BORDER)

    def _update_actions_state(self, change=None):
        context = self.context_widget.get_values()
        has_project = bool(context["project"])

        self.submit_button.disabled = not has_project
        self.monitor_widget.retrieve_jobs_button.disabled = not has_project

    def _load_projects(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            try:
                submitter = SASubmitter()
                projects = submitter.get_available_projects()

                if not projects:
                    self.context_widget.reset_projects()
                    self._update_actions_state()
                    self._show_error("No Service Account projects were found.")
                    return

                options = []
                for project in projects:
                    name = project.get("name")
                    if name:
                        options.append((name, name))

                if not options:
                    self.context_widget.reset_projects()
                    self._update_actions_state()
                    self._show_error("No valid Service Account projects could be parsed.")
                    return

                self.context_widget.project.options = options
                self.context_widget.project.disabled = False
                self.context_widget.project.value = options[0][1]

                self._update_actions_state()
                self._show_success("Service Account projects loaded successfully.")

            except Exception as exc:
                self.context_widget.reset_projects()
                self._update_actions_state()
                self._show_error(f"Could not retrieve Service Account projects: {exc}")

    def _submit_job(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            error = self._validate_inputs()
            if error:
                self._show_error(error)
                return

            try:
                context = self.context_widget.get_values()
                job_settings = self.job_settings_widget.get_values()

                # 1. Write start.py file
                self.package_builder.write_start_file(
                    trace_mode=job_settings["trace_mode"],
                    trace_value=job_settings["trace_value"],
                )

                # 2. Create zip from transfer folder
                zip_file = self.package_builder.create_zip()
                self.job_settings_widget.zip_path.value = str(zip_file)

                # 3. Submit via Service Account
                submitter = SASubmitter()
                response = submitter.submit_job(
                    zip_file=zip_file,
                    settings=job_settings,
                    hpc=context["hpc"],
                    project=context["project"],
                    tool_id=job_settings["tool_id"],
                )

                self.current_job_id = response.get("id")
                self.current_job_status = response.get("stage")

                self.retrieve_results_button.layout.display = "none"
                self.check_sim_button.disabled = False
                self.sim_status.value = (
                    f"<span style='color: #444;'>"
                    f"<b>Submitted:</b> {response.get('title', job_settings['job_name'])}<br>"
                    f"<b>Project:</b> {context['project']}<br>"
                    f"<b>Job id:</b> {self.current_job_id}<br>"
                    f"<b>Stage:</b> {self.current_job_status}"
                    f"</span>"
                )

                self._show_success("Job submitted successfully through Service Account.")

            except Exception as exc:
                self._show_error(f"Submission failed: {exc}")

    def _retrieve_jobs(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            try:
                context = self.context_widget.get_values()

                submitter = SASubmitter()
                jobs = submitter.get_service_account_jobs(project=context["project"])

                self._show_success("Service Account jobs retrieved successfully.")
                print(jobs)

            except Exception as exc:
                self._show_error(f"Could not retrieve Service Account jobs: {exc}")

    def _check_simulation(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            if self.current_job_id is None:
                self._show_error("No submitted Service Account job is available to inspect.")
                return

            try:
                submitter = SASubmitter()
                job_info = submitter.get_service_account_job(self.current_job_id)

                self.current_job_status = job_info.get("stage")

                terminal = bool(job_info.get("terminal_stage"))
                failed = bool(job_info.get("failed"))

                if terminal and not failed:
                    self.retrieve_results_button.layout.display = ""
                else:
                    self.retrieve_results_button.layout.display = "none"

                self.sim_status.value = (
                    f"<span style='color: #444;'>"
                    f"<b>Submitted:</b> {job_info.get('title', '')}<br>"
                    f"<b>Job id:</b> {job_info.get('id')}<br>"
                    f"<b>Remote job id:</b> {job_info.get('job_id', '')}<br>"
                    f"<b>Stage:</b> {job_info.get('stage', '')}<br>"
                    f"<b>Terminal:</b> {job_info.get('terminal_stage')}<br>"
                    f"<b>Failed:</b> {job_info.get('failed')}<br>"
                    f"<b>Start:</b> {job_info.get('init_date', '')}<br>"
                    f"<b>End:</b> {job_info.get('end_date', '')}"
                    f"</span>"
                )

                if terminal and not failed:
                    self._show_success("Simulation finished. Results are ready to retrieve.")
                elif terminal and failed:
                    self._show_error("Simulation finished with failure.")
                else:
                    self._show_success("Simulation status retrieved successfully.")

            except Exception as exc:
                self._show_error(f"Could not check simulation: {exc}")

    def _retrieve_results(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            if self.current_job_id is None:
                self._show_error("No submitted Service Account job is available.")
                return

            try:
                context = self.context_widget.get_values()
                job_settings = self.job_settings_widget.get_values()

                submitter = SASubmitter()
                result = submitter.get_service_account_job_results(
                    project=context["project"],
                    job_id=self.current_job_id,
                )

                if not result:
                    self._show_error("No results were returned for this Service Account job.")
                    return

                file_name = result["file_name"]
                file_content = result["file_content"]

                results_dir = self.results_sa_path / job_settings["job_name"]
                results_dir.mkdir(parents=True, exist_ok=True)

                archive_path = results_dir / file_name
                archive_path.write_bytes(file_content)

                self._show_success(f"Results downloaded to {results_dir}")

                print("Downloaded file:")
                print(archive_path)

                ResultsHandler.extract_output_archive(archive_path, results_dir)

                self.sim_status.value += f"<br><b>Results folder:</b> {results_dir}"

            except Exception as exc:
                self._show_error(f"Could not retrieve results: {exc}")

    def _show_success(self, message):
        self.status_message.value = f"<span style='color: green;'>{message}</span>"

    def _show_error(self, message):
        self.status_message.value = f"<span style='color: red;'>{message}</span>"

    def _validate_inputs(self):
        context = self.context_widget.get_values()
        job_settings = self.job_settings_widget.get_values()

        if not context["hpc"]:
            return "HPC is required."
        if not context["project"]:
            return "Project is required. Please load and select an available project."
        if not job_settings["tool_id"]:
            return "Tool ID is required."
        if not job_settings["job_name"]:
            return "Job name is required."

        return None
