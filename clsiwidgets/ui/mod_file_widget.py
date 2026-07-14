import ipywidgets
import shutil
from clsiwidgets.ui.base_widget import BaseWidget


class ModFileWidget(ipywidgets.HBox, BaseWidget):
    """
    Small widget for uploading model file.
    """

    def __init__(self, data_path, transfer_dir, **kwargs):
        super().__init__()
        self.data_path = data_path
        self.transfer_dir = transfer_dir

        self.mod_file_label = ipywidgets.HTML("Select mod file:")

        self.mod_file_rb = ipywidgets.RadioButtons(options=["default", "local"], value="default",)

        self.mod_file_box = ipywidgets.HBox([self.mod_file_label, self.mod_file_rb],
                                            layout=ipywidgets.Layout(align_items="flex-start", gap="30px"))

        self.default_mod_selector = ipywidgets.Dropdown(options=[(f.name, f) for f in self.data_path.glob("*.mod")],)

        self.use_default_button = ipywidgets.Button( description="Use selected .mod", button_style="primary")

        self.default_box = ipywidgets.HBox ([self.default_mod_selector, self.use_default_button],
                                            layout=ipywidgets.Layout(align_items="flex-start", gap="12px"))

        self.local_mod_uploader = ipywidgets.FileUpload(accept='.mod', multiple=False, description="Upload .mod file",
                                                        layout=ipywidgets.Layout(width="220px"))

        self.local_box = ipywidgets.VBox([self.local_mod_uploader])

        self.status_message = ipywidgets.HTML("")
        self.status_message.layout.display = 'none'

        self.output = ipywidgets.Output()

        self.mod_file_rb.observe(self.handle_mod_file, names="value")
        self.use_default_button.on_click(self._handle_default_upload)
        self.local_mod_uploader.observe(self._handle_local_upload, names="value")

        self.children = [
            self.mod_file_box,
            self.default_box,
            self.local_box,
            self.status_message,
            self.output
        ]

        self._update_visibility()

    def handle_mod_file(self, change):
        self._update_visibility()

    def _update_visibility(self):
        self._hide_status()

        if self.mod_file_rb.value == "default":
            self.default_box.layout.display = 'flex'
            self.local_box.layout.display = 'none'
        else:
            self.default_box.layout.display = 'none'
            self.local_box.layout.display = 'flex'

    def _handle_default_upload(self, _):
        with self.output:
            self.output.clear_output()

            selected_file = self.default_mod_selector.value
            if selected_file is None:
                self.logger.error("No bundle .mod file available.")
                return

            dest_file = self.transfer_dir / selected_file.name
            shutil.copy2(selected_file, dest_file)

            self.selected_mod_path = dest_file
            self._show_success(f"The {selected_file.name} file was selected.")
            self.logger.info(f"Using bundled .mod file: {dest_file}")

    def _handle_local_upload(self, _):
        with self.output:
            self.output.clear_output()

            if not self.local_mod_uploader.value:
                return

            uploaded_file = self.local_mod_uploader.value[0]

            filename = uploaded_file.name
            content = uploaded_file.content

            dest_file = self.transfer_dir / filename
            dest_file.write_bytes(content)
            self._show_success(f"Local {filename} file was uploaded.")
            self.logger.info(f"Uploaded {filename} to {dest_file}")

    def _show_success(self, message):
        self.status_message.value = f"<span style='color: green;'>{message}</span>"
        self.status_message.layout.display = "flex"

    def _hide_status(self):
        self.status_message.value = ""
        self.status_message.layout.display = "none"
