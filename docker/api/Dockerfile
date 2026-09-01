FROM python:3.10.14
ARG ENVIRONMENT
# ARG only exists during build; re-export it as ENV so the CMD below can still
# see which environment this image was built for.
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /app

COPY requirements/$ENVIRONMENT.txt requirements.txt

COPY system .

RUN pip install --no-cache-dir -r requirements.txt

# Development keeps Flask's auto-reloader; production runs a real WSGI server.
CMD sleep 15; \
    if [ "$ENVIRONMENT" = "production" ]; then \
        gunicorn "controller.app:create_app()" --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS:-5} --preload --access-logfile -; \
    else \
        python -m controller.app; \
    fi
