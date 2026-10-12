# Running Meridian

From the repository root:

    docker compose -f lab/docker-compose.yml up --build

The site is at http://127.0.0.1:5001. The first start builds the image, which
takes a few minutes. Later starts take seconds.

To stop it:

    docker compose -f lab/docker-compose.yml down

To stop it and throw the database away, so the next start seeds a clean one:

    docker compose -f lab/docker-compose.yml down -v

## Accounts

The database is seeded automatically on every start. These accounts exist:

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin1234!` | administrator, full access |
| `rmasri` | `Agent1234!` | support agent |
| `tokafor` | `Agent1234!` | support agent |
| `jdoe` | `Client1234!` | customer, no agent access |

These passwords are weak on purpose. This is a teaching build.

The seeded people, addresses and tickets are invented. There is no real
customer data in this application, and none may be put into it.

## Changing the code

`src/` is mounted into the container. Edit a file under `src/` and the
application restarts itself within a few seconds. You do not need to rebuild
the image, and you do not need to restart the stack.

Watch what it is doing:

    docker compose -f lab/docker-compose.yml logs -f app

## The shape of the stack

    browser (through Burp)
        |
        v
    nginx        the only port you can reach, on 127.0.0.1:5001
        |
        v
    app          Django under gunicorn, not reachable directly
        |
        v
    db           PostgreSQL, not reachable directly

Some labs are about nginx rather than about the application. Its configuration
is `lab/nginx.conf`.

## If something goes wrong

**Port 5001 already in use.** Another copy is running. `docker compose -f
lab/docker-compose.yml down` first.

**The page does not load just after `up`.** The application waits for the
database and then runs migrations. Give it about twenty seconds.

**A change to `src/` seems to do nothing.** Check the log. A syntax error stops
the reload, and the message says which line.
