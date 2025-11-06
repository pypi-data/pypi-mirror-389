# Modal

Types:

```python
from elicitlabs.types import ModalLearnResponse, ModalQueryResponse
```

Methods:

- <code title="post /v1/modal/learn">client.modal.<a href="./src/elicitlabs/resources/modal.py">learn</a>(\*\*<a href="src/elicitlabs/types/modal_learn_params.py">params</a>) -> <a href="./src/elicitlabs/types/modal_learn_response.py">ModalLearnResponse</a></code>
- <code title="post /v1/modal/query">client.modal.<a href="./src/elicitlabs/resources/modal.py">query</a>(\*\*<a href="src/elicitlabs/types/modal_query_params.py">params</a>) -> <a href="./src/elicitlabs/types/modal_query_response.py">ModalQueryResponse</a></code>

# Users

Types:

```python
from elicitlabs.types import UserCreateOrGetResponse
```

Methods:

- <code title="post /v1/users">client.users.<a href="./src/elicitlabs/resources/users.py">create_or_get</a>(\*\*<a href="src/elicitlabs/types/user_create_or_get_params.py">params</a>) -> <a href="./src/elicitlabs/types/user_create_or_get_response.py">UserCreateOrGetResponse</a></code>

# Data

Types:

```python
from elicitlabs.types import DataIngestResponse
```

Methods:

- <code title="post /v1/data/ingest">client.data.<a href="./src/elicitlabs/resources/data/data.py">ingest</a>(\*\*<a href="src/elicitlabs/types/data_ingest_params.py">params</a>) -> <a href="./src/elicitlabs/types/data_ingest_response.py">DataIngestResponse</a></code>

## Job

Types:

```python
from elicitlabs.types.data import JobRetrieveStatusResponse
```

Methods:

- <code title="post /v1/data/job/status">client.data.job.<a href="./src/elicitlabs/resources/data/job.py">retrieve_status</a>(\*\*<a href="src/elicitlabs/types/data/job_retrieve_status_params.py">params</a>) -> <a href="./src/elicitlabs/types/data/job_retrieve_status_response.py">JobRetrieveStatusResponse</a></code>

# Health

Methods:

- <code title="get /health">client.health.<a href="./src/elicitlabs/resources/health.py">check</a>() -> object</code>
