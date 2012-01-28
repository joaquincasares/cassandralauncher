#!/usr/bin/env python

import boto
import common
import time
from decimal import Decimal, ROUND_UP

config, KEY_PAIR, PEM_HOME, HOST_FILE, PEM_FILE = common.header()
sleepTime = 1 * 60 # 1 minute
conn = None
runningFile = 'running.log'


def updateLog(oldline, newline):
    with open(runningFile, 'r') as f:
        runninglog = f.read()
    
    runninglog = runninglog.replace(oldline, newline)

    with open(runningFile, 'w') as f:
        f.write(runninglog)

def getReservationByID(aws_access_key_id, aws_secret_access_key, reservationId):
    global conn
    if not conn:
        conn = boto.connect_ec2(aws_access_key_id, aws_secret_access_key)
    reservations = conn.get_all_instances()
    
    for reservation in reservations:
        if reservationId == reservation.id:
            return reservation

def checkAndCloseExpiredInstances():
    try:
        with open(runningFile, 'r') as f:
            runninglog = f.read().strip().split('\n')
    except:
        # Wait until runninglog is created
        return
    
    # Wait until the log is populated
    if not len(runninglog):
        return

    for line in runninglog:
        status, user, ttl, birthstamp, reservationId = line.split(',')
        ttl = float(Decimal(ttl).quantize(Decimal('1.'), rounding=ROUND_UP))
        ttl = ttl * 60 * 60 - (3 * 60)
        birthstamp = float(birthstamp)

        if status == 'Running':
            if time.time() > birthstamp + ttl:
                # Find and create a list for all instances under this reservation
                reservation = getReservationByID(config.get('EC2', 'aws_access_key_id'), 
                                                 config.get('EC2', 'aws_secret_access_key'), reservationId)
                instanceList = []
                for instance in reservation.instances:
                    instanceList.append(instance.id)
                
                # Terminate these instances
                conn.terminate_instances(instanceList)

                # Update log from running a termination on these instances
                updateLog(line, line.replace('Running', 'Stopped'))
try:
    while True:
        checkAndCloseExpiredInstances()
        time.sleep(sleepTime)
except:
    print "DataStax Cluster Launcher Demo Service exiting..."
    import traceback
    traceback.print_exc()
    with open('error.log', 'w') as f:
        f.write(traceback.format_exc())
