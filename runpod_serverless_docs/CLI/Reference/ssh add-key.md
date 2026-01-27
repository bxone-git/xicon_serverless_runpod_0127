> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# ssh add-key

Add an SSH public key to your Runpod account for secure Pod access. If no key is provided, a new key pair will be generated automatically.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl ssh add-key [flags]
  ```
</RequestExample>

## Example

Add an SSH key from a file:

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl ssh add-key --key-file ~/.ssh/id_rsa.pub
```

## Flags

<ResponseField name="--key" type="string">
  The SSH public key content to add to your account. This should be the full public key string.
</ResponseField>

<ResponseField name="--key-file" type="string">
  The path to a file containing the SSH public key to add. This is typically a `.pub` file from your SSH key pair.
</ResponseField>

## Related commands

- [`runpodctl ssh list-keys`](/runpodctl/reference/runpodctl-ssh-list-keys)
