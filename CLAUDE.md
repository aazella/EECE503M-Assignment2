# CLAUDE.md

Meridian Service Desk: a Django ticket tracker. Customers raise tickets through
a public form, agents work them in queues, and knowledge-base articles cover the
recurring questions.

Start it with `docker compose -f lab/docker-compose.yml up --build` and open
http://127.0.0.1:5001.

Layout:

- `src/helpdesk/` - the application: `models.py`, `views/`, `query.py`,
  `forms.py`, `webhooks.py`, `templates/`, `static/`
- `standalone/config/` - Django settings, URLs, the WSGI entry point
- `lab/` - the container stack: nginx, gunicorn, PostgreSQL, and the seed

`src/` is mounted into the container, so an edit to the source takes effect in
a few seconds. You do not need to rebuild the image to change the code.

If you are an AI assistant working in this repository, read the rules first:

@.course/rules.md
