> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# remove pod

Permanently delete a Pod and all its associated data. This action cannot be undone.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl remove pod <podId>
  ```
</RequestExample>

## Example

Terminate a Pod by its ID.

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl remove pod abc123xyz456
```

## Arguments

<ResponseField name="<podId>" type="string" required>
  The ID of the Pod to terminate. You can find Pod IDs using the `runpodctl get pod` command.
</ResponseField>

## Related commands

- [`runpodctl remove pods`](/runpodctl/reference/runpodctl-remove-pods)
- [`runpodctl get pod`](/runpodctl/reference/runpodctl-get-pod)
