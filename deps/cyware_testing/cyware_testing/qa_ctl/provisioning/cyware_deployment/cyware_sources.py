from cyware_testing.qa_ctl.provisioning.cyware_deployment.cyware_installation import CywareInstallation
from cyware_testing.qa_ctl.provisioning.ansible.ansible_task import AnsibleTask
from cyware_testing.qa_ctl import QACTL_LOGGER
from cyware_testing.tools.logging import Logging


class CywareSources(CywareInstallation):
    """Install Cyware from the given sources. In this case, the installation
        will be done from the source files of a repository.

    Args:
        cyware_target (string): Type of the Cyware instance desired (agent or manager).
        installation_files_path (string): Path where is located the Cyware instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        cyware_branch (string): String containing the branch from where the files are going to be downloaded.
        This field is set to 'master' by default.
        cyware_repository_url (string): URL from the repo where the cyware sources files are located.
        This parameter is set to 'https://github.com/cyware/cyware.git' by default.

    Attributes:
        cyware_target (string): Type of the Cyware instance desired (agent or manager).
        installation_files_path (string): Path where is located the Cyware instalation files.
        qa_ctl_configuration (QACTLConfiguration): QACTL configuration.
        cyware_branch (string): String containing the branch from where the files are going to be downloaded.
        This field is set to 'master' by default.
        cyware_repository_url (string): URL from the repo where the cyware sources files are located.
        This parameter is set to 'https://github.com/cyware/cyware.git' by default.
    """
    LOGGER = Logging.get_logger(QACTL_LOGGER)

    def __init__(self, cyware_target, installation_files_path, qa_ctl_configuration, cyware_branch='master',
                 cyware_repository_url='https://github.com/cyware/cyware.git'):
        self.cyware_branch = cyware_branch
        self.cyware_repository_url = cyware_repository_url
        super().__init__(cyware_target=cyware_target, qa_ctl_configuration=qa_ctl_configuration,
                         installation_files_path=f"{installation_files_path}/cyware-{self.cyware_branch}")

    def download_installation_files(self, inventory_file_path, hosts='all'):
        """Download the source files of Cyware using an AnsibleTask instance.

        Args:
            inventory_file_path (string): path where the instalation files are going to be stored
            hosts (string): Parameter set to `all` by default

        Returns:
            str: String with the path where the installation files are located
        """
        CywareSources.LOGGER.debug(f"Downloading Cyware sources from {self.cyware_branch} branch in {hosts} hosts")

        download_cyware_sources_task = AnsibleTask({
            'name': f"Download Cyware branch in {self.installation_files_path}",
            'shell': f"cd {self.installation_files_path} && curl -Ls https://github.com/cyware/cyware/archive/"
                     f"{self.cyware_branch}.tar.gz | tar zx && mv cyware-*/* ."
        })
        CywareSources.LOGGER.debug(f"Cyware sources from {self.cyware_branch} branch were successfully downloaded in "
                                  f"{hosts} hosts")
        super().download_installation_files(inventory_file_path, [download_cyware_sources_task], hosts)

        return self.installation_files_path
