import ipywidgets
from clsiwidgets.config import SERVICE_ACCOUNT_APP_KEY
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
            "or from CLB_AUTH when running locally. "
            "The AppKey is pre-filled for the Synaptic Events Fitting app "
            "and can be left unchanged unless a different app key is needed."
            "</span>"
        )

        self.app_key = ipywidgets.Password(
            value=SERVICE_ACCOUNT_APP_KEY,
            description="AppKey:",
            placeholder="Enter the Service Account AppKey",
            style={"description_width": "80px"},
            layout=ipywidgets.Layout(width="400px"),
        )

        self.hpc = ipywidgets.Dropdown(
            options=[("NSG", "NSG")],
            value="NSG",
            description="HPC:",
            style={"description_width": "45px"},
            layout=ipywidgets.Layout(width="150px"),
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
            layout=ipywidgets.Layout(width="400px"),
            disabled=True,
        )

        app_key_row = ipywidgets.HBox(
            [self.app_key, self.load_projects_button],
            layout=ipywidgets.Layout(
                align_items="center",
                gap="10px",
            ),
        )

        context_row = ipywidgets.HBox(
            [self.project, self.hpc],
            layout=ipywidgets.Layout(
                align_items="center",
                gap="20px",
            ),
        )

        super().__init__(
            [
                self.title,
                self.help_text,
                app_key_row,
                context_row,
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
            "app_key": self.app_key.value.strip(),
            "hpc": self.hpc.value,
            "project": self.project.value,
        }

    def reset_projects(self):
        self.project.options = []
        self.project.value = None
        self.project.disabled = True
