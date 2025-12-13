"""
Azure Blob Storage service for handling file uploads.
"""

import os
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient, PublicAccess
from azure.core.exceptions import AzureError, ResourceNotFoundError
from flask import current_app


class BlobStorageService:
    """Service for Azure Blob Storage operations."""

    def __init__(self):
        """Initialize blob storage service with connection string."""
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'avatars')

        if not connection_string:
            self.client = None
            self.container_name = None
            try:
                if current_app:
                    current_app.logger.warning("AZURE_STORAGE_CONNECTION_STRING not set in environment variables")
            except RuntimeError:
                # Flask app context not available
                pass
            return

        try:
            self.client = BlobServiceClient.from_connection_string(connection_string)
            self.container_name = container_name
            # Ensure container exists
            self._ensure_container_exists()
        except Exception as e:
            try:
                if current_app:
                    current_app.logger.error(f"Failed to initialize blob storage: {e}", exc_info=True)
            except RuntimeError:
                # Flask app context not available, print to console
                print(f"Failed to initialize blob storage: {e}")
            self.client = None
            self.container_name = None

    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't."""
        if not self.client:
            return

        try:
            container_client = self.client.get_container_client(self.container_name)
            if not container_client.exists():
                # Create container with public blob access (allows anonymous read access to blobs)
                container_client.create_container(public_access=PublicAccess.Blob)
                current_app.logger.info(f"Created container: {self.container_name} with public blob access")
            else:
                # Container already exists - public access must be set manually in Azure Portal
                # or when the container was created
                current_app.logger.info(f"Container {self.container_name} already exists")
        except AzureError as e:
            current_app.logger.error(f"Failed to ensure container exists: {e}")

    def is_configured(self) -> bool:
        """Check if blob storage is configured."""
        return self.client is not None and self.container_name is not None

    def upload_avatar(self, user_id: str, file_data: bytes, content_type: str) -> Optional[str]:
        """
        Upload avatar image to blob storage.

        Args:
            user_id: User ID for generating unique blob name
            file_data: Binary file data
            content_type: MIME type of the file

        Returns:
            Blob URL if successful, None otherwise
        """
        if not self.is_configured():
            current_app.logger.warning("Blob storage not configured, skipping upload")
            return None

        try:
            # Generate blob name: avatars/{user_id}.{ext}
            # Extract extension from content type
            ext_map = {
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/webp': 'webp'
            }
            extension = ext_map.get(content_type, 'jpg')
            
            blob_name = f"avatars/{user_id}.{extension}"

            # Upload blob (overwrite=True ensures old avatar is replaced)
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.upload_blob(
                file_data,
                content_type=content_type,
                overwrite=True
            )

            # Return blob URL
            blob_url = blob_client.url
            current_app.logger.info(f"Successfully uploaded avatar: {blob_name}")
            return blob_url

        except AzureError as e:
            current_app.logger.error(f"Failed to upload avatar: {e}")
            return None

    def delete_avatar(self, blob_url: str) -> bool:
        """
        Delete avatar from blob storage.

        Args:
            blob_url: Full URL of the blob to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            # Extract blob name from URL
            # URL format: https://{account}.blob.core.windows.net/{container}/{blob_name}
            blob_name = blob_url.split(f"{self.container_name}/")[-1] if f"{self.container_name}/" in blob_url else None
            
            if not blob_name:
                current_app.logger.warning(f"Could not extract blob name from URL: {blob_url}")
                return False

            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            current_app.logger.info(f"Successfully deleted avatar: {blob_name}")
            return True

        except AzureError as e:
            current_app.logger.error(f"Failed to delete avatar: {e}")
            return False

    def delete_user_avatars(self, user_id: str) -> None:
        """
        Delete all avatar files for a user (handles different extensions).

        Args:
            user_id: User ID whose avatars should be deleted
        """
        if not self.is_configured():
            return

        # Try to delete avatars with all possible extensions
        extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        for ext in extensions:
            blob_name = f"avatars/{user_id}.{ext}"
            try:
                blob_client = self.client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                if blob_client.exists():
                    blob_client.delete_blob()
                    current_app.logger.info(f"Deleted avatar: {blob_name}")
            except (AzureError, ResourceNotFoundError):
                # Ignore errors if blob doesn't exist
                pass

    def get_blob_url(self, blob_name: str) -> Optional[str]:
        """
        Get URL for a blob.

        Args:
            blob_name: Name of the blob

        Returns:
            Blob URL if successful, None otherwise
        """
        if not self.is_configured():
            return None

        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            return blob_client.url
        except AzureError as e:
            current_app.logger.error(f"Failed to get blob URL: {e}")
            return None

