# NCS Watch - Capture CLI commands to monitor NCS-55xx devices

## Installation

NCS Watch requires Python 3.8 or newer. This can be verified by pasting the following to a terminal window:
```
% python3 -c "import sys;assert sys.version_info>(3,8)" && echo "ALL GOOD"
```

If 'ALL GOOD' is printed it means Python requirements are met. If not, download and install the latest 3.x version at Python.org (https://www.python.org/downloads/).

Go to the ncs_watch directory and create a virtual environment
```
% cd ncs_watch
% python3 -m venv venv
```

Activate the virtual environment:
```
% source venv/bin/activate
(venv) %
```
- Note that the prompt is updated with the virtual environment name (venv), indicating that the virtual environment is active.
    
Upgrade built-in virtual environment packages:
```
(venv) % pip install --upgrade pip setuptools
```

Install ncs_watch:
```
(venv) % pip install --upgrade .
```

Validate that ncs_watch is installed:
```
(venv) % ncs_watch --version
ncs_watch Version 1.0
```

## Running

A yaml spec file is used to define target devices and commands to execute. There is an example of this file under examples/ncs_watch_spec.yml.

You can use the -h (or --help) to navigate across the contextual help.
```
(venv) % ncs_watch --help 
usage: ncs_watch [-h] [--version] {apply,schema} ...

NCS Watch - Capture CLI commands to monitor NCS-55xx devices

options:
  -h, --help      show this help message and exit
  --version       show program's version number and exit

commands:
  {apply,schema}
    apply         apply commands as per spec file
    schema        generate spec file JSON schema
    

(venv) % ncs_watch apply -h 
usage: ncs_watch apply [-h] [-u <user>] [-p <password>] [-f <filename>] [-s <filename>] [--keep-tmp] [--ssh-config-file <filename>]

options:
  -h, --help            show this help message and exit
  -u <user>, --user <user>
                        username, can also be defined via NCS_WATCH_USER environment variable. If neither is provided prompt for username.
  -p <password>, --password <password>
                        password, can also be defined via NCS_WATCH_PASSWORD environment variable. If neither is provided prompt for password.
  -f <filename>, --file <filename>
                        spec file containing instructions to execute (default: ncs_watch_spec.yml)
  -s <filename>, --save <filename>
                        save output to file (default: periodic_20230223_221529.zip)
  --keep-tmp            keep temporary directories
  --ssh-config-file <filename>
                        custom ssh configuration file to use
```

The apply option execute the instructions determined by the spec file:
```
(venv) % ncs_watch apply   
Device username: cisco
Device password: 
INFO: [ncs-5501] Starting session to 9.3.251.52
INFO: Connected (version 2.0, client Cisco-2.0)
INFO: Authentication (password) successful!
INFO: [ncs-5501] Slots: 1, Interfaces: 4
INFO: [ncs-5501] Starting line-card section
INFO: [ncs-5501][slot 0] Sending 'epm_show_ltrace -T 0x1 | grep dispatch_link_notify'
INFO: [ncs-5501][slot 0] Sending 'ofa_show_ltrace | grep dispatch_link_notify | grep linkstatus'
INFO: [ncs-5501] Finished line-card section
INFO: [ncs-5501] Sending 'show controllers optics 0/0/1/0'
INFO: [ncs-5501] Sending 'show controllers optics 0/0/1/1'
INFO: [ncs-5501] Sending 'show controllers optics 0/0/1/2'
INFO: [ncs-5501] Sending 'show controllers optics 0/0/1/3'
INFO: [ncs-5501] Sending 'show interface HundredGigE0/0/1/0'
INFO: [ncs-5501] Sending 'show interface HundredGigE0/0/1/1'
INFO: [ncs-5501] Sending 'show interface HundredGigE0/0/1/2'
<snip>
INFO: [ncs-5508] Sending 'show controllers HundredGigE0/0/0/23 phy'
INFO: [ncs-5508] Sending 'show controllers fia diagshell 0 "counter pbm=all" location 0/0/CPU0'
INFO: [ncs-5508] Sending 'show controllers fia diagshell 0 "show counters full" location 0/0/CPU0'
INFO: [ncs-5508] Closed session
INFO: Saved output to 'periodic_20230223_231443.zip'
```

The schema option generates a JSON schema describing all options available in the spec file:
```
(venv) % ncs_watch schema
INFO: Saved spec file schema as 'spec_file_schema.json'
```

## Spec file

The examples directory contain a sample ncs_watch_spec.yml file, with similar contents as below:

```yaml
---
globals:
    timeout_std: 30.0
    timeout_ext: 120.0

devices:
  r1:
    address: 10.85.58.240
  r2:
    address: 10.85.58.239

```

All commands in the 'commands' section are sent to each device listed in the 'devices' section. If a command contains 
the 'find' keyword, the provided regular expression is used to search the command output.

## Container Build

```
% docker build --no-cache -t ncs-watch .                                                                           
[+] Building 33.1s (11/11) FINISHED                                                                                                                       
 => [internal] load build definition from Dockerfile                                                                                                 0.0s
 => => transferring dockerfile: 684B                                                                                                                 0.0s
 => [internal] load .dockerignore                                                                                                                    0.0s
 => => transferring context: 2B                                                                                                                      0.0s
 => [internal] load metadata for docker.io/library/python:3.11-alpine                                                                                1.7s               
<snip>
```

### Running

The ncs_watch-run.sh script can be used to run ncs_watch commands inside the container. Any option passed to ncs_watch-run.sh is 
provided to the ncs_watch command line:
```
% ./ncs_watch_run.sh --version
ncs_watch Version 1.1

% ./ncs_watch_run.sh apply  
Device password: 
INFO: [r1] Starting session to 10.85.58.240
INFO: Connected (version 2.0, client Cisco-2.0)
INFO: Authentication (password) successful!
INFO: [r1] Sending 'show log'
INFO: [r1] Pattern '%PKT_INFRA-LINK' not found
INFO: [r1] Closed session
INFO: [r2] Starting session to 10.85.58.239
INFO: Connected (version 2.0, client Cisco-2.0)
INFO: Authentication (password) successful!
INFO: [r2] Sending 'show log'
INFO: [r2] Pattern '%PKT_INFRA-LINK' found: 317 hits, first: %PKT_INFRA-LINK
INFO: [r2] Closed session
WARNING: Search pattern found in the output from these devices: r2
INFO: Saved output from commands to 'output_20230215.txt'
```

### Troubleshooting

For troubleshooting, one can manually run the container image without any option, landing on a bash shell inside the container.

Create host directory to be mounted into the container:
```
% mkdir ncs_watch-data
```

Start the container:
```
docker run -it --rm --hostname ncs_watch --mount type=bind,source="$(pwd)"/ncs_watch-data,target=/shared-data ncs_watch:latest

```
