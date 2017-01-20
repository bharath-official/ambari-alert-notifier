# ambari-alert-notifier

## Prerequisites:
Configure mail subsystem on your headnodehost: sudo apt-get install mailutils

Replace email Address string with the email address where you want notifications. [Line 20]

Replace hdinsightsample with your cluster name and auth admin SamplePassword with your admin username and password. [Line 176]

## Running this script:

For testing purposes this can be run using python classifier.py

For installation on your prod environment, configure the script to run once in every 10 minutes using crontab -e. 10 minutes is the 
optimal time for this since it handles alerts on both sides of the five minute time limit set by Ambari.
