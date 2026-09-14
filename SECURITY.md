# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |

## Reporting a vulnerability

Open a private security advisory via GitHub ("Report a vulnerability" on the Security tab) or email **fernedy.arias@gmail.com**. Please do not open public issues for security reports.

## Design notes

- The tool never sends data off your machine by default. `--ai` calls only the local agent CLI you configure.
- It reads container metadata and logs through your own Docker socket; it never starts, stops or removes containers.
