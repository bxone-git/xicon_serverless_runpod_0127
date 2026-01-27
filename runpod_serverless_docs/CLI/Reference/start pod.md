> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# start pod

Start a stopped Pod, resuming compute and billing. Use this to restart Pods that were previously stopped.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl start pod <podId> [flags]
  ```
</RequestExample>

## Example

Start a stopped Pod with a custom bid price for spot instances:

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl start pod abc123xyz456 --bid 0.50
```

## Arguments

<ResponseField name="<podId>" type="string" required>
  The ID of the Pod to start. You can find Pod IDs using the `runpodctl get pod` command.
</ResponseField>

## Flags

<ResponseField name="--bid" type="float">
  The bid price per GPU in dollars per hour for spot instance pricing. This only applies to Community Cloud Pods.
</ResponseField>

## Related commands

- [`runpodctl stop pod`](/runpodctl/reference/runpodctl-stop-pod)
- [`runpodctl get pod`](/runpodctl/reference/runpodctl-get-pod)
