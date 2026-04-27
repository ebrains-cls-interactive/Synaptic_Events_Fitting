from pathlib import Path
import ipywidgets
from synapticwidgets.core.sa_submitter import SASubmitter
from synapticwidgets.ui.base_widget import BaseWidget
from synapticwidgets.core.nsg_package_builder import NSGPackageBuilder
from synapticwidgets.ui.sa_context_widget import SAContextWidget
from synapticwidgets.ui.nsg_job_settings_widget import NSGJobSettingsWidget


class RunWithSA(ipywidgets.VBox, BaseWidget):
    """
    Widget for submitting a NEURON simulation using Service Account.
    """

    def __init__(self, data_path, transfer_path, **kwargs):
        self.data_path = Path(data_path)
        self.transfer_path = Path(transfer_path)
        self.package_builder = NSGPackageBuilder(self.data_path, self.transfer_path)

        self.title = ipywidgets.HTML("<h3>Run a simulation on NSG using Service Account</h3>")

        self.context_widget = SAContextWidget()
        self.job_settings_widget = NSGJobSettingsWidget()

        self.submit_button = ipywidgets.Button(description="Submit job", button_style="primary", icon="play")

        self.retrieve_jobs_button = ipywidgets.Button(
            description="Retrieve jobs",
            icon="list",
        )

        submit_box = ipywidgets.VBox([ipywidgets.HTML("<b>Submit simulation</b>"),
                                      ipywidgets.HTML(
                                          "<span style='font-size:12px; color:#666;'>"
                                          "Create the Service Account from the prepared transfer folder and submit the "
                                          "simulation.</span>"
                                      ),
                                      self.submit_button,
                                      self.retrieve_jobs_button], layout=ipywidgets.Layout(padding="4px 16px 12px 16px",
                                                                                     margin="0 20px 0 0", width="420px",
                                                                                     gap="10px",))

        info_box = ipywidgets.HBox(
            [self.context_widget, self.job_settings_widget],
            layout=ipywidgets.Layout(align_items="flex-start", gap="40px")
        )

        self.status_message = ipywidgets.HTML("")
        self.output = ipywidgets.Output()

        self.submit_button.on_click(self._submit_job)
        self.retrieve_jobs_button.on_click(self._retrieve_jobs)

        super().__init__([self.title, info_box, submit_box, self.status_message, self.output], layout=self.DEFAULT_BORDER)

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

                self._show_success("Job submitted successfully through Service Account.")
                print(response.text)

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
            return "Project is required."
        if not job_settings["tool_id"]:
            return "Tool ID is required."
        if not job_settings["job_name"]:
            return "Job name is required."

        return None
