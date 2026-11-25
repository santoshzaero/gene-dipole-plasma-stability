# Local raw-data workflow

These scripts capture the original local run and diagnostic workflow. They expect to live in the Scripts directory directly under the full MAE190_Additional_Experiments data folder. That folder includes the two experiment directories with their Runs, Archive and Setup_Attempts records and raw GENE diagnostics.

The published repository can regenerate the figures from the curated diagnostic extracts using the [portable plot script](../../plot_additional_experiments.py). That path needs no GENE executable or local binary outputs.

The archived analysis and table scripts only read saved runs. The archived launcher starts new GENE simulations when invoked with an explicit batch and local repository. Use a new workspace for a repeat. The fixed-step definitions in the archived launcher contain the recovered inputs used after setup errors.
