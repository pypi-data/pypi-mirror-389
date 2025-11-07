# Changelog

All notable changes to the Lumen Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-29

### Added

- Initial release of the Lumen Python SDK
- Core customer management functions:
  - `get_subscription_status`
  - `get_customer_overview`
  - `get_seat_usage_by_user`
- Entitlement and feature checking functions:
  - `get_usage`
  - `get_features`
  - `is_feature_entitled`
- Event tracking with `send_event`
- Seat management functions:
  - `add_seat`
  - `remove_seat`
  - `get_seat_usage`
- User enrollment with `enroll_user`
- Subscription management with `create_free_subscription_if_none_exists`
- Framework handlers for Flask, FastAPI, and Django
- Full async/await support using httpx
- Comprehensive type hints
- Complete documentation and examples
- Custom exception types for better error handling

### Features

- Environment variable configuration support
- Optional API key and URL overrides
- Idempotency key support for critical operations
- Metadata support for seat operations
- Timestamp support for audit trails

[0.1.0]: https://github.com/getlumen/lumen-python-sdk/releases/tag/v0.1.0
