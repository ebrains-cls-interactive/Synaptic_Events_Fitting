import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

@dataclass
class SASubmitter:
    base_url: str = 'https://cls-sa.ebrains-italy.eu'

    def _job_url(self):
        return f"{self.base_url}/job"

    def _get_service_account_headers(self, zip_name=None, payload=False):
        """
        Returns the Service Account headers to pass in the requests object.
        """
        token = self._retrieve_token()
        app_key = '' #TODO store/retrieve?
        headers = {'Authorization': 'Bearer ' + token, 'Appkey': app_key,}
        if zip_name:
            content_type = ''
            if zip_name.endswith('.zip'):
                content_type = 'application/zip'
            elif zip_name.endswith('.tar'):
                content_type = 'application/x-tar'
            headers.update({
                'Content-Disposition': f"attachment;filename={zip_name}",
                'Content-Type': content_type
            })
        if payload:
            headers.update({'Content-Type': 'application/json'})
        return headers

    @staticmethod
    def _get_service_account_payload(hpc, project, tool, node_num, core_num, runtime, title):
        """
        Returns the service account payload
        """
        return {
            'hpc': hpc,
            'project': project,
            'tool': tool,
            'init_file': 'start.py',
            'node_number': node_num,
            'core_number': core_num,
            'runtime': runtime,
            'title': title
        }

    @staticmethod
    def _retrieve_token():
        """ returns HTTP headers containing OIDC bearer token """
        try:
            from clb_nb_utils import oauth as clb_oauth
            token = clb_oauth.get_token()
        except (ModuleNotFoundError, ConnectionError) as e:
            token = os.environ.get('CLB_AUTH')
            if token is None:
                raise RuntimeError("No auth token available. Could not retrieve a lab token or a CLB_AUTH environment"
                                   " variable.")

        return token

    def submit_job(self, zip_file, settings, hpc="NSG", project="nsg-project", tool_id="NEURON_EXPANSE"):
        """
        Submit a job behind the Service Account through NSG-R.
        """
        zip_file = Path(zip_file)
        if not zip_file.exists():
            raise FileNotFoundError(f"Zip file not found: {zip_file}")

        zip_name = zip_file.name
        payload = self._get_service_account_payload(
            hpc=hpc,
            project=project,
            tool=tool_id,
            node_num=settings['nr_nodes'],
            core_num=settings['nr_cores'],
            runtime=settings['run_time'],
            title=settings['job_name'],
        )

        headers = self._get_service_account_headers(payload=True)
        r = requests.post(url=self._job_url(), headers=headers, json=payload, timeout=300)

        if r.status_code != 201:
            raise RuntimeError(f"Service account job creation failed: {r.status_code} {r.text}")

        job_id = r.json().get("id")
        if not job_id:
            raise RuntimeError("Service account job creation succeeded but no job id was returned.")

        upload_url = f"{self._job_url()}/{job_id}/upload-input-file/"
        headers = self._get_service_account_headers(zip_name=zip_name)

        with zip_file.open("rb") as fd:
            r = requests.patch(url=upload_url, headers=headers, data=fd.read(), timeout=300)

        if r.status_code >= 400:
            raise RuntimeError(f"Service account input upload failed: {r.status_code} {r.text}")

        return r


    def get_service_account_jobs(self, project):
        """
        Returns a list of all jobs submitted using the Service Account
        """
        headers = self._get_service_account_headers()
        r = requests.get(url=self._job_url(), headers=headers, params={'project': project}, timeout=360000)
        print(f"requests: {r.url}; with headers: {r.headers}")
        if r.status_code != 200:
            raise RuntimeError(f"Service account jobs retrieval failed: {r.status_code} {r.content}")
        return r.json()

    def get_service_account_job_results(self, project, job_id):
        """
        Returns a list of the files once the job ends.
        """
        headers = self._get_service_account_headers()

        sa_endpoint = f"{self._job_url()}/results/"
        params = {
            'job_id': job_id,
            'project': project,
        }
        r = requests.get(url=sa_endpoint, params=params, headers=headers, timeout=360000)

        print(f"requests: {r.url} with headers: {r.headers}")
        if r.status_code != 200:
            raise RuntimeError(
                f"Service account job results retrieval failed: {r.status_code} {r.text}"
            )

        file_name = r.headers.get('Content-Disposition', 'results.zip').split('filename=')[1].replace('"', '')
        file_content = r.content

        file_list = {
            file_name: file_content
        }

        return file_list

