# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.1] - 2025-11-06

### Added
- **OTEL Correlation Support** - Crew execution tracking now supports OTEL span correlation
- While CrewAI uses LangChain callbacks internally, external OTEL correlation is available for cost reconciliation
- Version bump to align with other SDKs at 5.0.1

### Note
CrewAI SDK leverages AgentBill's LangChain callback handler internally for automatic tracking. For advanced OTEL correlation across systems, consider using the base Python SDK's `track_signal()` method which now accepts optional `trace_id` and `span_id` parameters.

## [5.0.0] - 2025-11-06

### Added
- **NEW**: Added `agent_id` support in `agentbill_config` for agent-specific tracking
- Added `event_name` support for custom event naming (default: 'crew_execution')
- Config-based approach for agent tracking

### Changed
- Updated crew tracking to include `agent_id` in metrics
- Enhanced signal tracking with custom event names

### Migration Guide
```python
# Before (v4.x)
result = track_crew(
    crew=my_crew,
    inputs={"task": "example"},
    agentbill_config={
        "api_key": "your-api-key",
        "customer_id": "customer-123"
    }
)

# After (v5.x) - Non-breaking, but recommended
result = track_crew(
    crew=my_crew,
    inputs={"task": "example"},
    agentbill_config={
        "api_key": "your-api-key",
        "customer_id": "customer-123",
        "agent_id": "agent-456",           # Optional, for agent tracking
        "event_name": "custom_crew_event"  # Optional custom event name
    }
)
```

## [3.0.2] - 2025-11-04

### Changed
- Version bump to match core SDK v3.0.2 (agent_id config support)

## [3.0.1] - 2025-11-04

### Changed
- Version bump to match core SDK fix for agent_external_id requirement

## [3.0.0] - 2025-11-04

### Changed
- Major version bump to 3.0.0 for clean release across all Python SDKs

## [2.0.1] - 2025-11-04

### Changed
- Version bump for republishing (2.0.0 was already published successfully)

## [2.0.0] - 2025-10-25

### Changed
- Updated package structure and dependencies
- Enhanced documentation

## [1.0.0] - 2025-10-21

### Added
- Initial release of AgentBill CrewAI Integration
- Zero-config crew tracking for CrewAI
- Automatic tracking of crew executions
- Agent performance tracking
- Task execution tracking
- Token usage and cost tracking
- Comprehensive test suite with pytest
- GitHub Actions CI/CD workflows
- Professional documentation and examples
- MIT License

### Features
- Seamless CrewAI integration via crew wrapping
- Automatic capture of all crew activities
- Rich metadata capture (agents, tasks, execution time)
- Customer-specific tracking support
- Debug logging capabilities
- Non-invasive wrapping (preserves crew functionality)
- Thread-safe operations

### Supported Tracking
- Crew kickoff events
- Individual agent actions
- Task completions
- LLM token usage
- Execution latency
- Error tracking

### Documentation
- Complete README with usage examples
- API documentation
- Contributing guidelines
- Security policy
- Integration examples
