<p align="center">
  <img width=300 height=150 src="https://cloud.githubusercontent.com/assets/4391815/26681386/05b857c4-46ab-11e7-8c71-15a46d886834.png">
</p>

# Microservices Application Testbed

<img width="717" alt="testbed" src="https://user-images.githubusercontent.com/12261551/45770729-2f5ead80-bc11-11e8-9d38-26394aabd63b.png">

## Overview

This project creates a microservices application in a Kubernetes cluster.
The main application is a simplified Twitter-like app with Cassandra database to persist data.
To monitor the app performance, Istio and Prometheus are used to gather the metrics from the underlying Kubernetes
cluster.
With the metrics, one critical step is to control the performance to a desired state.
To acheive it, the technologies from Turbonomic, including Kubeturbo, Prometurbo, and Turbo server
are used to further monitor and control the system.

## Components

**Twitter App** :

* The simplified Twitter-like application in scalable microservice architecture.
* See [`here`](./deploy/demoapp_yamls/app) for the architecture.

**Cassandra Cluster and Exporter** :

* The [`Cassandra cluster`](http://cassandra.apache.org/) is the backend databases for the Twitter app.
* The [`Cassandra exporter`](https://github.com/criteo/cassandra_exporter) gather metrics from Cassandra and allows
  other components to query.

**Istio and Prometheus** :

* [`Istio`](https://istio.io/) is used to gather metrics for HTTP and GRPC traffic in the application.
* [`Prometheus`](https://prometheus.io/) pulls metrics from Istio and Cassandra exporters.

**Turbo Server, Kubeturbo and Prometurbo** :

* [`Turbo Server`](https://www.ibm.com/products/turbonomic) performs analysis to the kubernetes cluster and control it
  to the desired state.
* [`Kubeturbo`](https://github.com/turbonomic/kubeturbo) gathers metrics from the k8s cluster, send them to Turbo
  server, and perform actions from Turbo server.
* [`Prometurbo`](https://github.com/turbonomic/prometurbo) pulls metrics of the app and Cassandra cluster from
  Prometheus and send them to Turbo server.

**User Simulator** :

* Simulate the users' behavior to visit the app. [`Locust`](https://locust.io/) cluster is used here.

## Prerequisites

* Turbonomic 8.2+
* Kubernetes 1.7.3+
* Istio 1.0+

## Testbed Deployment

* See [`Testbed Deployment`](./deploy) section.

