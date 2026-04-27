from dataclasses import dataclass
from pathlib import Path
import requests

@dataclass
class NSGSubmitter:
    username: str
    password: str
    app_key: str
    base_url: str = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'

    def _headers(self):
        return {
            'cipres-appkey': self.app_key,
        }

    def _job_url(self):
        return f"{self.base_url}/job/{self.username}"

    def get_job(self, job_handle):
        response = requests.get(
            f"{self._job_url()}/{job_handle}",
            auth=(self.username, self.password),
            headers=self._headers(),
            timeout=120,
        )
        response.raise_for_status()
        return response

    def submit_job(self, tool_id, job_name, zip_file, nr_cores, nr_nodes, run_time):
        """
            Submit a job to NSG Portal for NEURON_EXPANSE tool.
        """

        zip_file = Path(zip_file)
        if not zip_file.exists():
            raise FileNotFoundError(f"Zip file not found: {zip_file}")

        payload = {'tool' : tool_id,
                   'metadata.statusEmail' : 'false',
                   'metadata.clientJobId': job_name,
                   'metadata.clientJobName': job_name,
                   'vparam.pythonoption_' : '1',
                   'vparam.nrnivmodl_o_': '1',
                   'vparam.number_cores_' : str(nr_cores),
                   'vparam.number_nodes_' : str(nr_nodes),
                   'vparam.runtime_' : str(run_time),
                   'vparam.filename_': 'start.py'}
        with zip_file.open("rb") as f:
            files = {'input.infile_' : (zip_file.name, f, "application/zip")}

            response = requests.post(self._job_url(), auth=(self.username, self.password),
                              data=payload, headers=self._headers(), files=files, timeout=120)

        response.raise_for_status()
        return response

    def list_jobs(self):
        response = requests.get(
            self._job_url(),
            auth=(self.username, self.password),
            headers=self._headers(),
            timeout=120,
        )
        response.raise_for_status()
        return response

    def get_results_listing(self, results_uri):
        response = requests.get(
            results_uri,
            auth=(self.username, self.password),
            headers=self._headers(),
            timeout=120,
        )
        response.raise_for_status()
        return response

    def download_result_file(self, download_url, dest_path):
        dest_path = Path(dest_path)

        response = requests.get(
            download_url,
            auth=(self.username, self.password),
            headers=self._headers(),
            timeout=300,
            stream=True,
        )
        response.raise_for_status()

        with dest_path.open("wb") as fd:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fd.write(chunk)

        return dest_path
