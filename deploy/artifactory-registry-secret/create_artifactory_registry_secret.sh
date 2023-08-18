#!/bin/bash
kubectl create secret docker-registry artifactory-registry-secret \
  --docker-server=https://docker-na.artifactory.swg-devops.com/hyc-turbo-devops-team-docker-local \
  --docker-username="$ARTIFACTORY_USERNAME" \
  --docker-password="$ARTIFACTORY_PASSWORD" \
  --docker-email="$ARTIFACTORY_USERNAME"
