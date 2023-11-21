'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will check if the Cyware component (agent or manager) starts when
       the 'label' tag is set in the configuration, and the Cyware API returns the same values for
       the configured 'localfile' section.
       Log data collection is the real-time process of making sense out of the records generated by
       servers or devices. This component can receive logs through text files or Windows event logs.
       It can also directly receive logs via remote syslog which is useful for firewalls and
       other such devices.

components:
    - logcollector

suite: configuration

targets:
    - agent
    - manager

daemons:
    - cyware-logcollector
    - cyware-apid

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

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/log-data-collection/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html#label

tags:
    - logcollector_configuration
'''
import os
import sys
import pytest
import cyware_testing.api as api
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools import get_service
import cyware_testing.logcollector as logcollector


# Marks
pytestmark = pytest.mark.tier(level=0)

# Configuration
no_restart_windows_after_configuration_set = True
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
configurations_path = os.path.join(test_data_path, 'cyware_basic_configuration.yaml')

if sys.platform == 'win32':
    location = r'C:\TESTING\testfile.txt'
else:
    location = '/tmp/testing.txt'

cyware.khulnasoft.component = get_service()

parameters = [
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': '@source'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': 'agent.type'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': 'agent.location'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': 'agent.idgroup'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': 'group.groupnname'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': '109304'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': 'TestingTagNames'},
    {'LOCATION': f'{location}', 'LABEL': 'myapp', 'KEY': '?¿atag_tname'},
]
metadata = [
    {'location': f'{location}', 'label': 'myapp', 'key': '@source'},
    {'location': f'{location}', 'label': 'myapp', 'key': 'agent.type'},
    {'location': f'{location}', 'label': 'myapp', 'key': 'agent.location'},
    {'location': f'{location}', 'label': 'myapp', 'key': 'agent.idgroup'},
    {'location': f'{location}', 'label': 'myapp', 'key': 'group.groupnname'},
    {'location': f'{location}', 'label': 'myapp', 'key': '109304'},
    {'location': f'{location}', 'label': 'myapp', 'key': 'TestingTagNames'},
    {'location': f'{location}', 'label': 'myapp', 'key': '?¿atag_tname'}
]

configurations = load_cyware_configurations(configurations_path, __name__,
                                           params=parameters,
                                           metadata=metadata)
configuration_ids = [f"{x['location']}_{x['label']}_{x['key']}" for x in metadata]


# fixtures
@pytest.fixture(scope="module", params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


@pytest.mark.filterwarnings('ignore::urllib3.exceptions.InsecureRequestWarning')
def test_configuration_label(get_configuration, configure_environment, restart_logcollector):
    '''
    description: Check if the 'cyware-logcollector' daemon can monitor log files configured to use labels.
                 For this purpose, the test will configure the logcollector to use labels, setting them
                 in the label 'tag'. Once the logcollector has started, it will check if the 'analyzing'
                 event, indicating that the testing log file is being monitored, has been generated.
                 Finally, the test will verify that the Cyware API returns the same values for
                 the 'localfile' section that the configured one.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - restart_logcollector:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that the logcollector monitors files when using the 'label' tag.
        - Verify that the Cyware API returns the same values for the 'localfile' section as the configured one.

    input_description: A configuration template (test_basic_configuration_label) is contained in an external
                       YAML file (cyware_basic_configuration.yaml). That template is combined with different
                       test cases defined in the module. Those include configuration settings for
                       the 'cyware-logcollector' daemon.

    expected_output:
        - r'Analyzing file.*'

    tags:
        - invalid_settings
        - logs
    '''
    cfg = get_configuration['metadata']

    log_callback = logcollector.callback_analyzing_file(cfg['location'])
    cyware_log_monitor.start(timeout=5, callback=log_callback,
                            error_message=logcollector.GENERIC_CALLBACK_ERROR_ANALYZING_FILE)

    if cyware.khulnasoft.component == 'cyware-manager':
        real_configuration = dict((key, cfg[key]) for key in ['location'])
        real_configuration['label'] = {'key': cfg['key'], 'item': cfg['label']}
        api.wait_until_api_ready()
        api.compare_config_api_response([real_configuration], 'localfile')
