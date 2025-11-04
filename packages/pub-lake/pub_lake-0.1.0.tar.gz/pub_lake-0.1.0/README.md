# pub-lake

![PyPI version](https://img.shields.io/pypi/v/pub-lake.svg)
[![Documentation Status](https://readthedocs.org/projects/pub-lake/badge/?version=latest)](https://pub-lake.readthedocs.io/en/latest/?version=latest)

Aggregate publication metadata from bioRxiv, OpenAlex, and more.

* PyPI package: https://pypi.org/project/pub-lake/
* Free software: MIT License
* Documentation: https://pub-lake.readthedocs.io.

## Features

1. **bioRxiv preprints**: fetch metadata for preprints from the bioRxiv API and enrich it with OpenAlex topics.

## How it works

The package follows an ELT (Extract, Load, Transform) architecture and stores data in a relational database (SQLite by default).
Key steps:
1. **Extract**: Fetch raw metadata from bioRxiv and OpenAlex APIs.
2. **Load**: Store the raw metadata in the database.
3. **Transform**: Clean, normalize, and aggregate the data.

Data can then be queried and returns a unified view of publication metadata.

## Installation

```bash
uv add pub-lake
```

See [docs/installation.md](docs/installation.md) for more details.

## Usage

```bash
# ingest preprints from the given dates into the database
uv run python -m pub_lake preprints fetch --start "2025-01-02" --end "2025-01-04" --polite "eidens@embl.de"

# list preprints available in the database
uv run python -m pub_lake preprints list [--start "2025-01-02"] [--end "2025-01-04"]
```

See [docs/usage.md](docs/usage.md) for more details.

## Development

### Project Structure

`src/pub_lake/` has the following structure:

-   `cli.py`: main entry point for the command-line interface.
-   `elt/`: core logic for the Extract, Load, Transform pipeline.
    -   `extract/`: fetching data from external sources (e.g., bioRxiv, OpenAlex).
    -   `load/`: loading raw data into the database.
    -   `transform/`: cleaning and normalizing the loaded data.
-   `models/`: database schema and data models.
-   `interface/`: methods for querying the final, cleaned data.
-   `config.py`: configuration, such as database connections and API keys.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
