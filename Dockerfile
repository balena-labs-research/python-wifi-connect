## Build Python packages to avoid need for builds in main image
FROM python:3.8.10-alpine3.14 AS python-buildstep

# Prevent pip 'warn script location' warnings. Equivalent to --no-warn-script-location
ENV PATH=/root/.local/bin:$PATH

RUN apk add --no-cache \
  build-base \
  dbus-dev \
  dbus-libs \
  git \
  glib-dev

# Copy Python requirements file
COPY src/requirements.txt /tmp/

# Install packages into a directory
RUN pip install wheel --no-cache-dir
RUN pip install --user -r /tmp/requirements.txt --no-cache-dir


## Compile container
FROM python:3.8.10-alpine3.14

# Set system environment variables
ENV FLASK_APP=run
ENV FLASK_ENV=production
ENV PATH=/root/.local/bin:$PATH

# Set working directory 
WORKDIR /app

# Install dependencies
RUN apk add --no-cache \
  dbus-libs \
  dnsmasq \
  glib \
  iw

# Copy built Python packages from build container
COPY --from=python-buildstep /root/.local /root/.local

# Insert application
COPY src .

# Run the start script
CMD ["sh", "start.sh"]
