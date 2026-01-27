> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# Stop a Pod

> Stop a Pod.

## OpenAPI

```yaml POST /pods/{podId}/stop
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
  /pods/{podId}/stop:
    post:
      tags:
        - pods
      summary: Stop a Pod
      description: Stop a Pod.
      operationId: StopPod
      parameters:
        - name: podId
          in: path
          description: Pod ID to stop.
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Pod successfully stopped.
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
 --url https://rest.runpod.io/v1/pods/{podId}/stop \
 --header 'Authorization: Bearer <token>'

---
