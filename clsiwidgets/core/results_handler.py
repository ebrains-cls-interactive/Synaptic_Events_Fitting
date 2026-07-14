import shutil
import tarfile
import zipfile
from pathlib import Path


class ResultsHandler:
    """
    Shared helper for extracting and normalizing downloaded job results.
    """

    @staticmethod
    def extract_output_archive(archive_path, results_dir):
        archive_path = Path(archive_path)
        results_dir = Path(results_dir)

        if not archive_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        extract_dir = results_dir / "OUTPUT"
        extract_dir.mkdir(exist_ok=True)

        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)
        else:
            with tarfile.open(archive_path) as tf:
                tf.extractall(extract_dir)

        ResultsHandler._copy_relevant_files(extract_dir, results_dir)


    @staticmethod
    def _copy_relevant_files(extract_dir, results_dir):
        extract_dir = Path(extract_dir)
        results_dir = Path(results_dir)

        transfer_dir = extract_dir / "transfer"
        source_dir = transfer_dir if transfer_dir.exists() else extract_dir

        for file_path in source_dir.rglob("*"):
            if not file_path.is_file():
                continue

            keep = (
                file_path.suffix == ".txt"
                or (file_path.suffix == ".mod" and file_path.name != "netstims.mod")
                or file_path.name in {"test.csv", "start.py", "STDOUT", "STDERR"}
            )
            if keep:
                shutil.copy2(file_path, results_dir / file_path.name)