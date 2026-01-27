> ## Documentation Index
>
> Fetch the complete documentation index at: https://docs.runpod.io/llms.txt
> Use this file to discover all available pages before exploring further.

# config

Configure the Runpod CLI with your API credentials and API URL to enable programmatic access to your Runpod resources.

<RequestExample>
  ```sh Command theme={"theme":{"light":"github-light","dark":"github-dark"}}
  runpodctl config [flags]
  ```
</RequestExample>

## Example

Configure the CLI with your API key:

```sh theme={"theme":{"light":"github-light","dark":"github-dark"}}
runpodctl config \
  --apiKey "rpaPOIUYYULKDSALVIUT3Q2ZRKZ98IUYTSK2OQQ2CWQxkd01"
```

## Flags

<ResponseField name="--apiKey" type="string">
  Your Runpod API key, which authenticates the CLI to access your account. You can generate an API key from the [Runpod console](https://www.runpod.io/console/user/settings).
</ResponseField>

<ResponseField name="--apiUrl" type="string" default="https://api.runpod.io/graphql">
  The Runpod API endpoint URL. The default value should work for most users.
</ResponseField>
