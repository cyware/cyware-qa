'''
copyright: Copyright (C) 2015-2022, KhulnaSoft Ltd.

           Created by Cyware, Inc. <info@khulnasoft.com>.

           This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

type: integration

brief: File Integrity Monitoring (FIM) system watches selected files and triggering alerts when
       these files are modified. Specifically, these tests will check if FIM limits the size of
       'diff' information to generate from the file monitored to the default value of
       the 'diff_size_limit' attribute when the 'report_changes' option is enabled.
       The FIM capability is managed by the 'cyware-syscheckd' daemon, which checks configured
       files for changes to the checksums, permissions, and ownership.

components:
    - fim

suite: files_report_changes

targets:
    - agent
    - manager

daemons:
    - cyware-syscheckd

os_platform:
    - linux
    - windows
    - macos
    - solaris

os_version:
    - Arch Linux
    - Amazon Linux 2
    - Amazon Linux 1
    - CentOS 8
    - CentOS 7
    - Debian Buster
    - Red Hat 8
    - Solaris 10
    - Solaris 11
    - macOS Catalina
    - macOS Server
    - Ubuntu Focal
    - Ubuntu Bionic
    - Windows 10
    - Windows Server 2019
    - Windows Server 2016

references:
    - https://documentation.cyware.khulnasoft.com/current/user-manual/capabilities/file-integrity/index.html
    - https://documentation.cyware.khulnasoft.com/current/user-manual/reference/ossec-conf/syscheck.html#directories

pytest_args:
    - fim_mode:
        realtime: Enable real-time monitoring on Linux (using the 'inotify' system calls) and Windows systems.
        whodata: Implies real-time monitoring but adding the 'who-data' information.
        scheduled: Implies scheduled scan
    - tier:
        0: Only level 0 tests are performed, they check basic functionalities and are quick to perform.
        1: Only level 1 tests are performed, they check functionalities of medium complexity.
        2: Only level 2 tests are performed, they check advanced functionalities and are slow to perform.

tags:
    - fim_report_changes
'''
import os

import pytest
from cyware_testing import global_parameters, DATA, LOG_FILE_PATH
from cyware_testing.tools import PREFIX
from cyware_testing.tools.configuration import load_cyware_configurations
from cyware_testing.tools.monitoring import FileMonitor, generate_monitoring_callback
from cyware_testing.modules.fim import DIFF_DEFAULT_LIMIT_VALUE, REPORT_CHANGES, TEST_DIR_1, TEST_DIRECTORIES
from cyware_testing.modules.fim.event_monitor import (CB_MAXIMUM_FILE_SIZE, ERR_MSG_MAXIMUM_FILE_SIZE,
                                                     ERR_MSG_WRONG_VALUE_MAXIMUM_FILE_SIZE)
from cyware_testing.modules.fim.utils import generate_params
from cyware_testing.modules.fim import FIM_DEFAULT_LOCAL_INTERNAL_OPTIONS as local_internal_options
# Marks

pytestmark = [pytest.mark.tier(level=1)]

# Variables

cyware_log_monitor = FileMonitor(LOG_FILE_PATH)
test_directory = os.path.join(PREFIX, TEST_DIR_1)
test_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), DATA)
configurations_path = os.path.join(test_data_path, 'cyware_conf_diff.yaml')


# Configurations

parameters, metadata = generate_params(extra_params={REPORT_CHANGES.upper(): {REPORT_CHANGES: 'yes'},
                                                     TEST_DIRECTORIES: test_directory})

configurations = load_cyware_configurations(configurations_path, __name__, params=parameters, metadata=metadata)

# Fixtures


@pytest.fixture(scope='module', params=configurations)
def get_configuration(request):
    """Get configurations from the module."""
    return request.param


# Tests

def test_diff_size_limit_default(configure_local_internal_options_module, get_configuration, configure_environment,
                                 restart_syscheckd):
    '''
    description: Check if the 'cyware-syscheckd' daemon limits the size of 'diff' information to generate from
                 the default value of the 'diff_size_limit' attribute. For this purpose, the test will monitor
                 a directory and, once the FIM is started, it will wait for the FIM event related to the maximum
                 file size to generate 'diff' information. Finally, the test will verify that the value gotten
                 from that FIM event corresponds with the default value of the 'diff_size_limit' attribute (50MB).

    cyware_min_version: 4.6.0

    tier: 1

    parameters:
        - configure_local_internal_options_module:
            type: fixture
            brief: Configure the local internal options file.
        - get_configuration:
            type: fixture
            brief: Get configurations from the module.
        - configure_environment:
            type: fixture
            brief: Configure a custom environment for testing.
        - restart_syscheckd:
            type: fixture
            brief: Clear the 'ossec.log' file and start a new monitor.

    assertions:
        - Verify that an FIM event is generated indicating the size limit of 'diff' information to generate
          with the default value of the 'diff_size_limit' attribute (50MB).

    input_description: A test case (ossec_conf_diff_size_limit) is contained in external YAML
                       file (cyware_conf_diff.yaml) which includes configuration settings for
                       the 'cyware-syscheckd' daemon and, these are combined with the
                       testing directory to be monitored defined in the module.

    expected_output:
        - r'.*Maximum file size limit to generate diff information configured to'

    tags:
        - diff
        - scheduled
        - realtime
        - who_data
    '''

    diff_size_value = cyware_log_monitor.start(timeout=global_parameters.default_timeout,
                                              callback=generate_monitoring_callback(CB_MAXIMUM_FILE_SIZE),
                                              error_message=ERR_MSG_MAXIMUM_FILE_SIZE).result()

    assert diff_size_value == str(DIFF_DEFAULT_LIMIT_VALUE), ERR_MSG_WRONG_VALUE_MAXIMUM_FILE_SIZE
