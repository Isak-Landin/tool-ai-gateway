from __future__ import annotations

from errors import MessageHistoryPersistenceError, MessageRuntimeError


class MessageRuntime:
    """
    Project-bound message/history serving surface.

    This runtime object reuses the persistence-facing MessagesRepository for
    project-scoped history retrieval, execution-scoped ordered message work,
    and route/shared message shaping.
    """

    def __init__(self, *, project_id: int, messages_repository):
        """Create the bound message runtime for one project.

        Args:
            project_id: Persisted project identifier that scopes message access.
            messages_repository: Storage-shaped message repository reused underneath the runtime.

        Returns:
            None: The runtime stores the project scope and repository dependency.
        """
        if project_id is None:
            raise MessageRuntimeError("project_id is required")
        if messages_repository is None:
            raise MessageRuntimeError("messages_repository is required")

        self.project_id = project_id
        self._messages_repository = messages_repository

    def _validate_sequence_no(self, sequence_no: int, *, field_name: str) -> int:
        """Validate a positive message sequence number.

        Args:
            sequence_no: Sequence number value to validate.
            field_name: Field label to mention if validation fails.

        Returns:
            int: The validated sequence number.
        """
        if sequence_no < 1:
            raise MessageRuntimeError(f"{field_name} must be >= 1")

        return sequence_no

    def list_history(
        self,
        *,
        limit: int | None = None,
        before_sequence_no: int | None = None,
        after_sequence_no: int | None = None,
    ) -> list[dict]:
        """List ordered project history rows for route or shared consumers.

        Args:
            limit: Optional maximum number of message rows to return.
            before_sequence_no: Optional upper sequence bound for older history.
            after_sequence_no: Optional lower sequence bound for newer history.

        Returns:
            list[dict]: Ordered message rows scoped to the current project.
        """
        if before_sequence_no is not None:
            before_sequence_no = self._validate_sequence_no(
                before_sequence_no,
                field_name="before_sequence_no",
            )
        if after_sequence_no is not None:
            after_sequence_no = self._validate_sequence_no(
                after_sequence_no,
                field_name="after_sequence_no",
            )

        try:
            return self._messages_repository.list_message_rows(
                limit=limit,
                before_sequence_no=before_sequence_no,
                after_sequence_no=after_sequence_no,
            )
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e

    def get_message_by_sequence_no(self, sequence_no: int) -> dict | None:
        """Load one project message by its ordered sequence number.

        Args:
            sequence_no: Positive sequence number of the message to load.

        Returns:
            dict | None: Serialized message row when found, otherwise `None`.
        """
        sequence_no = self._validate_sequence_no(sequence_no, field_name="sequence_no")
        try:
            return self._messages_repository.get_message_row_by_sequence_no(sequence_no)
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e

    def load_recent_history(
        self,
        *,
        limit: int,
        before_sequence_no: int | None = None,
    ) -> list[dict]:
        """Load a bounded recent-history window for execution use.

        Args:
            limit: Maximum number of recent message rows to load.
            before_sequence_no: Optional sequence boundary to stop before.

        Returns:
            list[dict]: Ordered recent-history rows for the current project.
        """
        if before_sequence_no is not None:
            before_sequence_no = self._validate_sequence_no(
                before_sequence_no,
                field_name="before_sequence_no",
            )

        try:
            return self._messages_repository.load_recent_message_rows(
                limit=limit,
                before_sequence_no=before_sequence_no,
            )
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e

    def load_next_sequence_no(self) -> int:
        """Load the next sequence number for a new persisted message artifact.

        Args:
            None.

        Returns:
            int: Next ordered sequence number for the current project.
        """
        try:
            return self._messages_repository.load_next_message_sequence_no()
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e

    def store_artifact(self, artifact_data: dict) -> dict:
        """Persist one ordered message artifact through the storage repository.

        Args:
            artifact_data: Message-row payload to persist for the current project.

        Returns:
            dict: Serialized stored message row after persistence completes.
        """
        try:
            return self._messages_repository.store_message_artifact(artifact_data)
        except MessageHistoryPersistenceError as e:
            raise MessageRuntimeError(str(e)) from e
