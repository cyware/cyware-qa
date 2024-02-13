# Copyright (C) 2023-2024, KhulnaSoft Ltd.
# Created by Cyware, Inc. <info@khulnasoft.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2
import json
from setuptools import setup, find_packages
import os

package_data_list = [
    'data/agent.conf',
    'data/syscheck_event.json',
    'data/syscheck_event_windows.json',
    'data/mitre_event.json',
    'data/analysis_alert.json',
    'data/analysis_alert_windows.json',
    'data/state_integrity_analysis_schema.json',
    'data/gcp_event.json',
    'data/keepalives.txt',
    'data/rootcheck.txt',
    'data/syscollector.py',
    'data/winevt.py',
    'data/sslmanager.key',
    'data/sslmanager.cert',
    'tools/macos_log/log_generator.m',
    'qa_docs/schema.yaml',
    'qa_docs/VERSION.json',
    'qa_docs/dockerfiles/*',
    'qa_ctl/deployment/dockerfiles/*',
    'qa_ctl/deployment/dockerfiles/qa_ctl/*',
    'qa_ctl/deployment/vagrantfile_template.txt',
    'qa_ctl/provisioning/cyware_deployment/templates/preloaded_vars.conf.j2',
    'data/qactl_conf_validator_schema.json',
    'data/all_disabled_ossec.conf',
    'tools/migration_tool/delta_schema.json',
    'tools/migration_tool/CVE_JSON_5.0_bundled.json'
]

scripts_list = [
    'simulate-agents=cyware_testing.scripts.simulate_agents:main',
    'cyware-metrics=cyware_testing.scripts.cyware_metrics:main',
    'cyware-report=cyware_testing.scripts.cyware_report:main',
    'cyware-statistics=cyware_testing.scripts.cyware_statistics:main',
    'data-visualizer=cyware_testing.scripts.data_visualizations:main',
    'simulate-api-load=cyware_testing.scripts.simulate_api_load:main',
    'cyware-log-metrics=cyware_testing.scripts.cyware_log_metrics:main',
    'qa-docs=cyware_testing.scripts.qa_docs:main',
    'qa-ctl=cyware_testing.scripts.qa_ctl:main',
    'check-files=cyware_testing.scripts.check_files:main',
    'add-agents-client-keys=cyware_testing.scripts.add_agents_client_keys:main',
    'unsync-agents=cyware_testing.scripts.unsync_agents:main',
    'stress_results_comparator=cyware_testing.scripts.stress_results_comparator:main'
]


def get_files_from_directory(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


def get_version():
    script_path = os.path.dirname(__file__)
    rel_path = "../../version.json"
    abs_file_path = os.path.join(script_path, rel_path)
    f = open(abs_file_path)
    data = json.load(f)
    version = data['version']
    return version


package_data_list.extend(get_files_from_directory('cyware_testing/qa_docs/search_ui'))

setup(
    name='cyware_testing',
    version=get_version(),
    description='Cyware testing utilities to help programmers automate tests',
    url='https://github.com/cyware',
    author='Cyware',
    author_email='hello@cyware.khulnasoft.com',
    license='GPLv2',
    packages=find_packages(),
    package_data={'cyware_testing': package_data_list},
    entry_points={'console_scripts': scripts_list},
    include_package_data=True,
    zip_safe=False
)
