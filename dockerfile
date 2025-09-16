# Base image with Python
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    wget \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy Python requirements if you have a requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install pybind11 and setuptools
RUN pip install pybind11 setuptools

# Copy your src folder BEFORE building the pybind11 module
COPY src/ ./src

# Build the pybind11 module
WORKDIR /app/src
RUN python pybind11_setup.py build_ext --inplace

# Copy your dashboard folder
COPY dashboard/ ./dashboard

RUN mkdir -p /app/logs

# Set working directory to dashboard for Streamlit
WORKDIR /app/dashboard

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]



