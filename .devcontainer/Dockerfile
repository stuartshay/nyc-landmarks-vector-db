FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    zsh \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    vim \
    less \
    htop \
    wget \
    unzip \
    openjdk-17-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install SonarQube Scanner
RUN curl -o /tmp/sonar-scanner.zip -L https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip \
    && unzip /tmp/sonar-scanner.zip -d /opt/ \
    && mv /opt/sonar-scanner-5.0.1.3006-linux /opt/sonar-scanner \
    && ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner \
    && rm /tmp/sonar-scanner.zip

# Set SonarQube Scanner environment
ENV SONAR_SCANNER_HOME=/opt/sonar-scanner
ENV PATH=$SONAR_SCANNER_HOME/bin:$PATH

# Install Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update \
    && apt-get install -y google-cloud-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set Zsh as default shell for the user
RUN chsh -s /bin/zsh $USERNAME

# Install Oh My Zsh for better Zsh experience (optional)
RUN su $USERNAME -c "curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | sh"

# Set up Python environment
RUN pip install --upgrade pip \
    && pip install pytest pytest-cov pytest-asyncio black isort flake8 mypy pylint pre-commit pip-tools

# Install notebook tools and quality checks
RUN pip install nbqa nbstripout jupyter jupyterlab ipywidgets plotly seaborn tqdm

# Install development tools for pinecone and vector databases
RUN pip install pinecone tenacity pandas-stubs

# Set working directory
WORKDIR /workspace

# Create needed directories
RUN mkdir -p /workspace/test_output/notebooks

# Set the default user
USER $USERNAME

# Set Python path
ENV PYTHONPATH=/workspace

# Make Zsh the default shell when the container starts
SHELL ["/bin/zsh", "-c"]

# Add a welcome message
RUN echo 'echo "👋 Welcome to NYC Landmarks Vector DB Development Environment\n\nUse the VS Code task \"Check Development Environment\" to verify setup.\nUse the task \"Run All Tests\" to run the test suite.\n"' >> ~/.zshrc
