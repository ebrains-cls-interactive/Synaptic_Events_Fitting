import ipywidgets

class ServiceAccountMonitorWidget(ipywidgets.VBox):
    """
    Widget for Service Account job monitoring actions.
    """

    def __init__(self, **kwargs):
        self.title = ipywidgets.HTML("<b>Job monitoring</b>")
        self.help_text = ipywidgets.HTML(
            "<span style='font-size:12px; color:#666;'>"
            "Retrieve the jobs available for the selected project."
            "</span>"
        )

        self.retrieve_jobs_button = ipywidgets.Button(description="Retrieve jobs", icon="list", disabled=True)

        super().__init__(
            [
                self.title,
                self.help_text,
                self.retrieve_jobs_button,
            ],
            layout=ipywidgets.Layout(
                padding="4px 16px 12px 16px",
                margin="0 20px 0 0",
                width="420px",
                gap="10px",
            ),
            **kwargs
        )