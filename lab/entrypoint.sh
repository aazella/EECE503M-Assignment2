#!/bin/bash
# 503M lab entrypoint. Replaces the upstream one so students can edit the source
# and see the effect immediately, which the fix step of every lab requires.
#
# Upstream runs gunicorn with --preload, which loads the app once before forking
# and therefore ignores source changes. --preload and --reload are mutually
# exclusive, so this picks one.
set -e

cd /opt/meridian/standalone/

python manage.py migrate --noinput

if [ "${LAB_SEED:-1}" = "1" ] && [ -f /lab/seed.py ]; then
    python manage.py shell < /lab/seed.py || true
fi

if [ "${GUNICORN_RELOAD:-1}" = "1" ]; then
    MODE_FLAG="--reload"
    echo "503M: source reload ON. Edit files under src/ and the app restarts itself."
else
    MODE_FLAG="--preload"
fi

exec gunicorn standalone.config.wsgi:application \
     --name 503m-helpdesk \
     --bind 0.0.0.0:${GUNICORN_PORT:-8000} \
     --workers ${GUNICORN_NUM_WORKERS:-3} \
     --timeout ${GUNICORN_TIMEOUT:-60} \
     $MODE_FLAG \
     --log-level=info \
     --log-file=- \
     --access-logfile=- \
     "$@"
