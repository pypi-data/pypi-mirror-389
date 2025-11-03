# ReasonFlow

ReasonFlow is a powerful workflow orchestration framework designed for building and managing complex AI/ML pipelines with advanced observability and tracking capabilities.

## Features

- **Workflow Orchestration**
  - Task dependency management
  - Parallel execution support
  - Error handling and retries
  - State management
  - Dynamic task configuration

- **Advanced Observability**
  - Real-time task tracking
  - Metrics collection
  - Event logging
  - Alert management
  - Health monitoring

- **Integrations**
  - Multiple LLM providers (OpenAI, Ollama, Groq)
  - Vector databases (FAISS, Milvus, Pinecone)
  - Monitoring systems (Prometheus, Kafka)
  - Alert systems (Slack, Email)

- **RAG Capabilities**
  - Document processing
  - Vector storage
  - Semantic search
  - Context management

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reasonflow.git
cd reasonflow

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

### Core Dependencies
```
reasontrack>=0.1.0
reasonchain>=0.1.0
python-dotenv>=1.0.0
```

### Observability Dependencies
```
prometheus-client>=0.17.1
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-otlp>=1.20.0
influxdb-client>=1.38.0
elasticsearch>=8.10.1
elasticsearch-async>=6.2.0
confluent-kafka>=2.2.0
redis>=5.0.1
aioredis>=2.0.1
aiosmtplib>=2.0.0
```

### AI/ML Dependencies
```
sentence-transformers
faiss-cpu  # or faiss-gpu for GPU support
torch
transformers
```

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
ALERT_EMAIL=your_alert_email
ALERT_EMAIL_PASSWORD=your_email_password
ALERT_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

### ReasonTrack Configuration
Create `config/reasontrack.ini`:
```ini
[event_manager]
backend = kafka
broker_url = localhost:9092
topic_prefix = reasonflow_events_
client_id = reasonflow
batch_size = 100
flush_interval = 10

[metrics_collector]
backend = prometheus
pushgateway_url = localhost:9091
job_name = reasonflow_metrics
push_interval = 15

[alert_manager]
storage_path = alerts
retention_days = 30
severity_levels = INFO,WARNING,ERROR,CRITICAL

[alert_manager.slack]
webhook_url = ${SLACK_WEBHOOK_URL}

[alert_manager.email]
smtp_host = smtp.gmail.com
smtp_port = 587
username = ${ALERT_EMAIL}
password = ${ALERT_EMAIL_PASSWORD}
from_address = ${ALERT_EMAIL}
to_addresses = ${ALERT_RECIPIENTS}
use_tls = true

[state_manager]
storage_path = workflow_states
backend = memory
prefix = reasonflow_state_
ttl = 3600

[telemetry]
service_name = reasonflow
endpoint = localhost:4317
enable_metrics = true
enable_tracing = true

[logging]
level = INFO
format = %%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s
file = logs/reasontrack.log
```

## Usage

### Basic Example
```python
from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.tasks.task_manager import TaskManager
from reasonchain.memory import SharedMemory

# Initialize components
shared_memory = SharedMemory()
task_manager = TaskManager(shared_memory=shared_memory)
workflow_builder = WorkflowBuilder(
    task_manager=task_manager,
    tracker_type="basic"
)

# Define workflow
workflow_config = {
    "tasks": {
        "task1": {
            "type": "llm",
            "config": {
                "agent": llm_agent,
                "params": {"prompt": "Your prompt here"}
            }
        }
    }
}

# Create and execute workflow
workflow_id = workflow_builder.create_workflow(workflow_config)
results = workflow_builder.execute_workflow(workflow_id)
```

### Advanced Example with Tracking
See `example/1_advance_tracking_example.py` for a complete example demonstrating:
- RAG integration
- Multiple LLM providers
- Advanced tracking
- Metrics collection
- Alert management

## Directory Structure
```
reasonflow/
├── config/
│   └── reasontrack.ini
├── example/
│   ├── 1_advance_tracking_example.py
│   └── 2_tracking_example.py
├── reasonflow/
│   ├── agents/
│   ├── integrations/
│   ├── observability/
│   ├── orchestrator/
│   └── tasks/
├── tests/
├── .env
├── README.md
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ReasonTrack for observability components
- ReasonChain for memory management
- All the amazing open-source libraries that make this possible