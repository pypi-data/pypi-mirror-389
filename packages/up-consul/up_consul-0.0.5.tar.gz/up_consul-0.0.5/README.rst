=========
up-consul
=========

Limited functionality Consul Python client to interact with the consul API.

Provides limited functionality for getting and setting values.

Release Notes:
==============

[0.0.5] - 2025-11-03
--------------------

Changed:
    - correct the logic for 0.0.3 and 0.0.4 changes


[0.0.4] - 2025-11-01
--------------------

Changed:
    - Raise HTTP 404 if no data after removing non-specific matches


[0.0.3] - 2025-11-01
--------------------

Changed:
    - client.kv.get_keys, client.kv.get_many - remove non-specific matches


[0.0.2] - 2025-07-07
--------------------

Added:
    - url_scheme parameter, allowing http connections.


[0.0.1] - 2024-10-08
--------------------

Added:
    - ConsulClient connects to consul host using a requests session.
    - KVClient, for getting and settings values in the key-value storage.
