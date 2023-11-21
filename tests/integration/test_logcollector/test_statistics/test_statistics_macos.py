'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the logcollector updates the 'cyware-logcollector.state'
       file when using the macOS unified logging system (ULS). Log data collection is the real-time
       process of making sense out of the records generated by servers or devices. This component can
       receive logs through text files or Windows event logs. It can also directly receive logs via
       remote syslog which is useful for firewalls and other such devices.

components:
    - logcollector

suite: statistics

targets:
    - agent

daemons:
    - cyware-logcollector

os_platform:
    - macos

os_version:
    - macOS Catalina
    - macOS Server

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/statistics-files/cyware-logcollector-state.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/internal-options.html#logcollector

tags:
    - logcollector_statistics
'''
import os
import pytest

from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools import LOGCOLLECTOR_STATISTICS_FILE
from cyware_testing.tools.file import read_json
from cyware_testing import logcollector

# Marks
pytestmark = [pytest.mark.darwin, pytest.mark.tier(level=1)]

# Configuration
logcollector_stats_file_tout = 30
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_statistics_macos.yaml')

parameters = [
    {'LOCATION': 'macos', 'LOG_FORMAT': 'macos'},
]

metadata = [
    {'location': 'macos', 'log_format': 'macos'}
]

# Configuration data
configurations = load_cyware_configurations(configurations_path, __name__, params=parameters, metadata=metadata)
configuration_ids = [f"{x['LOCATION']}_{x['LOG_FORMAT']}" for x in parameters]

local_internal_options = {'logcollector.state_interval': 1}

daemons_handler_configuration = {'daemons': ['cyware-logcollector', 'cyware-agentd', 'cyware-execd'],
                                 'ignore_errors': False}


@pytest.fixture(scope='module', params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_options_state_interval_no_file(configure_local_internal_options_module, get_configuration,
                                        configure_environment, daemons_handler_module):
    '''
    description: Check if the 'cyware-logcollector' daemon updates the statistic file 'cyware-logcollector.state'
                 when using the macOS unified logging system (ULS). For this purpose, the test will configure
                 a 'localfile' section using the macOS settings. Once the logcollector is started, it will check
                 if the 'cyware-logcollector.state' file has been created. Finally, the test will verify that the
                 'cyware-logcollector.state' has the 'macos' value in its 'location' tag of the 'global' and
                 'interval' sections.

    cyware_min_version: 4.2.0

    tier: 1

    parameters:
        - configure_local_internal_options_module:
            type: fixture
            brief: Set internal configuration for testing.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - daemons_handler_module:
            type: fixture
            brief: Handler of Cyware daemons.

    assertions:
        - Verify that the logcollector creates the 'cyware-logcollector.state' file.
        - Verify that the 'macos' value is in the 'location' tag in the 'global' and 'interval' sections
          of the 'cyware-logcollector.state' file.

    input_description: A configuration template (test_statistics_macos) is contained in an external YAML file
                       (cyware_statistics_macos.yaml). That template is combined with a test case defined in
                       the module. Those include configuration settings for the 'cyware-logcollector' daemon.

    expected_output:
        - The content of the 'cyware-logcollector.state' file.

    tags:
        - stats_file
    '''
    # Ensure cyware-logcollector.state is created
    logcollector.wait_statistics_file(timeout=logcollector_stats_file_tout)

    data = read_json(LOGCOLLECTOR_STATISTICS_FILE)

    global_files = data['global']['files']
    interval_files = data['interval']['files']

    assert list(filter(lambda global_file: global_file['location'] == 'macos', global_files))
    assert list(filter(lambda interval_file: interval_file['location'] == 'macos', interval_files))