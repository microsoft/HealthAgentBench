# Setup

## Design

Biomni must run on the host machine rather than inside the Harbor task container because its installation is unusually heavy and slow.
In this repository, Harbor creates a fresh task environment for each trial, so installing Biomni inside the container would add a multi-hour setup step to the normal trial lifecycle.
Biomni also already lives in its own conda environment with Python 3.11, while MedCLI and Harbor run from a separate project environment.

For these reasons, Biomni should run on the host machine in its own conda environment.
MedCLI connects Biomni to the live Harbor task environment through a small bridge between Biomni MCP and Harbor.

## Install Biomni

To run Biomni, follow the [setup instructions](https://github.com/snap-stanford/Biomni/blob/main/biomni_env/README.md) in the Biomni repository.
This step may take up to 10 hours.
This workflow has been tested on Ubuntu 22.04 (Jammy).

Then set the required environment variables for Biomni.
Here is an example configuration for using Azure OpenAI:
```bash
export BIOMNI_LLM=<deployment>
export BIOMNI_TIMEOUT_SECONDS=1200
export BIOMNI_DATA_PATH=/path/to/biomni/data
export LLM_SOURCE=AzureOpenAI
export OPENAI_API_KEY=<the_api_key>
export OPENAI_ENDPOINT=https://<your_endpoint>.openai.azure.com/
# this variable is used in the Harbor bridge
export BIOMNI_PYTHON=/path/to/anaconda3/envs/biomni_e1/bin/python
```

You can test the setup with this Python script:
```python
from biomni.agent import A1
agent = A1()
agent.go('Reply me with hello world')
```

After the initial installation, make sure you initialize a Biomni agent at least once, since that will trigger the data download.

## Run it with Harbor

After exporting the environment variables above, use the following Harbor agent configuration:
```yaml
agents:
  - import_path: medcli.agents.harbor.host.biomni:BiomniHostAgent
    model_name: <deployment>
```

You can run the example job config with:
```bash
uv run harbor run -c jobs/medagentbench_biomni_host.yaml
```
