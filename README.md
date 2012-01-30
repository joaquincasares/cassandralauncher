# Cassandra Launcher (and Cluster Launcher)

This project has two offerings. They are:

1. Cassandra Launcher - An easy to use, interactive command line interface that allows you to deterministically launch a DataStax Community or DataStax Enterprise cluster in under a minute. This component also comes with a fully scriptable interface for cluster launches straight from the command line.
2. Cluster Launcher - A great tool that combines both Amazon's EC2 and Rackspace's Cloudservers into a single tool that allows for deterministicly easy clustering, keyless ssh, and interactive prompts for choosing your environment. No longer must you search for images IDs or wait past page reloads for a cluster since this is all done on the client side.

## Installation

Make sure `python-setuptools` and `python-pip` are installed, then run:

    pip install cassandralauncher

or if installing from source:

    python setup.py build
    python setup.py install

## Setup

Choose one of these things. They are checked by the programs in this order:

* Add `export CLUSTERLAUNCHER_CONF=<path>` to your `~/.bash_profile` or `~/.profile`.
* Open clusterlauncher.conf in your git checkout repo.
* Copy clusterlauncher.conf to `~/.clusterlauncher.conf`.
* Open `/etc/cassandralauncher/clusterlauncher.conf`.

Edit clusterlauncher.conf with your authentication parameters.

## Cassandra Launcher

    cassandralauncher

## EC2/RAX Plain Cluster Launcher

    clusterlauncher

## To destroy
    
Either run `cassandralauncher` or `clusterlauncher` again.

* With `cassandralauncher`:

    * Select Cluster, Confirm.

* With `clusterlauncher`:

    * Select EC2 or RAX, Destroy, Cluster, Confirm.

_THIS MUST BE DONE! IF NOT YOUR AWS ACCOUNT WILL GET A HUGE BILL. TAKE IT FROM ME!_

**Disclaimer:** Even though these tools try their best to keep track of launched clusters,
it is always best to ensure that all clusters are terminated periodically. This is especially
true in cases where AWS/RAX was unable to tag the machine as they were launched. If the tools
were unable to tag said machines, they will forever ignore them since we would rather not even
present the option to kill a cluster these tools did not launch.

## Sample Run for Cassandra Launcher

    Welcome to DataStax' Cassandra Cluster Launcher!

    No existing clusters currently running!

    Cluster Name: Test Cluster
    Total Nodes: 4
    Version:
      [0] Community
      [1] Enterprise
    1

    Username: riptano
    Password: 
    Realtime Nodes: 2
    CFS Replication Factor: 2

    Starting an EC2 cluster of type m1.large with image ami-fd23ec94...
    Ensuring DataStax pem key exists on AWS...
    Ensuring DataStax pem key exists on filesystem...
    Ensuring DataStax pem key's permissions are acceptable...
    Configuring ports...
    Launching cluster...
    Waiting for cluster...
    Cluster booted successfully!

    Unprimed Connection Strings:
    ssh -i /Users/joaquin/DataStaxLauncher.pem ubuntu@107.21.193.17
    ssh -i /Users/joaquin/DataStaxLauncher.pem ubuntu@50.17.168.25
    ssh -i /Users/joaquin/DataStaxLauncher.pem ubuntu@107.22.1.119
    ssh -i /Users/joaquin/DataStaxLauncher.pem ubuntu@23.20.9.38

    OpsCenter Address:
    http://107.21.193.17:8888
    Note: You must wait 60 seconds after Cassandra becomes active to access OpsCenter.

    Waiting 10 seconds for EC2 instances to warm up...
    Priming connections...
    The authenticity of host '107.21.193.17 (107.21.193.17)' can't be established.
    RSA key fingerprint is d5:c7:7c:39:a7:33:5a:5c:71:03:a4:68:2f:ba:b9:59.
    Are you sure you want to continue connecting (yes/no/all)? all
    Creating a keyless SSH ring...
    Waiting for the agent tarball to be created...
    Installing OpsCenter Agents...

    Primed Connection Strings:
    ssh -i /Users/joaquin/DataStaxLauncher.pem -o UserKnownHostsFile=/Users/joaquin/ds_known_hosts ubuntu@107.21.193.17
    ssh -i /Users/joaquin/DataStaxLauncher.pem -o UserKnownHostsFile=/Users/joaquin/ds_known_hosts ubuntu@50.17.168.25
    ssh -i /Users/joaquin/DataStaxLauncher.pem -o UserKnownHostsFile=/Users/joaquin/ds_known_hosts ubuntu@107.22.1.119
    ssh -i /Users/joaquin/DataStaxLauncher.pem -o UserKnownHostsFile=/Users/joaquin/ds_known_hosts ubuntu@23.20.9.38

    Choose the cluster to destroy:
      [0] jcasares - DataStaxAMI Time: 12-16-11 02:21 Size: 4
      [1] None
    0

    Confirm you wish to terminate DataStaxAMI 12-16-11 02:21 by pressing 'y'.
    y

    Termination command complete.

## Sample Run for Cluster Launcher

    host1:~ joaquin$ clusterlauncher
    Choose your Cloud Testing Host:
      [0] EC2
      [1] Rackspace
    1

    Choose your Cloud Command:
      [0] Create
      [1] Destroy
    0

    Choose your Cluster Size:
    3

    Choose your Testing Operating System:
      [0] CentOS
      [1] Debian
      [2] Fedora
      [3] Ubuntu
    0

    Choose your Operating System Version:
      [0] 5.4
      [1] 5.5
      [2] 5.6
    2

    Starting a Rackspace cluster of flavor 4 with image 77...
    Configuring ports...
    Launching cluster...
    Waiting for cluster...
    Cluster booted successfully!

    Connection Strings:
    ssh root@50.56.80.241
    ssh root@50.57.168.62
    ssh root@50.57.168.217

    Private IPs:
    10.183.0.156, 10.183.1.74, 10.183.2.204
    Public IPs:
    50.56.80.241, 50.57.168.62, 50.57.168.217


    host1:~ joaquin$ clusterlauncher
    Choose your Cloud Testing Host:
      [0] EC2
      [1] Rackspace
    1

    Choose your Cloud Command:
      [0] Create
      [1] Destroy
    1

    Choose the cluster to destroy:
      [0] jcasares-CentOS-5.6-Size-3-Time-11-07-11-20.33
      [1] jcasares-CentOS-5.6-Size-3-Time-11-07-11-21.18
    0

    Confirm you wish to kill jcasares-CentOS-5.6-Size-3-Time-11-07-11-20.33 by pressing 'y'.
    y

    Termination command complete.

## Programmatically Launching Cassandra Clusters

Run:

    cassandralauncher -h

to display all options. `clusterlauncher` does not have this functionality, but is easily scriptable at the Python level calling ec2.py or rax.py. See `clusterlauncher.py` for how to do this.
