'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: This module verifies the correct behavior of Cyware Agentd during the enrollment under different configurations.
components:
    - agentd

targets:
    - agent

daemons:
    - cyware-agentd
os_platform:
    - linux
    - windows

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Ubuntu Focal
    - Ubuntu Bionic
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

tags:
    - enrollment
'''

import pytest
import socket
import os
import sys
import subprocess

from cyware_testing.tools import get_version
from cyware_testing.tools.services import control_service
from cyware_testing.tools.file import read_yaml
from cyware_testing.tools.monitoring import QueueMonitor, make_callback
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.utils import get_host_name
from enrollment import AGENTD_ENROLLMENT_REQUEST_TIMEOUT

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.win32, pytest.mark.tier(level=0), pytest.mark.agent]

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
tests = read_yaml(os.path.join(test_data_path, 'cyware_enrollment_tests.yaml'))
configurations_path = os.path.join(test_data_path, 'cyware_enrollment_conf.yaml')
configurations = load_cyware_configurations(configurations_path, __name__)
host_name = socket.gethostname()
no_restart_windows_after_configuration_set = True
configuration_ids = ['agentd_enrollment']
test_case_ids = [f"{test_case['name']}" for test_case in tests]

# Fixtures


@pytest.fixture(scope='module', params=configurations, ids=configuration_ids)
def get_configuration(request):
    """
    Get configurations from the module
    """
    return request.param


@pytest.fixture(scope='function', params=tests, ids=test_case_ids)
def get_current_test_case(request):
    """
    Get current test case from the module
    """
    return request.param


@pytest.fixture(scope='function')
def restart_agentd(get_current_test_case):
    """
    Restart Agentd and control if it is expected to fail or not.
    """
    if 'cyware-agentd' in get_current_test_case.get('skips', []):
        pytest.skip("This test does not apply to agentd")

    try:
        control_service('restart', daemon='cyware-agentd')
    except Exception:
        pass

    yield
    control_service('stop', daemon='cyware-agentd')


def test_agentd_enrollment(configure_environment, override_cyware_conf, get_current_test_case, create_certificates,
                           set_keys, set_password, file_monitoring, configure_socket_listener, restart_agentd, request):
    """
        description:
            "Check that different configuration generates the adequate enrollment message or the corresponding error
            log. The configuration, keys, and password files will be written with the different scenarios described
            in the test cases. After this, Agentd is started to wait for the expected result."

        cyware_min_version: 4.2.0

        tier: 0

        parameters:
            - configure_environment:
                type: fixture
                brief: Configure a custom environment for testing.
            - override_cyware_conf:
                type: fixture
                brief: Write a particular Cyware configuration for the test case.
            - get_current_test_case:
                type: fixture
                brief: Get the current test case.
            - create_certificates:
                type: fixture
                brief: Write the certificate files used for SSL communication.
            - set_keys:
                type: fixture
                brief: Write pre-existent keys into client.keys.
            - set_password:
                type: fixture
                brief: Write the password file.
            - file_monitoring:
                type: fixture
                brief: Handle the monitoring of a specified file.
            - restart_agentd:
                type: fixture
                brief: Restart Agentd and control if it is expected to fail or not.
            - request:
                type: fixture
                brief: Provide information of the requesting test function.

        assertions:
            - The enrollment message is sent when the configuration is valid
            - The enrollment message is generated as expected when the configuration is valid.
            - The error log is generated as expected when the configuration is invalid.

        input_description:
            Different test cases are contained in an external YAML file (cyware_enrollment_tests.yaml) which includes the
            different available enrollment-related configurations.

        expected_output:
            - Enrollment request message on Authd socket
            - Error logs related to the wrong configuration block
    """

    # Check if socket listener is opened
    assert configure_socket_listener, 'The agent failed configuring socket listener to start listening on the socket.'

    if 'expected_error' in get_current_test_case:
        log_monitor = request.module.log_monitor
        expected_error_dict = get_current_test_case['expected_error']
        expected_error = expected_error_dict['agent-enrollment'] if 'agent-enrollment' in expected_error_dict else \
                                                                    expected_error_dict
        try:
            log_monitor.start(timeout=AGENTD_ENROLLMENT_REQUEST_TIMEOUT,
                              callback=make_callback(expected_error, prefix='.*',
                                                     escape=True),
                              error_message='Expected error log does not occured.')
        except Exception as error:
            expected_fail = get_current_test_case.get('expected_fail')
            if expected_fail and (expected_fail['os'] == "any" or expected_fail['os'] == sys.platform):
                is_xfail = True
                xfail_reason = expected_fail.get('reason')
            else:
                is_xfail = False

            if is_xfail:
                pytest.xfail(f"Xfailing due to {xfail_reason}")
            else:
                raise error

    else:
        test_expected = get_current_test_case['message']['expected'].format(host_name=get_host_name(),
                                                                            agent_version=get_version()).encode()
        test_response = get_current_test_case['message']['response'].format(host_name=get_host_name()).encode()

        # Monitor MITM queue
        socket_monitor = QueueMonitor(request.module.socket_listener.queue)
        event = (test_expected, test_response)

        try:
            # Start socket monitoring
            socket_monitor.start(timeout=AGENTD_ENROLLMENT_REQUEST_TIMEOUT,
                                 callback=lambda received_event: event == received_event,
                                 error_message='Enrollment request message never arrived', update_position=False)
        finally:
            socket_monitor.stop()
