# leap-bundle

Command line tool to create model bundles for Liquid Edge AI Platform ([LEAP](https://leap.liquid.ai)).

This tool enables everyone to create, manage, and download AI model bundles for deployment on edge devices. Upload your model directories, track bundle creation progress, and download optimized bundles ready for mobile integration.

See the [documentation](https://leap.liquid.ai/docs/leap-bundle/quick-start) for more details.

## Installation

```bash
pip install leap-bundle
```

## Quick Start

### Authenticate

1. Sign in on the [LEAP website](https://leap.liquid.ai/sign-in)
2. Click the account icon on the top right, and go to your [`profile`](https://leap.liquid.ai/profile)
3. Select the [`API keys` tab](https://leap.liquid.ai/profile#/api-keys) and create a new API key
4. Authenticate the Model Bundling Service with your API token:

```sh
leap-bundle login <api-key>
```

Example output:

```sh
ℹ Validating API token...
✓ Successfully logged in to LEAP platform!
```

### Create model bundle

1. Prepare your model checkpoint.
2. Create a bundle request:

```sh
leap-bundle create <path-to-your-model-checkpoint>
```

Example output:

```sh
ℹ Calculating directory hash...
ℹ Submitting bundle request...
✓ Bundle request created with ID: 1
ℹ Starting upload...
Uploading directory... ✓
✓ Upload completed successfully! Request ID: 1
```

3. Check request status:

```sh
leap-bundle list
```

Example output:

```sh
Bundle Requests (50 most recent)
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID   ┃ Input Path                      ┃ Status       ┃ Creation               ┃ Notes                       ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ /path/to/your/model/directory   │ processing   │ 2024-01-15T10:30:00Z   │ Request is being processed. │
└──────┴─────────────────────────────────┴──────────────┴────────────────────────┴─────────────────────────────┘
✓ Found 1 bundle requests.
```

Get details for a specific request:

```sh
leap-bundle list <request-id>
```

Example output:

```sh
✓ Request Details:
  ID:         1
  Input Path: /path/to/your/model/directory
  Status:     completed
  Creation:   2024-01-15T10:30:00Z
  Update:     2024-01-15T10:45:00Z
  Notes:
```

4. When the request is `Completed`, you can download the bundle:

```sh
leap-bundle download <request-id>
```

Example output:

```sh
ℹ Requesting download for bundle request 1...
✓ Download URL obtained for request 1
Downloading bundle output... ✓
✓ Download completed successfully! File saved to: input-8da4w_output_8da8w-seq_8196.bundle
```

The model bundle file will be saved in the current directory with a `.bundle` extension.

### Complete Example

Here's a complete example showing the full workflow:

```sh
# 1. Install and authenticate
pip install leap-bundle
leap-bundle login <api-key>
leap-bundle whoami

# 2. Create a bundle request
leap-bundle create <model-directory>

# 3. Monitor the request (repeat until completed)
leap-bundle list

# 4. Download when ready
leap-bundle download <request-id>

# 5. Your bundle file is now ready to use!
ls -la <downloaded-bundle-file>
```

### Next Steps

- Visit the [LEAP Model Library](https://leap.liquid.ai/models) to explore available models.
- Check the [CLI Spec](https://leap.liquid.ai/docs/leap-bundle/cli-spec) for detailed command reference.

## Commands

| Command | Description |
| --- | --- |
| `leap-bundle login` | Authenticate with LEAP using API token |
| `leap-bundle whoami` | Show current authenticated user |
| `leap-bundle logout` | Logout from LEAP |
| `leap-bundle config` | Show current configuration |
| `leap-bundle validate` | Validate directory for bundle creation |
| `leap-bundle create` | Submit new bundle request |
| `leap-bundle resume` | Resume an interrupted bundle request creation |
| `leap-bundle list` | List all bundle requests or a specific request |
| `leap-bundle cancel` | Cancel a bundle request |
| `leap-bundle download` | Download the bundle file for a specific request |

## CHANGELOG

https://leap.liquid.ai/docs/leap-bundle/changelog

## License

[LFM Open License v1.0](https://www.liquid.ai/lfm-license)
