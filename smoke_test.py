#!/usr/bin/env python3
"""End-to-end smoke test over the real HTTP server.

The unit suite (tests/) runs at module level and does not need Flask. This
script is the missing HTTP-level check: it boots the actual Flask app and
exercises every route the browser calls, in English and Hindi. Run it locally,
where Flask is installed:

    pip install -r requirements.txt
    python smoke_test.py

Exit code 0 means every endpoint answered as expected.

Note on sessions: the client keys its list with a `?sid=` query parameter (see
sessionId() in server/public/js/app.js), not a cookie, so this script threads
one sid through every request the same way the browser does.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "server")
SID = "smoke-test-session"


def _req(method, path, body=None, sid=SID, lang=None):
    """Issue a request, threading sid (and optionally lang) as query params."""
    query = {}
    if sid:
        query["sid"] = sid
    if lang:
        query["lang"] = lang
    sep = "&" if "?" in path else "?"
    url = BASE + path + (sep + urllib.parse.urlencode(query) if query else "")

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read().decode()


def main():
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=SERVER,
        env={**os.environ, "PORT": "8080"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        # Wait for the ONNX session + Flask to come up.
        for _ in range(60):
            try:
                _req("GET", "/api/health", sid=None)
                break
            except urllib.error.URLError:
                time.sleep(0.25)
        else:
            raise SystemExit("server did not start - run it manually to see why")

        checks = []

        def check(name, ok, detail=""):
            checks.append(ok)
            print("%s  %s%s" % ("PASS" if ok else "FAIL", name,
                                "  <- " + detail if detail and not ok else ""))

        # 1. Static app shell.
        status, html = _req("GET", "/", sid=None)
        check("GET /            serves the app shell",
              status == 200 and "<html" in html.lower())

        # 2. Health.
        status, _ = _req("GET", "/api/health", sid=None)
        check("GET /api/health  responds", status == 200)

        # 3. UI strings differ between languages.
        _, en = _req("GET", "/api/strings", sid=None, lang="en")
        _, hi = _req("GET", "/api/strings", sid=None, lang="hi")
        check("GET /api/strings en and hi both present and different",
              "ui" in json.loads(en) and "ui" in json.loads(hi) and en != hi)

        # 4. Start from a clean list for this sid.
        _req("POST", "/api/clear", {})

        # 5. English ADD.
        status, body = _req("POST", "/api/command",
                            {"text": "add 2 liters of milk"})
        check("POST /api/command add 2 liters of milk",
              status == 200 and "milk" in body.lower(), body[:200])

        # 6. The item persists for this sid.
        _, state = _req("POST", "/api/state", {})
        check("POST /api/state   list persists for the sid",
              "milk" in state.lower(), state[:200])

        # 7. Metric roll-up: 200 g + 1 kg of potatoes reads back as 1.2 kg.
        _req("POST", "/api/command", {"text": "add 200 grams of potatoes"})
        _, rolled = _req("POST", "/api/command", {"text": "add 1 kg of potatoes"})
        check("POST /api/command metric roll-up shows 1.2 kg",
              "1.2 kg" in rolled, rolled[:300])

        # 8. Search returns the right product, not a cheap false match.
        _, search = _req("POST", "/api/command",
                         {"text": "find apples under $3"})
        payload = json.loads(search)
        names = [p["name"].lower() for p in payload.get("search", {}).get("results", [])]
        check("POST /api/command search apples returns only apples",
              bool(names) and all("apple" in n for n in names), str(names))

        # 9. Hindi ADD lands on the list (offline normalisation).
        _, hindi_add = _req("POST", "/api/command",
                            {"text": "दो लीटर दूध डालो", "lang": "hi"})
        check("POST /api/command Hindi add lands on the list",
              "milk" in hindi_add.lower() or "दूध" in hindi_add,
              hindi_add[:200])

        # 10. Low-confidence input is refused rather than guessed.
        _, noise = _req("POST", "/api/command", {"text": "qwerty zxcvb"})
        check("POST /api/command gibberish is refused, not guessed",
              "rephras" in noise.lower(), noise[:200])

        # 11. Suggestions endpoint answers.
        _, sug = _req("GET", "/api/suggest", lang="en")
        check("GET /api/suggest  returns suggestions",
              "suggestions" in json.loads(sug))

        # 12. Download is a text file.
        status, _ = _req("GET", "/api/download")
        check("GET /api/download responds", status == 200)

        # 13. Clear empties the list.
        _, cleared = _req("POST", "/api/clear", {})
        check("POST /api/clear   empties the list",
              "milk" not in cleared.lower(), cleared[:200])

        # 14. Sessions are isolated. Uses a real vocabulary item on purpose: an
        # unrecognised word ("caviar") is never added at all, so this check
        # would pass vacuously even if isolation were broken.
        _, other = _req("POST", "/api/command",
                        {"text": "add 3 bananas"}, sid="other-session")
        check("other session's add actually landed (guards the next check)",
              "banana" in other.lower(), other[:200])
        _, mine = _req("POST", "/api/state", {})
        check("sessions are isolated (other sid's item not visible)",
              "banana" not in mine.lower(), mine[:200])

        passed = sum(1 for c in checks if c)
        print("\n%d/%d checks passed" % (passed, len(checks)))
        return 0 if passed == len(checks) else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
