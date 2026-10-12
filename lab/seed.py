"""Fill an empty lab database so the site looks like a service desk in use.

Run by lab/entrypoint.sh on every start. It is idempotent: it creates what is
missing and leaves what is already there, so a restart never duplicates data
and never resets a password a student has changed.

Every person, address and ticket here is invented for the lab. No real
customer, employee or account data goes in this file.
"""

from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.utils import timezone

from helpdesk.models import FollowUp, KBCategory, KBItem, Queue, Ticket

# Passwords are weak on purpose: this is a teaching build, never a real desk.
STAFF = [
    ("admin", "admin@meridian.invalid", "Admin1234!", True),
    ("rmasri", "r.masri@meridian.invalid", "Agent1234!", False),
    ("tokafor", "t.okafor@meridian.invalid", "Agent1234!", False),
]
CUSTOMER = ("jdoe", "j.doe@northwind.invalid", "Client1234!")

QUEUES = [
    ("Customer Support", "support", "support@meridian.invalid"),
    ("Billing", "billing", "billing@meridian.invalid"),
    ("Infrastructure", "infra", "infra@meridian.invalid"),
]

TICKETS = [
    ("support", "Cannot sign in after password reset",
     "I asked for a reset link yesterday. The link opens but the new password "
     "is never accepted. I have tried two browsers.",
     "j.doe@northwind.invalid", Ticket.OPEN_STATUS, 2, "rmasri"),
    ("support", "Attachment upload fails over 5 MB",
     "Uploading the site survey PDF returns an error page. Smaller files are "
     "fine. The file is 7.4 MB.",
     "m.haddad@northwind.invalid", Ticket.OPEN_STATUS, 3, None),
    ("support", "Export of closed tickets is empty",
     "The monthly export downloads a file with only the header row, although "
     "the list on screen shows 84 closed tickets.",
     "s.ferreira@lakeside.invalid", Ticket.REOPENED_STATUS, 2, "tokafor"),
    ("billing", "Invoice 4471 charged twice",
     "Our statement shows invoice 4471 taken on the 3rd and again on the 5th. "
     "Please reverse one of them.",
     "accounts@lakeside.invalid", Ticket.OPEN_STATUS, 1, "tokafor"),
    ("billing", "Need a VAT receipt for March",
     "The portal only offers a summary. We need a receipt showing the VAT "
     "line for our records.",
     "accounts@northwind.invalid", Ticket.RESOLVED_STATUS, 4, "tokafor"),
    ("infra", "Nightly backup job did not run",
     "No backup recorded for the 11th or the 12th. The job shows as scheduled "
     "but there is no log entry.",
     "ops@meridian.invalid", Ticket.OPEN_STATUS, 1, "rmasri"),
    ("infra", "Certificate expires in 9 days",
     "The wildcard certificate on the customer portal expires shortly. Raising "
     "this now so the renewal is not left to the last day.",
     "ops@meridian.invalid", Ticket.OPEN_STATUS, 2, None),
    ("support", "Knowledge base search returns nothing",
     "Searching the knowledge base returns no results for any word, including "
     "words I can see in an article title.",
     "j.doe@northwind.invalid", Ticket.CLOSED_STATUS, 3, "rmasri"),
]

FOLLOWUPS = [
    ("Cannot sign in after password reset", "rmasri",
     "Reset link acknowledged",
     "Thank you for the detail. I have sent a fresh link that is valid for one "
     "hour. Please tell me the exact message you see if it fails again.", True),
    ("Cannot sign in after password reset", None,
     "Customer reply",
     "The new link gives the same result. The message is 'that password cannot "
     "be used'.", True),
    ("Invoice 4471 charged twice", "tokafor",
     "Duplicate confirmed",
     "I can see both entries. The second was a retry after a gateway timeout. "
     "A refund is raised and takes three to five working days.", True),
    ("Invoice 4471 charged twice", "tokafor",
     "Internal note",
     "Gateway retry logic fired although the first charge had settled. Worth "
     "raising with the payments team.", False),
    ("Nightly backup job did not run", "rmasri",
     "Investigating",
     "The scheduler is running but the job holds no recorded start. Checking "
     "whether the credential the job uses has expired.", False),
]

KB = [
    ("support", "Accounts and access", "Accounts and access",
     "Signing in, passwords, and who can see what.", [
         ("I cannot sign in. What should I check first?",
          "Confirm the address you are using is the one the account was opened "
          "with. Reset links are valid for one hour and can only be used once. "
          "If a reset link has already been opened, ask for a new one."),
         ("How do I change the address on my account?",
          "Raise a ticket in Customer Support from the address currently on the "
          "account. We cannot move an account to a new address on the word of "
          "the new address alone."),
     ]),
    ("billing", "Invoices and payments", "Invoices and payments",
     "Statements, receipts and refunds.", [
         ("Where do I find a VAT receipt?",
          "Open the invoice from the billing page and choose the full document "
          "rather than the summary. If the VAT line is missing, raise a ticket "
          "in Billing with the invoice number."),
         ("How long does a refund take?",
          "Three to five working days once it is raised. The refund returns to "
          "the card that was charged, and we cannot send it elsewhere."),
     ]),
]


def ensure_users():
    people = {}
    for username, email, password, is_super in STAFF:
        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )
        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = is_super
            user.save()
        people[username] = user

    user, created = User.objects.get_or_create(
        username=CUSTOMER[0], defaults={"email": CUSTOMER[1]}
    )
    if created:
        user.set_password(CUSTOMER[2])
        user.save()
    people[CUSTOMER[0]] = user

    # Agents get the general helpdesk permissions but only the queue-access
    # permission for their own queue, so each is scoped to one queue. rmasri
    # works Customer Support, tokafor works Billing. Set (not add) every run so
    # a restart re-applies the scope even though the users already exist.
    general = Permission.objects.filter(
        content_type__app_label="helpdesk"
    ).exclude(codename__startswith="queue_access_")
    scope = {"rmasri": "queue_access_support", "tokafor": "queue_access_billing"}
    for username, codename in scope.items():
        perms = list(general)
        try:
            perms.append(Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
        people[username].user_permissions.set(perms)

    return people


def ensure_queues():
    queues = {}
    for title, slug, email in QUEUES:
        queue, _ = Queue.objects.get_or_create(
            slug=slug,
            defaults={
                "title": title,
                "email_address": email,
                "allow_public_submission": True,
                "escalate_days": 3,
            },
        )
        queues[slug] = queue

    # A queue that polls a mailbox stores the mailbox login. Invented creds.
    support = queues["support"]
    if not support.email_box_user:
        support.email_box_type = "imap"
        support.email_box_host = "imap.meridian.invalid"
        support.email_box_user = "support-bot@meridian.invalid"
        support.email_box_pass = "S3rv1ceDesk!mail"
        support.save()

    return queues


def ensure_tickets(queues, people):
    now = timezone.now()
    tickets = {}
    for offset, row in enumerate(TICKETS):
        slug, title, description, submitter, status, priority, owner = row
        ticket, created = Ticket.objects.get_or_create(
            title=title,
            queue=queues[slug],
            defaults={
                "description": description,
                "submitter_email": submitter,
                "status": status,
                "priority": priority,
                "assigned_to": people.get(owner),
                "created": now - timedelta(days=len(TICKETS) - offset, hours=3),
            },
        )
        if created and status == Ticket.RESOLVED_STATUS:
            ticket.resolution = "Receipt issued and sent to the address on file."
            ticket.save()
        tickets[title] = ticket
    return tickets


def ensure_followups(tickets, people):
    for offset, row in enumerate(FOLLOWUPS):
        ticket_title, username, title, comment, public = row
        ticket = tickets[ticket_title]
        FollowUp.objects.get_or_create(
            ticket=ticket,
            title=title,
            defaults={
                "comment": comment,
                "public": public,
                "user": people.get(username),
                "date": ticket.created + timedelta(hours=offset + 1),
            },
        )


def ensure_kb(queues):
    for slug, name, title, description, articles in KB:
        category, _ = KBCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "title": title,
                "description": description,
                "queue": queues[slug],
                "public": True,
            },
        )
        for order, (question, answer) in enumerate(articles, start=1):
            KBItem.objects.get_or_create(
                category=category,
                title=question,
                defaults={
                    "question": question,
                    "answer": answer,
                    "order": order,
                    "enabled": True,
                },
            )


people = ensure_users()
queues = ensure_queues()
tickets = ensure_tickets(queues, people)
ensure_followups(tickets, people)
ensure_kb(queues)

print(
    f"seed: {User.objects.count()} users, {Queue.objects.count()} queues, "
    f"{Ticket.objects.count()} tickets, {KBItem.objects.count()} articles"
)
