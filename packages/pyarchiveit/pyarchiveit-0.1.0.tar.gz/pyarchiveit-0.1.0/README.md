🚨<span style="color:red; font-weight:bold;">
  THIS LIBRARY IS UNDER ACTIVE DEVELOPMENT. USE AT YOUR OWN RISK.
</span>🚨

# Pyarchiveit

Pyarchiveit is a Python library designed to interact with the Internet Archive's Archive-it API. It provides a simple interface to manage the seeds and collections within Archive-it accounts.

## Features
- Create and update seeds with metadata validation
- Retrieve seed lists with their metadata for single or multiple collections

## Example usage

First, you will need to initialize the Archive-it API client with your account credentials.
```python
from pyArchiveit.api import ArchiveItAPI

# Initialize the Archive-it API client with your credentials
archive_it_client = ArchiveItAPI(
    account_name='your_username',
    account_password='your_password'
)
```

To create a new seed with metadata, or update an existing seed's metadata, you can use the following code:
```python
# Create a new seed with metadata
metadata = [
    {"value": "Example Metadata 1"},
    {"value": "Example Metadata 2"}
]
new_seed = archive_it_client.create_seed(
    collection_id=123456,
    url='http://example.com',
    crawl_definition_id=789012,
    other_params=None,
    metadata=metadata
)
```

To update an existing seed's metadata:
```python
# Update an existing seed's metadata
updated_metadata = [
    {"value": "Updated Metadata 1"},
    {"value": "Updated Metadata 2"}
]
updated_seed = archive_it_client.update_seed_metadata(
    seed_id=123456,
    metadata=updated_metadata
)
```

To retrieve the seed list of a collection or multiple collections:
```python
# Get seed list of a collection
seeds = archive_it_client.get_seeds(collection_ids=123456)

# Or get seeds from multiple collections
seeds = archive_it_client.get_seeds(collection_ids=[123456, 789012])
```

## ⚫ Issues
For questions or support, please open an issue on the [GitHub repository](https://github.com/kenlhlui/pyarchiveit/issues).

## 🖊️ Author
[Ken Lui](https://github.com/kenlhlui) - Data Curation Specialist at [Map & Data Library, University of Toronto](https://mdl.library.utoronto.ca/)