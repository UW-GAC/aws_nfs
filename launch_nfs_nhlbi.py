#! /usr/bin/env python
import  time
import  csv
import  sys
import  os.path
import  os
import  subprocess
from    argparse import ArgumentParser
from    datetime import datetime, timedelta

try:
    import boto3
except ImportError:
    print ("python boto3 not supported.")
    sys.exit(1)

# init globals
version='1.0'
msgErrPrefix='>>> Error: '
msgInfoPrefix='>>> Info: '
debugPrefix='>>> Debug: '

# def functions
def getInstance(aClient, aPvtIP):
    response = client.describe_instances(
        Filters = [
            {
                "Name": 'network-interface.addresses.private-ip-address',
                "Values": [
                    ls_privateIP
                ]
            }
        ]
    )
    return response

def waitForLaunch(aClient, aPvtIP):
    # get the instance id by checking for private ip
    response = getInstance(aClient, aPvtIP)
    noRs = len(response['Reservations'])
    while noRs == 0:
        time.sleep(5)
        response = getInstance(aClient, aPvtIP)
        noRs = len(response['Reservations'])

    instanceID = response['Reservations'][0]['Instances'][0]['InstanceId']
    return instanceID

def waitForRunning(aClient, aPvtIP):
    # get the state by checking for private IP
    response = getInstance(aClient, aPvtIP)
    runState = response['Reservations'][0]['Instances'][0]['State']['Name']
    while runState != 'running':
        pDebug('Current launch state: ' + runState)
        time.sleep(5)
        response = getInstance(aClient, aPvtIP)
        runState = response['Reservations'][0]['Instances'][0]['State']['Name']

    return

def pInfo(msg):
    print msgInfoPrefix+msg

def pError(msg):
    print msgErrPrefix+msg

def pDebug(msg):
    if debug:
        print debugPrefix+msg
def Summary(hdr):
    pInfo(hdr)
    pInfo('   Spot Launch NFS Server\tVersion: ' + version)
    pInfo('\tSpot attributes:')
    pInfo('\t\tType: ' + sa_type)
    pInfo('\t\tInterruption: ' + sa_interrupt)
    pInfo('\tLaunch specification:')
    pInfo('\t\tAvailability zone: ' + ls_availabilityZone)
    pInfo('\t\tami id: ' + ls_amiID)
    pInfo('\t\tec2 instance type: ' + ls_instanceType)
    pInfo('\t\tprivate key name: ' + ls_privateKey)
    pInfo('\t\tec2 image name tag: ' + ls_instanceName)
    pInfo('\t\tprivate ip address: ' + ls_privateIP)
    pInfo('\t\tsubnet: ' + ls_subnet)
    pInfo('\t\tsecurity groups: ' + ls_securityGroups)
    pInfo('\tVolume specification:')
    pInfo('\t\tID: ' + vol_ID)
    pInfo('\t\tDevice: ' + vol_device)
    tbegin=time.asctime()
    pInfo( '\tTime: ' + tbegin + "\n" )
# def values
def_sa_type = 'persistent'
def_sa_interrupt = 'stop'
def_ls_availabilityZone = 'us-east-1a'
def_ls_instanceType = 'm4.4xlarge'
def_ls_privateKey = 'topmed_admin'
def_ls_instanceName = 'nfs_server_topmed'
def_ls_privateIP = '172.31.33.0'
def_ls_subnet = 'subnet-7740c42b'
def_ls_securityGroups = 'sg-0b50a1a8916a0ddf2'
def_ls_amiID = 'ami-0c4e83268e71df84a'
def_vol_ID = 'vol-0deeb876fc1619994'
def_vol_device = '/dev/sdf'

# command line parser
parser = ArgumentParser( description = "Launch a spot instance of the nfs server for topmed" )

parser.add_argument( "-b", "--behavior", default = def_sa_interrupt,
                     help = "Behavior of spot interrupt - terminate, stop, hibernate [default: " +
                     def_sa_interrupt + "]" )
parser.add_argument( "-a", "--ami", default = def_ls_amiID,
                     help = "ami id [default: " + def_ls_amiID + "]")
parser.add_argument( "-v", "--volumeid", default = def_vol_ID,
                     help = "volume id [default: " + def_vol_ID + "]")
parser.add_argument( "-d", "--device", default = def_vol_device,
                     help = "volume device [default: " + def_vol_device + "]")
parser.add_argument( "-z", "--zone", default = def_ls_availabilityZone,
                     help = "availability zone [default: " + def_ls_availabilityZone + "]")
parser.add_argument( "-i", "--instance", default = def_ls_instanceType,
                     help = "instance type [default: " + def_ls_instanceType + "]")
parser.add_argument( "-k", "--key", default = def_ls_privateKey,
                     help = "private key [default: " + def_ls_privateKey + "]")
parser.add_argument( "-n", "--name", default = def_ls_instanceName,
                     help = "name of instance [default: " + def_ls_instanceName + "]")
parser.add_argument( "-p", "--privateip", default = def_ls_privateIP,
                     help = "private IP [default: " + def_ls_privateIP + "]")
parser.add_argument( "-s", "--securitygroups", default = def_ls_securityGroups,
                     help = "security group ids [default: " + def_ls_securityGroups + "]")
parser.add_argument( "-D", "--debug", help = "Output debug information [default: false]",
                     action = "store_true", default = False)
parser.add_argument("--version", action="store_true", default = False,
                    help = "Print version of " + __file__ )
parser.add_argument( "-S", "--summary", help = "Summary info only [default: false]",
                     action = "store_true", default = False)

# set the specs
sa_type = def_sa_type
ls_subnet = def_ls_subnet
args = parser.parse_args()
# set result of arg parse_args
sa_interrupt = args.behavior
ls_amiID = args.ami
ls_availabilityZone = args.zone
ls_instanceType = args.instance
ls_privateKey = args.key
ls_instanceName = args.name
ls_privateIP = args.privateip
ls_securityGroups = args.securitygroups
vol_ID = args.volumeid
vol_device = args.device
debug = args.debug
summary = args.summary

if args.version:
    print(__file__ + " version: " + version)
    sys.exit()

# summarize and check for required params
Summary("Summary of " + __file__)
if summary:
    sys.exit()

# change security groups into a list
ls_sgs = ls_securityGroups.split(",")
if debug:
    pDebug("Security groups: " + str(ls_sgs))

# populate the launch spec dictionary
ls = {'ImageId': ls_amiID,
      'InstanceType': ls_instanceType,
      'KeyName': ls_privateKey,
      'NetworkInterfaces': [
        {
            'PrivateIpAddress': ls_privateIP,
            'SubnetId': ls_subnet,
            'DeviceIndex': 0,
            'Groups': ls_sgs
        }
      ],
      'Placement': {
        'AvailabilityZone': ls_availabilityZone
      }

}
if debug:
    pDebug("launch specs " + str(ls))
# get the ec2 client
profile = 'nhlbi_dev'
session = boto3.Session(profile_name=profile)
client = session.client('ec2')

# make the request to launch
pInfo("Sending request for spot instance ...")
response = client.request_spot_instances(
    LaunchSpecification = ls,
    Type = sa_type,
    InstanceInterruptionBehavior = sa_interrupt
)
# wait for instance to launch
pInfo("Waiting for instance (ip: " + ls_privateIP + ") to get launch ...")
instanceID=waitForLaunch(client,ls_privateIP)
# set the name of the instance
pInfo("Creating a name tag " + ls_instanceName + " on the instance " + instanceID)
response = client.create_tags(
    Resources = [
        instanceID
    ],
    Tags = [
        {
            'Key': 'Name',
            'Value': ls_instanceName
        }
    ]
)

# attach the volume
if vol_ID != 'x':
    # wait for instance to get in running state
    pInfo("Waiting for instance " + ls_instanceName + " to enter running state ...")
    waitForRunning(client,ls_privateIP)
    pInfo("Attaching volume to instance " + ls_instanceName)
    response = client.attach_volume(
        Device=vol_device,
        InstanceId=instanceID,
        VolumeId=vol_ID
    )
    pDebug('Attach vol response:\n' + str(response))
else:
    pInfo('Not attaching a volue to instance ' + ls_instanceName)
