
import os
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import gettempdir

from cyware_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from cyware_testing.qa_ctl.provisioning.ansible.ansible_runner import AnsibleRunner
from cyware_testing.qa_ctl import QACTL_LOGGER
from cyware_testing.tools.logging import Logging


class CywareDeployment(ABC):
    """Deploy Cyware with all the elements needed, set from the configuration file

    Args:
        installation_files_path (string): Path where is located the Cyware instalation files.
        configuration (CywareConfiguration): Configuration object to be set.
        inventory_file_path (string): Path where is located the ansible inventory file.
        install_mode (string): 'package' or 'sources' installation mode.
        install_dir_path (string): Path where the Cyware installation will be stored.
        hosts (string): Group of hosts to be deployed.
        server_ip (string): Manager IP to let agent get autoenrollment.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        ansible_admin_user (str): User to launch the ansible task with admin privileges (ansible_become_user)

    Attributes:
        installation_files_path (string): Path where is located the Cyware instalation files.
        configuration (CywareConfiguration): Configuration object to be set.
        inventory_file_path (string): Path where is located the ansible inventory file.
        install_mode (string): 'package' or 'sources' installation mode.
        install_dir_path (string): Path where the Cyware installation will be stored.
        hosts (string): Group of hosts to be deployed.
        server_ip (string): Manager IP to let agent get autoenrollment.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        ansible_admin_user (str): User to launch the ansible task with admin privileges (ansible_become_user)
    """
    LOGGER = Logging.get_logger(QACTL_LOGGER)

    def __init__(self, installation_files_path, inventory_file_path, qa_ctl_configuration, configuration=None,
                 install_mode='package', install_dir_path='/var/ossec', hosts='all', server_ip=None,
                 ansible_admin_user='vagrant'):

        self.installation_files_path = installation_files_path
        self.configuration = configuration
        self.inventory_file_path = inventory_file_path
        self.install_mode = install_mode
        self.install_dir_path = install_dir_path
        self.hosts = hosts
        self.server_ip = server_ip
        self.qa_ctl_configuration = qa_ctl_configuration
        self.ansible_admin_user = ansible_admin_user

    @abstractmethod
    def install(self, install_type):
        """Installs Cyware (agent or manager) by creating an ansible playbook and launching it

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        CywareDeployment.LOGGER.debug(f"Installing cyware {install_type} via {self.install_mode} in {self.hosts} hosts")
        tasks_list = []
        parent_path = Path(__file__).parent
        if self.install_mode == 'sources':
            tasks_list.append(AnsibleTask({
                'name': 'Render the "preloaded-vars.conf" file',
                'template': {'src': os.path.join(parent_path, 'templates', 'preloaded_vars.conf.j2'),
                             'dest': f'{self.installation_files_path}/etc/preloaded-vars.conf',
                             'owner': 'root', 'group': 'root', 'mode': '0644'},
                'vars': {'install_type': install_type,
                         'install_dir_path': f'{self.install_dir_path}',
                         'server_ip': f'{self.server_ip}',
                         'ca_store': f'{self.installation_files_path}/wpk_root.pem',
                         'make_cert': 'y' if install_type == 'server' else 'n'},
                'become': True,
                'when': 'ansible_system == "Linux"'
            }))

            tasks_list.append(AnsibleTask({
                'name': 'Executing "install.sh" script to build and install Cyware',
                'shell': f"./install.sh > {gettempdir()}/cyware_qa_ctl/cyware_install_log.txt",
                'args': {'chdir': f'{self.installation_files_path}'},
                'become': True,
                'when': 'ansible_system == "Linux"'
            }))

        elif self.install_mode == 'package':
            tasks_list.append(AnsibleTask({
                'name': 'Install Cyware Agent from .deb packages',
                'apt': {'deb': f'{self.installation_files_path}'},
                'become': True,
                'when': 'ansible_os_family|lower == "debian"'
            }))

            tasks_list.append(AnsibleTask({
                'name': 'Install Cyware Agent from .rpm packages | dnf',
                'dnf': {'name': f'{self.installation_files_path}', 'disable_gpg_check': 'yes'},
                'become': True,
                'when': 'ansible_os_family|lower == "redhat"'
            }))

            tasks_list.append(AnsibleTask({
                'name': 'Install Cyware Agent from Windows packages',
                'win_package': {'path': f'{self.installation_files_path}'},
                'become': True,
                'become_method': 'runas',
                'become_user': self.ansible_admin_user,
                'when': 'ansible_system == "Win32NT"'
            }))

            tasks_list.append(AnsibleTask({
                'name': 'Install macOS cyware package',
                'shell': 'installer -pkg cyware-* -target /',
                'args': {'chdir': f'{self.installation_files_path}'},
                'become': True,
                'when': 'ansible_system == "Darwin"'
            }))

        playbook_parameters = {'tasks_list': tasks_list, 'hosts': self.hosts, 'gather_facts': True, 'become': False}

        tasks_result = AnsibleRunner.run_ephemeral_tasks(self.inventory_file_path, playbook_parameters,
                                                         output=self.qa_ctl_configuration.ansible_output)
        CywareDeployment.LOGGER.debug(f"Cyware installation has been successfully done in {self.hosts} hosts")

        return tasks_result

    def __control_service(self, command, install_type):
        """Private method to control the Cyware service in different systems.

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        CywareDeployment.LOGGER.debug(f"{command}ing cyware service in {self.hosts} hosts")
        tasks_list = []
        service_name = install_type if install_type == 'agent' else 'manager'
        service_command = f'{command}ed' if command != 'stop' else 'stopped'

        tasks_list.append(AnsibleTask({
            'name': f'Cyware manager {command} service from systemd',
            'become': True,
            'systemd': {'name': f'cyware-{service_name}', 'state': f'{service_command}'},
            'register': 'output_command',
            'ignore_errors': 'true',
            'when': 'ansible_system == "Linux"'
        }))

        tasks_list.append(AnsibleTask({
            'name': f'Cyware agent {command} service from cyware-control',
            'become': True,
            'command': f'{self.install_dir_path}/bin/cyware-control {command}',
            'when': 'ansible_system == "Darwin" or ansible_system == "SunOS"'
        }))

        tasks_list.append(AnsibleTask({
            'name': f'Cyware agent {command} service from Windows',
            'win_shell': 'Get-Service -Name CywareSvc -ErrorAction SilentlyContinue |' +
                         f' {command.capitalize()}-Service -ErrorAction SilentlyContinue',
            'args': {'executable': 'powershell.exe'},
            'become': True,
            'become_method': 'runas',
            'become_user': self.ansible_admin_user,
            'when': 'ansible_system == "Win32NT"'
        }))

        playbook_parameters = {'tasks_list': tasks_list, 'hosts': self.hosts, 'gather_facts': True, 'become': False}

        tasks_result = AnsibleRunner.run_ephemeral_tasks(self.inventory_file_path, playbook_parameters,
                                                         output=self.qa_ctl_configuration.ansible_output)
        CywareDeployment.LOGGER.debug(f"Cyware service was {command}ed in {self.hosts} hosts")

        return tasks_result

    @abstractmethod
    def start_service(self, install_type):
        """Abstract method to start service

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        self.__control_service('start', install_type)

    @abstractmethod
    def restart_service(self, install_type):
        """Abstract method to restart service

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        self.__control_service('restart', install_type)

    @abstractmethod
    def stop_service(self, install_type):
        """Abstract method to stop service

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        self.__control_service('stop', install_type)

    @abstractmethod
    def health_check(self):
        """Check if the installation is full complete, and the necessary items are ready

        Returns:
            AnsibleOutput: Result of the ansible playbook run.
        """
        CywareDeployment.LOGGER.debug(f"Starting cyware deployment healthcheck in {self.hosts} hosts")
        tasks_list = []
        tasks_list.append(AnsibleTask({
            'name': 'Read ossec.log searching errors (Unix)',
            'lineinfile': {'path': f'{self.install_dir_path}/logs/ossec.log', 'line': 'ERROR|CRITICAL'},
            'register': 'exists',
            'check_mode': 'yes',
            'become': True,
            'failed_when': 'exists is not changed',
            'when': 'ansible_system != "Win32NT"'
        }))

        tasks_list.append(AnsibleTask({
            'name': 'Read ossec.log searching errors (Windows)',
            'win_lineinfile': {'path': f'{self.install_dir_path}\\ossec.log', 'line': 'ERROR|CRITICAL'},
            'register': 'exists',
            'check_mode': 'yes',
            'become': True,
            'become_method': 'runas',
            'become_user': self.ansible_admin_user,
            'failed_when': 'exists is not changed',
            'when': 'ansible_system == "Win32NT"'
        }))

        playbook_parameters = {'tasks_list': tasks_list, 'hosts': self.hosts, 'gather_facts': True, 'become': False}

        tasks_result = AnsibleRunner.run_ephemeral_tasks(self.inventory_file_path, playbook_parameters,
                                                         output=self.qa_ctl_configuration.ansible_output)
        CywareDeployment.LOGGER.debug(f"Cyware deployment healthcheck OK in {self.hosts} hosts")

        return tasks_result

    def cyware_is_already_installed(self):
        """Check if Cyware is installed in the system

        Returns:
            bool: True if cyware is already installed, False if not
        """
        tasks_list = []
        tasks_list.append(AnsibleTask({
            'name': 'Check Cyware directory exist',
            'stat': {'path': f'{self.install_dir_path}'},
            'register': 'dir_exist',
            'failed_when': 'dir_exist.stat.exists and dir_exist.stat.isdir'
        }))

        playbook_parameters = {'tasks_list': tasks_list, 'hosts': self.hosts, 'gather_facts': True, 'become': True}

        output = AnsibleRunner.run_ephemeral_tasks(self.inventory_file_path, playbook_parameters, raise_on_error=False,
                                                   output=self.qa_ctl_configuration.ansible_output)

        if output.rc == 0:
            return False
        else:
            return True
