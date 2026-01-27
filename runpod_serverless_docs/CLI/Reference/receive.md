> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# receive

Receive files or folders sent from another machine using a secure peer-to-peer connection established with a connection code.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl receive <code> [flags]
  ```
</RequestExample>

## Example

Receive files using a connection code.

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl receive rainbow-unicorn-42
```

## Arguments

<ResponseField name="<code>" type="string">
  The connection code phrase that matches the code used by the sender with the `send` command. If not provided, you'll be prompted to enter it.
</ResponseField>

## Related commands

- [`runpodctl send`](/runpodctl/reference/runpodctl-send)
- [`runpodctl`](/runpodctl/reference/runpodctl)
