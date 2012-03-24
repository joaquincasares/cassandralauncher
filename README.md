# Cassandra Launcher (and Plain Image Launcher)

This project has two offerings. They are:

1. Cassandra Launcher - An easy to use, interactive command line interface that allows you to deterministically launch a DataStax Community or DataStax Enterprise cluster in under a minute. This component also comes with a fully scriptable interface for cluster launches straight from the command line.
2. Plain Image Launcher - A great tool that combines both Amazon's EC2 and Rackspace's Cloudservers into a single tool that allows for deterministicly easy clustering, keyless ssh, and interactive prompts for choosing your environment. No longer must you search for images IDs or wait past page reloads for a cluster since this is all done on the client side.

## Installation

**Note:** This repository does not need to be cloned. Everything is already included in the pip commands.

Make sure `python-setuptools` and `python-pip` are installed, then run:

    pip install cassandralauncher

## Upgrading

    pip install --upgrade cassandralauncher

## Setup

Start the program once to copy the default `/etc/cassandralauncher/clusterlauncher.conf` to `~/.clusterlauncher.conf`.

Exit the program and edit `~/.clusterlauncher.conf` with your appropriate authentication parameters.

## Cassandra Launcher

    cassandralauncher

## EC2/RAX Plain Image Launcher

    imagelauncher

## To destroy
    
Either run `cassandralauncher` or `imagelauncher` again.

* With `cassandralauncher`:

    * Select Cluster, Confirm.

* With `imagelauncher`:

    * Select EC2 or RAX, Destroy, Cluster, Confirm.

_THIS MUST BE DONE! IF NOT YOUR AWS ACCOUNT WILL GET A HUGE BILL. TAKE IT FROM ME!_

**Disclaimer:** Even though these tools try their best to keep track of launched clusters,
it is always best to ensure that all clusters are terminated periodically. This is especially
true in cases where AWS/RAX was unable to tag the machine as they were launched. If the tools
were unable to tag said machines, they will forever ignore them since we would rather not even
present the option to kill a cluster these tools did not launch.

## More Documentation

* [CHANGES](https://github.com/joaquincasares/cassandralauncher/tree/master/CHANGES.md)
* [Sample Runs](https://github.com/joaquincasares/cassandralauncher/tree/master/docs/sample_runs.md)
* [New Features](https://github.com/joaquincasares/cassandralauncher/tree/master/docs/new_features.md)

## Programmatically Launching Cassandra Clusters

Run:

    cassandralauncher -h

to display all options. `imagelauncher` does not have this functionality, but is easily scriptable at the Python level calling ec2.py or rax.py. See `clusterlauncher.py` for how to do this.

## FAQ

My cluster is not done launching one (or several) of my nodes. What did I do wrong?

    Nothing. EC2 and Rackspace do this from time to time. You can either continue on to do
    basic testing, or terminate this cluster and try again. Using EC2 and Rackspace off it's
    peak hours helps in this scenario, in general.
