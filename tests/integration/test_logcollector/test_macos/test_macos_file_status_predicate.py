'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: The 'cyware-logcollector' daemon monitors configured files and commands for new log messages.
       Specifically, these tests will verify that the logcollector does not add to the 'file_status.json'
       file event-related data when the predicate used in the 'query' tag is invalid. Log data collection
       is the real-time process of making sense out of the records generated by servers or devices.
       This component can receive logs through text files or Windows event logs. It can also directly
       receive logs via remote syslog which is useful for firewalls and other such devices.

components:
    - logcollector

suite: macos

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
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/localfile.html#query

tags:
    - logcollector_macos
'''
import pytest
import sys
import time

from cyware_testing.logcollector import (LOG_COLLECTOR_GLOBAL_TIMEOUT,
                                        callback_log_macos_stream_exit,
                                        callback_log_bad_predicate)
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.monitoring import wait_file
from cyware_testing.tools.file import read_json
from os.path import dirname, join, realpath
if sys.platform != 'win32':
    from cyware_testing.tools import LOGCOLLECTOR_FILE_STATUS_PATH

# Marks
pytestmark = [pytest.mark.darwin, pytest.mark.tier(level=0)]

# Configuration
test_data_path = join(dirname(realpath(__file__)), 'data')
configurations_path = join(test_data_path, 'cyware_macos_file_status_predicate.yaml')

parameters = [{'ONLY_FUTURE_EVENTS': 'yes'}, {'ONLY_FUTURE_EVENTS': 'no'}]
metadata = [{'only-future-events': 'yes'}, {'only-future-events': 'no'}]

daemons_handler_configuration = {'daemons': ['cyware-logcollector'], 'ignore_errors': False}

# Configuration data
configurations = load_cyware_configurations(configurations_path, __name__, params=parameters, metadata=metadata)
configuration_ids = [f"only_future_events_{x['ONLY_FUTURE_EVENTS']}" for x in parameters]

# Time in seconds to update the file_status.json
file_status_update_time = 4

local_internal_options = {'logcollector.vcheck_files': file_status_update_time}


# Fixtures
@pytest.fixture(scope='module', params=configurations, ids=configuration_ids)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_macos_file_status_predicate(restart_logcollector_required_daemons_package, truncate_log_file,
                                     delete_file_status_json,
                                     configure_local_internal_options_module,
                                     get_configuration, configure_environment,
                                     file_monitoring, daemons_handler_module):
    """
    description: Check if the 'cyware-logcollector' does not update the 'file_status.json' file from logging
                 events when using an invalid predicate in the 'query' tag of the 'localfile' section.
                 The agent uses a dummy localfile (/Library/Ossec/logs/active-responses.log) which triggers
                 the creation of the 'file_status.json' file.
                 For this purpose, the test will configure a 'localfile' section using the macOS settings
                 but using an invalid predicate. Once the logcollector is started, it will verify that
                 event errors are generated, indicating that an invalid setting has been detected. After
                 this, the test will check if the 'file_status.json' file has been created, and finally,
                 it will verify that the 'macos' key is not inside it since the predicate used is invalid.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - restart_logcollector_required_daemons_package:
            type: fixture
            brief: Restart the 'cyware-agentd', 'cyware-logcollector', and 'cyware-modulesd' daemons.
        - truncate_log_file:
            type: fixture
            brief: Clear the 'ossec.log' file.
        - delete_file_status_json:
            type: fixture
            brief: Delete the 'file_status.json' file from logcollector.
        - configure_local_internal_options_module:
            type: fixture
            brief: Set internal configuration for testing.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
        - daemons_handler_module:
            type: fixture
            brief: Handler of Cyware daemons.

    assertions:
        - Verify that the logcollector generates error events when it detects an invalid predicate.
        - Verify that the logcollector generates the 'file_status.json' file without the 'macos' key.

    input_description: A configuration template (test_macos_file_status_predicate) is contained in an external
                       YAML file (cyware_macos_file_status_predicate.yaml). That template is combined with
                       two test cases defined in the module. Those include configuration settings
                       for the 'cyware-logcollector' daemon.

    expected_output:
        - r'Execution error .*'
        - r"macOS 'log stream' process exited"

    tags:
        - logs
    """
    time.sleep(file_status_update_time)
    log_monitor.start(timeout=LOG_COLLECTOR_GLOBAL_TIMEOUT,
                      callback=callback_log_bad_predicate(),
                      error_message='Expected log that matches the regex ".*Execution error \'log:" could not be found')

    log_monitor.start(timeout=LOG_COLLECTOR_GLOBAL_TIMEOUT,
                      callback=callback_log_macos_stream_exit(),
                      error_message='Expected log that matches the regex '
                                    '".*macOS \'log stream\' process exited, pid:" could not be found')

    # Waiting for file_status.json to be created, with a timeout about the time needed to update the file
    wait_file(LOGCOLLECTOR_FILE_STATUS_PATH, LOG_COLLECTOR_GLOBAL_TIMEOUT)

    file_status_json = read_json(LOGCOLLECTOR_FILE_STATUS_PATH)

    # Check if json has a structure
    if 'macos' in file_status_json:
        assert False, 'Error, "macos" key should not be present on the status file'
