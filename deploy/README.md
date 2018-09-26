<p align="center">
  <img width=300 height=150 src="https://cloud.githubusercontent.com/assets/4391815/26681386/05b857c4-46ab-11e7-8c71-15a46d886834.png">
</p>


# Kubernetes Testbed Deployment

<img width="717" alt="testbed" src="https://user-images.githubusercontent.com/12261551/45770729-2f5ead80-bc11-11e8-9d38-26394aabd63b.png">


## Overview
To deploy the testbed, follow the steps below.

## Steps

**1. Install Istio** : 
   * Follow the [`instructions`]( https://istio.io/docs/setup/kubernetes/quick-start/) to install Istio;
   
**2. Deploy Cassandra Cluster and Exporter** :
   * Use the [`yaml file`](./cassandra/cass.yaml) to deploy Cassandra and its exporter;
   (See detail [`here`](https://github.com/MySocialApp/kubernetes-helm-chart-cassandra))
   * Note: depending on the cloud provider, additional instructions may be needed for the persistent disks/volumes;

**3. Deploy Twitter App** :
   * Use the [`yaml file`](./app/deploy-with-istio.yaml) to deploy the container pods with Istio injected;
   * Once deployed, users can go to *http://<APP_IP>:8699* and login with username as any positive number, 
   e.g., 100 and password same as the username.

**4. Configure Istio/Prometheus/Grafana** :
   * Deploy the [`yaml file`](./metrics/ip.turbo.metric.yaml) for the Istio/Prometheus integration;
   * Add Cassandra nodes to the Prometheus target list:
   ```yaml
    - job_name: 'cassandra-nodes'
      static_configs:
      - targets: ['<Cassandra_Node_1_IP>:8080','1<Cassandra_Node_2_IP>:8080’]
  ```
   * Optional: import the [`dashboard`](./metrics/cass-testbed-grafana-dashboard.json) to Grafana;

**5. Install Turbo Server, Kubeturbo and Prometurbo** :
   * [`Turbo server installation guide`](https://turbonomic.com/wp-content/uploads/2018/09/Turbonomic_INSTALL_PRINT_6.2.pdf)
   * [`Deploy Kubeturbo`](https://github.com/turbonomic/kubeturbo/tree/master/deploy)
   * [`Deploy Prometurbo`](https://github.com/turbonomic/prometurbo/tree/master/deploy)

**6. Deploy User Simulator (Locust)** :
   * *Run locally*: [`install Locust`](https://docs.locust.io/en/stable/installation.html) locally. 
   Replace *$API_SERVICE_IP* in [`local_run.sh`](./locust/local_run.sh) with the public IP of the twitter app. 
   Run the script and browse its [`UI`](http://localhost:8089) to start the simulation.
   * *Locust cluster*: Deploy the Locust cluster with the [`locust-cluster.yaml`](./locust/locust-cluster.yaml) after configuring the IP fields inside.
               See more detail [`here`](https://github.com/GoogleCloudPlatform/distributed-load-testing-using-kubernetes).
