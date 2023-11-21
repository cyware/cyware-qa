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

from cyware_testing.logcollector import LOG_COLLECTOR_GLOBAL_TIMEOUT, callback_logcollector_started
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.file import read_json, write_json_file
from cyware_testing.tools.monitoring import wait_file
from os.path import dirname, join, exists, realpath
from tempfile import gettempdir
from time import sleep
from os import remove
if sys.platform != 'win32':
    from cyware_testing.tools import LOGCOLLECTOR_FILE_STATUS_PATH

# Marks
pytestmark = [pytest.mark.darwin, pytest.mark.tier(level=0)]

# Configuration
test_data_path = join(dirname(realpath(__file__)), 'data')
configurations_path = join(test_data_path, 'cyware_macos_file_status_when_no_macos.yaml')

dummy_file = join(gettempdir(), 'dummy_file.log')
parameters = [{'FILE_TO_MONITOR': dummy_file}]

# Configuration data
configurations = load_cyware_configurations(configurations_path, __name__, params=parameters)

daemons_handler_configuration = {'daemons': ['cyware-logcollector'],
                                 'ignore_errors': False}

# Time in seconds to update the file_status.json
file_status_update_time = 4

local_internal_options = {'logcollector.vcheck_files': file_status_update_time}

# Time to wait for file_status.json to be updated (the +8 is due to a delay added by the cyware-agentd daemmon)
wait_file_status_update_time = file_status_update_time + 8


# Fixtures
@pytest.fixture(scope='module')
def handle_files():
    """Create dummy file to be monitored by logcollector, after the test it is deleted."""
    with open(dummy_file, 'w') as f:
        pass

    yield

    remove(dummy_file) if exists(dummy_file) else None


@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


def test_macos_file_status_when_no_macos(restart_logcollector_required_daemons_package, truncate_log_file, handle_files,
                                         delete_file_status_json, configure_local_internal_options_module,
                                         get_configuration, configure_environment, file_monitoring,
                                         daemons_handler_module):
    '''
    description: Check if the 'cyware-logcollector' does not store and removes if exists, previous
                 macos-formatted localfile data in the 'file_status.json' file when the macOS localfile
                 section does not exist in the configuration. For this purpose, the test will create a
                 testing log file and configure a 'localfile' section to monitor it. Once the logcollector
                 is started, it will check if the 'file_status.json' file exists, if not, the test
                 will create it. Then it will verify that the 'macos' key is inside of that file, adding
                 the key if necessary. After this, it will wait for the update of the 'file_status.json'
                 file, and finally, the test will verify that the macOS key is not inside it since
                 the localfile related section does not exist in the main configuration file.

    cyware_min_version: 4.2.0

    tier: 0

    parameters:
        - restart_logcollector_required_daemons_package:
            type: fixture
            brief: Restart the 'cyware-agentd', 'cyware-logcollector', and 'cyware-modulesd' daemons.
        - truncate_log_file:
            type: fixture
            brief: Clear the 'ossec.log' file.
        - handle_files:
            type: fixture
            brief: Create a dummy file to be monitored by logcollector.
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
        - Verify that the logcollector starts to monitor a log file.
        - Verify that the logcollector removes the 'macos' key from the 'file_status.json'
          when no localfile is configured with macOS settings.

    input_description: A configuration template (test_macos_file_status_when_no_macos) is contained in an external
                       YAML file (cyware_macos_file_status_when_no_macos.yaml). That template is combined with
                       a test case defined in the module. That include configuration settings
                       for the 'cyware-logcollector' daemon.

    expected_output:
        - r'Started'

    tags:
        - logs
    '''
    file_status_json = {}

    log_monitor.start(timeout=LOG_COLLECTOR_GLOBAL_TIMEOUT,
                      callback=callback_logcollector_started(),
                      error_message="Logcollector did not start")

    # Check if json_status contains 'macos' data and if not insert it
    if exists(LOGCOLLECTOR_FILE_STATUS_PATH):
        file_status_json = read_json(LOGCOLLECTOR_FILE_STATUS_PATH)
        if 'macos' not in file_status_json:
            file_status_json['macos'] = {}
            file_status_json['macos']['timestamp'] = '2021-10-22 04:59:46.796446-0700'
            file_status_json['macos']['settings'] = 'message CONTAINS "testing"'
            write_json_file(LOGCOLLECTOR_FILE_STATUS_PATH, file_status_json)
    else:
        # If the file does not exist, then is created and then macos data is added
        with open(LOGCOLLECTOR_FILE_STATUS_PATH, 'w') as f:
            pass
        file_status_json['macos'] = {}
        file_status_json['macos']['timestamp'] = '2021-10-22 04:59:46.796446-0700'
        file_status_json['macos']['settings'] = 'message CONTAINS "testing"'
        write_json_file(LOGCOLLECTOR_FILE_STATUS_PATH, file_status_json)

    # Waits for file_status.json to be created, with a timeout about the time needed to update the file
    wait_file(LOGCOLLECTOR_FILE_STATUS_PATH, LOG_COLLECTOR_GLOBAL_TIMEOUT)

    # Waits about the time needed to update the file status
    sleep(wait_file_status_update_time)

    file_status_json = read_json(LOGCOLLECTOR_FILE_STATUS_PATH)

    # Check if json has a structure
    if 'macos' in file_status_json:
        assert False, 'Error, macos should not be present on the status file'