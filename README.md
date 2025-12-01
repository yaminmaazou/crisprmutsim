## Installation

### Using a Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

### Globally

```bash
pip install .
```

## Usage

### Starting the GUI

```bash
python -m crisprmutsim [PATH_TO_DB_FOLDER]
```

`crisprmutsim` will attempt to load and save dataset `.db` files in the specified `PATH_TO_DB_FOLDER`. If none is provided, the current working directory is used.

After running the command, you should see output similar to the following:

```
 Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'crisprmutsim.webapp.app'
 * Debug mode: on
```

Open the provided URL in your web browser to access the GUI. <br>
The port number may vary depending on your system configuration.

> [!IMPORTANT]  
> After running a simulation in the GUI, you need to stop (Ctrl+C) and restart the program to have the newly created dataset available for analysis in the GUI. Reloading the browser page is not sufficient!

### Loading a dataset from CSV

```bash
python -m crisprmutsim --csv [PATH_TO_CSV_FILE] [PATH_TO_DB_FOLDER]
```

This command will load a dataset from the specified CSV file into the specified database file.

By default, the following CSV column format is expected:

- "array_name": Unique ID for each CRISPR array
- "repeat_sequences": Space-separated repeat sequences of the CRISPR array in IUPAC nucleotide code
- "consensus_repeat": Consensus repeat sequence in IUPAC nucleotide code
- "cas_type": Cas type classification (no specific format required)
  Additional columns will be ignored.

The database file will be created in a `crisprmutsim`-specific format. Duplicate arrays (based on consensus sequence and Cas type) will be dropped by default.

If you wish to customize the column names or disable duplicate dropping, you can use the module `crisprmutsim.csv_parser` directly, e.g., by writing a script, or by using the Python REPL:

```python
from crisprmutsim.csv_parser import load_csv

...
load_csv(
    csv_file_path,
    db_file_path,
    id_column,                  # default "array_name"
    repeats_column,             # default "repeat_sequences"
    consensus_column,           # default "consensus_repeat"
    cas_type_column,            # default "cas_type"
    drop_consensus_duplicates,  # default True
    drop_full_duplicates,       # default True
)
```

### All command line options

```bash
python -m crisprmutsim --help
```
