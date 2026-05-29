# CTF Performance Challenges

Performance engineering challenges deployed via [CTFd](https://github.com/CTFd/CTFd). Each challenge presents a real-world performance problem — participants fix the code/query/architecture to meet a target threshold.

## Challenge Categories

| # | Challenge | Category | Difficulty | Target |
|---|-----------|----------|------------|--------|
| 01 | Missing Index | Database | Beginner | < 5ms query |
| 02 | Transaction Batching | Database | Intermediate | < 500ms for 1000 writes |
| 03 | Chatty API | Network/IO | Beginner | < 2s total load time |
| 04 | Bounded Concurrency | Concurrency | Intermediate | Max throughput without errors |
| 05 | List to Set Lookup | Algorithmic | Beginner | < 50ms for 10K checks |
| 06 | N² Deduplication | Algorithmic | Intermediate | < 200ms for 100K records |

## Architecture

```
┌──────────────────────┐       ┌──────────────────────────┐
│  CTFd Platform       │       │  Challenge Containers    │
│  (scoring, users,    │◄─────►│  (per-user isolated)     │
│   hints, flags)      │       │                          │
└──────────────────────┘       │  ┌─────────┐ ┌────────┐ │
                               │  │ App/DB  │ │Verifier│ │
                               │  └─────────┘ └────────┘ │
                               └──────────────────────────┘
```

- **CTFd** manages scoring, user accounts, hints, and challenge metadata
- **Challenge containers** are isolated per-user environments with the broken code + verification sidecar
- **Verification** runs the participant's fix against the threshold and returns a flag on success

## Local Development

```bash
# Start CTFd + all challenge containers
docker compose up -d

# Start only a specific challenge for development
docker compose up challenge-01-missing-index

# Import challenges into CTFd
./scripts/import-challenges.sh

# Reset all challenge environments
./scripts/reset-environments.sh
```

## Adding a New Challenge

1. Create a directory under `challenges/` following the naming convention: `NN-short-name/`
2. Include:
   - `challenge.yml` — CTFd metadata (title, description, points, hints, flag format)
   - `Dockerfile` — participant environment
   - `docker-compose.yml` — challenge-specific services (DB, fake APIs, toxiproxy)
   - `verify/` — verification script/endpoint
   - `solution/` — maintainer-only reference solution
   - Seed data files as needed
3. Add the challenge to the root `docker-compose.yml`
4. Test locally, then run `./scripts/import-challenges.sh`

## Deployment

CTFd runs as a containerized service (Azure Container Apps or any Docker host). Challenges are orchestrated as on-demand containers per participant.

See `infrastructure/` for deployment configs.

## Contributing

Each challenge should:
- Present a **real** problem (something you'd find in production, not contrived)
- Have a **consistent** slow path (deterministic, not flaky)
- Be **verifiable** automatically (no manual grading)
- Include **hints** at increasing cost (CTFd deducts points per hint)
- Have a clean **solution** for maintainers to reference
