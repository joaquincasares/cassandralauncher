## OpsCenter Agents

OpsCenter Agents are now preinstalled with all clusters that are OpsCenter enabled. No longer do you have to enter credentials via the OpsCenter GUI.

## Nodelist

If you ever need a list of your Cassandra nodes, simply look at `/etc/cassandralauncher/nodelist`.

## DataStax SSH Client

Now you can simply run the DataStax SSH Client by executing: `datastax_ssh`. This will connect you to all machines by serially executing your command of choice on all machines in your cluster.

## Modified /etc/hosts

Now you can simply run an `ssh node0` or `ssh node1` command and easily jump from node to node from within your cluster.

## DataStax Parallel SSH Client

Now you can simply run the DataStax Parallel SSH Client by executing: `datastax_pssh`. This will connect you to all machines and executing your command of choice on all machines in your cluster in parallel.

## S3 Store and Restore

Now you can use the `datastax_s3_store` and `datastax_s3_restore` commands to simply upload and download your `cassandra/data` directory to and from S3. Think of it as an "experimental EBS functionality for S3."

The files are stored in `s3://datastax_s3_storage-<YOUR_AWS_ACCESS_KEY_ID>/<CLUSTER_NAME>/<NODES_TOKEN>` using the `~/.s3cfg` file.

You may also use `datastax_pssh` command to store and restore an entire cluster.

To automatically preconfigure `s3cmd`, which `datastax_s3_store` and `datastax_s3_restore` rely on, add/change this on your `clusterlauncher.conf`:

    [S3]
    send_s3_credentials = True

That will send .s3cfg preconfigured with your aws_access_key_id and aws_secret_access_key, properly set under 400 permissions, to your home directory.
