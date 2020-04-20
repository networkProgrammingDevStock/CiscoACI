import sys
import time
import datetime
import requests
import json
import urllib3

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



if __name__ == "__main__":
    #First, we get the starting time, in fact, there is no effect to take this,
    #but, I like to show what time process takes,
    startingTime = time.time()
    #Creating an instance of Apic class,
    #Simply, use ip address of sdn controller web interface, and your login credentials,
    exampleApic = Apic("ManagementIpAddressOfYourACIWebScreen", "Username", "Password")
    #After, creating instance, try to get authentication with sdn controller
    exampleApic.login()
    #And, let's get what we have in physical network
    exampleApic.getFabric()
    #For showing all of what you have, you can run this part
    """
    for pod in exampleApic.pods:
        print("Pod name is " + pod.name)
        for device in pod.devices:
            print("\t Device name: %s \tmodel: %s \t serial: %s \tdn: %s" % (device.name, device.model, device.serial, device.dn))
            for interface in device.interfaces:
                print("\t\t Interface id : {0} \t speed: {1} \t admin state: {2} \t operational state: {3} \t sfp serial : {4} \t dn: {5} \t lastStateChange: {6}".format(interface.name, interface.speed, \
                      interface.adminState, interface.operationalState, str(interface.sfpSerial), interface.dn, interface.lastLinkStateChange))
    """

    #Or you can run this part, to find sfp's on ports, staying on down state more than 10 days, and having no deployed epg
    acceptableDaysToBeSurePortIsUnused = 10
    for pod in exampleApic.pods:
        print("Pod name is " + pod.name)
        for device in pod.devices:
            #print("\t Device name: %s \tmodel: %s \t serial: %s \tdn: %s" % (device.name, device.model, device.serial, device.dn))
            for interface in device.interfaces:
                if interface.adminState != 'up' and interface.operationalState != 'up' and interface.sfpSerial and \
                   (datetime.date.today() - interface.lastLinkStateChange).days > acceptableDaysToBeSurePortIsUnused and len(interface.deployedEPGs) == 0:
                    print(interface.dn + "\t" + interface.adminState + "\t" + interface.operationalState + "\t" + interface.sfpModel + "\t" + interface.sfpSerial + '\t Deployed epg count ' + str(len(interface.deployedEPGs)))
                    print("Last Up time: " + str(interface.lastLinkStateChange) + " (1970-01-01 means that it has never been up)")

    print("Process take %s seconds to complete" % str(time.time() - startingTime))


