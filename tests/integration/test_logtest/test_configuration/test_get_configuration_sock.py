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

suite: configuration

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

tags:
    - logtest_configuration
'''
import os
import re

import pytest
from cyware_testing.tools import CYWARE_PATH
from cyware_testing.tools.configuration import load_cyware_configurations

# Marks
pytestmark = [pytest.mark.linux, pytest.mark.tier(level=0), pytest.mark.server]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_conf.yaml')
configurations = load_cyware_configurations(configurations_path, __name__)

# Variables
logtest_sock = os.path.join(os.path.join(CYWARE_PATH, 'queue', 'sockets', 'analysis'))
receiver_sockets_params = [(logtest_sock, 'AF_UNIX', 'TCP')]
receiver_sockets = None
msg_get_config = '{"version": 1, "origin": {"module": "api"}, "command": "getconfig", "module": "api",\
                 "parameters": {"section": "rule_test"}}'


# Fixture
@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Test
def test_get_configuration_sock(get_configuration, configure_environment, restart_cyware, connect_to_sockets_function):
    '''
    description: Check analysis Unix socket returns the correct Logtest configuration under different sets of
                 configurations, `cyware-analisysd` returns the right information from the `rule_test` configuration
                 block. To do this, it overwrites wrong field values and checks that the values within the received
                 message after establishing a connection using the logtest AF_UNIX socket that uses TCP are the same
                 that the loaded fields from the 'cyware_conf.yaml' file.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configuration from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing
        - restart_cyware:
            type: fixture
            brief: Restart cyware, ossec.log and start a new monitor.
        - connect_to_sockets_function:
            type: fixture
            brief: Function scope version of 'connect_to_sockets' which connects to the specified sockets for the test.

    assertions:
        - Verify that a valid configuration is loaded.
        - Verify that wrong loaded configurations are fixed with limit values.
        - Verify that each message field received matches the loaded configuration fields.

    input_description: Five test cases are defined in the module. These include some configurations stored in
                       the 'cyware_conf.yaml'.

    expected_output:
        - 'Real message was: .*'
        - 'Expected value in enabled tag: .*. Value received: .*'
        - 'Expected value in threads tag: .*.  Value received: .*'
        - 'Expected value in max_sessions tag: .*.  Value received: .*'
        - 'Expected value in session_timeout tag: .*.  Value received: .*'

    tags:
        - settings
        - analysisd
    '''
    configuration = get_configuration['sections'][0]['elements']

    if 'invalid_threads_conf' in get_configuration['tags']:
        configuration[1]['threads']['value'] = '128'
    elif 'invalid_users_conf' in get_configuration['tags']:
        configuration[2]['max_sessions']['value'] = '500'
    elif 'invalid_timeout_conf' in get_configuration['tags']:
        configuration[3]['session_timeout']['value'] = '31536000'

    receiver_sockets[0].send(msg_get_config, True)
    msg_recived = receiver_sockets[0].receive().decode()

    matched = re.match(r'.*{"enabled":"(\S+)","threads":(\d+),"max_sessions":(\d+),"session_timeout":(\d+)}}',
                       msg_recived)
    assert matched is not None, f'Real message was: "{msg_recived}"'

    assert matched.group(1) == configuration[0]['enabled']['value'], f"""Expected value in enabled tag:
           '{configuration[0]['enabled']['value']}'. Value received: '{matched.group(1)}'"""

    assert matched.group(2) == configuration[1]['threads']['value'], f"""Expected value in threads tag:
           '{configuration[1]['threads']['value']}'. Value received: '{matched.group(2)}'"""

    assert matched.group(3) == configuration[2]['max_sessions']['value'], f"""Expected value in max_sessions tag:
           '{configuration[2]['max_sessions']['value']}'. Value received: '{matched.group(3)}'"""
    assert matched.group(4) == configuration[3]['session_timeout']['value'], f"""Expected value in session_timeout tag:
           '{configuration[3]['session_timeout']['value']}'. Value received: '{matched.group(4)}'"""
