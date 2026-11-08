# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.12-slim-bookworm

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
# 3. Run with production settings. Without the required env
#    (DJANGO_SECRET_KEY, ALLOWED_HOSTS) startup fails instead of silently
#    using dev settings.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=rypt.settings.production

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install the application server.
RUN pip install "gunicorn==20.0.4"

# Install the project requirements.
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user. This Wagtail project
# uses SQLite, the folder needs to be owned by the user that
# will be writing to the database file.
RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files. Production settings require DJANGO_SECRET_KEY and
# ALLOWED_HOSTS; here they are throwaway values valid only for this build step.
# STATIC_ROOT points to a path writable by the "wagtail" user inside the image.
RUN DJANGO_SECRET_KEY=build-time-only-placeholder-key-not-a-secret \
    ALLOWED_HOSTS=rypt.folomin.com \
    STATIC_ROOT=/app/static \
    python manage.py collectstatic --noinput --clear

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application server.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   Wagtail instance can be started with a simple "docker run" command.
#
# SECURITY: production settings are mandatory (see ENV above). Provide real
# DJANGO_SECRET_KEY/ALLOWED_HOSTS at runtime; the app fails closed otherwise.
# Gunicorn binds 127.0.0.1:8000 by default — do NOT publish port 8000 publicly;
# put an HTTPS proxy (Nginx) in front. The systemd deploy (deploy/rypt.service)
# already binds 127.0.0.1:8000.
CMD set -xe; python manage.py migrate --noinput; gunicorn rypt.wsgi:application
