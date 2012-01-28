# Cluster Launcher and Cassandra Launcher from Source

## Prereqs for source only downloads

    pip install boto
    pip install python-cloudservers

## Setup

Same as pip install instructions.

## EC2/RAX Plain Cluster Launcher

Run `./clusterlauncher.py` from this directory.

## Cassandra Launcher

Run `./cassandralauncher.py` from this directory

## To destroy

Same as pip installation instructions except the files are located in this directory:

    ./clusterlauncher.py
    ./cassandralauncher.py

_THIS MUST BE DONE! IF NOT YOUR AWS ACCOUNT WILL GET A HUGE BILL. TAKE IT FROM ME!_

**Disclaimer:** Even though these tools try their best to keep track of launched clusters,
it is always best to ensure that all clusters are terminated periodically. This is especially
true in cases where AWS/RAX was unable to tag the machine as they were launched. If the tools
were unable to tag said machines, they will forever ignore them since we would rather not even
present the option to kill a cluster these tools did not launch.
