---
name: local-colima
description: Operate the reusable Docker Interview Lab on this Mac through local Colima, including Redis, MySQL, PostgreSQL, Elasticsearch, MongoDB, RabbitMQ, Kafka, MinIO, and kind. Use only when the user explicitly says the Docker or Kubernetes workload must run locally, on this Mac, or in local Colima. Never use for servers, SSH hosts, CI/CD, remote builds, or deployments. If location is ambiguous, ask whether execution is local Colima or remote before using this skill.
---

# Local Colima

Use the shared Docker Interview Lab for explicitly local work. Keep remote Docker and server operations completely outside this workflow.

## Location gate

Before running anything, classify the requested execution location:

- Local confirmed: the user says local, this Mac, my computer, localhost with local execution, or Colima. Continue.
- Remote confirmed: the user says server, SSH, remote host, CI/CD, deployment, cloud runner, or remote Docker context. Do not use this skill.
- Ambiguous: ask one concise question: "Docker 要运行在本机 Colima，还是远程服务器？" Do not inspect, start, or alter Colima while waiting.

An explicit `$local-colima` invocation counts as local confirmation unless the same request names a remote target.

## Workflow

1. Resolve the Lab by running `scripts/local-colima path`. The default is `/Users/zoe/Documents/daily/docker-interview-lab`; `LOCAL_COLIMA_LAB_DIR` can override it.
2. Read `services.yaml` and the repository `AGENTS.md` before selecting services.
3. Run `scripts/local-colima doctor`. Report any missing dependency or wrong Docker context instead of silently switching contexts.
4. Start only the required dependency with `scripts/local-colima up <service-or-profile>`.
5. Verify health with `scripts/local-colima status` and, when relevant, a real client query.
6. Stop workloads with `scripts/local-colima stop` when requested. Stopping preserves data.

Common profiles are `search`, `nosql`, `mq`, `object`, and `all`. Core Redis, MySQL, and PostgreSQL start with `up` and no profile. Service names such as `elasticsearch` or `kafka` are also accepted and mapped by the Lab.

## Kubernetes

- Use `scripts/local-colima k8s-up basic` for ordinary Kubernetes exercises.
- Use `scripts/local-colima k8s-up multinode` for scheduling, affinity, taints, DaemonSets, rollout placement, or node-failure exercises.
- Use `scripts/local-colima k8s-status` to inspect existing clusters.
- Use `scripts/local-colima k8s-stop basic|multinode` to release resources without deleting a cluster.
- kind nodes run as Docker containers inside Colima; they are logical nodes sharing the same Colima VM resources.
- Do not enable Colima's embedded K3s for this Lab.

## Safety rules

- Read-only checks, health checks, starts, and stops are allowed after the location gate passes.
- Never delete or prune containers, volumes, images, BuildKit cache, kind clusters, Colima profiles, or Lab data without explicit confirmation of exact targets.
- Never resize or recreate the Colima VM without explicit confirmation because doing so can make existing data unavailable.
- Never expose Lab ports beyond `127.0.0.1` without explicit approval.
- Do not substitute floating `latest` tags for the versions pinned in `compose.yaml` or the kind configs.
- Treat `.env` credentials as local development secrets and never publish them.

## Commands

Run `scripts/local-colima help` for the Lab's command list. The wrapper validates the Lab location and delegates to its checked-in `./lab` entrypoint; do not duplicate raw Compose commands unless diagnosing the entrypoint itself.
