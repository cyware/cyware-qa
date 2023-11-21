'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.
           Created by Cyware, Inc. <info@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-remoted' program is the server side daemon that communicates with the agents.
       Specifically, this test will check that remoted fails when 'local_ip' is configured with
       an invalid value, searching the error message produced.

components:
    - remoted

suite: configuration

targets:
    - manager

daemons:
    - cyware-remoted

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
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/daemons/cyware-remoted.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/remote.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/agents/agent-life-cycle.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/agent-key-polling.html

tags:
    - remoted
'''
import os
import pytest

import cyware_testing.remote as remote
from cyware_testing.tools.configuration import load_cyware_configurations

# Marks
pytestmark = [pytest.mark.server, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

# Set invalid local_ip configuration
parameters = [
    {'LOCAL_IP': '9.9.9.9', 'IPV6': 'no'},
    {'LOCAL_IP': '1.1.1.1', 'IPV6': 'no'},
    {'LOCAL_IP': '::ffff:909:909', 'IPV6': 'yes'},
    {'LOCAL_IP': '::ffff:101:101', 'IPV6': 'yes'}
]
metadata = [
    {'local_ip': '9.9.9.9', 'ipv6': 'no'},
    {'local_ip': '1.1.1.1', 'ipv6': 'no'},
    {'local_ip': '::ffff:909:909', 'ipv6': 'yes'},
    {'local_ip': '::ffff:101:101', 'ipv6': 'yes'}
]

configurations = load_cyware_configurations(configurations_path, "test_basic_configuration_local_ip", params=parameters,
                                           metadata=metadata)

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

configuration_ids = [f"{x['LOCAL_IP']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_local_ip_invalid(get_configuration, configure_environment, restart_remoted):
    '''
    description: Check if 'cyware-remoted' fails when 'local_ip' is configured with invalid values.
                 For this purpose, it uses the configuration from test cases and monitor the logs
                 to find the error message produced.
    
    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing. Restart Cyware is needed for applying the configuration.
        - restart_remoted:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.
    
    assertions:
        - Verify that remoted starts correctly.
        - Verify that a critical error is created when invalid local ip value is provided.
    
    input_description: A configuration template (test_basic_configuration_ipv6) is contained in an external YAML
                       file, (cyware_basic_configuration.yaml). That template is combined with different test cases
                       defined in the module. Those include configuration settings for the 'cyware-remoted' daemon and
                       agents info.
    
    expected_output:
        - r'Started <pid>: .* Listening on port .*'
        - r'API query '{protocol}://{host}:{port}/manager/configuration?section=remote' doesn't match the 
          introduced configuration on ossec.conf.'
        - The expected error output has not been produced.
        - r'CRITICAL: .* Unable to Bind port '1514' due to .* Cannot assign requested address .*'
    
    tags:
        - simulator
    '''
    log_callback = remote.callback_error_bind_port()
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")
