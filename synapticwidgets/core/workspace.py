import shutil
from pathlib import Path
import importlib_resources

def prepare_workspace_environment():
    home_path = Path.home() / "synapticwidgets"
    data_path = home_path / "data"
    transfer_path = home_path / "transfer"
    results_path = home_path / "results"
    best_fit_workspace_path = home_path / "best_fit_workspace"

    transfer_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)
    best_fit_workspace_path.mkdir(parents=True, exist_ok=True)

    if not (data_path.exists() and any(data_path.iterdir())):
        copy_from_installed_wheel("synapticwidgets.data", resource="", dest_path=data_path)

    populate_workspace_folder(transfer_path, data_path)
    populate_workspace_folder(best_fit_workspace_path, data_path)
    return {
        "home_path": home_path,
        "data_path": data_path,
        "transfer_path": transfer_path,
        "best_fit_workspace_path": best_fit_workspace_path,
        "results_path": results_path,
    }

def copy_from_installed_wheel(package_name, resource="", dest_path=None):
    """
    Copy directory from installed package to destination path.
    """
    if dest_path is None:
        dest_path = package_name.split(".")[-1]

    dest_path = Path(dest_path).expanduser().resolve()

    # Get the resource reference
    ref = importlib_resources.files(package_name)
    if resource:
        ref = ref.joinpath(resource)

    # Create the temporary folder context
    with importlib_resources.as_file(ref) as resource_path:
        resource_path = Path(resource_path).resolve()

        if not resource_path.is_dir():
            raise ValueError(
                f"Resource '{resource}' in package '{package_name}' is not a directory."
            )

        if resource_path == dest_path:
            return dest_path

        shutil.copytree(resource_path, dest_path, dirs_exist_ok=True)

    return dest_path

def populate_workspace_folder(transfer_path, data_path):
    model_support_path = data_path / "model_support"

    # Remove old exp or config files
    for txt_file in transfer_path.glob("*.txt"):
        txt_file.unlink()

    for file_path in model_support_path.iterdir():
        dest_file = transfer_path / file_path.name
        if not dest_file.exists():
            shutil.copy2(file_path, dest_file)
