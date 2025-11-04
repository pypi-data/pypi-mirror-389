# Tasks

Types:

```python
from agentlin_client.types import (
    AgentTaskEvent,
    AnnotationContainerFileCitation,
    AnnotationFileCitation,
    AnnotationFilePath,
    AnnotationURLCitation,
    AudioContentItem,
    FileContentItem,
    ImageContentItem,
    JsonrpcError,
    LogProb,
    MessageContent,
    MessageItem,
    ReasoningItem,
    TaskAudioDeltaEvent,
    TaskAudioDoneEvent,
    TaskCanceledEvent,
    TaskCompletedEvent,
    TaskContentPartAddedEvent,
    TaskContentPartDoneEvent,
    TaskContextCompressionCompletedEvent,
    TaskContextCompressionCreatedEvent,
    TaskContextCompressionInProgressEvent,
    TaskCreatedEvent,
    TaskExpiredEvent,
    TaskFailedEvent,
    TaskFileDeltaEvent,
    TaskFileDoneEvent,
    TaskImageDeltaEvent,
    TaskImageDoneEvent,
    TaskInputRequiredEvent,
    TaskObject,
    TaskOutputItemAddedEvent,
    TaskOutputItemDoneEvent,
    TaskPausedEvent,
    TaskQueuedEvent,
    TaskReasoningSummaryPartAddedEvent,
    TaskReasoningSummaryPartDoneEvent,
    TaskReasoningSummaryTextDeltaEvent,
    TaskReasoningSummaryTextDoneEvent,
    TaskReasoningTextDeltaEvent,
    TaskReasoningTextDoneEvent,
    TaskRolloutEvent,
    TaskTextDeltaEvent,
    TaskTextDoneEvent,
    TaskToolCallArgumentsDeltaEvent,
    TaskToolCallArgumentsDoneEvent,
    TaskToolResultDeltaEvent,
    TaskToolResultDoneEvent,
    TaskToolsUpdatedEvent,
    TaskWorkingEvent,
    TextContentItem,
    ToolCallItem,
    ToolResultItem,
    TopLogProb,
    TaskCreateResponse,
    TaskRetrieveResponse,
    TaskDeleteResponse,
    TaskCancelResponse,
)
```

Methods:

- <code title="post /tasks">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">create</a>(\*\*<a href="src/agentlin_client/types/task_create_params.py">params</a>) -> <a href="./src/agentlin_client/types/task_create_response.py">TaskCreateResponse</a></code>
- <code title="get /tasks/{task_id}">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">retrieve</a>(task_id) -> <a href="./src/agentlin_client/types/task_retrieve_response.py">TaskRetrieveResponse</a></code>
- <code title="delete /tasks/{task_id}">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">delete</a>(task_id) -> <a href="./src/agentlin_client/types/task_delete_response.py">TaskDeleteResponse</a></code>
- <code title="post /tasks/{task_id}/cancel">client.tasks.<a href="./src/agentlin_client/resources/tasks.py">cancel</a>(task_id) -> <a href="./src/agentlin_client/types/task_cancel_response.py">TaskCancelResponse</a></code>
