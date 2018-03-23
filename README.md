# NFS on AWS  #

This project contains files to facilitate launching and configuring an NFS server that exports an external EBS volume containing TOPMed project data to various NFS clients.  The NFS clients include:
1. analysis pipeline jobs running on AWS batch
2. TOPMed docker instances running on AWS
3. Other clients that have permissions via the security groups associated with the NFS server

## Installing and Setting Up NFS Server on Ubuntu 16.04 ##
A description of the general process is described in the following URL:
```{r}
https://help.ubuntu.com/community/SettingUpNFSHowTo
```

The basic steps are:
1. Install NFS server kernel
2. Bind the folders to export (or share) to an exported bind point
3. Update `/etc/exports` file
4. Update `/etc/fstab` file

## Background with NFS Server on AWS ##

In AWS, we want to do the following:
1. From the server export an external EBS volume that has been previously initialized (i.e., file system created and project data added) and attached  
2. When launching the server, utilize a custom AWS AMI which has NFS server installed and can easily be configured to export the external EBS volume
3. Provide a cost effective way to use spot pricing when launching the NFS Server
4. Provide an efficient way to terminate and re-launch the NFS server with a different computer instance type.
5. Insure that the NFS clients have minimal if any impact when the NFS server is re-launched

## Creating an NFS Server Instance on AWS ##

To create the NFS server on AWS the following steps are done:
1. Terminate the previously launched NFS server (if applicable)
2. From a properly configured computer (see next section) execute the server launch program `launch_nfs.py`
3. From the AWS console, associate an elastic IP address to the newly launched server
4. From an authorized computer, connect to the newly launched server and execute `configure_nfs_server.bash`

The last step includes rebooting the NFS server.  After rebooting, the NFS server is functional and accessible by NFS clients.

## launch_nfs.py ##
This file can run on any computer that has been configured as follows:
1. Python is installed
2. Python API to AWS (boto3) is installed
3. AWS command line interface has been installed and configured to access the TOPMed account on AWS

`launch_nfs.py` program launches the NFS server using spot pricing and attaches the external EBS volume to the running NFS server instance.  It also assigns a private IP address to the server insuring that AWS clients (e.g., AWS batch service) do not require changes in order to connect successfully to the NFS server.

The program has numerous options to configure the server.  The configuration includes:
1. Spot attributes of a `persistent` type and termination behavior of `stop`.
2. Launch specifications including availability zone, ec2 instance type, private IP address, security groups
3. Volume ID and device name of the volume attach to the launched server

Examples of running `launch_nfs.py`:
```{r}
# Output help
python launch_nfs.py -h
# Output of summary of the default configurations
python launch_nfs.py -S

# Launch an NFS server with default configurations
python launch_nfs.py

# Launch an NFS server with a different private IP
python launch_nfs.py -p 172.255.33.1
```
## configure_nfs_server.bash ##
This program is run on the launched NFS server.  A version of this program exists in the custom AMI located in the user `ubuntu` home directory.  It is available when the server is launched from the custom AMI.

The program does the following:
1. Gets information about the attached EBS volume (e.g.,the UUID)
2. If necessary, create mount points for the external EBS volume and the exported folder
3. Binds the external EBS volume to the exported mount points
4. Update /etc/exports and /etc/fstab appropriately
5. Reboots the computer

`configure_nfs_server.bash` is configured with the following defaults:
1. The external EBS mount point is /ext_ebs
2. The exported EBS mount point is /export_ebs
3. The `/etc/exports` files enables all client computers to connect (security is enforced using AWS security groups)
4. Both the mounting of the external EBS volume and the exported EBS folder is appended to the `/etc/fstab` file

By exercuting the program without any command line arguments, the server will be configured with the above configuration.
