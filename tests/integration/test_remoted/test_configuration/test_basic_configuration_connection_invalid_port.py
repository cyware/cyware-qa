'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.
           Created by Cyware, Inc. <info@khulnasoft.com>.
           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-remoted' program is the server side daemon that communicates with the agents.
       Specifically, this test will check that the expected error message is produced
       when invalid 'port' values are used in the configuration.

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

import cyware_testing.generic_callbacks as gc
import cyware_testing.remote as remote
from cyware_testing.tools.monitoring import REMOTED_DETECTOR_PREFIX
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools import CYWARE_CONF_RELATIVE

# Marks
pytestmark = [pytest.mark.server, pytest.mark.tier(level=0)]

# Configuration
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

parameters = [
    {'PROTOCOL': 'TCP', 'CONNECTION': 'secure', 'PORT': '99999'}
]
metadata = [
    {'protocol': 'TCP', 'connection': 'secure', 'port': '99999'}
]

configurations = load_cyware_configurations(configurations_path, "test_basic_configuration_connection",
                                           params=parameters, metadata=metadata)
configuration_ids = [f"{x['PROTOCOL']}_{x['CONNECTION']}_{x['PORT']}" for x in parameters]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_invalid_port(get_configuration, configure_environment, restart_remoted):
    '''
    description: Check if 'cyware-remoted' fails using invalid 'port' values and shows the expected error message
                 to inform about it. For this purpose, the test will set a configuration from the module test cases and
                 check if is correct using a FileMonitor catching the errors.
    
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
        - Verify that the agent has no 'port' invalid value.
        - Verify that remoted logs an error in ossec.log when it had to.
        - Verify that remoted logs a critical error in ossec.log when it had to.
    
    input_description: A configuration template (test_basic_configuration_connection) is contained in an external YAML
                       file, (cyware_basic_configuration.yaml). That template is combined with different test cases
                       defined in the module. Those include configuration settings for the 'cyware-remoted' daemon and
                       agents info.
    
    expected_output:
        - The expected error output has not been produced
        - r'.* Invalid value for element .*.'
        - r'.* Configuration error at .*'
    
    tags:
        - simulator
        - remoted
    '''
    cfg = get_configuration['metadata']

    log_callback = remote.callback_error_invalid_port(cfg['port'])
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
