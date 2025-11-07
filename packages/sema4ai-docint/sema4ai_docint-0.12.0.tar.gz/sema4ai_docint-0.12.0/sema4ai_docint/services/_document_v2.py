from reducto.types import ParseResponse

from sema4ai_docint.models.document_v2 import DocumentV2

from ..utils import compute_document_id
from ._context import _DIContext


class _DocumentServiceV2:
    """Alpha version of DocumentService with breaking API changes.

    This service is intended to evolve the DocumentService with breaking changes
    while keeping the v1 API stable for existing users. When ready, this will
    become the default DocumentService.
    """

    def __init__(self, context: _DIContext) -> None:
        """Initialize the DocumentService V2 with shared context.

        Args:
            context: Shared DI context with access to external clients
        """
        self._context = context

    async def new_document(self, file_name: str) -> DocumentV2:
        """
        Create a Document object from a file that exists in Thread file storage.

        Args:
            file_name: The name of the file to create a Document object for.
            cached_path: The path to the file if it has already been localized.
        Returns:
            A Document object.
        """
        assert self._context.agent_server_transport is not None, (
            "AgentServer transport is required."
        )
        # Localize the file
        local_path = self._context.agent_server_transport.get_file(file_name)

        return DocumentV2(
            file_name=file_name,
            document_id=compute_document_id(local_path),
            local_file_path=local_path,
        )

    async def parse(self, document: DocumentV2, *, force_reload: bool = False) -> ParseResponse:
        assert self._context.extraction_service_async is not None, "Extraction service is required."
        assert self._context.persistence_service is not None, "Persistence service is required."
        assert self._context.agent_server_transport is not None, (
            "Agent server transport is required."
        )

        if not force_reload:
            cached = await self._context.persistence_service.load(document.file_name)
            if cached is not None:
                return ParseResponse.model_validate_json(cached)

        reducto_id = await self._context.extraction_service_async.upload(
            document.get_local_path(self._context.agent_server_transport)
        )
        response = await self._context.extraction_service_async.parse(reducto_id)
        await self._context.persistence_service.save(
            document.file_name, response.model_dump_json().encode()
        )

        return response
