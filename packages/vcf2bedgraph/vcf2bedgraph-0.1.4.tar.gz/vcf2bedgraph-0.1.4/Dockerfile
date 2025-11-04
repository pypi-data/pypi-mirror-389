FROM astral/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Create a virtual environment and install the package
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install vcf2bedgraph and its dependencies
RUN uv pip install vcf2bedgraph

# Set the entrypoint
ENTRYPOINT ["vcf2bedgraph"]
CMD ["--help"]
