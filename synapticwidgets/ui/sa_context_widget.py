import ipywidgets
from synapticwidgets.ui.base_widget import BaseWidget


class SAContextWidget(ipywidgets.VBox, BaseWidget):
    """
    Small widget for configuring the Service Account execution context.
    """

    def __init__(self, **kwargs):
        self.title = ipywidgets.HTML("<b>Service Account</b>")
        self.help_text = ipywidgets.HTML(
            "<span style='font-size:12px; color:#666;'>"
            "Authentication is resolved automatically from the lab environment "
            "or from CLB_AUTH when running locally."
            "</span>"
        )

        self.hpc = ipywidgets.Dropdown(
            options=[("NSG", "NSG")],
            value="NSG",
            description="HPC:",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="320px"),
        )

        self.project = ipywidgets.Text(
            value="nsg-project",
            description="Project:",
            style={"description_width": "120px"},
            layout=ipywidgets.Layout(width="350px"),
        )

        super().__init__(
            [
                self.title,
                self.help_text,
                self.hpc,
                self.project,
            ],
            layout=ipywidgets.Layout(
                padding="4px 16px 12px 16px",
                margin="0 20px 0 0",
                width="480px",
                gap="10px",
            ),
            **kwargs
        )

    def get_values(self):
        return {
            "hpc": self.hpc.value,
            "project": self.project.value.strip(),
        }
