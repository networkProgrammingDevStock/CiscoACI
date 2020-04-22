Cisco ACI sfpDigger

Original Author: Sadık Turgut - st.sadik.turgut@gmail.com


Description

sfpDigger is a tool that mainly purposes giving informations about sfps and their usage in ACI Fabric,

Especially, at reporting level, it is a little bit hard to say that there are x number of sfp in fabric or there are x number of sfps are installed but not used in a fabric. This project can give the information where sfps are located and total count of sfps, fabric contains or total count of unused sfps with detailed information like model, serial number and location (pod, device and port)

sfpDigger can be fired from cli with some arguments, there is no need to change code except the situation a development is required,

It consumes rest api of Cisco Api, it means that it takes a token with given username and password and some get responses, it doesn't do any configurational changes.

If you are interested with requests in code, you can look your ACI screen right top and click 'Help and Tools', then choose 'Show Api Inspector'. This screen can show what urls are used to obtain informations shown on WEB GUI where you click. Moreover, if you are interested in more deep knowledge, you can search via Managed Object Tree of Cisco ACI, you can read this:
https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/1-x/aci-fundamentals/b_ACI-Fundamentals/b_ACI-Fundamentals_chapter_010001.html

If you have any problem to run this code, or any suggestion to develop this, you can reach me via st.sadik.turgut@gmail.com


Installation
Environment

Required

    Python 3.7+

Recommended:

    Git (to install from github)

Downloading and installing

Just clone this repo on your platform

git clone https://github.com/networkProgrammingDevStock/CiscoACI.git

and go to project folder

cd CiscoACI

Sure you can use pip to install some additional packages:

pip install -r requirements.txt

if you are using Windows, and you add python do batch, means you can run python from command prompt,
try this

python -m pip install -r requirements.txt

If you have two versions of python on your platform, please be sure what command to get in python3,
Sometimes, keyword 'python' can call python3 idle, and sometimes that can be 'python3'. If 'python3' calls
the newer version of python, use line as below,

python3 -m pip install -r requirements.txt


Usage

First be sure, can you reach our ACI ip address over where this code placed,
Let's say your ACI web url https://A.B.C.D/#, you will use A.B.C.D(of course, this is an ip address)
If you reach your ACI web GUI with url like https://ourACIonProdorWhatever.domain.com/#, try to ping this section 'ourACIonProdorWhatever.domain.com' to get ip address of your ACI Web address. In fact, you can use 'ourACIonProdorWhatever.domain.com' as a credential though to code, but, sometimes, script can not use dns services, and I am not suggest or solve that yet,

There are two modes of operation in sfpDigger, 

1-  You can get all of the sfps information in your fabric in a way:

- change to directory with 'cd CiscoACI'

- to run sfpDigger in 'all' mode,

python sfpDigger.py --ip A.B.C.D --username YourUsername --password YourPassword --mode all

- after running that you will outputs like:

Libraries are imported

TOKEN OBTAINED FROM YOUR ACI, it is a hash 

You are authenticated to Apic on  A.B.C.D

Login process to Apic on A.B.C.D is finished

Digging interfaces for Leaf1

Digging interfaces for Leaf4

Digging interfaces for Leaf3

Digging interfaces for Leaf8

Digging interfaces for Spine12

Digging interfaces for Leaf2

Digging interfaces for Leaf5

Digging interfaces for Leaf7

Digging interfaces for Leaf6

Digging interfaces for Spine11

Pod name is Pod_HowYouNamed

Location:topology/pod-1/node-1/sys/phys-[eth1/48]     Admin State:down        Operational State:down   Model:MODELA SN:SERIALXXXX           Deployed epg count 0

Location:topology/pod-1/node-2/sys/phys-[eth1/36]     Admin State:up        Operational State:up   Model:MODELA  SN:SERIALXXXX           Deployed epg count 17 

Location:topology/pod-1/node-11/sys/phys-[eth1/37]     Admin State:down        Operational State:down   Model:MODELB  SN:SERIALXXXX           Deployed epg count 0

Location:topology/pod-1/node-12/sys/phys-[eth1/38]     Admin State:up        Operational State:up   Model:MODELB SN:SERIALXXXX           Deployed epg count 0
.
.
.
Result obtained from ALL SFP MODE:

You have 1247 sfps in ACI located on ip A.B.C.D

Process take 123.456 seconds to complete


2-  You can get unused sfps information in your fabric, in this mode, script goes a way like if a port down for 10 days and there is no deployed epg, this port is unused, you can tune this '10' days value wtih changing 'acceptableDaysToBeSurePortIsUnused' variable value in sfpDigger.py:

- change to directory with 'cd CiscoACI'

- to run sfpDigger in 'unused' mode,

python sfpDigger.py --ip A.B.C.D --username YourUsername --password YourPassword --mode unused

- after running that you will outputs like:

Libraries are imported

TOKEN OBTAINED FROM YOUR ACI, it is a hash 

You are authenticated to Apic on  A.B.C.D

Login process to Apic on A.B.C.D is finished

Digging interfaces for Leaf1

Digging interfaces for Leaf4

Digging interfaces for Leaf3

Digging interfaces for Leaf8

Digging interfaces for Spine12

Digging interfaces for Leaf2

Digging interfaces for Leaf5

Digging interfaces for Leaf7

Digging interfaces for Leaf6

Digging interfaces for Spine11

Pod name is Pod_HowYouNamed

Location:topology/pod-1/node-1/sys/phys-[eth1/48]     Admin State:down        Operational State:down   Model:MODELA SN:SERIALXXXX           Deployed epg count 0

Last Up time: 2020-04-11 (1970-01-01 means that it has never been up)

Location:topology/pod-1/node-2/sys/phys-[eth1/36]     Admin State:down        Operational State:down   Model:MODELA  SN:SERIALXXXX           Deployed epg count 17 

Last Up time: 1970-01-01 (1970-01-01 means that it has never been up)

Location:topology/pod-1/node-11/sys/phys-[eth1/37]     Admin State:down        Operational State:down   Model:MODELB  SN:SERIALXXXX           Deployed epg count 0

Last Up time: 2019-11-08 (1970-01-01 means that it has never been up)

Location:topology/pod-1/node-12/sys/phys-[eth1/38]     Admin State:down        Operational State:down   Model:MODELB SN:SERIALXXXX           Deployed epg count 0

Last Up time: 1970-01-01 (1970-01-01 means that it has never been up)

.
.
.
Result obtained from UNUSED SFP MODE:

You have 11 unused sfps in ACI located on ip A.B.C.D

Process take 123.456 seconds to complete




   
