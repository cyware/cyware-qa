'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logtest' tool allows the testing and verification of rules and decoders against provided log examples
       remotely inside a sandbox in 'cyware-analysisd'. This functionality is provided by the manager, whose work
       parameters are configured in the ossec.conf file in the XML rule_test section. Test logs can be evaluated through
       the 'cyware-logtest' tool or by making requests via RESTful API. These tests will check if the logtest
       configuration is valid. Also checks rules, decoders, decoders, alerts matching logs correctly.

components:
    - logtest

suite: remove_old_sessions

targets:
    - manager

daemons:
    - cyware-analysisd

os_platform:
    - linux

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

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/tools/cyware-logtest.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/cyware-logtest/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/daemons/cyware-analysisd.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/internal-options.html#analysisd

tags:
    - logtest_configuration
'''
import pytest
import os

from cyware_testing.logtest import callback_remove_session, callback_session_initialized
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools import LOGTEST_SOCKET_PATH
from cyware_testing import global_parameters
from time import sleep
from json import dumps

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configurations
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_conf.yaml')
configurations = load_cyware_configurations(configurations_path, __name__)
local_internal_options = {'analysisd.debug': '2'}

# Variables
receiver_sockets_params = [(LOGTEST_SOCKET_PATH, 'AF_UNIX', 'TCP')]
receiver_sockets = None
local_internal_options = {'analysisd.debug': '1'}
create_session_data = {'version': 1, 'command': 'log_processing',
                       'parameters': {'event': 'Oct 15 21:07:56 linux-agent sshd[29205]: Invalid user blimey '
                                      'from 18.18.18.18 port 48928',
                                      'log_format': 'syslog',
                                      'location': 'master->/var/log/syslog'}}
msg_create_session = dumps(create_session_data)


# Fixtures

@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Test

def test_remove_old_session_for_inactivity(configure_local_internal_options_module,
                                           get_configuration,
                                           configure_environment,
                                           restart_required_logtest_daemons,
                                           file_monitoring,
                                           wait_for_logtest_startup,
                                           connect_to_sockets_function):
    '''
    description: Check if 'cyware-logtest' correctly detects and handles the situation where trying to remove old
                 sessions due to inactivity. To do this, it creates more sessions than allowed and waits session_timeout
                 seconds, then checks that 'cyware-logtest' has removed the session due to inactivity.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the local internal options file.
        - get_configuration:
            type: fixture
            brief: Get configuration from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing. Restart Cyware is needed for applying the configuration.
        - restart_required_logtest_daemons:
            type: fixture
            brief: Cyware logtests daemons handler.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - wait_for_logtest_startup:
            type: fixture
            brief: Wait until logtest has begun.
        - connect_to_sockets_function:
            type: fixture
            brief: Function scope version of 'connect_to_sockets' which connects to the specified sockets for the test.

    assertions:
        - Verify that the session is created.
        - Verify that the old session is removed after 'session_timeout' delay due to inactivity.

    input_description: Some test cases are defined in the module. These include some input configurations stored in
                       the 'cyware_conf.yaml' and the session creation data from the module.

    expected_output:
        - 'Session initialization event not found'
        - 'Session removal event not found'
        - r'Error when executing .* in daemon .*. Exit status: .*'

    tags:
        - inactivity
        - analysisd
    '''
    session_timeout = int(get_configuration['sections'][0]['elements'][3]['session_timeout']['value'])

    receiver_sockets[0].send(msg_create_session, True)
    msg_recived = receiver_sockets[0].receive()[4:]
    msg_recived = msg_recived.decode()

    log_monitor.start(timeout=global_parameters.default_timeout,
                      callback=callback_session_initialized,
                      error_message="Session initialization event not found")

    sleep(session_timeout)

    log_monitor.start(timeout=global_parameters.default_timeout,
                      callback=callback_remove_session,
                      error_message="Session removal event not found")
