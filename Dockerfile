FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies if any needed (none obvious from requirements.txt, but keeping apt-get update for good measure)
# If you need specific libraries for PIL or others, add them here.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    tzdata \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    libmtdev1 \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libxcb1 \
    libx11-dev \
    libxi-dev \
    libxrender-dev \
    libxext-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
