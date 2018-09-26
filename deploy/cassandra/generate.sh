#!/bin/sh

set -e

# generate gce persistent disks
gcloud compute disks create --size 100GB --zone=us-east1-b --type pd-standard pd-cass-testbed-disk-100g-0
gcloud compute disks create --size 100GB --zone=us-east1-b --type pd-standard pd-cass-testbed-disk-100g-1

# IGNORE THE MESSAGE BELOW
#New disks are unformatted. You must format and mount a disk before it
#can be used. You can find instructions on how to do this at:
#https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting

# create storage class and persistent volume objects in k8s
kubectl create -f gce-storageclass.yaml
kubectl create -f gce-persistentvolume.yaml

# create the cassandra cluster in k8s
kubectl create -f cass.yaml
