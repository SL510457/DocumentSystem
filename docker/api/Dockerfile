FROM python:3.10.14
ARG ENVIRONMENT
# ARG only exists during build; re-export it as ENV so the CMD below can still
# see which environment this image was built for.
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /app

# Dependencies before source: editing a .py file then invalidates only the
# COPY below, not the pip install above. The other way round, every one-line
# change reinstalls every package -- slow here, painful on a small server.
COPY requirements/$ENVIRONMENT.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY system .

# Development keeps Flask's auto-reloader; production runs a real WSGI server.
CMD sleep 15; \
    if [ "$ENVIRONMENT" = "production" ]; then \
        gunicorn "controller.app:create_app()" --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS:-5} --preload --access-logfile -; \
    else \
        python -m controller.app; \
    fi
