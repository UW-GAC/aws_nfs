#!/bin/bash
# configure an nfs server where an external ebs volume is mounted and is to be
# shared

f () {
    errcode=$? # save the exit code as the first thing done in the trap function
    echo "error $errorcode"
    echo "the command executing at the time of the error was"
    echo "$BASH_COMMAND"
    echo "on line ${BASH_LINENO[0]}"
    # do some error handling, cleanup, logging, notification
    # $BASH_COMMAND contains the command that was being executed at the time of the trap
    # ${BASH_LINENO[0]} contains the line number in the script of that command
    # exit the script or return to try again, etc.
    exit $errcode  # or use some other value or do return instead
}
trap f ERR
# cmd line arguments
EBS_DEVICE=${1:-nvme1n1}
EBS_MOUNT=${2:-/ext_ebs}
EBS_EXPORT=${3:-/export_ebs}
# check for device
echo "Checking the ebs device /dev/$EBS_DEVICE"
lsblk /dev/$EBS_DEVICE > /tmp/check_device.log 2>&1
# create a mount point if it does already exist
echo "Mount /dev/$EBS_DEVICE to $EBS_MOUNT"
if [ ! -d $EBS_MOUNT ]; then
    sudo mkdir $EBS_MOUNT
fi
# mount
sudo mount /dev/$EBS_DEVICE $EBS_MOUNT
# get the UUID
EBS_UUID=`findmnt /ext_ebs -o UUID -n`
echo "EBS UUID is $EBS_UUID; bind $EBS_MOUNT to $EBS_EXPORT"
# bind to the exported ebs volume
if [ ! -d $EBS_EXPORT ]; then
    sudo mkdir $EBS_EXPORT
fi

sudo mount --bind $EBS_MOUNT $EBS_EXPORT

echo "Update /etc/exports and /etc/fstab"
# append to /etc/exports
echo "$EBS_EXPORT *(rw,nohide,insecure,no_subtree_check,async,no_root_squash)" | sudo tee -a /etc/exports

# append mounts to /etc/fstab
echo "UUID=$EBS_UUID   $EBS_MOUNT   ext4    defaults,nofail        0       2" | sudo tee -a /etc/fstab
echo "$EBS_MOUNT $EBS_EXPORT none bind" | sudo tee -a /etc/fstab

# reboot
echo "Reboot ..."
#sudo reboot
