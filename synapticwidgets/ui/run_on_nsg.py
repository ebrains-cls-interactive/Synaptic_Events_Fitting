import ipywidgets
from pathlib import Path
from synapticwidgets.core.nsg_submitter import NSGSubmitter
from synapticwidgets.core.nsg_package_builder import NSGPackageBuilder
from synapticwidgets.ui.base_widget import BaseWidget
from synapticwidgets.ui.nsg_credentials_widget import NSGCredentialsWidget
from synapticwidgets.ui.nsg_job_settings_widget import NSGJobSettingsWidget
from synapticwidgets.ui.nsg_monitor_widget import NSGMonitorWidget
from synapticwidgets.core.nsg_parsers import parse_submitted_job_xml, parse_checked_job_xml, parse_results_listing, parse_list_jobs_xml
from synapticwidgets.core.results_handler import ResultsHandler

class RunOnNSG(ipywidgets.VBox, BaseWidget):
    """
    Widget for submitting a NEURON simulation using NSG Portal.
    """

    def __init__(self, data_path, transfer_path, results_path, **kwargs):
        self.data_path = Path(data_path)
        self.transfer_path = Path(transfer_path)
        self.results_path = Path(results_path)
        self.results_nsg_path = self.results_path / "results_NSG"
        self.results_nsg_path.mkdir(parents=True, exist_ok=True)

        self.package_builder = NSGPackageBuilder(self.data_path, self.transfer_path)
        self.current_job_handle = None
        self.current_job_stage = None
        self.current_results_uri = None

        self.title = ipywidgets.HTML("<h3>Connect and run a simulation using NSG Portal</h3>")

        self.credentials_widget = NSGCredentialsWidget()

        self.job_settings_widget = NSGJobSettingsWidget()

        self.submit_button = ipywidgets.Button(description="Submit job", button_style="primary", icon="play")

        self.check_sim_button = ipywidgets.Button(description="Check simulation", icon="refresh", disabled=True)


        self.sim_status = ipywidgets.HTML("")

        submit_buttons = ipywidgets.HBox(
            [self.submit_button, self.check_sim_button],
            layout=ipywidgets.Layout(gap="10px")
        )

        submit_box = ipywidgets.VBox([ipywidgets.HTML("<b>Submit simulation</b>"),
                                      ipywidgets.HTML(
                                          "<span style='font-size:12px; color:#666;'>"
                                          "Create the NSG package from the prepared transfer folder and submit the "
                                          "simulation.</span>"
                                      ),
                                      submit_buttons, self.sim_status], layout=ipywidgets.Layout(padding="4px 16px 12px 16px",
                                                                                     margin="0 20px 0 0", width="420px",
                                                                                     gap="10px",))

        self.monitor_widget = NSGMonitorWidget()

        actions_box = ipywidgets.HBox([submit_box, self.monitor_widget],
                                      layout=ipywidgets.Layout(align_items="flex-start", gap="40px"))


        info_box = ipywidgets.HBox([self.credentials_widget, self.job_settings_widget],
                                      layout=ipywidgets.Layout(align_items="flex-start", gap="40px"))

        self.status_message = ipywidgets.HTML("")
        self.output = ipywidgets.Output()

        self.credentials_widget.username.observe(self._update_actions_state, names="value")
        self.credentials_widget.password.observe(self._update_actions_state, names="value")
        self.credentials_widget.app_key.observe(self._update_actions_state, names="value")

        self._update_actions_state()
        self.submit_button.on_click(self._submit_job)
        self.check_sim_button.on_click(self._check_simulation)
        self.monitor_widget.check_jobs_button.on_click(self._check_jobs)
        self.monitor_widget.download_results_button.on_click(self._retrieve_selected_job_results)

        super().__init__([
            self.title,
            info_box,
            actions_box,
            self.status_message,
            self.output,
        ], layout=self.DEFAULT_BORDER)

    def _show_success(self, message):
        self.status_message.value = f"<span style='color: green;'>{message}</span>"

    def _show_error(self, message):
        self.status_message.value = f"<span style='color: red;'>{message}</span>"

    def _validate_inputs(self):
        creds = self.credentials_widget.get_credentials()
        job_settings = self.job_settings_widget.get_values()

        if not creds["username"]:
            return "Username is required."
        if not creds["password"]:
            return "Password is required."
        if not creds["app_key"]:
            return "App key is required."
        if not job_settings["tool_id"]:
            return "Tool ID is required."
        if not job_settings["job_name"]:
            return "Job name is required."

        return None

    def _submit_job(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            error = self._validate_inputs()
            if error:
                self._show_error(error)
                return

            try:
                job_settings = self.job_settings_widget.get_values()

                # 1. Write start.py file
                self.package_builder.write_start_file(
                    trace_mode=job_settings["trace_mode"],
                    trace_value=job_settings["trace_value"],
                )

                # 2. Create zip from transfer folder
                zip_file = self.package_builder.create_zip()
                self.job_settings_widget.zip_path.value = str(zip_file)

                # 3. Submit to NSG
                creds = self.credentials_widget.get_credentials()
                submitter = NSGSubmitter(
                    username=creds["username"],
                    password=creds["password"],
                    app_key=creds["app_key"],
                )

                response = submitter.submit_job(
                    tool_id=job_settings["tool_id"],
                    job_name=job_settings["job_name"],
                    zip_file=zip_file,
                    nr_cores=job_settings["nr_cores"],
                    nr_nodes=job_settings["nr_nodes"],
                    run_time=job_settings["run_time"],
                )

                job_info = parse_submitted_job_xml(response.text)
                self.current_job_handle = job_info["job_handle"]
                self.current_job_stage = job_info["job_stage"]

                self.current_results_uri = None

                self.check_sim_button.disabled = False
                self.sim_status.value = (
                    f"<span style='color: #444;'>"
                    f"<b>Submitted job:</b> {job_info['job_handle']}<br>"
                    f"<b>Stage:</b> {job_info['job_stage']}"
                    f"</span>"
                )

                self._show_success("Job submitted successfully.")
                self.logger.info("Status code: ", response.status_code)
                self.logger.info(response.text)

            except Exception as exc:
                self._show_error(f"Submission failed: {exc}")

    def _check_simulation(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            if not self.current_job_handle:
                self._show_error("No submitted job available to inspect.")
                return

            try:
                creds = self.credentials_widget.get_credentials()

                submitter = NSGSubmitter(
                    username=creds["username"],
                    password=creds["password"],
                    app_key=creds["app_key"],
                )

                response = submitter.get_job(self.current_job_handle)
                job_info = parse_checked_job_xml(response.text)

                self.current_job_stage = job_info["job_stage"]
                self.current_results_uri = job_info["results_uri"]

                terminal = str(job_info["terminal_stage"]).lower() == "true"
                failed = str(job_info["failed"]).lower() == "true"
                has_results = bool(self.current_results_uri)

                self.sim_status.value = (
                    f"<span style='color: #444;'>"
                    f"<b>Job:</b> {job_info['job_name']}<br>"
                    f"<b>Stage:</b> {job_info['job_stage']}<br>"
                    f"<b>Terminal:</b> {job_info['terminal_stage']}<br>"
                    f"<b>Failed:</b> {job_info['failed']}<br>"
                    f"<b>Submitted:</b> {job_info['date_submitted_cet']}"
                    f"</span>"
                )

                if terminal and not failed and has_results:
                    self._show_success("Simulation finished. You can retrieve the results from the Job monitoring "
                                       "section.")
                elif terminal and failed:
                    self._show_error("Simulation finished with failure.")
                else:
                    self._show_success("Simulation status retrieved successfully.")

            except Exception as exc:
                self._show_error(f"Could not check simulation: {exc}")

    def _check_jobs(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            try:
                creds = self.credentials_widget.get_credentials()

                submitter = NSGSubmitter(username=creds["username"], password=creds["password"],
                                         app_key=creds["app_key"],)

                response = submitter.list_jobs()
                jobs = parse_list_jobs_xml(response.text)

                if not jobs:
                    self.monitor_widget.reset_jobs()
                    self._show_error("No jobs were found.")
                    return

                options = []
                for job in jobs:
                    options.append((job["title"], job["handle"]))

                self.monitor_widget.set_jobs(options)
                self._show_success("Jobs retrieved successfully.")

            except Exception as exc:
                self.monitor_widget.reset_jobs()
                self._show_error(f"Could not retrieve jobs: {exc}")

    def _retrieve_selected_job_results(self, _):
        with self.output:
            self.output.clear_output()
            self.status_message.value = ""

            selected_handle = self.monitor_widget.jobs_dropdown.value
            if not selected_handle:
                self._show_error("No job selected.")
                return

            try:
                creds = self.credentials_widget.get_credentials()

                submitter = NSGSubmitter(
                    username=creds["username"],
                    password=creds["password"],
                    app_key=creds["app_key"],
                )

                response = submitter.get_job(selected_handle)
                job_info = parse_checked_job_xml(response.text)

                terminal = str(job_info["terminal_stage"]).lower() == "true"
                failed = str(job_info["failed"]).lower() == "true"
                results_uri = job_info["results_uri"]

                if not terminal:
                    self._show_error("Selected job is not finished yet.")
                    return

                if failed:
                    self._show_error("Selected job finished with failure.")
                    return

                if not results_uri:
                    self._show_error("No results are available for the selected job.")
                    return

                listing_response = submitter.get_results_listing(results_uri)
                files = parse_results_listing(listing_response.text)

                if not files:
                    self._show_error("No files were found in the NSG results listing.")
                    return

                imp_folders = {"output.tar.gz", "STDOUT", "STDERR"}
                selected = [item for item in files if item["name"] in imp_folders]

                if not selected:
                    self._show_error("No downloadable output.tar.gz, STDOUT or STDERR files were found.")
                    return

                results_dir = self.results_nsg_path / selected_handle
                results_dir.mkdir(parents=True, exist_ok=True)

                downloaded = []
                for item in selected:
                    dest = results_dir / item["name"]
                    submitter.download_result_file(item["url"], dest)
                    downloaded.append(dest)

                archive_path = results_dir / "output.tar.gz"
                if archive_path.exists():
                    ResultsHandler.extract_output_archive(archive_path, results_dir)


                self._show_success(f"Results downloaded to {results_dir}")

                print("Downloaded files:")
                for path in downloaded:
                    print(path)

            except Exception as exc:
                self._show_error(f"Could not retrieve selected job results: {exc}")

    def _update_actions_state(self, change=None):
        has_credentials = self.credentials_widget.has_credentials()
        self.monitor_widget.check_jobs_button.disabled = not has_credentials
