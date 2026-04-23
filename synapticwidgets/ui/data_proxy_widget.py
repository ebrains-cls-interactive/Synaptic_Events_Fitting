import json
from importlib import resources
import ipywidgets
import requests

from synapticwidgets.ui.base_widget import BaseWidget


class DataProxyWidget(ipywidgets.VBox, BaseWidget):
    """
    Small widget for downloading experimental data from Data Proxy.
    """

    def __init__(self, transfer_dir):
        super().__init__()

        self.transfer_dir = transfer_dir

        with resources.files("synapticwidgets.data").joinpath("experimental_data.json").open("r", encoding="utf-8") as f:
            self.exp_data = json.load(f)

        self.exp_dict = {e["exp_name"]: e["exp_link"] for e in self.exp_data}

        self.mult_select = ipywidgets.SelectMultiple(options=self.exp_dict.keys(), description="Select experimental data:",
                                                     layout=ipywidgets.Layout(width="690px"), style={"description_width": "initial"})
        self.button = ipywidgets.Button(description="Download", button_style="primary")
        self.default_box = ipywidgets.HBox([self.mult_select, self.button],
                                           layout=ipywidgets.Layout(align_items="flex-start", gap="12px"))
        self.output = ipywidgets.Output()

        self.button.on_click(self._download_data)
        self.children = [self.default_box, self.output]

    def _download_data(self, _):
        with self.output:
            self.output.clear_output()
            for name in self.mult_select.value:
                url = self.exp_dict[name]
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                exp_name = 'exp' + name[name.find('(')+1:name.find(')')] + '.txt'
                path = self.transfer_dir / exp_name
                path.write_bytes(response.content)
                print(f"Downloaded {exp_name} to {path}")