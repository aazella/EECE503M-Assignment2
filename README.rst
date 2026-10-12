Meridian Service Desk
=====================

.. warning::

   **This application is insecure on purpose. Do not deploy it.**

   It is teaching material for a university software-security course. Flaws are
   planted in it deliberately for students to find and repair. It binds to
   ``127.0.0.1`` and must stay there. Never expose it to a network you do not
   control, and never put real data in it. Every account, address and ticket it
   ships with is invented.

Meridian is a ticket tracker for internal support teams. Customers raise
tickets through a public form or by e-mail, agents work them in queues, and
knowledge-base articles cover the questions that keep coming back.

It is a Django application. The support desk itself lives in ``src/helpdesk``;
``standalone/`` holds the project that wires it into a runnable site.

Running it
----------

Everything runs in containers. From the repository root::

    docker compose -f lab/docker-compose.yml up --build

The site is then at http://127.0.0.1:5001/ .

The stack is three services:

``nginx``
  The only port you can reach. It serves static files and uploaded
  attachments, and passes everything else to the application.

``app``
  Django, under gunicorn. ``src/`` is mounted into the container, so an edit
  you make to the source takes effect within a few seconds. You do not need to
  rebuild the image to change the code.

``db``
  PostgreSQL. Not reachable from your browser.

The database is seeded on every start. Sign-in details and
troubleshooting are in ``lab/README.md``.

Layout
------

::

    src/helpdesk/        the application
      models.py          tickets, queues, follow-ups, attachments
      views/             staff.py, public.py, kb.py, api.py
      query.py           ticket search and saved searches
      forms.py           ticket creation and edit forms
      webhooks.py        outbound notifications
      templates/         the pages
      static/            CSS, JavaScript, images
    standalone/config/   Django settings, URLs, WSGI entry point
    lab/                 the container stack: nginx, gunicorn, PostgreSQL

Licensing
---------

Meridian is licensed under the terms of the BSD 3-clause license. See the
``LICENSE`` file for the full terms.

Meridian is distributed with third-party components that carry their own
licences. See ``LICENSE.3RDPARTY``.
