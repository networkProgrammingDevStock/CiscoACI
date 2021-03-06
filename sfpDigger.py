import sys
import time
import datetime
import requests
import json
import urllib3
import click

print("Libraries are imported")

urllib3.disable_warnings()

class Interface():
    def __init__(self, name):
        '''
        This class is representative of physical interfaces of dc switches
        '''
        self.name = name
        self.dn = ''
        self.adminState = ''
        self.operationalState = ''
        self.speed = ''
        self.sfpModel = 'unset'
        self.sfpSerial = 'unset'
        self.lastLinkStateChange = datetime.datetime(1970, 1, 1)
        self.deployedEPGs = []


class Device():
    def __init__(self, name):
        '''
        This class is representative of pyhsical switches in Pod
        '''
        self.name = name
        self.serial = ''
        self.model = ''
        self.dn = ''
        self.interfaces = []


class Pod():
    def __init__(self, name):
        '''
        This class is representative of a group of switches combined as a data centre pod
        '''
        self.name = name
        self.devices = []


class Apic:
    def __init__(self, managementIP, username, password):
        '''
        This class is representative of Cisco Aci sdn controller,
        Mainly; it holds authentication process, get and post data operations, and
        organizing obtained data with specific functions
        '''
        self.IP = managementIP
        self.username = username
        self.password = password
        self.cookies = {}
        self.headers = {
            'content-type': "application/json",
            'cache-control': "no-cache"
        }
        self.authentication = False
        self.pods = []

    def login(self):
        try:
            AUTHENTICATION_URL = "https://%s/api/aaaLogin.json" % self.IP
            AUTHENTICATION_DATA = "{\"aaaUser\":{\"attributes\":{\"name\":\"%s\" , \"pwd\":\"%s\"}}}" % (
            self.username, self.password)
            auth = json.loads(requests.post(AUTHENTICATION_URL, AUTHENTICATION_DATA, self.headers, verify=False).text)
            auth_token = auth['imdata'][0]['aaaLogin']['attributes']['token']
            self.cookies['APIC-Cookie'] = auth_token
            print(auth_token)
            self.authentication = True
            print("You are authenticated to Apic on ", self.IP)
        except:
            e = sys.exc_info()[0]
            print("Token failed with exception: %s" % e)
        finally:
            print("Login process to Apic on %s is finished" % self.IP)

    def getData(self, URL):
        if self.authentication:
            Data = json.loads(requests.get(url=URL, cookies=self.cookies, verify=False).text)["imdata"]
            return Data
        else:
            return False

    def getPods(self):
        podsJson = self.getData("https://%s/api/node/class/fabricPod.json" % self.IP)
        if podsJson:
            #print(podsJson)
            for pod in podsJson:
                self.pods.append(Pod(pod['fabricPod']['attributes']['dn'].split('/')[1]))

    def getDevices(self):
        for pod in self.pods:
            devicesOfPodJson = self.getData("https://%s/api/node/mo/topology/%s.json?query-target=children&target-subtree-class=fabricNode" % (self.IP, pod.name))
            for fabricNode in devicesOfPodJson:
                tempDevice = Device(fabricNode['fabricNode']['attributes']['name'])
                tempDevice.model = fabricNode['fabricNode']['attributes']['model']
                tempDevice.serial = fabricNode['fabricNode']['attributes']['serial']
                tempDevice.dn = fabricNode['fabricNode']['attributes']['dn']
                #Obtain interfaces of devices
                interfacesOfDeviceJson = self.getData("https://%s/api/node/class/%s/l1PhysIf.json?rsp-subtree=children&rsp-subtree-class=ethpmPhysIf" % (self.IP, tempDevice.dn))
                #print(interfacesOfDeviceJson)
                if interfacesOfDeviceJson:
                    print("Digging interfaces for " + tempDevice.name)
                    for interface in interfacesOfDeviceJson:
                        tempInterface = Interface(interface['l1PhysIf']['attributes']['id'])
                        tempInterface.dn = interface['l1PhysIf']['attributes']['dn']
                        tempInterface.adminState = interface['l1PhysIf']['attributes']['adminSt']
                        tempInterface.operationalState = interface['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['operSt']
                        timeSentence = interface['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']['lastLinkStChg']
                        tempInterface.lastLinkStateChange = datetime.date(int(timeSentence.split('T')[0].split('-')[0]), int(timeSentence.split('T')[0].split('-')[1]), int(timeSentence.split('T')[0].split('-')[2]))
                        tempInterface.speed = interface['l1PhysIf']['attributes']['speed']
                        #Getting sfp serial through api, we have to gel a call from api
                        sfpInfoOfInterface = self.getData("https://%s/api/node/mo/%s/phys.json?query-target=children&target-subtree-class=ethpmFcot" % (self.IP, tempInterface.dn))
                        if sfpInfoOfInterface:
                            try:
                                tempInterface.sfpModel = sfpInfoOfInterface[0]['ethpmFcot']['attributes']['guiPN']
                                tempInterface.sfpSerial = sfpInfoOfInterface[0]['ethpmFcot']['attributes']['guiSN']
                            except:
                                print(tempInterface.dn)
                                pass
                            finally:
                                pass

                        #Getting deployed EPGs on interface
                        deployedEpgInfoOfInterface = self.getData("https://%s/api/node/mo/%s.json?rsp-subtree-include=full-deployment&target-node=all&target-path=l1EthIfToEPg" % (self.IP, tempInterface.dn))
                        try:
                            for item in deployedEpgInfoOfInterface:
                                for child in item['l1PhysIf']['children'][0]['pconsCtrlrDeployCtx']['children']:
                                    #print(child['pconsResourceCtx']['attributes']['ctxDn'])
                                    tempInterface.deployedEPGs.append(child['pconsResourceCtx']['attributes']['ctxDn'])
                        except:
                            pass
                        finally:
                            pass
                        tempDevice.interfaces.append(tempInterface)
                        del tempInterface
                pod.devices.append(tempDevice)
                del tempDevice

    def getFabric(self):
        self.getPods()
        self.getDevices()





@click.group(invoke_without_command=True)
# user input ip address
@click.option("--ip", help="Enter ip address or url of your ACI web screen")
# prompt user for input username
@click.option("--username", help="username when you use to log in your Aci", prompt=True)
# prompt user for input password
@click.option("--password", help="password when you use to log in your Aci", prompt=True)
#mode of operation full means all of the sfp's, unused means unused sfps
@click.option("--mode", help="all:\t all of the sfp in fabric\nunused: sfp's on ports staying down for 10 days and having no deployed epg", prompt=True)
@click.pass_context
def inputParser(ctx, ip, username, password,mode):
    if mode == 'all' or mode == 'unused':
        # First, we get the starting time, in fact, there is no effect to take this,
        # but, I like to show what time process takes,
        startingTime = time.time()
        ACI_Fabric = Apic(ip, username, password)
        ACI_Fabric.login()
        ACI_Fabric.getFabric()
        if mode == 'unused':
            unusedSfpCounter = 0
            acceptableDaysToBeSurePortIsUnused = 10
            for pod in ACI_Fabric.pods:
                print("Pod name is " + pod.name)
                for device in pod.devices:
                    #print("\t Device name: %s \tmodel: %s \t serial: %s \tdn: %s" % (device.name, device.model, device.serial, device.dn))
                    for interface in device.interfaces:
                        if interface.adminState != 'up' and interface.operationalState != 'up' and interface.sfpSerial and \
                           (datetime.date.today() - interface.lastLinkStateChange).days > acceptableDaysToBeSurePortIsUnused and len(interface.deployedEPGs) == 0:
                            print("Location:" + interface.dn + "\tAdmin State:" + interface.adminState + "\tOperational State:" + interface.operationalState + "\t Model:" + interface.sfpModel + "\tSN:" + interface.sfpSerial + '\t Deployed epg count ' + str(len(interface.deployedEPGs)))
                            print("Last Up time: " + str(interface.lastLinkStateChange) + " (1970-01-01 means that it has never been up)")
                            unusedSfpCounter += 1
            print("Result obtained from UNUSED SFP MODE:\nYou have " + str(unusedSfpCounter) + " unused sfps in ACI located on ip " + ACI_Fabric.IP)
        if mode == 'all':
            sfpCount = 0
            for pod in ACI_Fabric.pods:
                print("Pod name is " + pod.name)
                for device in pod.devices:
                    #print("\t Device name: %s \tmodel: %s \t serial: %s \tdn: %s" % (device.name, device.model, device.serial, device.dn))
                    for interface in device.interfaces:
                        if interface.sfpSerial:
                            print("Location:" + interface.dn + "\tAdmin State:" + interface.adminState + "\tOperational State:" + interface.operationalState + "\t Model:" + interface.sfpModel + "\tSN:" + interface.sfpSerial + '\t Deployed epg count ' + str(len(interface.deployedEPGs)))
                            sfpCount += 1
            print("Result obtained from ALL SFP MODE:\nYou have " + str(sfpCount) + " sfps in ACI located on ip " + ACI_Fabric.IP)
        print("Process take %s seconds to complete" % str(time.time() - startingTime))
    else:
        print('Invalid operation mode is written,\nPlease use "all" or "unused" keyword after --mode')

if __name__ == "__main__":
    inputParser()


