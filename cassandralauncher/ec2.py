#!/usr/bin/env python

import os
import stat
import sys
import time

try:
    import boto
except:
    sys.stderr.write("'boto' is not installed on your system. Please run:\n")
    sys.stderr.write("    pip install boto\n")
    sys.stderr.write("and try again.\n")
    sys.exit(1)

from xml.dom.minidom import parseString

import common

def authorize(security_group, port, realm, port_end_range=False):

    # Setup single ports, unless noted
    if not port_end_range:
        port_end_range = port
    
    # Catch errors from overpopulating
    try:
        # Open ports publicly
        if realm == 'public':
            security_group.authorize('tcp', port, port_end_range, '0.0.0.0/0')
        # Open ports privately
        elif realm == 'private':
            security_group.authorize('tcp', port, port_end_range, src_group=security_group)
        # Error out if code was changed
        else:
            sys.stderr.write('Unknown realm assigned!\n')
            sys.exit(1)
    except boto.exception.EC2ResponseError:
        # Continue since ports were probably trying to be overwritten
        pass

def print_boto_error():
    """Attempts to extract the XML from boto errors to present plain errors with no stacktraces."""

    try:
        quick_summary, null, xml = str(sys.exc_info()[1]).split('\n')
        error_msg = parseString(xml).getElementsByTagName('Response')[0].getElementsByTagName('Errors')[0].getElementsByTagName('Error')[0]
        print
        sys.stderr.write('AWS Error: {0}\n'.format(quick_summary))
        sys.stderr.write('{0}: {1}\n'.format(error_msg.getElementsByTagName('Code')[0].firstChild.data, error_msg.getElementsByTagName('Message')[0].firstChild.data))
        print
    except:
        # Raise the exception if parsing failed
        raise
    sys.exit(1)



def create_cluster(aws_access_key_id, aws_secret_access_key, reservation_size, image, tag, key_pair, instance_type, placement, pem_home, user_data=None, noprompts=False):

    # Connect to EC2
    print 'Starting an EC2 cluster of type {0} with image {1}...'.format(instance_type, image)
    conn = boto.connect_ec2(aws_access_key_id, aws_secret_access_key)

    # Ensure PEM key is created
    try:
        print "Ensuring DataStax pem key exists on AWS..."
        try:
            key = conn.get_all_key_pairs(keynames=[key_pair])[0]
        except boto.exception.EC2ResponseError:
            print_boto_error()

        print "Ensuring DataStax pem key exists on filesystem..."
        # Print a warning message if the pem file can't be found
        pem_file = os.path.join(pem_home, key_pair + '.pem')
        if os.path.isfile(pem_file):
            print "Ensuring DataStax pem key's permissions are acceptable..."
            # Print a warning message is the pem file does not have the correct file permissions
            permissions = os.stat(pem_file).st_mode
            if not (bool(permissions & stat.S_IRUSR) and     # Ensure owner can read
                    not bool(permissions & stat.S_IRWXG) and # Ensure that group has no permissions
                    not bool(permissions & stat.S_IRWXO)):   # Ensure that others have no permissions

                sys.stderr.write("WARNING: The pem file has permissions that are too open!\n\n")

                if noprompts:
                    sys.exit(1)
                if raw_input("Do you wish to reset file permissions? [y/N] ").lower() == 'y':
                    try:
                        # Reset permissions
                        os.chmod(pem_file, 0400)
                    except:
                        sys.stderr.write("Unable to reset file permissions!\n")
                        if raw_input("Do you wish to continue? [y/N] ").lower() != 'y':
                            sys.exit(1)
                else:
                    print "File permissions unchanged."
                    if raw_input("Do you wish to continue? [y/N] ").lower() != 'y':
                        sys.exit(1)
        else:
            sys.stderr.write("WARNING: The created pem file no longer exists at %s!\n" % pem_file)
            sys.stderr.write("         Please copy it out of the previous 'pem_home' directory.\n\n")

            if noprompts or raw_input("Do you wish to continue? [y/N] ").lower() != 'y':
                sys.exit(1)

    except boto.exception.EC2ResponseError, e:
        if e.code == 'InvalidKeyPair.NotFound':
            print 'Creating keypair...'
            key = conn.create_key_pair(key_pair)
            try:
                key.save(pem_home)
            except:
                conn.delete_key_pair(key_pair)
                print "Saving keypair failed! Removing keypair from AWS and exiting. Nothing was launched.\n"
                raise
        else:
            raise

    # Check if DataStax security group exists
    ds_security_group = False
    for security_group in conn.get_all_security_groups():
        if security_group.name == 'DataStax':
            ds_security_group = security_group
            break

    # Create the DataStax security group if it doesn't exist
    if not ds_security_group:
        ds_security_group = conn.create_security_group('DataStax', 'Security group for running DataStax products')
    
    # Ensure all Security settings are active
    print "Configuring ports..."
    authorize(ds_security_group, 22, 'public')
    authorize(ds_security_group, 9160, 'public')
    authorize(ds_security_group, 8012, 'public')
    authorize(ds_security_group, 50030, 'public')
    authorize(ds_security_group, 50060, 'public')
    authorize(ds_security_group, 8983, 'public')
    authorize(ds_security_group, 8888, 'public')

    authorize(ds_security_group, 7000, 'private')
    authorize(ds_security_group, 7199, 'private')
    authorize(ds_security_group, 8983, 'private')
    authorize(ds_security_group, 9290, 'private')
    authorize(ds_security_group, 61621, 'private')
    authorize(ds_security_group, 1024, 'private', 65535)
    authorize(ds_security_group, 50031, 'private')
    authorize(ds_security_group, 61620, 'private')

    try:
        # Create the EC2 cluster
        print 'Launching cluster...'
        try:
            reservation = conn.run_instances(image, 
                                             min_count=reservation_size, 
                                             max_count=reservation_size, 
                                             instance_type=instance_type, 
                                             key_name=key_pair, 
                                             placement=placement, 
                                             security_groups=['DataStax'], user_data=user_data)
        except boto.exception.EC2ResponseError:
            print_boto_error()

        # Sleep so Amazon recognizes the new instance
        print 'Waiting for EC2 cluster to instantiate...'
        time.sleep(10)
        for instance in reservation.instances:
            while not instance.update() == 'running':
                time.sleep(3)
        print "Cluster booted successfully!"
        print

        # Tag the instances in this reservation
        for instance in reservation.instances:
            conn.create_tags([instance.id], {'Name': tag, 'Initializer': 'DataStax'})
    except:
        print "\n\nERROR: Tags were never applied to started instances!!! Make sure you TERMINATE instances here:"
        print "    https://console.aws.amazon.com/ec2/home?region=us-east-1#s=Instances\n"
        
        # Ensure the user acknowledges pricing danger
        while raw_input('Acknowledge warning [Type OK]: ').lower() != 'ok':
            pass
        raise

    # Collect ip addresses
    private_ips = []
    public_ips = []
    for instance in reservation.instances:
        private_ips.append(instance.private_ip_address)
        public_ips.append(instance.ip_address)

    return [private_ips, public_ips, reservation]

def terminate_cluster(aws_access_key_id, aws_secret_access_key, search_term, prompt_continuation=False):

    # Grab all the infomation for clusters spawn by this tool that are still alive
    ds_reservations = {}
    conn = boto.connect_ec2(aws_access_key_id, aws_secret_access_key)

    try:
        reservations = conn.get_all_instances()
    except boto.exception.EC2ResponseError:
        print_boto_error()

    for reservation in reservations:
        if 'Initializer' in reservation.instances[0].tags and reservation.instances[0].tags['Initializer'] == 'DataStax' and reservation.instances[0].update() == 'running':
            if not reservation.instances[0].tags['Name'] in ds_reservations and search_term.lower() in reservation.instances[0].tags['Name'].lower():
                ds_reservations[reservation.instances[0].tags['Name']] = {
                    'Reservation': reservation
                }

    if not ds_reservations.keys():
        print "No existing clusters currently running!"
        print
        return

    # Prompt for cluster to destroy
    selection = common.choose("Choose the cluster to destroy (if you wish):", ds_reservations.keys(), noneOption=True)

    # Return if you do not with to kill a cluster
    if selection == 'None':
        return

    # Confirm cluster termination
    print "Confirm you wish to terminate {0} by pressing 'y'.".format(selection)
    if raw_input().lower() != 'y':
        print "Cluster was not terminated."
        print
        sys.exit()
    print

    # The actual termination command
    for instance in ds_reservations[selection]['Reservation'].instances:
        conn.terminate_instances([instance.id])

    print "Termination command complete."
    print

    if prompt_continuation:
        if raw_input('Do you wish to launch another cluster? [Y/n] ').lower() == 'n':
            sys.exit(0)
        print
