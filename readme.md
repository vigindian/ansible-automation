# Ansible Automation Platform QuickStart
As remarkable as the Ansible documentation is, one might find it challenging to discover a suitable guide for establishing end-to-end automation through the Ansible Automation Platform (previously Ansible Tower). To address this, we shall now delve into the process of setting up Ansible automation for a sample project focused on extracting data from remote Linux hosts.

![plot](./image-ansible-automation-quickstart.png)

## Pre-requisites
- Linux hosts inventory to provide as input to Ansible.
- A remote user pre-configured in the remote hosts in which this automation will run. Let us call the remote user "ansible" for this demonstration.
- Ansible credential: Pre-configured ssh private-keys for the remote Linux hosts in Ansible credentials. If elevated privileges are required, then the remote user must have corresponding sudo access. If sudo password is needed, update the Ansible credential with the sudo password of the user.

## 1. Overview
Here is a **TLDR** version of what we will do in this automation project:
- We prepare the Linux hosts inventory.
- We create a GIT repo with our Ansible code.
- We create a new Ansible Project for the GIT repository.
- We use an Ansible compatible inventory file or a dynamic inventory script to load the linux hosts into Ansible.
- We create multiple Ansible Job Templates for different batches of Linux hosts.
- Using the Ansible Job Templates, we run the playbook task that extracts info we need and adds it into host facts. We leverage Ansible Tower's facts cache feature for this.
- As each host in our inventory will have the data we need in its 'Facts', we can easily retrieve it using another playbook or Ansible API.
- We use a collate-output playbook to collate output from facts of all hosts.
- Once we have collected the data, we can clear the facts cache using Ansible's built-in meta task.

## 2. Code Structure
- Ansible follows a specific format for certain types of files. For instance, before running a job, Ansible Automation platform will install the pre-requisite packages listed in collections/requirements.yml.
- We leverage a blend of Ansible's format and best practices to ensure a well-structured and efficient Ansible codebase.
  - playbooks: playbooks directory.
  - linux: linux server list and dynamic inventory script.
  - collections: Ansible modules.
  - utilities: helper script(s).

### 2.1. Dynamic Inventory Generate Script 
Ansible Dynamic Inventory script, [inv_create.py](./linux/inv_create.py), to generate inventory based on a flat-file input file (linux-servers.txt) or local list of hosts within the script:
- The options "--list" and "--host" are [required](https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#inventory-script-conventions) by Ansible.
- Linux server naming convention is used to split servers into sub-groups.
- In hostname, the 2nd column separated by "-" has the app-name. So each sub-group will have all hosts of the same app.
- All hosts added to common-group "linux"
- Add ansible connection parameters as sub-group variables
- **Note**: If you use Ansible container execution environment, it does not honor locally sourced files. So this version of the inventory script also accepts hard-coded servers in a variable within the script.
- Key connection attributes added to the host-group config:
```
ansible_connection=ssh
ansible_user=ansible
```

**Windows Git Hack**:
The dynamic inventory script needs execution permission to be set so Ansible can run it. However Windows VSCode does not have a provision to set that. First stage the file and use below git command to enable exec permission for the script:
```
git update-index --chmod=+x .\linux\inv_create.py
```

**Usage**:
```
./inv_create.py --list
```

**Example**:
Given these 3 servers:
```
server1-prom.prod.linux.com
server2-graf.prod.linux.com
server3-nagi.prod.linux.com
```

This is the sample output of the inventory script:
```
{"linux": {"children": ["prom", "graf", "nagi"]}, "prom": {"hosts": ["server1-prom.prod.linux.com"], "vars": {"ansible_connection": "ssh", "ansible_user": "ansible"}}, "graf": {"hosts": ["server2-graf.prod.linux.com"], "vars": {"ansible_connection": "ssh", "ansible_user": "ansible"}}, "nagi": {"hosts": ["server3-nagi.prod.linux.com"], "vars": {"ansible_connection": "ssh", "ansible_user": "ansible"}}}
```

### 2.2. Collections
Note: In this example project, collections is just for demo and not used by the Ansible code.

#### 2.2.1. Pre-requisites
In Ansible Job settings (Settings -> Jobs -> Jobs settings), the "Enable Collection(s) Download" must be set to "On".

#### 2.2.2. Details
- The file [requirements.yml](./collections/requirements.yml) contains the modules.
- Ansible will automatically install modules from this file prior to job execution.

## 3. Playbooks
### 3.1. Extract Data
- A sample [uptime](./playbooks/uptime_nix.yml) playbook that extracts server uptime from each remote host.
- Sample Output:
```
{
  "server_uptime.stdout_lines[0]": [
    {
      "host":"server1-prom.prod.linux.com",
      "uptime":"2 days"
    }
  ]
}
```

### 3.2. Collate Output
- This playbook [collate_output](./playbooks/collate_output.yml) uses Ansible Tower's facts cache to gather facts from all hosts.
- The 'outputMode' variable in the playbook controls if Ansible job output will be in json or csv format:
  - json: prints json output in Ansible job log.
  - csv: uses [ansible_json_to_csv.py](./utilities/ansible_json_to_csv.py) to convert json value in Facts to csv.
- This task does not make a remote connection to the target hosts.
- Sample Output (csv):
```
ok: [server1-prom.prod.linux.com -> localhost] => {
    "uptime_output.stdout_lines[0]": "\\"server1-prom.prod.linux.com\\",\\"2 days\\""
}
```

### 3.3. Clear Facts
- This playbook [clear_facts](./playbooks/clear_facts.yml) uses Ansible's meta task to clear the gathered facts from all hosts.
- This task does not make a remote connection to the target hosts.
```
- name: Clear Facts from Hosts
  gather_facts: false
  hosts: all
  tasks:
    - name: Clear gathered facts
      meta: clear_facts
```

## 4. Ansible Automation Platform Setup
In this example, let us consider the Ansible URL: https://ansible.example.com/

### 4.1. Repo
- Create a private Git repo in your repository hub. Examples: Github, Gitlab, Bitbucket, etc.
- Ensure repo is accessible by Ansible: The git user must have access to the repo. You can use git token, user/pass or ssh-keys to authenticate to the repo.

### 4.2. Ansible Projects
Create a new Ansible project:
- Source Control Type: Git
- Source Countrol URL: the scm url created in previous step
- Source Control Credential: If you use Ansible credentials to connect to git, then select the corresponding Git credential.
- Once the project is created, ensure the sync is successful (Last Job Status). If not, fix the errors and manually sync it.

### 4.3. Ansible Inventories
Create a new inventory.
- Navigate to sources of the new inventory and create a new source:
  - Source: Sourced from a Project
  - Project: select previously created project
- Inventory File: select inventory file from drop-down. If using a dynamic inventory script, manually type script name and press 'Enter' key. Dynamic script must have execute permissions in the source repo (chmod +x). Example dynamic script input: linux/inv_create.py
- Update options: Select "Overwrite" and "Overwrite Variables"
- Save and run sync.
- Validate if you can see the hosts under the new inventory.
- Repeat this for each inventory file in the repo.

### 4.4. Ansible Templates
#### 4.4.1. Extract Data
Create new job template for a set of hosts. We can split them into multiple job templates using 'Limit' based on hostname patterns:
- Job Type: Run
- Inventory: Select the inventory created earlier.
- Project: Select the project created earlier.
- Playbook: Select the playbook "playbooks/uptime_nix.yml" from drop-down.
- Credentials: Select the corresponding ssh private-key.
- **IMPORTANT** Limit: Specify host pattern to constrain the list of hosts in which the playbook should run. Example: "abc:def" (without quotes) to run playbook in both abc and def hosts.
- Options: Enable "Enable Fact Storage" (This ensures facts set in playbook are persisted into host in the inventory).
- Options: Enable "Privilege Escalation" (This is only applicable for remote user that has sudo access enabled).

#### 4.4.2. Collate Output
Lets create an Ansible Job Template based off the collate playbook:
- Job Type: Run
- Inventory: Select the inventory created earlier.
- Project: Select the project created earlier.
- Playbook: Select the playbook "playbooks/collate_output.yml" from drop-down.
- Options: Enable "Enable Fact Storage".

#### 4.4.3. Clear Facts
Create a new Ansible Job Template:
- Job Type: Run
- Inventory: Select the inventory created earlier.
- Project: Select the project created earlier.
- Playbook: Select the playbook "playbooks/clear_facts.yml" from drop-down.
- Options: Enable "Enable Fact Storage".

## 5. Data Extraction
### 5.1. Option 1: Ansible Job (Preferred)
- Launch the extract data Ansible Job templates for all Linux hosts.
- At this point, we should have the uptime data added to each host's 'Facts'. We will retrieve it using the collate_output playbook.

#### 5.1.2. Job Launch & Output: Collate Output
- In 'outputMode' of collate_output, ensure value "csv" is set.
- Launch the collate_output job template.
- Once the job run has completed successfully, the output will contain uptime of all the hosts.

#### 5.1.3. Ansible Job log to csv
- Once the collate_output Ansible job is completed, download the job log and run below command in a NIX system to get output in proper csv format:
```
cat job_123.txt |grep uptime_output.stdout_lines |awk -F"]\": " '{print $2}' | sed "s/\\\\//g"| sed "s/\"\"/\"/g" > joblog.csv
```

- Sample output line in csv format:
```
"server1-prom.prod.linux.com","2 days"
```

### 5.2. Option 2: Ansible API
- Use Ansible Tower API to extract the job output.
- This makes it easier to automate data extraction and manipulate the Ansible output to suit our needs.
- Example - Download output into stdout file in 'json' format:
```
curl -O -k -J -L -u "user:passwordgoeshere" https://ansible.example.com/api/v2/jobs/123/stdout?format=json
```

- Example - Download output into stdout file in 'txt' format:
```
curl -O -k -J -L -u "user:passwordgoeshere" https://ansible.example.com/api/v2/jobs/123/stdout?format=txt
```

- Example - Download output into a separate txt file for given job:
```
curl -O -k -J -L -u "user:passwordgoeshere" https://ansible.example.com/api/v2/jobs/123/stdout?format=txt_download
```

### 5.3. Option 3: Ansible Job Template Output
- Navigate to the corresponding job run and extract output from 'Output' section.
- Example: https://ansible.example.com/#/jobs/playbook/123/output

## 6. Ansible Clear Facts
Once the data extraction task is completed, we do not need the hosts' facts (cache) anymore. Lets clean it up:
- Launch the clear_facts job template created earlier.
- If you check any host in this project's inventory, the facts should be "{}".
