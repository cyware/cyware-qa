import os
import sys
from tempfile import gettempdir
from time import sleep

from cyware_testing.qa_ctl.provisioning.ansible import read_ansible_instance, remove_known_host
from cyware_testing.qa_ctl.provisioning.ansible.ansible_inventory import AnsibleInventory
from cyware_testing.qa_ctl.provisioning.cyware_deployment.cyware_local_package import CywareLocalPackage
from cyware_testing.qa_ctl.provisioning.cyware_deployment.cyware_s3_package import CywareS3Package
from cyware_testing.qa_ctl.provisioning.cyware_deployment.cyware_sources import CywareSources
from cyware_testing.qa_ctl.provisioning.cyware_deployment.agent_deployment import AgentDeployment
from cyware_testing.qa_ctl.provisioning.cyware_deployment.manager_deployment import ManagerDeployment
from cyware_testing.qa_ctl.provisioning.ansible.ansible_runner import AnsibleRunner
from cyware_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from cyware_testing.qa_ctl.provisioning.qa_framework.qa_framework import QAFramework
from cyware_testing.tools.thread_executor import ThreadExecutor
from cyware_testing.qa_ctl import QACTL_LOGGER
from cyware_testing.tools.logging import Logging
from cyware_testing.tools.time import get_current_timestamp
from cyware_testing.tools import file
from cyware_testing.qa_ctl.provisioning.local_actions import qa_ctl_docker_run


class QAProvisioning():
    """Class to control different options and instances to provisioning with Cyware and QA Framework.

    Args:
        provision_info (dict): Dict with all the info needed coming from config file.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.

    Attributes:
        provision_info (dict): Dict with all the info needed coming from config file.
        instances_list (list): List with every instance (each host) needed to build the ansible inventory.
        group_dict (dict): Dict with groups and every host belonging to them.
        host_list (list): List with every host given in config file.
        inventory_file_path (string): Path of the inventory file generated.
        cyware_installation_paths (dict): Dict indicating the Cyware installation paths for every host.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
    """

    LOGGER = Logging.get_logger(QACTL_LOGGER)

    def __init__(self, provision_info, qa_ctl_configuration):
        self.provision_info = provision_info
        self.instances_list = []
        self.group_dict = {}
        self.host_list = []
        self.inventory_file_path = None
        self.cyware_installation_paths = {}
        self.qa_ctl_configuration = qa_ctl_configuration

        self.__process_inventory_data()

    def __process_inventory_data(self):
        """Process config file info to generate the ansible inventory file."""
        QAProvisioning.LOGGER.debug('Processing inventory data from provisioning hosts info')

        for root_key, root_value in self.provision_info.items():
            if root_key == 'hosts':
                for _, host_value in root_value.items():
                    for module_key, module_value in host_value.items():
                        if module_key == 'host_info':
                            current_host = module_value['host']

                            # Remove the host IP from known host file to avoid the SSH key fingerprint error
                            remove_known_host(current_host, QAProvisioning.LOGGER)

                            if current_host:
                                self.instances_list.append(read_ansible_instance(module_value))
            elif root_key == 'groups':
                self.group_dict.update(self.provision_info[root_key])

        inventory_instance = AnsibleInventory(ansible_instances=self.instances_list,
                                              ansible_groups=self.group_dict)
        self.inventory_file_path = inventory_instance.inventory_file_path
        QAProvisioning.LOGGER.debug('The inventory data from provisioning hosts info has been processed successfully')

    def __process_config_data(self, host_provision_info):
        """Process config file info to generate all the tasks needed for deploy Cyware

        Args:
            host_provision_info (dict): Dicionary with host provisioning info
        """
        current_host = host_provision_info['host_info']['host']

        if 'cyware_deployment' in host_provision_info:
            deploy_info = host_provision_info['cyware_deployment']
            health_check = False if 'health_check' not in host_provision_info['cyware_deployment'] \
                else host_provision_info['cyware_deployment']['health_check']
            install_target = None if 'target' not in deploy_info else deploy_info['target']
            install_type = None if 'type' not in deploy_info else deploy_info['type']
            installation_files_path = None if 'installation_files_path' not in deploy_info \
                else deploy_info['installation_files_path']
            cyware_install_path = '/var/ossec' if 'cyware_install_path' not in deploy_info else \
                deploy_info['cyware_install_path']
            cyware_branch = 'master' if 'cyware_branch' not in deploy_info else deploy_info['cyware_branch']
            s3_package_url = None if 's3_package_url' not in deploy_info else deploy_info['s3_package_url']
            system = None if 'version' not in deploy_info else deploy_info['system']
            version = None if 'version' not in deploy_info else deploy_info['version']
            repository = None if 'repository' not in deploy_info else deploy_info['repository']
            revision = None if 'revision' not in deploy_info else deploy_info['revision']
            local_package_path = None if 'local_package_path' not in deploy_info else deploy_info['local_package_path']
            manager_ip = None if 'manager_ip' not in deploy_info else deploy_info['manager_ip']
            ansible_admin_user = 'vagrant' if 'ansible_admin_user' not in host_provision_info['host_info'] else \
                host_provision_info['host_info']['ansible_admin_user']

            installation_files_parameters = {'cyware_target': install_target}

            if installation_files_path:
                installation_files_parameters['installation_files_path'] = installation_files_path

            installation_files_parameters['qa_ctl_configuration'] = self.qa_ctl_configuration

            if install_type == 'sources':
                installation_files_parameters['cyware_branch'] = cyware_branch
                installation_files_parameters['cyware_install_path'] = cyware_install_path
                installation_instance = CywareSources(**installation_files_parameters)

            if install_type == 'package':
                if s3_package_url is None and local_package_path is None:
                    installation_files_parameters['system'] = system
                    installation_files_parameters['version'] = version
                    installation_files_parameters['revision'] = revision
                    installation_files_parameters['repository'] = repository
                    installation_instance = CywareS3Package(**installation_files_parameters)
                    remote_files_path = installation_instance.download_installation_files(self.inventory_file_path,
                                                                                          hosts=current_host)
                elif s3_package_url is None and local_package_path is not None:
                    installation_files_parameters['local_package_path'] = local_package_path
                    installation_instance = CywareLocalPackage(**installation_files_parameters)
                    remote_files_path = installation_instance.download_installation_files(self.inventory_file_path,
                                                                                          hosts=current_host)
                else:
                    installation_files_parameters['s3_package_url'] = s3_package_url
                    installation_instance = CywareS3Package(**installation_files_parameters)
                    remote_files_path = installation_instance.download_installation_files(self.inventory_file_path,
                                                                                          hosts=current_host)

            if install_target == 'agent':
                deployment_instance = AgentDeployment(remote_files_path,
                                                      inventory_file_path=self.inventory_file_path,
                                                      install_mode=install_type,
                                                      hosts=current_host,
                                                      server_ip=manager_ip,
                                                      install_dir_path=cyware_install_path,
                                                      qa_ctl_configuration=self.qa_ctl_configuration,
                                                      ansible_admin_user=ansible_admin_user)
            if install_target == 'manager':
                deployment_instance = ManagerDeployment(remote_files_path,
                                                        inventory_file_path=self.inventory_file_path,
                                                        install_mode=install_type,
                                                        hosts=current_host,
                                                        install_dir_path=cyware_install_path,
                                                        qa_ctl_configuration=self.qa_ctl_configuration,
                                                        ansible_admin_user=ansible_admin_user)
            deployment_instance.install()

            if health_check:
                # Wait for Cyware initialization before health_check
                health_check_sleep_time = 30
                QAProvisioning.LOGGER.info(f"Performing a Cyware installation healthcheck in {current_host} host")
                sleep(health_check_sleep_time)
                deployment_instance.health_check()

            self.cyware_installation_paths[deployment_instance.hosts] = deployment_instance.install_dir_path

        if 'qa_framework' in host_provision_info:
            qa_framework_info = host_provision_info['qa_framework']
            cyware_qa_branch = 'master' if 'cyware_qa_branch' not in qa_framework_info \
                else qa_framework_info['cyware_qa_branch']

            QAProvisioning.LOGGER.info(f"Provisioning the {current_host} host with the Cyware QA framework using "
                                       f"{cyware_qa_branch} branch.")
            qa_instance = QAFramework(qa_branch=cyware_qa_branch, workdir=qa_framework_info['qa_workdir'],
                                      ansible_output=self.qa_ctl_configuration.ansible_output)
            qa_instance.download_qa_repository(inventory_file_path=self.inventory_file_path, hosts=current_host)
            qa_instance.install_dependencies(inventory_file_path=self.inventory_file_path, hosts=current_host)
            qa_instance.install_framework(inventory_file_path=self.inventory_file_path, hosts=current_host)

    def __check_hosts_connection(self, hosts='all'):
        """Check that all hosts are reachable via SSH connection

        Args:
            hosts (str): Hosts to check.
        """
        QAProvisioning.LOGGER.info('Checking hosts SSH connection')
        wait_for_connection_unix = AnsibleTask({
            'name': 'Waiting for SSH hosts connection are reachable (Unix)',
            'wait_for_connection': {'delay': 5, 'timeout': 60},
            'when': 'ansible_system != "Win32NT"'
        })

        wait_for_connection_windows = AnsibleTask({
            'name': 'Waiting for SSH hosts connection are reachable (Windows)',
            'win_wait_for': {'delay': 5, 'timeout': 60},
            'when': 'ansible_system == "Win32NT"'
        })

        playbook_parameters = {'hosts': hosts, 'gather_facts': True, 'tasks_list': [wait_for_connection_unix,
                                                                                    wait_for_connection_windows]}
        AnsibleRunner.run_ephemeral_tasks(self.inventory_file_path, playbook_parameters,
                                          output=self.qa_ctl_configuration.ansible_output)
        QAProvisioning.LOGGER.info('Hosts connection OK. The instances are accessible via ssh')

    def run(self):
        """Provision all hosts in a parallel way"""
        # If Windows, then run a Linux docker container to run provisioning stage with qa-ctl provision
        if sys.platform == 'win32':
            tmp_config_file_name = f"config_{get_current_timestamp()}.yaml"
            tmp_config_file = os.path.join(gettempdir(), 'cyware_qa_ctl', tmp_config_file_name)

            # Write a custom configuration file with only provision section
            file.write_yaml_file(tmp_config_file, {'provision': self.provision_info})

            try:
                qa_ctl_docker_run(tmp_config_file_name, self.qa_ctl_configuration.qa_ctl_launcher_branch,
                                  self.qa_ctl_configuration.debug_level, topic='provisioning the instances')
            finally:
                file.remove_file(tmp_config_file)
        else:
            self.__check_hosts_connection()
            provision_threads = [ThreadExecutor(self.__process_config_data,
                                                parameters={'host_provision_info': host_value})
                                 for _, host_value in self.provision_info['hosts'].items()]
            QAProvisioning.LOGGER.info(f"Provisioning {len(provision_threads)} instances")

            for runner_thread in provision_threads:
                runner_thread.start()

            for runner_thread in provision_threads:
                runner_thread.join()

            QAProvisioning.LOGGER.info('The instances have been provisioned successfully')

    def destroy(self):
        """Destroy all the temporary files created by an instance of this object"""
        if os.path.exists(self.inventory_file_path) and sys.platform != 'win32':
            os.remove(self.inventory_file_path)
