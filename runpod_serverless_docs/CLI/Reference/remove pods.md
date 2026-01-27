> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# remove pods

Terminate multiple Pods that share the same name. This is useful for cleaning up groups of Pods created with the `create pods` command.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl remove pods <name> [flags]
  ```
</RequestExample>

## Example

Terminate all Pods named "training-worker":

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl remove pods training-worker
```

## Arguments

<ResponseField name="<name>" type="string" required>
  The name of the Pods to terminate. All Pods with this exact name will be removed.
</ResponseField>

## Flags

<ResponseField name="--podCount" type="integer">
  The number of Pods with the specified name to terminate. This limits the removal to a specific count rather than removing all matching Pods.
</ResponseField>

## Related commands

- [`runpodctl remove pod`](/runpodctl/reference/runpodctl-remove-pod)
- [`runpodctl get pod`](/runpodctl/reference/runpodctl-get-pod)
