> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# Restart a pod

> Restart a Pod.

## OpenAPI

```yaml POST /pods/{podId}/restart
openapi: 3.0.3
info:
  title: Runpod API
  description: Public Rest API for managing Runpod programmatically.
  version: 0.1.0
  contact:
    name: help
    url: https://contact.runpod.io/hc/requests/new
    email: help@runpod.io
servers:
  - url: https://rest.runpod.io/v1
security:
  - ApiKey: []
tags:
  - name: docs
    description: This documentation page.
  - name: pods
    description: Manage Pods.
  - name: endpoints
    description: Manage Serverless endpoints.
  - name: network volumes
    description: Manage Runpod network volumes.
  - name: templates
    description: Manage Pod and Serverless templates.
  - name: container registry auths
    description: >-
      Manage authentication for container registries such as dockerhub to use
      private images.
  - name: billing
    description: Retrieve billing history for your Runpod account.
externalDocs:
  description: Find out more about Runpod.
  url: https://runpod.io
paths:
  /pods/{podId}/restart:
    post:
      tags:
        - pods
      summary: Restart a Pod
      description: Restart a Pod.
      operationId: RestartPod
      parameters:
        - name: podId
          in: path
          description: Pod ID to restart.
          required: true
          schema:
            type: string
      responses:
        "400":
          description: Invalid Pod ID.
        "401":
          description: Unauthorized.
components:
  securitySchemes:
    ApiKey:
      type: http
      scheme: bearer
      bearerFormat: Bearer
```

---

curl --request POST \
 --url https://rest.runpod.io/v1/pods/{podId}/restart \
 --header 'Authorization: Bearer <token>'

---
