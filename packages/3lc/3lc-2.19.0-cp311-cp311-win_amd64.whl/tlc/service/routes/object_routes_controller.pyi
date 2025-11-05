import pydantic
from _typeshed import Incomplete
from litestar.connection.request import Request as Request
from litestar.controller import Controller
from litestar.response.base import Response
from tlc.core import ObjectRegistry as ObjectRegistry
from tlc.core.json_helper import JsonHelper as JsonHelper
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import MalformedContentError as MalformedContentError, NotRegisteredError as NotRegisteredError
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.system_tables.indexing_table import IndexingTable as IndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.config_indexing_table import ConfigIndexingTable as ConfigIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.run_indexing_table import RunIndexingTable as RunIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.table_indexing_table import TableIndexingTable as TableIndexingTable
from tlc.core.objects.tables.system_tables.log_table import LogTable as LogTable
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from typing import Any, Literal

logger: Incomplete

class TLCObject(pydantic.BaseModel):
    """In-flight representation of a TLCObject."""
    type: str
    url: str | None
    model_config: Incomplete

class TLCPatchOptions(pydantic.BaseModel):
    """TLC patch request."""
    delete_old_url: bool
    model_config: Incomplete

class TLCPatchRequest(pydantic.BaseModel):
    """In-flight representation of a patch request for a TLCObject."""
    patch_object: TLCObject
    patch_options: TLCPatchOptions
    model_config: Incomplete

class ReindexRequest(pydantic.BaseModel):
    '''Request model for re-indexing operations.

    :param force: Whether to force re-indexing to disregard the state of the current index timestamp files.
    :param types: The types of objects to reindex. Defaults to "all".
    '''
    force: bool
    types: list[Literal['run', 'table', 'config', 'all']]
    model_config: Incomplete

class RollbackDeleteContext:
    """A context manager for rollback object creation without interfering with InsufficientCredits."""
    def __init__(self, url: Url) -> None: ...
    def rollback(self) -> None: ...
    def __enter__(self) -> RollbackDeleteContext: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Literal[False]:
        """Exit the context, performing rollback if not committed and handling exceptions."""

class ObjectRoutesController(Controller):
    """Controller for all object-related routes"""
    path: str
    async def get_encoded_url(self, encoded_url: str, request: Request) -> Response: ...
    async def get_encoded_url_rows(self, encoded_url: str, attribute: str, request: Request) -> Response[bytes]: ...
    async def list_urls(self) -> list[str]:
        """Return all the objects.

        Returns:
            list[Any]: List of the URLs of all the objects.
        """
    async def request_reindex(self, data: ReindexRequest) -> Response:
        """Request a reindex operation.

        :param data: The reindex request parameters.
        :returns: Response with status message.
        """
    async def new_object(self, data: TLCObject) -> Response:
        """Create a new object.

        :param data: Object to be created
        :returns: Empty response. URL of the created object will be in the 'Location' field of the response headers.
        """
    async def delete_object(self, encoded_url: str) -> None:
        """Delete an object.

        :param encoded_url: URL of the object to be deleted.
        :raises: HTTPException if no object can be found at the URL.
        """
    async def update_object(self, encoded_url: str, data: TLCPatchRequest) -> Response:
        """Update the attributes of an object.


        Raises:
            HTTPException: If the object type of `obj_in` does not match the
            type of the object at `object_url`.
        """
