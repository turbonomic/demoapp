<p align="center">
  <img width=300 height=150 src="https://cloud.githubusercontent.com/assets/4391815/26681386/05b857c4-46ab-11e7-8c71-15a46d886834.png">
</p>

### Prerequisite
The following prerequisite must be met before the install:
* Kubernetes 1.22+, or OCP 4.11+.
* A preconfigured `StorageClass`. This is needed by `Cassandra` to dynamically provision PVs. 

### Install Istio

Follow the [`instructions`]( https://istio.io/latest/docs/setup/getting-started/) to install `Istio` (**1.17.1** at the time
of writing).
The recommended install method is `istioctl`:

* [Download](https://istio.io/latest/docs/setup/getting-started/#download) the **Istio** distribution and upack it.
* [Install](https://istio.io/latest/docs/setup/getting-started/#install) **Istio**:
    * For vanilla Kubernetes cluster, use the `demo` profile.
    * For vendor-specific cluster, use the corresponding profile
      outlined [here](https://istio.io/latest/docs/setup/platform-setup/).
    * For example, use the following command to install `Istio` in an Openshift cluster:
      ```shell
      $ istioctl install --set profile=openshift -y
      ```
    * Install the `Prometheus` add-on.
      ```shell
      $ kubectl apply -f samples/addons/prometheus.yaml
      ```
* Verify all pods are running:
  ```shell
  $ kubectl -n istio-system get po
  NAME                                    READY   STATUS    RESTARTS   AGE
  istio-ingressgateway-7954975d69-wtdnp   1/1     Running   0          14d
  istiod-584b74f7f9-ll8z8                 1/1     Running   0          14d
  prometheus-6549d6bdcc-jtkcj             2/2     Running   0          13d
  ```
* Verify prometheus dashboard is up and running:
  ```shell
  $ istioctl dashboard prometheus
  ```
* Create a `demoapp` namespace and enable istio auto-injection:
  ```shell
  $ kubectl create ns demoapp
  $ kubectl label namespace demoapp istio-injection=enabled
  namespace/demoapp labeled
  ```

### Install Testbed

Use Helm to install the testbed. The Helm charts packages Cassandra, TwitterApp and Locust workload generator to make the installation easier.

* Specify proper settings in `values.yaml`

   **Parameter** | **Default Value**          | **Type** |  **Description**
    ---|----------------------------|----------|--------------
   `image.repository` | `icr.io/cpopen/turbonomic` | String   | The container image repository
   `image.tag` | `1.0`                      | String   | The image tag for demoapp containers
   `image.locustTag` | `1.0`                      | String   |  The image tag for Locust load generator containers
   `image.pullPolicy` | `IfNotPresent`             | String   | Specify `IfNotPresent`, or `Always`
   `instana.enabled` | `false`                    | Boolean  | Enable **Instana** monitoring. Do not enable if **Istio** service mesh is deployed and Istio sidecar injection is enabled
   `grpc.max_connection_age_ms` |                            | Number   | Specify the time after which server will close the gRPC channel to force client reconnection for load balancing. Do not specify when service mesh is enabled
   `locust.time_slot_probability` | `"1.0,0.1"`                | String   | Specify the alternating traffic patterns between `0.0` (no traffic) and `1.0` (full traffic load)
   `locust.time_slo_probability_step_in_min` | `30`                       | Number   | Specify the time interval before traffic patterns change
   `cassandra.exporter.enabled` | `true`                     | Boolean  | Specify if cassandra exporter should be enabled
   `cassandra.persistence.size` | `30Gi`                     | String   | Specify the storage size for each cassandra node
   `cassandra.config.cluster_size` | `3`                        | Number   | Sepcify the size of cassandra cluster
   `cassandra.config.seed_size` | `2`                        | Number   | Specify the seed size of cassandra cluster
   `istioingress.enabled` | `true`                     | Boolean  | Enable **Istio** ingress. Do not enable if **Istio** is not installed


* Update the helm charts:
  ```shell
  $ cd deploy/demoapp
  $ helm dependency update
  Saving 1 charts
  Deleting outdated charts
  ```
* Deploy the charts in the `demoapp` namespace:
  ```shell
  $ cd deploy
  $ helm -n demoapp install demoapp ./demoapp
  ```

### Verify the Install

* Once deployed, users can visit the website at *http://<APP_IP>* where APP_IP is the ingress IP of the **Istio**
  ingress
  gateway, which can be found by:
  ```console
  kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
  ```
* Login with username as any positive integer between 1 and 100, and password same as the username.

* Optional: import the [`dashboard`](./demoapp_yamls/metrics/cass-testbed-grafana-dashboard.json) to Grafana;

### Generate Load
To generate load on the testbed, you can use the Locust load generator that is already installed as part of the Helm chart.
Here's how to use it:

* Open a new terminal and run the following command to start the Locust master:
  ```shell
  $ kubectl -n demoapp port-forward svc/locust-master 8089:8089
  ```

* Open a web browser and go to http://localhost:8089. This will open the Locust web interface.
* Enter the desired number of users and spawn rate (for example, `300` and `20` respectively), and then start the test by clicking the "Start swarming" button.
* Monitor the load and performance metrics on the Prometheus Dashboard to see how the testbed is performing under load.

Note that the testbed is configured to alternate between periods of high and low traffic every 30 minutes by default. 
You can adjust this setting by changing the `locust.time_slo_probability` and `locust.time_slo_probability_step_in_min` parameter in the `values.yaml` file.
