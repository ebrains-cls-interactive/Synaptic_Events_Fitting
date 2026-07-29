import ipywidgets
from clsiwidgets.ui.base_widget import BaseWidget
from clsiwidgets.ui.data_proxy_widget import DataProxyWidget
from clsiwidgets.ui.mod_file_widget import ModFileWidget


class SynapticEventsFitting(ipywidgets.VBox, BaseWidget):
    """
    Parent Widget for controlling the synaptic events fitting workflow.
    """

    def __init__(self, data_path, transfer_path, **kwargs):
        self.title = ipywidgets.HTML("<h3>Prepare configuration for a simulation</h3>")

        self.section_1 = ipywidgets.HTML("<h4>1. Retrieve experimental data</h4>")
        self.experimental_data = DataProxyWidget(transfer_dir=transfer_path)

        self.section_2 = ipywidgets.HTML("<h4>2. Model File</h4>")
        self.model_file_widget = ModFileWidget(data_path=data_path, transfer_dir=transfer_path)


        experimental_data_section = ipywidgets.VBox([self.section_1, self.experimental_data, self.section_2,
                                                     self.model_file_widget])

        super().__init__([self.title, experimental_data_section], layout=self.DEFAULT_BORDER)