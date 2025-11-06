# aind_disrnn_utils

[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
[![semantic-release: angular](https://img.shields.io/badge/semantic--release-angular-e10079?logo=semantic-release)](https://github.com/semantic-release/semantic-release)
![Interrogate](https://img.shields.io/badge/interrogate-100.0%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python->=3.11-blue?logo=python)

## Usage
- Obtain a list of NWB files you wish to fit the model to
```python
import aind_dynamic_foraging_multisession_analysis.multisession_load as ms_load
import aind_disrnn_utils as dl

nwbs, df_trials = ms_load.make_multisession_trials_df(nwb_files)
dataset = dl.create_disrnn_dataset(df_trials)
```

- You don't need to use `make_multisession_trials_df`, but the trials data frame does need to have a column "ses_idx" that splits trials into sessions. 

## Level of Support
 - Occasional updates: We are planning on occasional updating this tool with no fixed schedule. Community involvement is encouraged through both issues and pull requests.

## Installation
To install the software from PyPi
```bash
pip install aind-disrnn-utils
```
To use the software, in the root directory, run
```bash
pip install -e .
```

To develop the code, run
```bash
pip install -e . --group dev
```
Note: --group flag is available only in pip versions >=25.1

Alternatively, if using `uv`, run
```bash
uv sync
```

### Required dependency
> [!IMPORTANT]  
> PyPi does not allow "direct dependencies" where you install straight from github, therefore you must manually install the disentangled_rnn package
> ```bash
> pip install git+https://github.com/google-deepmind/disentangled_rnns.git
> ```

