# cyware-qa

Cyware - Manager Agents provisioning

## Enviroment description
This enviroment sets a Manager with three (3) agents. Each agent has a especific version. It is designed to allow testing on different versions of the cyware agent working in conjunction with a specific version of the cyware manager.

## Setting up the provisioning

To run this provisioning we need to use a **Linux** machine and install the following tools:

- [Docker](https://docs.docker.com/install/)
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

## Structure

```bash
manager_agent
├── ansible.cfg
├── destroy.yml
├── inventory.yml
├── playbook.yml
├── README.md
├── roles
│   ├── agent-role
│   │   ├── files
│   │   │   └── ossec.conf
│   │   └── tasks
│   │       └── main.yml
│   ├── manager-role
│   │   ├── files
│   │   │   └── ossec.conf
│   │   └── tasks
│   │       └── main.yml
└── vars
    ├── configurations.yml
    └── main.yml
```

#### ansible.cfg

Ansible configuration file in the current directory. In this file, we setup the configuration of Ansible for this
provisioning.

#### destroy.yml

In this file we will specify that we want to shut down the docker machines in our environment.

##### inventory.yml

File containing the inventory of machines in our environment. In this file we will set the connection method and its
python interpreter

##### playbook.yml

Here we will write the commands to be executed in order to use our environment

##### roles

Folder with all the general roles that could be used for start our environment. Within each role we can find the
following structure:

- **files**: Configuration files to be applied when the environment is setting up.
- **tasks**: Main tasks to be performed for each role

#### Vars

This folder contains the variables used to configure our environment. Variables like the cluster key or the agent key.
- **agent#-package**: link to the cyware agent package  to be installed on each agent host. (currently versions 4.1.5, 4.2.2 and 4.2.5)

## Environment

The base environment defined for Docker provisioning is

- A master node
- Three agents.

| Agent        | Reports to    |
|--------------|---------------|
| cyware-agent1 | cyware-manager |
| cyware-agent2 | cyware-manager |
| cyware-agent3 | cyware-manager |

## Environment management

For running the docker provisioning we must execute the following command:

```shell script
ansible-playbook -i inventory.yml playbook.yml --extra-vars='{"package_repository":"packages", "repository": "4.x", "package_version": "4.4.0", "package_revision": "1"}'
```

To destroy it, the command is:

```shell script
ansible-playbook -i inventory.yml destroy.yml
```

## Example

```shell script
ansible-playbook -i inventory.yml playbook.yml

PLAY [Create our container (Manager)] *********************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************
ok: [localhost]

TASK [Create a network] *************************************************************************************************************************
ok: [localhost]

TASK [docker_container] *************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent1)] **********************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************************
ok: [localhost]

TASK [docker_container] **************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent2)] **********************************************************************************************************************

TASK [Gathering Facts] **************************************************************************************************************************
ok: [localhost]

TASK [docker_container] **************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent3)] **********************************************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ****************************************************************************************************************************
changed: [localhost]

PLAY [Cyware Manager] ************************************************************************************************************************

TASK [Gathering Facts] ************************************************************************************************************************
ok: [cyware-manager]

TASK [roles/manager-role : Check and update debian repositories] ******************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Installing dependencies using apt] *********************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Clone cyware repository] ********************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Install manager] ***************************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Copy ossec.conf file] **********************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Set cluster key] ***************************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Set Cyware Manager IP] **********************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Stop Cyware] ********************************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Remove client.keys] ************************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : enable execd debug mode] *******************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Register agents] ***************************************************************************************************************
changed: [cyware-manager]

TASK [roles/manager-role : Start Cyware] *******************************************************************************************************************
changed: [cyware-manager]

PLAY [Cyware Agent1] **********************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************
ok: [cyware-agent1]

TASK [roles/agent-role : Check and update debian repositories] ********************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Installing dependencies using apt] ***********************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Create log source] ***************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Download package] ****************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Install agent] *******************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Copy ossec.conf file] ************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : enable execd debug mode] *********************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Remove client.keys] **************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Register agents] *****************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Set Cyware Manager IP] ************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Restart Cyware] *******************************************************************************************************************
changed: [cyware-agent1]

PLAY [Cyware Agent2] ***************************************************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************************************
ok: [cyware-agent2]

TASK [roles/agent-role : Check and update debian repositories] ******************************************************************************************** 
changed: [cyware-agent2]

TASK [roles/agent-role : Installing dependencies using apt] ***********************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Create log source] ***************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Download package] ****************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Install agent] *******************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Copy ossec.conf file] ************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : enable execd debug mode] *********************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Remove client.keys] **************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Register agents] *****************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Set Cyware Manager IP] ************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Restart Cyware] *******************************************************************************************************************
changed: [cyware-agent2]

PLAY [Cyware Agent3] **********************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************
ok: [cyware-agent3]

TASK [roles/agent-role : Check and update debian repositories] *******************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Installing dependencies using apt] ***********************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Create log source] ***************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Download package] ****************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Install agent] *******************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Copy ossec.conf file] ************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : enable execd debug mode] *********************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Remove client.keys] **************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Register agents] *****************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Set Cyware Manager IP] ************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Restart Cyware] *******************************************************************************************************************
changed: [cyware-agent3]

PLAY RECAP ************************************************************************************************************************************************
localhost                  : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent1               : ok=12   changed=11   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent2               : ok=12   changed=11   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent3               : ok=12   changed=11   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-manager              : ok=13   changed=12   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
=============================================================================== 
Playbook run took 0 days, 0 hours, 15 minutes, 47 seconds 

```

```shell script
ansible-playbook -i inventory.yml destroy.yml

PLAY [localhost] **********************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]
PLAY RECAP ****************************************************************************************************************************************************************
localhost                  : ok=5    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```
