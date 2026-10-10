# Contributing to container-autopsy

Thanks for helping containers rest in peace with answers. 🪦

## Ground rules

- **Zero dependencies**: the tool must stay Python stdlib only (the Docker CLI is the only external requirement).
- **One file**: keep the core in `container_autopsy.py`.
- **Human in the loop**: AI mode is always optional, local and clearly labeled. Never send data anywhere by default.
- **Dogfooding rule**: PRs must not lower the repo's own Glow Score (run [repo-glow](https://github.com/fernedy/repo-glow) before pushing).

## Workflow

1. Fork / branch.
2. Add or update tests (`python -m unittest discover -v`) — every new rule or flag needs one.
3. Keep the exit-code table and log patterns honest: only add entries backed by real behavior.
4. Open a PR with a clear description of the death being diagnosed.

## Ideas worth doing

- `--watch` mode: autopsy every container that dies, stream reports
- Kubernetes flavor (kube-autopsy exists — Docker Swarm and Podman do not)
- HTML report with the docker inspect diff of a working vs dead replica
