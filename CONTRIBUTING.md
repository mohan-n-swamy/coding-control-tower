# Contributing

Keep runtime dependency-free where practical. New collectors must:

1. remain read-only;
2. identify provenance;
3. preserve unknown correlation as `Unassigned`;
4. redact before snapshot writes;
5. include synthetic tests with no private paths or credentials.

Run the tests:

```bash
python -m pytest tests/ -q
```

