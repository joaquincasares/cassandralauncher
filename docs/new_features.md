## OpsCenter Agents

OpsCenter Agents are now preinstalled with all clusters that are OpsCenter enabled. No longer do you have to enter credentials via the OpsCenter GUI.

## Nodelist

If you ever need a list of your Cassandra nodes, simply look at `/etc/cassandralauncher/nodelist`.

## DataStax SSH Client

Now you can simply run the DataStax SSH Client by executing: `datastax_ssh`. This will connect you to all machines by serially executing your command of choice on all machines in your cluster.

## Modified /etc/hosts

Now you can simply run an `ssh node0` or `ssh node1` command and easily jump from node to node from within your cluster.
