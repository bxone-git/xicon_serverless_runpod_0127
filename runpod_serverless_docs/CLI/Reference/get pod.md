> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# get pod

List all your Pods or retrieve details about a specific Pod by its ID.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl get pod <podId> [flags]
  ```
</RequestExample>

## Example

List all your Pods with complete field information:

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl get pod --allfields
```

## Arguments

<ResponseField name="<pod_id>" type="string">
  The ID of a specific Pod to retrieve. If no ID is provided, all Pods will be listed.
</ResponseField>

## Flags

<ResponseField name="-a, --allfields">
  Include all available fields in the output, providing complete Pod information.
</ResponseField>
