# Ariadne Quantum Circuit Router - Multi-Platform Container
#
# This Dockerfile creates a containerized environment for Ariadne that supports:
# - CPU-based quantum simulation (all platforms)
# - Automated testing and benchmarking
# - Development and research workflows

# =============================================================================
# Stage 1: Base Python Environment
# =============================================================================
FROM python:3.11-slim AS base

# Set environment variables for better Python behavior
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 ariadne

# Set working directory
WORKDIR /home/ariadne

# =============================================================================
# Stage 2: Development Environment
# =============================================================================
FROM base AS development

# Install development tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        vim \
        nano \
        htop \
        tree \
    && rm -rf /var/lib/apt/lists/*

# Copy source code with proper ownership
COPY --chown=ariadne:ariadne . ./ariadne/

# Install Ariadne in development mode
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.4.3
RUN cd ariadne && pip install --no-cache-dir -e ".[dev]"

# Switch to non-root user
USER ariadne

# Set up environment
ENV ARIADNE_LOG_LEVEL=INFO
ENV ARIADNE_BACKEND_PREFERENCE="stim,tensor_network,qiskit"
ENV PYTHONPATH=/home/ariadne/ariadne/src

# Create workspace
RUN mkdir -p /home/ariadne/workspace

# Default command for development
CMD ["/bin/bash"]

# =============================================================================
# Stage 3: Testing Environment
# =============================================================================
FROM development AS testing

# Switch back to root for installations
USER root

# Copy test configuration
COPY --chown=ariadne:ariadne pyproject.toml ./ariadne/

# Switch back to non-root user
USER ariadne

# Set environment for testing
ENV ARIADNE_ENABLE_BENCHMARKS=true
ENV PYTEST_TIMEOUT=30

# Default command runs test suite
CMD ["python", "-m", "pytest", "ariadne/tests/", "-v", "--tb=short"]

# =============================================================================
# Stage 4: Production Environment (Lightweight)
# =============================================================================
FROM base AS production

# Copy only necessary files for production
COPY --chown=ariadne:ariadne src/ ./ariadne/src/
COPY --chown=ariadne:ariadne pyproject.toml ./ariadne/
COPY --chown=ariadne:ariadne README.md ./ariadne/

# Install Ariadne with core dependencies only
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.4.3
RUN cd ariadne && pip install --no-cache-dir .

# Switch to non-root user
USER ariadne

# Set up production environment
ENV ARIADNE_LOG_LEVEL=WARNING
ENV ARIADNE_BACKEND_PREFERENCE="stim,qiskit"

# Create volume mount point for results
VOLUME ["/home/ariadne/results"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import ariadne; print('OK')" || exit 1

# Default production command
CMD ["python", "-c", "import ariadne; print(f'Ariadne v{ariadne.__version__} ready')"]

# =============================================================================
# Stage 5: Quantum Full Environment (With All Platforms)
# =============================================================================
FROM base AS quantum-full

# Install additional system dependencies for quantum libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Try to install OpenCL if available (optional)
RUN apt-get update && \
    (apt-get install -y --no-install-recommends ocl-icd-opencl-dev || echo "OpenCL not available") && \
    rm -rf /var/lib/apt/lists/*

# Copy source code
COPY --chown=ariadne:ariadne . ./ariadne/

# Install core Ariadne first
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.4.3
RUN cd ariadne && pip install --no-cache-dir -e .

# Install quantum platforms with single command for better stability
RUN cd ariadne && \
    echo "Installing quantum platforms with single pip command..." && \
    pip install --no-cache-dir --timeout=300 --prefer-binary \
        pennylane>=0.30.0 \
        pyquil>=3.0.0 \
        amazon-braket-sdk>=1.40.0 \
        qsharp>=1.0.0 \
        || echo "Some quantum platforms failed to install - continuing with available ones"

# Install missing dependencies that might have been skipped
RUN pip install --no-cache-dir autograd || echo "autograd install failed"
RUN pip install --no-cache-dir toml || echo "toml install failed"

# Switch to non-root user
USER ariadne

# Set up quantum-full environment
ENV ARIADNE_LOG_LEVEL=INFO
ENV ARIADNE_BACKEND_PREFERENCE="stim,qiskit"
ENV PYTHONPATH=/home/ariadne/ariadne/src

# Create workspace and test installation
RUN mkdir -p /home/ariadne/workspace

# Test the installation in a separate step
RUN cd /home/ariadne/workspace && \
    python -c "import sys; print(f'Python {sys.version}')" && \
    python -c "import ariadne; print(f'Ariadne {ariadne.__version__}')" && \
    python -c "from ariadne import get_available_backends; backends = get_available_backends(); print(f'Available backends: {len(backends)}'); [print(f'  - {b}') for b in backends]" && \
    echo "Quantum-full environment ready!"

# Health check for quantum-full
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import ariadne; print('OK')" || exit 1

# Default command shows available backends
CMD ["python", "-c", "from ariadne import get_available_backends; import ariadne; print(f'Ariadne v{ariadne.__version__} Quantum-Full Environment'); print(f'Available backends ({len(get_available_backends())}):'); [print(f'  - {b}') for b in get_available_backends()]"]

# =============================================================================
# Metadata and Labels
# =============================================================================
LABEL org.opencontainers.image.title="Ariadne Quantum Circuit Router"
LABEL org.opencontainers.image.description="Intelligent quantum circuit routing with automatic backend selection"
LABEL org.opencontainers.image.authors="Hunter Bown <hunter@shannonlabs.dev>"
LABEL org.opencontainers.image.url="https://github.com/Hmbown/ariadne"
LABEL org.opencontainers.image.source="https://github.com/Hmbown/ariadne"
LABEL org.opencontainers.image.version="0.4.3"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Expose port for potential web interface (future)
EXPOSE 8000
