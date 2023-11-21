'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.
           Created by Cyware, Inc. <info@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-remoted' program is the server side daemon that communicates with the agents.
       Specifically, this test will check that 'cyware-remoted' doesn't start and produces an error
       message when 'denied-ips' values are invalid.

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
from cyware_testing.tools.monitoring import REMOTED_DETECTOR_PREFIX
import cyware_testing.generic_callbacks as gc
from cyware_testing.tools import CYWARE_CONF_RELATIVE

# Marks
pytestmark = [pytest.mark.server, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

parameters = [
    {'ALLOWED': '127.0.0.0', 'DENIED': '192.168.1.1.1'},
    {'ALLOWED': '127.0.0.0', 'DENIED': 'Testing'},
    {'ALLOWED': '127.0.0.0', 'DENIED': '192.168.1.1/7890'},
    {'ALLOWED': '::1', 'DENIED': 'ec97:6bcc:8675:20e8:1c27:da5a:fdbf:fd3f:1c27'},
    {'ALLOWED': '::1', 'DENIED': 'ec97:6bcc:8675:20e8'},
    {'ALLOWED': '::1', 'DENIED': 'ec97::8675::20e8'},
    {'ALLOWED': '::1', 'DENIED': 'Testing'},
    {'ALLOWED': '::1', 'DENIED': 'ec97:6bcc:8675:20e8:1c27:da5a:fdbf:fd3f/512'},
    {'ALLOWED': '::1', 'DENIED': '::fd3f/512'}
]

metadata = [
    {'allowed-ips': '127.0.0.0', 'denied-ips': '192.168.1.1.1'},
    {'allowed-ips': '127.0.0.0', 'denied-ips': 'Testing'},
    {'allowed-ips': '127.0.0.0', 'denied-ips': '192.168.1.1/7890'},
    {'allowed-ips': '::1', 'denied-ips': 'ec97:6bcc:8675:20e8:1c27:da5a:fdbf:fd3f:1c27'},
    {'allowed-ips': '::1', 'denied-ips': 'ec97:6bcc:8675:20e8'},
    {'allowed-ips': '::1', 'denied-ips': 'ec97::8675::20e8'},
    {'allowed-ips': '::1', 'denied-ips': 'Testing'},
    {'allowed-ips': '::1', 'denied-ips': 'ec97:6bcc:8675:20e8:1c27:da5a:fdbf:fd3f/512'},
    {'allowed-ips': '::1', 'denied-ips': '::fd3f/512'}
]

configurations = load_cyware_configurations(configurations_path, "test_basic_configuration_allowed_denied_ips",
                                           params=parameters, metadata=metadata)
configuration_ids = [f"{x['ALLOWED']}_{x['DENIED']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_denied_ips_syslog_invalid(get_configuration, configure_environment, restart_remoted):
    '''
    description: Check that 'cyware-remoted' fails when 'denied-ips' has invalid values.
                 For this purpose, it uses the configuration from test cases and check if the different errors are
                 logged correctly.
    
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
        - Verify that the warning is logged correctly in ossec.log when receives an invalid ip.
        - Verify that the error is logged correctly in ossec.log when receives an invalid ip.
        - Verify that the critical error is logged correctly in ossec.log when receives an invalid ip.
    
    input_description: A configuration template (test_basic_configuration_allowed_denied_ips) is contained in an
                       external YAML file, (cyware_basic_configuration.yaml). That template is combined with different
                       test cases defined in the module. Those include configuration settings for the 'cyware-remoted'
                       daemon and agents info.
    
    expected_output:
        - r'Started <pid>: .* Listening on port .*'
        - The expected error output has not been produced.
        - r'ERROR: .* Invalid ip address:.*'
        - r'(ERROR|CRITICAL): .* Configuration error at '.*'
    
    tags:
        - remoted
    '''
    cfg = get_configuration['metadata']

    log_callback = remote.callback_error_invalid_ip(cfg['denied-ips'])
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")

    log_callback = gc.callback_error_in_configuration('ERROR', prefix=REMOTED_DETECTOR_PREFIX,
                                                      conf_path=CYWARE_CONF_RELATIVE)
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")

    log_callback = gc.callback_error_in_configuration('CRITICAL', prefix=REMOTED_DETECTOR_PREFIX,
                                                      conf_path=CYWARE_CONF_RELATIVE)
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message="The expected error output has not been produced")
