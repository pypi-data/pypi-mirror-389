"""A module for interacting with the Archive-it API."""

import logging

from .httpx_client import HTTPXClient
from .utils import is_valid_metadata_structure

logger = logging.getLogger(__name__)


class ArchiveItAPI:
    """A client for interacting with the Archive-it API."""

    def __init__(
        self,
        account_name: str,
        account_password: str,
        base_url: str = "https://partner.archive-it.org/api/",
        default_timeout: float | None = None,
    ) -> None:
        """Initialize the ArchiveItAPI client with authentication and base URL.

        Args:
            account_name (str): The account name for authentication.
            account_password (str): The account password for authentication.
            base_url (str): The base URL for the API endpoints. Defaults to Archive-it API base URL.
            default_timeout (float | None): Default timeout in seconds. Defaults to None. Use None for no timeout.

        """
        self.http_client = HTTPXClient(
            account_name=account_name,
            account_password=account_password,
            base_url=base_url,
            default_timeout=default_timeout,
        )

    def __enter__(self) -> "ArchiveItAPI":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool:
        """Exit context manager and close the HTTP client."""
        self.close()
        return False

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self.http_client.close()

    def get_seed_list(
        self,
        collection_id: str | int | list[str | int],
        limit: int = -1,
        format: str = "json",
        timeout: float | None = None,
    ) -> list[dict]:
        """Get seeds for a given collection ID or list of collection IDs.

        Args:
            collection_id (str | int | list[str | int]): Collection ID or list of Collection IDs.
            limit (int): Maximum number of seeds to retrieve per collection. Defaults to -1 (no limit).
            format (str): The format of the response (json or xml). Defaults to "json".
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            list[dict]: List of seeds from all requested collections.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
            httpx.TimeoutException: If the request times out.

        """
        # Normalize input to a list
        collection_ids = (
            [collection_id] if isinstance(collection_id, (str, int)) else collection_id
        )

        all_seeds = []

        for coll_id in collection_ids:
            logger.info(f"Fetching seeds for collection ID: {coll_id}")
            try:
                response = self.http_client.get(
                    "seed",
                    params={"collection": coll_id, "limit": limit, "format": format},
                    timeout=timeout,
                )
                data = response.json()

                # API returns a list of seeds
                if isinstance(data, list):
                    all_seeds.extend(data)
                    logger.info(
                        f"Retrieved {len(data)} seeds for collection ID: {coll_id}"
                    )
                else:
                    logger.warning(
                        f"Unexpected response format for collection ID {coll_id}: {type(data)}"
                    )
            except Exception as e:
                logger.error(f"Failed to fetch seeds for collection ID {coll_id}: {e}")
                raise

        return all_seeds

    def update_seed_metadata(
        self,
        seed_id: str | int,
        metadata: dict,
    ) -> None:
        """Update metadata for a specific seed.

        Args:
            seed_id (str | int): The ID of the seed to update.
            metadata (dict): The metadata to update for the seed.

        """
        logger.info(f"Updating metadata for seed ID: {seed_id}")

        # Check whether the key after the first key start with 'value' or else reject
        all_have_value = is_valid_metadata_structure(metadata)
        if not all_have_value:
            msg = 'Each metadata list item must be a dict containing a "value" key.'
            logger.error(
                f"Invalid metadata structure for seed ID {seed_id}: {metadata}"
            )
            raise ValueError(msg)

        try:
            self.http_client.patch(
                f"seed/{seed_id}",
                data={"metadata": metadata},
            )
            logger.info(f"Successfully updated metadata for seed ID: {seed_id}")
        except Exception as e:
            logger.error(f"Failed to update metadata for seed ID {seed_id}: {e}")
            raise

    def create_seed(
        self,
        url: str,
        collection_id: str | int,
        crawl_definition_id: str | int,
        other_params: dict | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a new seed in a specified collection with given crawl definition.

        Args:
            url (str): The URL of the seed to create.
            collection_id (str | int): The ID of the collection to add the seed to.
            crawl_definition_id (str | int): The ID of the crawl definition to associate with the seed.
            other_params (dict | None): Additional parameters for the seed creation.
            metadata (dict | None): Metadata to set for the seed after creation.

        Returns:
            dict: The created seed data returned by the API.

        """
        logger.info(f"Creating new seed in collection ID: {collection_id}")

        payload = {
            "url": url,
            "collection": collection_id,
            "crawl_definition": crawl_definition_id,
        }

        # Handle metadata from other_params
        if other_params:
            if "metadata" in other_params:
                other_params_metadata = other_params["metadata"]
                other_params.pop("metadata")  # Remove metadata from other_params
                # Combine with metadata parameter if provided
                if metadata:
                    metadata.update(other_params_metadata)
                else:
                    metadata = other_params_metadata
            payload.update(other_params)

        # Validate metadata structure if provided
        if metadata and not is_valid_metadata_structure(metadata):
            logger.error(
                f"Invalid metadata structure for seed creation in collection ID {collection_id}: {metadata}"
            )
            msg = 'Each metadata list item must be a dict containing a "value" key.'
            raise ValueError(msg)

        try:
            response = self.http_client.post(
                "seed",
                data=payload,
            )
            seed_data = response.json()
            logger.debug(f"Response from seed creation: {seed_data}")
            logger.info(f"Successfully created seed in collection ID: {collection_id}")

            # If metadata is provided, update it after seed creation
            if metadata:
                seed_id = seed_data.get("id")
                if seed_id:
                    logger.info(
                        f"Updating metadata for newly created seed ID: {seed_id}"
                    )
                    self.update_seed_metadata(seed_id=seed_id, metadata=metadata)
                    # Refresh seed_data to include updated metadata
                    seed_data["metadata"] = metadata
                else:
                    logger.warning(
                        "Seed created but no ID returned, cannot update metadata"
                    )

            return seed_data

        except Exception as e:
            logger.error(f"Failed to create seed in collection ID {collection_id}: {e}")
            raise

    def delete_seed(
        self,
        seed_id: str | int,
    ) -> dict:
        """Delete a seed by its ID.

        Args:
            seed_id (str | int): The ID of the seed to delete.

        Returns:
            dict: The seed data from the API after deletion. If successful, the 'deleted' flag should be True.

        """
        logger.info(f"Deleting seed ID: {seed_id}")

        try:
            response = self.http_client.patch(
                f"seed/{seed_id}",
                data={"deleted": True},
            )  # The API uses PATCH 'deleted' flag to delete seeds
            logger.info(f"Successfully deleted seed ID: {seed_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to delete seed ID {seed_id}: {e}")
            raise
