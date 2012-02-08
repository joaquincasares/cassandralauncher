#!/usr/bin/env python

import os
import time
import sys

import ec2
import rax
import common

config, KEY_PAIR, PEM_HOME, HOST_FILE, PEM_FILE = common.header()

# Cluster choice dataset
clusterChoices = {
    'EC2':{
        'Ubuntu':{
            'RightScale':{
                '10.10':{
                    'User': 'root',
                    'Manifest': 'RightImage_OSS_Ubuntu_Maverick_x86_64_5.5.9.7_RC3.manifest.xml',
                    'AMI': 'ami-46f0072f'  
                },
                '10.04':{
                    'User': 'root',
                    'Manifest': 'RightImage_Ubuntu_10.04_x64_v5.6.8.1.manifest.xml',
                    'AMI': 'ami-70fb0a19'
                }
            },
            'Canonical':{
                '11.10':{
                    'User': 'ubuntu',
                    'Manifest': 'ubuntu-oneiric-11.10-amd64-server-20111205.manifest.xml',
                    'AMI': 'ami-c162a9a8'
                },
                '11.04':{
                    'User': 'ubuntu',
                    'Manifest': 'ubuntu-natty-11.04-amd64-server-20111003.manifest.xml',
                    'AMI': 'ami-71589518'
                },
                '10.10':{
                    'User': 'ubuntu',
                    'Manifest': 'ubuntu-maverick-10.10-amd64-server-20111001.manifest.xml',
                    'AMI': 'ami-1933fe70'
                },
                '10.04':{
                    'User': 'ubuntu',
                    'Manifest': 'ubuntu-lucid-10.04-amd64-server-20110930.manifest.xml',
                    'AMI': 'ami-1136fb78'
                },
            }
        },
        'CentOS':{
            'RightScale':{
                '5.6':{
                    'User': 'root',
                    'Manifest': 'RightImage_CentOS_5.6_x64_v5.7.14.manifest.xml',
                    'AMI': 'ami-49e32320'
                },
                '5.4':{
                    'User': 'root',
                    'Manifest': 'RightImage_CentOS_5.4_x64_v5.6.8.1.manifest.xml',
                    'AMI': 'ami-9ae312f3'
                }
            }
        },
        'Debian':{
            'RightScale':{
                '6.0':{
                    'User': 'root',
                    'Manifest': 'rightimage_debian_6.0.1_amd64_20110406.1.manifest.xml',
                    'AMI': 'ami-c40df0ad'
                }
            }
        }
    },
    'Rackspace': {
        'Ubuntu':{
            '11.10':{
                'Image': 119
            },
            '11.04':{
                'Image': 115
            },
            '10.10 (deprecated)':{
                'Image': 69
            },
            '10.04':{
                'Image': 112
            }
        },
        'CentOS':{
            '6.0':{
                'Image': 118
            },
            '5.6':{
                'Image': 114
            },
            '5.5 (deprecated)':{
                'Image': 51
            },
            '5.4 (deprecated)':{
                'Image': 187811
            }
        },
        'Debian':{
            '6.0':{
                'Image': 104
            },
            '5.0':{
                'Image': 103
            }
        },
        'Fedora':{
            '16':{
                'Image': 120
            },
            '15':{
                'Image': 116
            },
            '14':{
                'Image': 106
            },
            '13 (deprecated)':{
                'Image': 53
            }
        }
    }
}



def printConnections(user, private_ips, public_ips, pem_file=False):
    # Print SSH commands
    for publicIP in public_ips:
        # Allow for a quicker SSH command into the cluster
        low_security_args = ''
        if config.getboolean('Cluster', 'low_security_ssh'):
            low_security_args = ' -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'

        if pem_file:
            print '{0}{1} -i {2} {3}@{4}'.format(config.get('System', 'ssh'), low_security_args, pem_file, user, publicIP)
        else:
            print '{0}{1} {2}@{3}'.format(config.get('System', 'ssh'), low_security_args, user, publicIP)
    print

    # Print IPs (CSV)
    print ", ".join(public_ips)
    print ", ".join(private_ips)
    print

def main():
    if not config.get('Shared', 'handle'):
        sys.stderr.write("Ensure {0} is appropriately set.\n".format(config.get('Internal', 'last_location')))
        sys.stderr.write("    'Shared:handle' is missing.\n")
        sys.exit(1)

    cloud = common.choose("Choose your Cloud Testing Host: ", clusterChoices.keys())

    # Ensure access keys are setup
    if cloud == 'EC2':
        if not config.get('EC2', 'aws_access_key_id') or not config.get('EC2', 'aws_secret_access_key'):
            sys.stderr.write("Ensure {0} is appropriately set.\n".format(config.get('Internal', 'last_location')))
            sys.stderr.write("    'EC2:aws_access_key_id|aws_secret_access_key' are missing.\n")
            sys.exit(1)
        if (config.get('EC2', 'aws_access_key_id')[0] == '"' or config.get('EC2', 'aws_secret_access_key')[0] == '"' or
            config.get('EC2', 'aws_access_key_id')[0] == "'" or config.get('EC2', 'aws_secret_access_key')[0] == "'"):
            sys.stderr.write("None of the configurations should be wrapped in quotes.\n")
            sys.stderr.write("    EC2:aws_access_key_id or EC2:aws_secret_access_key appears to be.\n")
            sys.exit(1)
    if cloud == 'Rackspace':
        if not config.get('Rax', 'rax_user') or not config.get('Rax', 'rax_api_key'):
            sys.stderr.write("Ensure {0} is appropriately set.\n".format(config.get('Internal', 'last_location')))
            sys.stderr.write("    'Rax:rax_user|rax_api_key' are missing.\n")
            sys.exit(1)
        if (config.get('Rax', 'rax_user')[0] == '"' or config.get('Rax', 'rax_api_key')[0] == '"' or
            config.get('Rax', 'rax_user')[0] == "'" or config.get('Rax', 'rax_api_key')[0] == "'"):
            sys.stderr.write("None of the configurations should be wrapped in quotes.\n")
            sys.stderr.write("    Rax:rax_user or Rax:rax_api_key appears to be.\n")
            sys.exit(1)

    action = common.choose("Choose your Cloud Command: ", ['Create', 'Destroy'])

    if action == 'Destroy':
        if cloud == 'EC2':
            ec2.terminate_cluster(config.get('EC2', 'aws_access_key_id'), config.get('EC2', 'aws_secret_access_key'), config.get('Shared', 'handle'))
        if cloud == 'Rackspace':
            rax.terminate_cluster(config.get('Rax', 'rax_user'), config.get('Rax', 'rax_api_key'), config.get('Shared', 'handle'))
        sys.exit()

    reservation_size = common.typed_input(int, "Choose your Cluster Size: ")
    print

    operating_system = common.choose("Choose your Testing Operating System: " , clusterChoices[cloud].keys())

    if cloud == 'EC2':
        provider = common.choose("Choose your Image Provider: ", clusterChoices[cloud][operating_system].keys())

        version = common.choose("Choose your Operating System Version: ", clusterChoices[cloud][operating_system][provider].keys())

        image = clusterChoices[cloud][operating_system][provider][version]['AMI']
        user = clusterChoices[cloud][operating_system][provider][version]['User']
        tag = "{5} - {0} Time: {4} {1} {2} Size: {3}".format(provider, operating_system, version, reservation_size, time.strftime("%m-%d-%y %H:%M", time.localtime()), config.get('Shared', 'handle'))

        user_data = raw_input("Enter EC2 user data: ")
        print

        clusterinfo = ec2.create_cluster(config.get('EC2', 'aws_access_key_id'), config.get('EC2', 'aws_secret_access_key'),
                                        reservation_size, image, tag, KEY_PAIR,
                                        config.get('EC2', 'instance_type'), config.get('EC2', 'placement'), PEM_HOME, user_data)
        private_ips, public_ips, reservation = clusterinfo

        printConnections(user, private_ips, public_ips, PEM_FILE)
    
    if cloud == 'Rackspace':
        version = common.choose("Choose your Operating System Version: ", clusterChoices[cloud][operating_system].keys())

        image = clusterChoices[cloud][operating_system][version]['Image']
        tag = "{0} Time {4} {1} {2} Size {3}".format(config.get('Shared', 'handle'), operating_system, version, reservation_size, time.strftime("%m-%d-%y %H:%M", time.localtime())).replace(' ', '-').replace(':', '_').replace('.', '_')

        private_ips, public_ips = rax.create_cluster(config.get('Rax', 'rax_user'), config.get('Rax', 'rax_api_key'),
                                                  reservation_size, image, tag,
                                                  config.get('Rax', 'flavor'))

        printConnections(config.get('Rax', 'user'), private_ips, public_ips)



def run():
    try:
        main()
    except KeyboardInterrupt:
        print
        sys.stderr.write("Program Aborted.\n")
        print
        sys.exit(1)



if __name__ == "__main__":
    run()
