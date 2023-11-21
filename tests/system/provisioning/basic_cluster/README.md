# cyware-qa

Cyware - Basic cluster provisioning

## Setting up the provisioning

To run this provisioning we need to use a **Linux** machine and install the following tools:

- [Docker](https://docs.docker.com/install/)
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

## Structure

```bash
basic_cluster
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
│   ├── master-role
│   │   ├── files
│   │   │   └── ossec.conf
│   │   └── tasks
│   │       └── main.yml
│   └── worker-role
│       ├── files
│       │   └── ossec.conf
│       └── tasks
│           └── main.yml
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

## Environment

The base environment defined for Docker provisioning is

- A master node
- Two workers nodes
- Three agents, each connected to a different manager.

| Agent        | Reports to    |
|--------------|---------------|
| cyware-agent1 | cyware-master  |
| cyware-agent2 | cyware-worker1 |
| cyware-agent3 | cyware-worker2 |

## Environment management

For running the docker provisioning we must execute the following command:

```shell script
ansible-playbook -i inventory.yml playbook.yml --extra-vars='{"package_repository":"packages", "repository": "4.x", "package_version": "4.4.0", "package_revision": "1", "cyware_qa_branch":"v4.3.0-rc1"}'
```

To destroy it, the command is:

```shell script
ansible-playbook -i inventory.yml destroy.yml
```

## Example

```shell script
ansible-playbook -i inventory.yml playbook.yml

PLAY [Create our container (Master)] **************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [Create a network] ***************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Worker1)] *************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Worker2)] *************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent1)] **************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent2)] **************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Create our container (Agent3)] **************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY [Cyware Master] *******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-master]

TASK [roles/master-role : Installing dependencies using apt] **************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Clone cyware repository] *************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Install master] *********************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Copy ossec.conf file] ***************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Set cluster key] ********************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Set Cyware Master IP] ****************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Stop Cyware] *************************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Remove client.keys] *****************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Register agents] ********************************************************************************************************************************
changed: [cyware-master]

TASK [roles/master-role : Start Cyware] ************************************************************************************************************************************
changed: [cyware-master]

PLAY [Cyware Worker1] ******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-worker1]

TASK [roles/worker-role : Installing dependencies using apt] **************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Clone cyware repository] *************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Install worker] *********************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Copy ossec.conf file] ***************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Set cluster key] ********************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Set Cyware Worker name] **************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Set Cyware Worker IP] ****************************************************************************************************************************
changed: [cyware-worker1]

TASK [roles/worker-role : Restart Cyware] **********************************************************************************************************************************
changed: [cyware-worker1]

PLAY [Cyware Worker2] ******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-worker2]

TASK [roles/worker-role : Installing dependencies using apt] **************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Clone cyware repository] *************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Install worker] *********************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Copy ossec.conf file] ***************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Set cluster key] ********************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Set Cyware Worker name] **************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Set Cyware Worker IP] ****************************************************************************************************************************
changed: [cyware-worker2]

TASK [roles/worker-role : Restart Cyware] **********************************************************************************************************************************
changed: [cyware-worker2]

PLAY [Cyware Agent1] *******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-agent1]

TASK [roles/agent-role : Installing dependencies using apt] ***************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Clone cyware repository] **************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Install agent] ***********************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Copy ossec.conf file] ****************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Remove client.keys] ******************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Register agents] *********************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Set Cyware Manager IP] ****************************************************************************************************************************
changed: [cyware-agent1]

TASK [roles/agent-role : Restart Cyware] ***********************************************************************************************************************************
changed: [cyware-agent1]

PLAY [Cyware Agent2] *******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-agent2]

TASK [roles/agent-role : Installing dependencies using apt] ***************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Clone cyware repository] **************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Install agent] ***********************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Copy ossec.conf file] ****************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Remove client.keys] ******************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Register agents] *********************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Set Cyware Manager IP] ****************************************************************************************************************************
changed: [cyware-agent2]

TASK [roles/agent-role : Restart Cyware] ***********************************************************************************************************************************
changed: [cyware-agent2]

PLAY [Cyware Agent3] *******************************************************************************************************************************************************

TASK [Gathering Facts] ****************************************************************************************************************************************************
ok: [cyware-agent3]

TASK [roles/agent-role : Installing dependencies using apt] ***************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Clone cyware repository] **************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Install agent] ***********************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Copy ossec.conf file] ****************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Remove client.keys] ******************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Register agents] *********************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Set Cyware Manager IP] ****************************************************************************************************************************
changed: [cyware-agent3]

TASK [roles/agent-role : Restart Cyware] ***********************************************************************************************************************************
changed: [cyware-agent3]

PLAY RECAP ****************************************************************************************************************************************************************
localhost                  : ok=13   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent1               : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent2               : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-agent3               : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-master               : ok=11   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-worker1              : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
cyware-worker2              : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

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

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

TASK [docker_container] ***************************************************************************************************************************************************
changed: [localhost]

PLAY RECAP ****************************************************************************************************************************************************************
localhost                  : ok=7    changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```
