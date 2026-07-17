from clsiwidgets.ui.run_with_sa import RunWithSA
from clsiwidgets.ui.sa_context_widget import SAContextWidget
from clsiwidgets.ui.sa_monitor_widget import ServiceAccountMonitorWidget


def test_sa_context_widget():
    widget = SAContextWidget()

    try:
        assert widget.get_values() == {
            "hpc": "NSG",
            "project": None,
        }
        assert widget.project.disabled is True

        widget.project.options = [
            ("Project One", "project-one"),
            ("Project Two", "project-two"),
        ]
        widget.project.disabled = False
        widget.project.value = "project-one"

        assert widget.get_values() == {
            "hpc": "NSG",
            "project": "project-one",
        }

        widget.reset_projects()

        assert tuple(widget.project.options) == ()
        assert widget.project.value is None
        assert widget.project.disabled is True
    finally:
        widget.close()

def test_sa_monitor_widget():
    widget = ServiceAccountMonitorWidget()

    try:
        assert widget.retrieve_jobs_button.disabled is True
        assert widget.jobs_dropdown.disabled is True
        assert widget.download_results_button.disabled is True

        jobs = [
            ("First job", ("job-1", "remote-job-1")),
            ("Second job", ("job-2", "remote-job-2")),
        ]

        widget.set_jobs(jobs)

        assert tuple(widget.jobs_dropdown.options) == tuple(jobs)
        assert widget.jobs_dropdown.value == ("job-1", "remote-job-1")
        assert widget.jobs_dropdown.disabled is False
        assert widget.download_results_button.disabled is False

        widget.reset_jobs()

        assert tuple(widget.jobs_dropdown.options) == ()
        assert widget.jobs_dropdown.value is None
        assert widget.jobs_dropdown.disabled is True
        assert widget.download_results_button.disabled is True
    finally:
        widget.close()

def test_run_with_sa_submits_job_with_mocked_service(mocker, tmp_path):
    zip_file = tmp_path / "transfer.zip"

    # Mock package creation
    package_builder = mocker.Mock()
    package_builder.create_zip.return_value = zip_file

    package_builder_class = mocker.patch(
        "clsiwidgets.ui.run_with_sa.NSGPackageBuilder",
        return_value=package_builder,
    )

    # Mock the Service Account backend
    submitter = mocker.Mock()
    submitter.submit_job.return_value = {
        "id": 123,
        "job_id": "remote-job-123",
        "stage": "QUEUE",
        "title": "test-job",
    }

    submitter_class = mocker.patch(
        "clsiwidgets.ui.run_with_sa.SASubmitter",
        return_value=submitter,
    )

    widget = RunWithSA(
        data_path=tmp_path / "data",
        transfer_path=tmp_path / "transfer",
        results_path=tmp_path / "results",
    )

    try:
        widget.context_widget.project.options = [
            ("Test Project", "test-project"),
        ]
        widget.context_widget.project.disabled = False
        widget.context_widget.project.value = "test-project"

        widget.job_settings_widget.tool_id.value = "TEST_TOOL"
        widget.job_settings_widget.job_name.value = "test-job"
        widget.job_settings_widget.traces_opt.value = "singletrace"
        widget.job_settings_widget.traces.value = "7"

        expected_settings = widget.job_settings_widget.get_values()

        widget._submit_job(None)

        package_builder_class.assert_called_once_with(
            tmp_path / "data",
            tmp_path / "transfer",
        )

        package_builder.write_start_file.assert_called_once_with(
            trace_mode="singletrace",
            trace_value="7",
        )
        package_builder.create_zip.assert_called_once_with()

        submitter_class.assert_called_once_with()

        submitter.submit_job.assert_called_once_with(
            zip_file=zip_file,
            settings=expected_settings,
            hpc="NSG",
            project="test-project",
            tool_id="TEST_TOOL",
        )

        assert widget.job_settings_widget.zip_path.value == str(zip_file)
        assert widget.current_job_id == 123
        assert widget.current_remote_job_id == "remote-job-123"
        assert widget.current_job_status == "QUEUE"
        assert widget.check_sim_button.disabled is False

        assert "test-job" in widget.sim_status.value
        assert "test-project" in widget.sim_status.value
        assert "123" in widget.sim_status.value
        assert "QUEUE" in widget.sim_status.value
        assert (
            "Job submitted successfully through Service Account."
            in widget.status_message.value
        )
    finally:
        widget.close()
