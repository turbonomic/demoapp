#!/usr/bin/env bash

istioctl kube-inject -f deploy.yaml > deploy-with-istio.yaml