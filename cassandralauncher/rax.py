#!/usr/bin/env python

import os
import re
import time
import sys

try:
    from cloudservers import CloudServers
    from cloudservers import Image
except:
    sys.stderr.write("'cloudservers' is not installed on your system. Please run:\n")
    sys.stderr.write("    pip install python-cloudservers\n")
    sys.stderr.write("and try again.\n")
    sys.exit(1)

import common

def create_cluster(rax_user, rax_api_key, reservation_size, image, tag, flavor):

    # Create the Rackspace cluster
    print 'Starting a Rackspace cluster of flavor {0} with image {1}...'.format(flavor, image)
    cloudservers = CloudServers(rax_user, rax_api_key)
    servers = []
    print 'Launching cluster...'
    for i in range(reservation_size):
        transfer_files = {
            '/root/.ssh/authorized_keys' : open(os.path.expanduser("~/.ssh/id_rsa.pub"), 'r')
            # '/root/.ssh/id_rsa.pub' : open(os.path.expanduser("~/.ssh/id_rsa.pub"), 'r')
            # '/root/.ssh/id_rsa' : open(os.path.expanduser("~/.ssh/id_rsa"), 'r')
        }

        servers.append(
            cloudservers.servers.create(
                image=image,
                flavor=flavor,
                name=tag,
                files=transfer_files
            )
        )
    
    print 'Waiting for cluster...'
    time.sleep(10)
    for server in servers:
        while cloudservers.servers.get(server.id).status != "ACTIVE":
            time.sleep(3)
    print "Cluster booted successfully!"

    # Print SSH commands
    public_ips = []
    private_ips = []
    for server in servers:
        public_ips.append(server.public_ip)
        private_ips.append(server.private_ip)
    print

    return [private_ips, public_ips]

def terminate_cluster(rax_user, rax_api_key, search_term):

    # Grab all the infomation for clusters spawn by this tool that are still alive
    ds_reservations = {}
    cloudservers = CloudServers(rax_user, rax_api_key)
    serverlist = cloudservers.servers.list()

    p = re.compile("{0}.*".format(search_term))

    for server in serverlist:
        if p.match(server.name):
            try:
                if cloudservers.servers.get(server.id).status == "ACTIVE":
                    if not server.name in ds_reservations:
                        ds_reservations[server.name] = {
                            'Servers': []
                        }
                    ds_reservations[server.name]['Servers'].append(server)
            except:
                # Server was recently shut down
                pass

    # Prompt for cluster to destroy
    selection = common.choose("Choose the cluster to destroy:", ds_reservations.keys())

    # Confirm cluster termination
    print "Confirm you wish to terminate {0} by pressing 'y'.".format(selection)
    if raw_input().lower() != 'y':
        print "Cluster was not terminated."
        print
        sys.exit()
    print

    # The actual termination command
    for server in ds_reservations[selection]['Servers']:
        try:
            server.delete()
        except:
            print "This server appears to have already been shut down. Please give it some time for the API to adjust."

    print "Termination command complete."
    print

# NOTES:
# cloudservers = CloudServers(user, apiKey)
# 
# Find Flavor List
# for i in cloudservers.flavors.list():
#     print "ID: %s = %s" % (i.id, i.name)
# 
# Find Image List
# for i in cloudservers.images.list():
#     print "ID: %s = %s" % (i.id, i.name)
