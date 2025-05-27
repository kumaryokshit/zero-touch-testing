#!/usr/bin/env python3

import os
import sys
import pandas as pd

def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "apps.xlsx"
    df = pd.read_excel(excel_path)

    for _, row in df.iterrows():
        app = row["appName"]
        image = row["image"]
        pull_secret = row.get("pullSecret")
        cpu = row.get("cpuLimit")
        mem = row.get("memLimit")
        chart = row.get("chart")
        version = row.get("version")
        values_repo = row.get("valuesRepo")

        path = f"apps/{app}"
        os.makedirs(path, exist_ok=True)

        if chart and version and values_repo:
            with open(f"{path}/helm.yaml", "w") as f:
                f.write(f"""apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {app}
spec:
  project: default
  source:
    repoURL: {values_repo}
    chart: {chart}
    targetRevision: {version}
  destination:
    server: https://kubernetes.default.svc
    namespace: {app}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
""")
        else:
            container = f"""
        - name: {app}
          image: {image}
          ports:
            - containerPort: 80
"""
            if cpu or mem:
                container += f"""          resources:
            limits:
              cpu: {cpu or '250m'}
              memory: {mem or '256Mi'}
"""

            spec = f"""
    spec:
      containers:
{container}"""

            if pull_secret:
                spec += f"""
      imagePullSecrets:
        - name: {pull_secret}
"""

            deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {app}
  template:
    metadata:
      labels:
        app: {app}
{spec}"""

            with open(f"{path}/deployment.yaml", "w") as f:
                f.write(deployment_yaml)

            with open(f"{path}/kustomization.yaml", "w") as f:
                f.write("resources:\n  - deployment.yaml\n")

if __name__ == "__main__":
    main()
