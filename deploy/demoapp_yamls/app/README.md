<p align="center">
  <img width=300 height=150 src="https://cloud.githubusercontent.com/assets/4391815/26681386/05b857c4-46ab-11e7-8c71-15a46d886834.png">
</p>


# The Simplified Twitter App

<img width="1000" alt="testbed-app" src="https://user-images.githubusercontent.com/12261551/45776137-faa62280-bc1f-11e8-9d79-f218685d8bef.png">


## Overview
The simplified Twitter App is designed and implemented in mircoservice architecture with Cassandra as the backend database cluster.
There are four services including API, User, Tweet, and Friend written in Python.
Each of the services can be vertically and horizontally scaled to better test the app performance under different traffic load with different available resources. 

## Services

**API Service** : 
   * The API service servers as an API gateway;
   * Receive incoming HTTP requests from app users;
   * Query User/Tweet/Friend services via [`GRPC`](https://grpc.io/);

**User Service** :
   * Provide APIs for user profile and login sessions;
   * Persist the login sessions in Cassandra;

**Friend Service** :
   * Provide APIs for following users and getting friend info;
   * Persist the friend info in Cassandra;

**Tweet Service** :
   * Provide APIs for tweet, newsfeed, and timeline;
   * Persist the tweet messages in Cassandra;

Each of the services is deployed in Kubernetes with a Deployment controller and a regular Service, where each pod is Istio-injected.
Note that as a comparison, the Cassandra cluster is deployed in Kubernetes with a StatefulSet and a headless service without Istio injected.
