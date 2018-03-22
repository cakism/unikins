# coding=utf-8
import json, sys, requests, time, flash_unicorn, config
import unicornhat as uh
from collections import deque
from threading import Thread

jenkinsUrl = config.jenkinsUrl
buildQueue = deque(maxlen=7) ## since we only have 8 LED's in a row, and last should blink! :)
uh.set_layout(uh.PHAT)
uh.brightness(0.4)
devSnapBuildStatus = 'blue'

def startUpAndPopulate():
    print("Starting up...")
    flash_unicorn.flash_rainbow_once()
    json = requests.get(jenkinsUrl).json()
    #print(json)
    lastSuccessfulBuild = json['lastSuccessfulBuild']['number']
    lastUnsuccessfulBuild = json['lastUnsuccessfulBuild']['number']
    lastCompletedBuild = json['lastCompletedBuild']['number']

    failedBuilds = (lastCompletedBuild-lastSuccessfulBuild)
    successfulBuilds = (lastCompletedBuild-lastUnsuccessfulBuild)

    if failedBuilds > 0:
        buildQueue.append(True) ##Last successful build
        for i in range(1, failedBuilds):
            buildQueue.append(False)
    elif successfulBuilds > 0:
        buildQueue.append(False) ##Last unsuccessful build
        for i in range(1, successfulBuilds):
            buildQueue.append(True)
    lastBuildStatus = lastCompletedBuild == lastSuccessfulBuild
    buildQueue.append(lastBuildStatus)
    print("Starting queue: ")
    print(buildQueue)
    return


def checkDevSnap():
    print("Starting checkDevSnap")
    sleepTime = 10
    json = requests.get(jenkinsUrl).json()
    lastBuildBuilt = json['lastBuild']['number']

    while True:
        print("Waiting 10s before next devsnap poll...")
        time.sleep(sleepTime)
        try:
            json = requests.get(jenkinsUrl).json()
        except Exception as e:
            print("Exception in request to jenkins api "+str(e))
            uh.off()
            sys.exit()

        lastSuccessfulBuild = json['lastSuccessfulBuild']['number']
        lastCompletedBuild = json['lastCompletedBuild']['number']
        lastBuild = json['lastBuild']['number']
        lastBuildStatus = lastCompletedBuild == lastSuccessfulBuild
        nextBuildNow = json['nextBuildNumber']
        global devSnapBuildStatus
        devSnapBuildStatus = json['color']
        if lastBuild > lastBuildBuilt:
            buildQueue.append(lastBuildStatus)
            lastBuildBuilt = lastBuild
            if lastBuildStatus:
                #Do Rainbow
                flash_unicorn.flash_rainbow_once()
                print("Build " + str(lastBuild) + " finished successfully!!")
            else:
                #Do Angry
                flash_unicorn.flash_warning_once()
                print("Build " + str(lastBuild) + " failed miserably...")

            print(buildQueue)
        else:
            print("Still building " + str(lastBuild))
        printBuildQueue()

def checkCITest():
    print("Starting checkCITest")

def printBuildQueue():
    for idx, build in enumerate(buildQueue):
        #print("Index: " + str(idx) + " Successful: " + str(build))
        if build == True:
            uh.set_pixel(7-idx, 0, 0, 255, 0)
        else:
            uh.set_pixel(7-idx, 0, 255, 0, 0)


def main():
    ####### Start loop from here
    try:
        devSnapThread = Thread(target=checkDevSnap, args=())
        devSnapThread.start()
        ## Offset start citest with 5 seconds to avoid build animations at the same time
        time.sleep(5)
        citestThread = Thread(target=checkCITest, args=())
        citestThread.start()
    except (KeyboardInterrupt, SystemExit):
        print("Error!! Error!! Error!!")
        uh.off()
        sys.exit()

    #Print queue in leds
    try:
        while True:
            ## Check if building: color : red/blue_anime = building, red = locked and not building
            ## Kolla "claimed" : true, på bygge-api
            #printBuildQueue()
            global devSnapBuildStatus
            if 'blue' in devSnapBuildStatus:
                uh.set_pixel(0,0,0,0,255)
            if 'red' in devSnapBuildStatus:
                uh.set_pixel(0,0,255,0,0)
            uh.show()
            if 'anime' in devSnapBuildStatus:
                time.sleep(0.3)
                uh.set_pixel(0,0,0,0,0)
                uh.show()
                time.sleep(0.3)
    except (KeyboardInterrupt, SystemExit):
        uh.off()
        sys.exit()

### RUN IT! ###
startUpAndPopulate()
main()
