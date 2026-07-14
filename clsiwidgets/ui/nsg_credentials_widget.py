import ipywidgets


class NSGCredentialsWidget(ipywidgets.VBox):
    """
    Small widget for entering NSG credentials
    """

    def __init__(self, **kwargs):
        self.title = ipywidgets.HTML("<b>Credentials</b>")
        self.help_text = ipywidgets.HTML("<span style='font-size:12px; color:#666;'>"
            "Enter your NSG credentials."
            "</span>"
        )

        self.username = ipywidgets.Text(description="Username:", style={"description_width": "120px"},
                                        layout=ipywidgets.Layout(width="350px"), )

        self.password = ipywidgets.Password(description="Password:", style={"description_width": "120px"},
                                            layout=ipywidgets.Layout(width="350px"),)

        self.app_key = ipywidgets.Text(value="", description="App key:", placeholder="Enter your NSG app key",
                                       style={"description_width": "120px"}, layout=ipywidgets.Layout(width="350px"),)

        super().__init__(
            [
                self.title,
                self.help_text,
                self.username,
                self.password,
                self.app_key,
            ],
            layout=ipywidgets.Layout(
                padding="12px 16px 12px 16px",
                margin="0 20px 0 0",
                width="420px",
                gap="10px",
            ),
            **kwargs
        )

    def get_credentials(self):
        return {
            "username": self.username.value.strip(),
            "password": self.password.value,
            "app_key": self.app_key.value.strip(),
        }

    def has_credentials(self):
        return bool(
            self.username.value.strip()
            and self.password.value.strip()
            and self.app_key.value.strip()
        )