import ipywidgets


class NSGMonitorWidget(ipywidgets.VBox):
    """
    Widget for NSG job monitoring actions.
    """

    def __init__(self, **kwargs):
        self.title = ipywidgets.HTML("<b>Job monitoring</b>")
        self.help_text = ipywidgets.HTML(
            "<span style='font-size:12px; color:#666;'>"
            "Enter your NSG credentials to inspect submitted jobs."
            "</span>"
        )

        self.check_jobs_button = ipywidgets.Button(description="Retrieve jobs", icon="list", disabled=True,
                                                   layout=ipywidgets.Layout(width="160px"))

        self.jobs_dropdown = ipywidgets.Dropdown(description="Jobs:", options=[], disabled=True,
                                                 style={"description_width": "60px"},
                                                 layout=ipywidgets.Layout(width="225px"))

        self.download_results_button = ipywidgets.Button(description="Download results", icon="download",
                                                          disabled=True, layout=ipywidgets.Layout(width="160px"))

        jobs_row = ipywidgets.HBox(
            [self.check_jobs_button, self.jobs_dropdown],
            layout=ipywidgets.Layout(align_items="center", gap="12px")
        )

        super().__init__(
            [
                self.title,
                self.help_text,
                jobs_row,
                self.download_results_button
            ],
            layout=ipywidgets.Layout(
                padding="4px 16px 12px 16px",
                margin="0 20px 0 0",
                width="420px",
                gap="10px",
            ),
            **kwargs
        )

    def reset_jobs(self):
        self.jobs_dropdown.options = []
        self.jobs_dropdown.value = None
        self.jobs_dropdown.disabled = True
        self.download_results_button.disabled = True

    def set_jobs(self, options):
        self.jobs_dropdown.options = options
        self.jobs_dropdown.disabled = False
        self.download_results_button.disabled = False
        if options:
            self.jobs_dropdown.value = options[0][1]