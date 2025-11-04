# svine

Lightweight Python wrapper for a highly limited number of `svn` subcommands.
Meant for use in mining Subversion repositories.

## Installation

`pip install svine`

## Usage

Setup for all use cases is the same:

```python
from svine import SvnClient, SvnException

remote = SvnClient("https://svn.repository.url/whoever/still/uses/svn/")
```

### `svn log`

Returns log entries in named tuples with fields for message (`msg`), author, revision and date.

```python
try:
    for log_entry in remote.log():
        print(log_entry.msg)
except SvnException:
    # Handle
    pass

# Get latest log entry only
try:
    for log_entry in remote.log(limit=1):
        print(log_entry.author)
except SvnException:
    # Handle
    pass
```

### `svn info`

Provides a named tuple with the info returned by the `svn info` subcommand. Fields are:
"url", "relative_url", "entry_kind", "entry_path", "entry_revision", "repository_root", "repository_uuid", 
"wcinfo_wcroot_abspath", "wcinfo_schedule", "wcinfo_depth", "commit_author", "commit_date", "commit_revision".

```python
try:
    info = remote.info()
    print(info.repository_root)
except SvnException:
    # Handle
    pass
```

### `svn list`

Yields the contents only of the remote repository root directory.

```python
try:
    for root_content in remote.list():
        print(root_content)
except SvnException:
    # Handle
    pass

# Prints, e.g.:
# 
# trunk/
# branches/
# tags/
```

## Contributing

Contributions are generally welcome. Please open an issue to start the contribution process.

Please note that there are currently no plans or dedicated resources to do development or maintenance of this project.

## Licenses

This project is compliant with the [REUSE Specifications version 3.2](https://reuse.software/).
Applicable licenses are defined in [`REUSE.toml`](REUSE.toml) and the respective license texts
are available in [`LICENSES/`](LICENSES/).
