from pathlib import Path
import ipywidgets
from clsiwidgets.core.results_handler import ResultsHandler
from clsiwidgets.core.sa_submitter import SASubmitter
from clsiwidgets.ui.base_widget import BaseWidget
from clsiwidgets.core.nsg_package_builder import NSGPackageBuilder
from clsiwidgets.ui.sa_context_widget import SAContextWidget
from clsiwidgets.ui.nsg_job_settings_widget import NSGJobSettingsWidget
from clsiwidgets.ui.sa_monitor_widget import ServiceAccountMonitorWidget


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
        self.current_remote_job_id = None
        self.current_job_status = None

        self.title = ipywidgets.HTML("<h3>Run a simulation on NSG using Service Account</h3>")

        self.context_widget = SAContextWidget()
        self.job_settings_widget = NSGJobSettingsWidget()

        self.submit_button = ipywidgets.Button(description="Submit job", button_style="primary", icon="play",
                                               disabled=True)

        self.check_sim_button = ipywidgets.Button(description="Check simulation", icon="refresh", disabled=True)

        self.sim_status = ipywidgets.HTML("")

        submit_buttons = ipywidgets.HBox(
            [self.submit_button, self.check_sim_button],
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
        self.monitor_widget.retrieve_jobs_button.on_click(self._retrieve_jobs)
        self.monitor_widget.download_results_button.on_click(self._retrieve_selected_job_results)

        self._update_actions_state()
        super().__init__([self.title, info_box, actions_box, self.status_message, self.output], layout=self.DEFAULT_BORDER)

    def _get_submitter(self):
        context = self.context_widget.get_values()
        app_key = context["app_key"]

        if not app_key:
            raise ValueError(
                "Application Key is required. "
                "Please enter it before using the Service Account."
            )

        return SASubmitter(app_key=app_key)

    def _update_actions_state(self, change=None):
        context = self.context_widget.get_values()
        has_project = bool(context["project"])

        self.submit_button.disabled = not has_project
        self.monitor_widget.retrieve_jobs_button.disabled = not has_project

        if not has_project:
            self.monitor_widget.reset_jobs()

    def _load_projects(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            self._reset_service_account_state()
            self._update_actions_state()

            try:
                submitter = self._get_submitter()
                projects = submitter.get_available_projects()

                if not projects:
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
                submitter = self._get_submitter()
                response = submitter.submit_job(
                    zip_file=zip_file,
                    settings=job_settings,
                    hpc=context["hpc"],
                    project=context["project"],
                    tool_id=job_settings["tool_id"],
                )

                self.current_job_id = response.get("id")
                self.current_remote_job_id = response.get("job_id")
                self.current_job_status = response.get("stage")

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

                submitter = self._get_submitter()
                jobs = submitter.get_service_account_jobs(project=context["project"])

                if not jobs:
                    self.monitor_widget.reset_jobs()
                    self._show_error("No Service Account jobs were found.")
                    return

                options = []
                for job in jobs:
                    job_title = job.get("title", "")
                    job_id = job.get("id")
                    remote_job_id = job.get("job_id")

                    if job_id is None or remote_job_id is None:
                        continue

                    options.append((job_title, (job_id, remote_job_id)))

                if not options:
                    self.monitor_widget.reset_jobs()
                    self._show_error("No valid Service Account jobs could be parsed.")
                    return

                self.monitor_widget.set_jobs(options)
                self._show_success("Service Account jobs retrieved successfully.")

            except Exception as exc:
                self.monitor_widget.reset_jobs()
                self._show_error(f"Could not retrieve Service Account jobs: {exc}")

    def _check_simulation(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            if self.current_job_id is None:
                self._show_error("No submitted Service Account job is available to inspect.")
                return

            try:
                submitter = self._get_submitter()
                context = self.context_widget.get_values()
                job_info = submitter.get_service_account_job(self.current_job_id, self.current_remote_job_id,
                                                             context["project"],)

                self.current_job_status = job_info.get("stage")

                terminal = bool(job_info.get("terminal_stage"))
                failed = bool(job_info.get("failed"))

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
                    self._show_success("Simulation finished. You can retrieve the results from the Job monitoring "
                                       "section.")
                elif terminal and failed:
                    self._show_error("Simulation finished with failure.")
                else:
                    self._show_success("Simulation status retrieved successfully.")

            except Exception as exc:
                self._show_error(f"Could not check simulation: {exc}")

    def _retrieve_selected_job_results(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            selected_value = self.monitor_widget.jobs_dropdown.value
            if not selected_value:
                self._show_error("No job selected.")
                return

            selected_job_id, selected_remote_job_id = selected_value

            try:
                context = self.context_widget.get_values()
                print("dropdown value:", selected_job_id)
                submitter = self._get_submitter()
                job_info = submitter.get_service_account_job(selected_job_id, selected_remote_job_id, context["project"])

                terminal = bool(job_info.get("terminal_stage"))
                failed = bool(job_info.get("failed"))

                if not terminal:
                    self._show_error("Selected job is not finished yet.")
                    return

                if failed:
                    self._show_error("Selected job finished with failure.")
                    return

                result = submitter.get_service_account_job_results(
                    project=context["project"],
                    job_id=selected_remote_job_id,
                )

                if not result:
                    self._show_error("No results were returned for the selected Service Account job.")
                    return

                file_name = result["file_name"]
                file_content = result["file_content"]

                job_label = job_info.get("title") or str(selected_job_id)
                results_dir = self.results_sa_path / job_label
                results_dir.mkdir(parents=True, exist_ok=True)

                archive_path = results_dir / file_name
                archive_path.write_bytes(file_content)

                ResultsHandler.extract_output_archive(archive_path, results_dir)

                self._show_success(f"Results downloaded to {results_dir}")

                print("Downloaded file:")
                print(archive_path)

            except Exception as exc:
                self._show_error(f"Could not retrieve results: {exc}")

    def _show_success(self, message):
        self.status_message.value = f"<span style='color: green;'>{message}</span>"

    def _show_error(self, message):
        self.status_message.value = f"<span style='color: red;'>{message}</span>"

    def _reset_service_account_state(self):
        self.context_widget.reset_projects()
        self.monitor_widget.reset_jobs()

        self.current_job_id = None
        self.current_remote_job_id = None
        self.current_job_status = None

        self.check_sim_button.disabled = True
        self.sim_status.value = ""

    def _validate_inputs(self):
        context = self.context_widget.get_values()
        job_settings = self.job_settings_widget.get_values()

        if not context["app_key"]:
            return "Application Key is required. Please enter it and load the available projects."
        if not context["hpc"]:
            return "HPC is required."
        if not context["project"]:
            return "Project is required. Please load and select an available project."
        if not job_settings["tool_id"]:
            return "Tool ID is required."
        if not job_settings["job_name"]:
            return "Job name is required."

        return None
