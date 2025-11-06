# solveit
Solve it with code FastHTML app

## Installation

Works for Python 3.12

```bash
pip install -e .
pip install -r requirements.txt
```

To setup ipykernel_helper auto-import, you must setup it via an nbextension (this is required):

```sh
mkdir -p ~/.ipython/profile_default
echo "c.InteractiveShellApp.extensions.append('ipykernel_helper')" >> ~/.ipython/profile_default/ipython_kernel_config.py
echo "c.InteractiveShell.display_page=True" >> ~/.ipython/profile_default/ipython_kernel_config.py
```

Setup the api keys as described in the [wiki](https://github.com/AnswerDotAI/answerdotai/wiki/Accounts-and-Compute):
1. Anthropic - for AI prompts
2. Deepseek - for supercompletions
3. AAI_OPENAI_PROXY_URL - for ghost text (defaults to https://openai-answer-ai.pla.sh/v1)

## Usage

The following starts the ipykernel server along with the main solveit app.

```
./start.sh
```

Make sure you have ANTHROPIC_API_KEY set in your environment variables, and DEEP_SEEK_API (for ghost text, for now). And GITHUB_TOKEN for gist-it. For the Anthropic and DeepSeek api keys, you can find them in our sharded wiki [here](https://github.com/AnswerDotAI/answerdotai/wiki/Accounts-and-Compute#api-keys).

For debugging you can set `export ANTHROPIC_LOG=debug` to see the API calls.

Here is a video from Johno on how to use the current Solve-it app: https://www.loom.com/share/f5fc62ac469844b7a54e64dc9f0f04c1?sid=759f9925-0995-4e44-8814-fc514fbb4673

## Feature Flags

The following are all the feature flags that are able to be enabled for solveit by adding them as secrets:

1. MAX_THINKTOK - enables extended thinking mode for AI prompts

## Using VertexAI authentication

If you want your instance of solveit to rely on VertexAI in order to access the underlying model from Anthropic, then you will need to place VertexAI authentication information in your environment or on disk.

Instructions and an AnswerAI key are available here: https://github.com/AnswerDotAI/answerdotai/wiki/Accounts-and-Compute#access-via-vertexauth

## Ghost Text

There are 3 ghost text hotkeys:
- `right`: accept an inline suggestion
- `alt-period`: trigger a ghost text suggestion
- `alt-shift-right`: trigger a super completion (multiline Deepseek response)

## Playwright
We have a small e2e test suite `test_selection_mode.py` that checks if selection mode is working correctly.
To run these tests locally follow the steps below:

- `pip install playwright pytest pytest-playwright`
- `playwright install chromium`
- `close any local solveit tabs in your browser`
- `./playwright_tests.sh`

## NB: Make sure to run all notebooks in order to set up the DB as required for certain tests.
