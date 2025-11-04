"""Utility functions for pyArchiveit."""


def is_valid_metadata_structure(metadata: dict) -> bool:
    """Check if the metadata structure is valid.

    Args:
        metadata (dict): The metadata to validate.

    """
    if (
        isinstance(metadata, dict)
        and any(isinstance(v, list) for v in metadata.values())
        or metadata == {}
    ):
        return all(
            isinstance(value_list, list)
            and all(isinstance(item, dict) and "value" in item for item in value_list)
            for value_list in metadata.values()
        )

    return False
