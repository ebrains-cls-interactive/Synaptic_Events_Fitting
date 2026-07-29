from clsiwidgets.ui.nsg_credentials_widget import NSGCredentialsWidget
from clsiwidgets.ui.nsg_job_settings_widget import NSGJobSettingsWidget
from clsiwidgets.ui.run_on_nsg import RunOnNSG


def test_get_credentials(nsg_credentials_widget):
    widget = nsg_credentials_widget

    assert isinstance(widget, NSGCredentialsWidget)
    assert widget.get_credentials() == {
        "username": "",
        "password": "",
        "app_key": "",
    }
    assert widget.has_credentials() is False

    widget.username.value = "  test-user  "
    widget.password.value = "  password with spaces  "
    widget.app_key.value = "  test-app-key  "

    assert widget.get_credentials() == {
        "username": "test-user",
        "password": "  password with spaces  ",
        "app_key": "test-app-key",
    }
    assert widget.has_credentials() is True

    widget.app_key.value = ""
    assert widget.has_credentials() is False

def test_nsg_job_settings_widget():
    widget = NSGJobSettingsWidget()

    try:
        assert widget.traces_opt.value == "all_traces"
        assert widget.traces.layout.display == "none"

        # Selecting a single trace should display the trace field
        widget.traces_opt.value = "singletrace"
        widget.traces.value = "7"
        widget.tool_id.value = "  TEST_TOOL  "
        widget.job_name.value = "  test-job  "

        assert widget.traces.layout.display == ""

        assert widget.get_values() == {
            "tool_id": "TEST_TOOL",
            "trace_mode": "singletrace",
            "trace_value": "7",
            "job_name": "test-job",
            "nr_cores": 12,
            "nr_nodes": 1,
            "run_time": 0.5,
            "zip_path": "",
        }
    finally:
        widget.close()


def test_run_on_nsg_updates_actions_from_credentials(tmp_path):
    widget = RunOnNSG(
        data_path=tmp_path / "data",
        transfer_path=tmp_path / "transfer",
        results_path=tmp_path / "results",
    )

    try:
        assert widget.monitor_widget.check_jobs_button.disabled is True

        widget.credentials_widget.username.value = "test-user"
        widget.credentials_widget.password.value = "test-password"
        widget.credentials_widget.app_key.value = "test-app-key"

        assert widget.monitor_widget.check_jobs_button.disabled is False

        widget.credentials_widget.password.value = ""
        assert widget.monitor_widget.check_jobs_button.disabled is True
    finally:
        widget.close()

def test_run_on_nsg_submits_job_with_mocked_service(mocker, tmp_path):
    zip_file = tmp_path / "transfer.zip"

    # Mock package creation
    package_builder = mocker.Mock()
    package_builder.create_zip.return_value = zip_file

    package_builder_class = mocker.patch(
        "clsiwidgets.ui.run_on_nsg.NSGPackageBuilder",
        return_value=package_builder,
    )

    # Mock the external NSG client
    response = mocker.Mock(
        text="<submitted-job />",
        status_code=200,
    )

    submitter = mocker.Mock()
    submitter.submit_job.return_value = response

    submitter_class = mocker.patch(
        "clsiwidgets.ui.run_on_nsg.NSGSubmitter",
        return_value=submitter,
    )

    # Mock XML parsing so this test does not depend on parser details
    parse_submitted_job = mocker.patch(
        "clsiwidgets.ui.run_on_nsg.parse_submitted_job_xml",
        return_value={
            "job_handle": "test-job-handle",
            "job_stage": "QUEUE",
        },
    )

    widget = RunOnNSG(
        data_path=tmp_path / "data",
        transfer_path=tmp_path / "transfer",
        results_path=tmp_path / "results",
    )

    try:
        widget.credentials_widget.username.value = "test-user"
        widget.credentials_widget.password.value = "test-password"
        widget.credentials_widget.app_key.value = "test-app-key"

        widget.job_settings_widget.tool_id.value = "TEST_TOOL"
        widget.job_settings_widget.job_name.value = "test-job"
        widget.job_settings_widget.traces_opt.value = "singletrace"
        widget.job_settings_widget.traces.value = "7"

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

        submitter_class.assert_called_once_with(
            username="test-user",
            password="test-password",
            app_key="test-app-key",
        )

        submitter.submit_job.assert_called_once_with(
            tool_id="TEST_TOOL",
            job_name="test-job",
            zip_file=zip_file,
            nr_cores=12,
            nr_nodes=1,
            run_time=0.5,
        )

        parse_submitted_job.assert_called_once_with(response.text)

        assert widget.job_settings_widget.zip_path.value == str(zip_file)
        assert widget.current_job_handle == "test-job-handle"
        assert widget.current_job_stage == "QUEUE"
        assert widget.current_results_uri is None
        assert widget.check_sim_button.disabled is False
        assert "test-job-handle" in widget.sim_status.value
        assert "QUEUE" in widget.sim_status.value
        assert "Job submitted successfully." in widget.status_message.value
    finally:
        widget.close()
