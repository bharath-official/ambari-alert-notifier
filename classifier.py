#!/usr/bin/env python
import json
import requests
import os
import subprocess
from subprocess import Popen

#Prerequisites
#Configure mail subsystem on your headnodehost.
#sudo apt-get install mailutils

criticalAlertsJsonFile = '/tmp/critical_alerts.json'
unknownAlertsJsonFile = '/tmp/unknown_alerts.json'
warningAlertsJsonFile = '/tmp/warning_alerts.json'
sentCriticalJsonFile = '/tmp/sent_critical_list.json'
sentWarningJsonFile = '/tmp/sent_warning_list.json'
sentUnknownJsonFile = '/tmp/sent_unknown_list.json'
ignoreListFile = '/tmp/ignore_list'

#Replace this with the email address where you want notifications.
emailAddress="microsoftsample@microsoft.com"
criticalList = []
unknownList = []
warningList = []


def getAlertString(alert):
    retAlert = str(alert["Alert"]["definition_id"])
    if alert["Alert"]["host_name"]:
        retAlert = str(alert["Alert"]["definition_id"]) + alert["Alert"]["host_name"]
    return retAlert


def loadIgnoreListFromFile():
    if os.path.isfile(ignoreListFile):
        ignoreDict = {}
        with open(ignoreListFile) as ignoreJsonFileFP:
            for line in ignoreJsonFileFP:
                alertEntry = line.split()
                ignoreDict[alertEntry[0]]=alertEntry[1]
        return ignoreDict
    return


def loadPrevJsonFromFile(prevJsonFile):
    if os.path.isfile(prevJsonFile):
        with open((prevJsonFile)) as prevJsonFileFP:
            prevJson = json.load(prevJsonFileFP)
        return prevJson
    return


def loadCurrentAlerts(alerts):
    for alert in alerts:
        alert["occurrence"] = 1
        if alert["Alert"]["state"] == "CRITICAL":
            criticalList.append(alert)
        elif alert["Alert"]["state"] == "UNKNOWN":
            unknownList.append(alert)
        else:
            warningList.append(alert)


def updateSentList(currentJson, sentJsonFile):
    currentAlertSet = set()
    currentSentList = []
    if currentJson:
        for alert in currentJson:
            entry = getAlertString(alert)
            currentAlertSet.add(entry)

    sentJson=loadPrevJsonFromFile(sentJsonFile)
    if sentJson:
        for alert in sentJson:
            entry = getAlertString(alert)
            if entry in currentAlertSet:
                currentSentList.append(alert)

    if currentSentList:
        with open(sentJsonFile, 'w') as sentFileFP:
            json.dump(currentSentList, sentFileFP, indent=4)
    else:
        if os.path.isfile(sentJsonFile):
            os.remove(sentJsonFile)


def raiseAlerts(prevJson, currentJson, sentJson, sentJsonFile):

    prevAlertsDict = {}
    sentAlertSet = set()
    sendList = []
    alertString=""

    if prevJson:
        for alert in prevJson:
            entry = getAlertString(alert)
            prevAlertsDict[entry] = alert["occurrence"]

    if sentJson:
        for alert in sentJson:
            entry = getAlertString(alert)
            sentAlertSet.add(entry)

    ignoreDict = loadIgnoreListFromFile()
    if currentJson:
        for alert in currentJson:
            entry = getAlertString(alert)
            alert_definition = alert["Alert"]["definition_name"]
            if alert_definition in ignoreDict.keys():
                if prevAlertsDict:
                    if entry in prevAlertsDict.keys():
                        if int(prevAlertsDict[entry]) >= int(ignoreDict[alert_definition]):
                            if sentAlertSet:
                                if entry not in sentAlertSet:
                                    alertString += json.dumps(alert, indent=4)
                                    alertString += "\n"
                                    sendList.append(alert)
                            else:
                                alertString += json.dumps(alert, indent=4)
                                alertString += "\n"
                                sendList.append(alert)
                        else:
                            alert["occurrence"]=prevAlertsDict[entry]+1

            else:
                #Trigger email here
                if sentAlertSet:
                    if entry not in sentAlertSet:
                        alertString += json.dumps(alert, indent=4)
                        alertString += "\n"
                        sendList.append(alert)
                else:
                    alertString += json.dumps(alert, indent=4)
                    alertString += "\n"
                    sendList.append(alert)

        if currentJson[0]["Alert"]["state"] == "CRITICAL":
            criticalFile = open(criticalAlertsJsonFile, 'w')
            json.dump(currentJson, criticalFile, indent=4)
        elif currentJson[0]["Alert"]["state"] == "UNKNOWN":
            unknownFile = open(unknownAlertsJsonFile, 'w')
            json.dump(currentJson, unknownFile, indent=4)
        else:
            warningFile = open(warningAlertsJsonFile, 'w')
            json.dump(currentJson, warningFile, indent=4)

        if alertString:
            alertState = currentJson[0]["Alert"]["state"]
            mailSubject = "Ambari Alert state " + alertState
            mailContent = Popen(['/bin/echo', alertString], stdout=subprocess.PIPE)
            Popen(['/usr/bin/mail', '-s', mailSubject, emailAddress], stdin=mailContent.stdout)

        if sentJson:
            if sendList:
                for alert in sentJson:
                    sendList.append(alert)
                with open(sentJsonFile, 'w') as sentFileFP:
                    json.dump(sendList, sentFileFP, indent=4)
        else:
            if sendList:
                with open(sentJsonFile, 'w') as sentFileFP:
                    json.dump(sendList, sentFileFP, indent=4)

    updateSentList(currentJson, sentJsonFile)


def main():
    prevCriticalJson = loadPrevJsonFromFile(criticalAlertsJsonFile)
    prevUnknownJson = loadPrevJsonFromFile(unknownAlertsJsonFile)
    prevWarningJson = loadPrevJsonFromFile(warningAlertsJsonFile)
    sentCriticalJson = loadPrevJsonFromFile(sentCriticalJsonFile)
    sentUnknownJson = loadPrevJsonFromFile(sentUnknownJsonFile)
    sentWarningJson = loadPrevJsonFromFile(sentWarningJsonFile)

    # Replace hdinsightsample with your cluster name and auth admin SamplePassword with your admin username and password.
    r = requests.get('http://headnodehost:8080/api/v1/clusters/hdinsightsample/alerts?Alert/state!=OK', auth=('admin', 'SamplePassword'))
    alerts = r.json()["items"]
    loadCurrentAlerts(alerts)
    raiseAlerts(prevCriticalJson, criticalList, sentCriticalJson, sentCriticalJsonFile)
    raiseAlerts(prevUnknownJson, unknownList, sentUnknownJson, sentUnknownJsonFile)
    raiseAlerts(prevWarningJson, warningList, sentWarningJson, sentWarningJsonFile)
    #dumpCurrentListToFile()

if __name__ == "__main__":
    main()
