# Run the gate on untrusted (AI-written) Lean with no network and no secrets:
#   docker build -t harness-lean .
#   docker run --rm --network none -v "$PWD":/repo -w /repo harness-lean \
#     python3 -m harness gate <slug> <path/to/Solution.lean> --direction disproof
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git python3 \
    && rm -rf /var/lib/apt/lists/*
ARG LEAN_TOOLCHAIN=leanprover/lean4:v4.35.0
RUN curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain ${LEAN_TOOLCHAIN}
ENV PATH="/root/.elan/bin:${PATH}"
RUN lean --version
