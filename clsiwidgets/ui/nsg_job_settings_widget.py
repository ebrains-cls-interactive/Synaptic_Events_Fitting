import ipywidgets


class NSGJobSettingsWidget(ipywidgets.VBox):
    """
    Small widget for entering NSG job settings
    """

    def __init__(self, **kwargs):
        self.title = ipywidgets.HTML("<b>Job settings</b>")
        self.help_text = ipywidgets.HTML(
            "<span style='font-size:12px; color:#666;'>"
            "Configure job settings for NSG."
            "</span>"
        )

        self.tool_id = ipywidgets.Text(value="NEURON_EXPANSE", description="Tool ID:",
                                       style={"description_width": "120px"}, layout=ipywidgets.Layout(width="350px"), )

        self.traces_opt_label = ipywidgets.HTML(
            "<div style='width:120px; text-align:right; padding-top:4px;'>Run:</div>"
        )

        self.traces_opt = ipywidgets.RadioButtons(
            options=["all_traces", "singletrace", "demo"],
            layout=ipywidgets.Layout(width="220px"),
        )

        self.traces_opt_box = ipywidgets.HBox(
            [self.traces_opt_label, self.traces_opt],
            layout=ipywidgets.Layout(align_items="flex-start", gap="10px", margin="6px 0 0 0")
        )

        self.traces = ipywidgets.Text(description="Trace:", style={"description_width": "120px"},
                                      layout=ipywidgets.Layout(width="350px", display="none"))

        self.job_name = ipywidgets.Text(
            description="Job name:",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        self.nr_cores = ipywidgets.IntText(
            value=12,
            min=0,
            max=24,
            description="Cores/node:",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        self.nr_nodes = ipywidgets.IntText(
            value=1,
            description="Nodes:",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        self.run_time = ipywidgets.FloatText(
            value=0.5,
            description="Run time (h):",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        self.zip_path = ipywidgets.Text(
            value="",
            description="Zip file:",
            disabled=True,
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        self.traces_opt.observe(self._run_method, names='value')
        self._run_method()

        super().__init__(
            [self.title, self.help_text, self.tool_id, self.traces_opt_box, self.traces, self.job_name,
             self.nr_cores, self.nr_nodes, self.run_time,self.zip_path],
            layout=ipywidgets.Layout(
                padding="4px 16px 12px 16px",
                margin="0 20px 0 0",
                width="420px",
                gap="10px",
            ),
            **kwargs
        )

    def _run_method(self, change=None):
        if self.traces_opt.value == 'all_traces':
            self.traces.value = '3'
            self.traces.layout.display = 'none'
        else:
            self.traces.value = '3'
            self.traces.layout.display = ''

    def get_values(self):
        return {
            "tool_id": self.tool_id.value.strip(),
            "trace_mode": self.traces_opt.value,
            "trace_value": self.traces.value,
            "job_name": self.job_name.value.strip(),
            "nr_cores": self.nr_cores.value,
            "nr_nodes": self.nr_nodes.value,
            "run_time": self.run_time.value,
            "zip_path": self.zip_path.value,
        }
