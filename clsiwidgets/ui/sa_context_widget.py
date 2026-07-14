import ipywidgets
from clsiwidgets.ui.base_widget import BaseWidget


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
            style={"description_width": "80px"},
            layout=ipywidgets.Layout(width="220px"),
        )

        self.load_projects_button = ipywidgets.Button(
            description="Load projects",
            icon="refresh",
            layout=ipywidgets.Layout(width="150px"),
        )

        self.project = ipywidgets.Dropdown(
            options=[],
            description="Project:",
            style={"description_width": "80px"},
            layout=ipywidgets.Layout(width="375px"),
            disabled=True,
        )

        self.hpc_box = ipywidgets.HBox(
            [self.hpc, self.load_projects_button],
            layout=ipywidgets.Layout(
                align_items="center",
                gap="12px",
            ),
        )

        super().__init__(
            [
                self.title,
                self.help_text,
                self.hpc_box,
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
            "project": self.project.value,
        }

    def reset_projects(self):
        self.project.options = []
        self.project.value = None
        self.project.disabled = True
