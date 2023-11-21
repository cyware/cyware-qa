'''
copyright: Copyright (C) 2015-2021, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: This module verifies the correct behavior of the setting 'timeout' and 'queue_size'.

tier: 0

modules:
    - authd

components:
    - manager

daemons:
    - cyware-authd

os_platform:
    - linux

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - CentOS 6
    - Ubuntu Focal
    - Ubuntu Bionic
    - Ubuntu Xenial
    - Ubuntu Trusty
    - Debian Buster
    - Debian Stretch
    - Debian Jessie
    - Debian Wheezy
    - Red Hat 8
    - Red Hat 7
    - Red Hat 6

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/auth.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/registering/key-request.html

tags:
    - key_request
'''
import os

import pytest
from cyware_testing.fim import generate_params
from cyware_testing.tools import LOG_FILE_PATH, CYWARE_PATH
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.file import read_yaml
from cyware_testing.authd import validate_authd_logs

# Marks

pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]


# Configurations

test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
message_tests = read_yaml(os.path.join(test_data_path, 'test_key_request_limits.yaml'))
configurations_path = os.path.join(test_data_path, 'cyware_authd_configuration.yaml')
local_internal_options = {'authd.debug': '2'}
script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')
script_filename = 'fetch_keys_sleep.py'

DEFAULT_QUEUE_SIZE = '1024'
DEFAULT_TIMEOUT = '60'
conf_params = {'QUEUE_SIZE': [], 'TIMEOUT': []}

for case in message_tests:
    conf_params['QUEUE_SIZE'].append(case.get('QUEUE_SIZE', DEFAULT_QUEUE_SIZE))
    conf_params['TIMEOUT'].append(case.get('TIMEOUT', DEFAULT_TIMEOUT))

p, m = generate_params(extra_params=conf_params, modes=['scheduled'] * len(message_tests))
configurations = load_cyware_configurations(configurations_path, __name__, params=p, metadata=m)

# Variables
kreq_sock_path = os.path.join(CYWARE_PATH, 'queue', 'sockets', 'krequest')
log_monitor_paths = [LOG_FILE_PATH]
receiver_sockets_params = [(kreq_sock_path, 'AF_UNIX', 'UDP')]
test_case_ids = [f"{test_case['name'].lower().replace(' ', '-')}" for test_case in message_tests]

monitored_sockets_params = [('cyware-authd', None, True)]
receiver_sockets, monitored_sockets, log_monitors = None, None, None  # Set in the fixtures


@pytest.fixture(scope='module', params=configurations, ids=test_case_ids)
def get_configuration(request):
    """Get configurations from the module"""
    yield request.param


@pytest.fixture(scope='function')
def get_current_test_case():
    """Get current test case from the module"""
    return message_tests.pop(0)


def test_key_request_limits(configure_environment, get_current_test_case, copy_tmp_script,
                            configure_local_internal_options_module, restart_authd_function,
                            wait_for_authd_startup_function, connect_to_sockets_function, tear_down):
    '''
    description:
        Checks that every input message on the key request port with different limits 'timeout' and 'queue_size'
        configuration, along with a delayed script, shows the corresponding error in the manager logs.

    cyware_min_version: 4.4.0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get the configuration of the test.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - get_current_test_case:
            type: fixture
            brief: Gets the current test case from the tests' list.
        - copy_tmp_script:
            type: fixture
            brief: Copy the script to a temporary folder for testing.
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the local internal options file.
        - restart_authd_function:
            type: fixture
            brief: Stops the cyware-authd daemon.
        - wait_for_authd_startup_function:
            type: fixture
            brief: Waits until Authd is accepting connections.
        - connect_to_sockets_function:
            type: fixture
            brief: Bind to the configured sockets at function scope.
        - tear_down:
            type: fixture
            brief: Cleans the client.keys file.

    assertions:
        - The exec_path must be configured correctly
        - The script works as expected

    input_description:
        Different test cases are contained in an external YAML file (test_key_request_limits.yaml) which
        includes the different possible key requests with different configurations and the expected responses.

    expected_log:
        - Key request responses on 'authd' logs.
    '''

    key_request_sock = receiver_sockets[0]

    for stage in get_current_test_case['test_case']:
        messages = stage.get('input', [])
        response = stage.get('log', [])

        for input in messages:
            key_request_sock.send(input, size=False)
        # Monitor expected log messages
        validate_authd_logs(response)
