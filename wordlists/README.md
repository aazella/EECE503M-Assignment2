# Wordlists

Burp's built-in payload lists (**Payloads > Add from list**) are a Professional
feature. On Community that dropdown is greyed out and reads "Pro version only",
so the lists the worksheets ask for are supplied here instead.

Load one with **Payloads > Load ...** and pick the file, or open it in a text
editor and paste the contents into the payload box.

| File | Used by | Contains |
|---|---|---|
| `usernames.txt` | Lab 6 step 4, username enumeration | The seeded accounts mixed with names that do not exist. Sorting the responses by status code is the exercise, so the misses matter as much as the hits. |
| `hex-chars.txt` | Lab 1 step 8, blind extraction | `0-9a-f`. One payload position per character. Lab 1 asks you to extend it with the other characters a `pbkdf2` hash uses. |
| `passwords-20.txt` | nothing, at present | 20 common passwords, kept for a spraying exercise. No worksheet currently uses it, and none of these passwords opens a seeded account: the seeded ones are in `lab/seed.py`. |

Keep them short on purpose. Community throttles Intruder to roughly one request
per second, so a 20-entry list finishes in about 20 seconds and a 14-million-entry
list from the internet never finishes at all. The lesson is the method.
