> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# stop pod

Stop a running Pod to pause compute operations. The Pod's persistent storage will be retained, but you'll continue to be charged for storage until the Pod is removed.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl stop pod <podId> [flags]
  ```
</RequestExample>

## Example

Stop a running Pod.

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl stop pod abc123xyz456
```

## Arguments

<ResponseField name="<podId>" type="string" required>
  The ID of the Pod to stop. You can find Pod IDs using the `runpodctl get pod` command.
</ResponseField>

## Related commands

- [`runpodctl start pod`](/runpodctl/reference/runpodctl-start-pod)
- [`runpodctl get pod`](/runpodctl/reference/runpodctl-get-pod)
