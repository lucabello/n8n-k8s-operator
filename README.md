# operator-template

## Description

This repository contains the source code for a Charmed Operator that drives [n8n](https://n8n.io/) on Kubernetes.

n8n is a workflow automation tool that allows to easily automate tasks across different services. Its node-based approach makes it highly versatile, enabling you to connect anything to everything.

## Usage

Having a bootstraped Juju controller on Kubernetes, the deployment is as simple as:

```bash
juju deploy n8n-k8s
```

The deployment can be monitored through `juju status`; the command also show the IP address of the unit where n8n will be running. You can also get that address by running

```bash
juju status --format=json | jq -r '.applications."n8n-k8s".address'
```

You can connect to `http://<address>:5678` and register your account at the n8n homepage.

## Relations

The currently supported relations are:

* [**Ingress**](https://charmhub.io/nginx-ingress-integrator), through the *ingress* interface
    ```bash
    juju relate n8n nginx-ingress-integrator
    juju config n8n-k8s external-hostname=<hostname>
    ```
* [**Prometheus**](https://github.com/canonical/prometheus-k8s-operator), through the *prometheus_scrape* interface.
    ```bash
    juju relate n8n prometheus-k8s
    ```


## OCI Images

This charm uses the [latest version](https://hub.docker.com/r/n8nio/n8n) of the image provided upstream.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
charm following best practice guidelines, and
[CONTRIBUTING.md](https://github.com/lucabello/n8n-k8s-operator/blob/main/CONTRIBUTING.md) for developer
guidance.
