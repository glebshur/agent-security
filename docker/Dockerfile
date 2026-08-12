# syntax=docker/dockerfile:1.6
#
# Python dev container — sysbox-runc + systemd + sshd
#
#
# Designed for sysbox-runc, not default runc. With sysbox you do NOT need
# --privileged to run systemd + sshd inside; that's the security win.
#
# Build:   docker compose build
# Run:     docker compose up -d
# Connect: ssh -p 2223 dev@localhost   (from WSL2 host or from Windows)

FROM ubuntu:22.04

# systemd inside a container shuts down on SIGRTMIN+3; without this,
# `docker stop` waits the full grace period and SIGKILLs.
STOPSIGNAL SIGRTMIN+3

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

ARG DEV_USER=dev
ARG DEV_UID=1000
ARG DEV_GID=1000
ARG PYTHON_VERSION=3.12
ARG NODE_MAJOR=20

# ─── base packages ──────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        systemd systemd-sysv dbus \
        ca-certificates curl gnupg \
        sudo locales tzdata \
        openssh-server \
        git build-essential pkg-config \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8

# ─── Python ─────────────────────────────────────────────────────────────────
# Ubuntu 22.04 ships Python 3.10; deadsnakes gives us a current interpreter
# without touching /usr/bin/python3 (apt tooling depends on the system one).
RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# A baked-in virtualenv at /opt/venv is the default environment: `python`,
# `pip` and `pytest` resolve there for every shell, and `pip install` needs
# no sudo. It lives outside /home/dev on purpose — that path is a named
# volume, so anything under it would be shadowed at runtime.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN python${PYTHON_VERSION} -m venv ${VIRTUAL_ENV} \
    && ${VIRTUAL_ENV}/bin/pip install --no-cache-dir --upgrade \
        pip setuptools wheel \
    && ${VIRTUAL_ENV}/bin/pip install --no-cache-dir \
        uv \
        pipx \
        ipython \
        pytest \
        ruff \
        black \
        mypy

# ─── Node.js — solely to provide the Claude Code CLI ────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

# ─── dev user (UID-matched to typical WSL2 user 1000) ───────────────────────
RUN groupadd -g ${DEV_GID} ${DEV_USER} \
    && useradd -m -u ${DEV_UID} -g ${DEV_GID} -s /bin/bash ${DEV_USER} \
    && install -d -m 0700 -o ${DEV_USER} -g ${DEV_USER} /home/${DEV_USER}/.ssh \
    && echo "${DEV_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-${DEV_USER} \
    && chmod 0440 /etc/sudoers.d/90-${DEV_USER} \
    && chown -R ${DEV_USER}:${DEV_USER} ${VIRTUAL_ENV}

# ─── agent user — the account AI agents run under ───────────────────────────
# Deliberately NO sudoers entry. `dev` (you) can escalate to root; `agent`
# cannot, so it can't read root-only credentials, install systemd units to
# persist itself, or edit this container's own configuration.
#
# The separation only holds if the agent's session actually IS this user:
# SSH in as `agent` to run it. Logging in as `dev` and starting an agent from
# that shell gives it `dev`'s sudo and voids the whole thing.
RUN groupadd -g 1001 agent \
    && useradd -m -u 1001 -g 1001 -s /bin/bash agent \
    && install -d -m 0700 -o agent -g agent /home/agent/.ssh

# Login shells (and VS Code's remote server) inherit the venv + pipx bins.
RUN { \
        echo "export VIRTUAL_ENV=${VIRTUAL_ENV}"; \
        echo 'export PATH=/opt/venv/bin:$HOME/.local/bin:$PATH'; \
    } > /etc/profile.d/10-python-venv.sh \
    && chmod 0644 /etc/profile.d/10-python-venv.sh

# ─── force all egress through the filtering proxy ───────────────────────────
# The container has no direct internet (compose puts it on an `internal`
# network); egress-proxy enforces the domain allowlist. These vars make git,
# pip, npm, curl and Claude Code use it. /etc/environment is read by PAM so
# the VS Code remote server picks it up; the profile.d file covers login shells.
RUN { \
        echo 'http_proxy=http://egress-proxy:3128';  echo 'https_proxy=http://egress-proxy:3128'; \
        echo 'HTTP_PROXY=http://egress-proxy:3128';  echo 'HTTPS_PROXY=http://egress-proxy:3128'; \
        echo 'no_proxy=localhost,127.0.0.1,::1';     echo 'NO_PROXY=localhost,127.0.0.1,::1'; \
    } >> /etc/environment \
    && printf 'export %s\n' \
        'http_proxy=http://egress-proxy:3128'  'https_proxy=http://egress-proxy:3128' \
        'HTTP_PROXY=http://egress-proxy:3128'  'HTTPS_PROXY=http://egress-proxy:3128' \
        'no_proxy=localhost,127.0.0.1,::1'     'NO_PROXY=localhost,127.0.0.1,::1' \
      > /etc/profile.d/30-egress-proxy.sh \
    && chmod 0644 /etc/profile.d/30-egress-proxy.sh

# ─── sshd: key-only, no root, no forwarding of any kind ─────────────────────
# AllowAgentForwarding is off on purpose. 
# All forwarding is off too (TCP, stream-local/unix-socket, tun, gateway).
# A contained agent with any of these can tunnel out, pivot through the box,
# or proxy traffic
RUN mkdir -p /run/sshd \
    && { \
        echo 'PermitRootLogin no'; \
        echo 'PasswordAuthentication no'; \
        echo 'KbdInteractiveAuthentication no'; \
        echo 'UsePAM yes'; \
        echo 'X11Forwarding no'; \
        echo 'AllowAgentForwarding no'; \
        echo 'AllowTcpForwarding local'; \
        echo 'PermitOpen 127.0.0.1:*'; \
        echo 'AllowStreamLocalForwarding no'; \
        echo 'PermitTunnel no'; \
        echo 'GatewayPorts no'; \
        echo 'PrintMotd no'; \
        echo 'AcceptEnv LANG LC_*'; \
        echo "AllowUsers ${DEV_USER} agent"; \
    } > /etc/ssh/sshd_config.d/10-dev.conf \
    && ln -sf /lib/systemd/system/ssh.service \
              /etc/systemd/system/multi-user.target.wants/ssh.service

# ─── systemd hygiene for unprivileged systemd-in-container ──────────────────
# Mask units that don't make sense without host kernel/device access. Sysbox
# handles /sys, /proc, /run, /tmp etc. for us — no manual tmpfs mounts needed.
RUN systemctl mask \
        systemd-udevd.service \
        systemd-udevd-kernel.socket \
        systemd-udevd-control.socket \
        systemd-modules-load.service \
        sys-kernel-debug.mount \
        sys-kernel-tracing.mount \
        sys-fs-fuse-connections.mount \
        systemd-firstboot.service

EXPOSE 22

CMD ["/sbin/init"]
