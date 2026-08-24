# Approach write-up

A voice-driven shopping list assistant with one firm constraint: **no LLM
anywhere** in the request path. Intent is classified by a small model trained
offline; everything else is deterministic rules. The whole thing runs from a
single Python process with no network calls at request time.

## Frontend

Built with **Next.js (React) and Tailwind CSS** using the Web Speech API for speech-to-text, with a dark
"Jarvis HUD" orb as the voice control (idle breathing pulse, faster pulse while
listening, brief tightening while processing; `prefers-reduced-motion` falls
back to a static ring). The client is a modern SPA that captures the
transcript, POSTs it alongside the current state, and updates the React state with the returned JSON. A collapsible
trace panel shows how each command was understood (intent, confidence, and the
extracted slots), which doubles as a debugging aid.

## Backend

A Python Flask app (`api/index.py`) exposed as **Serverless API Functions on Vercel** handles the logic. Intent classification (ADD / REMOVE / SEARCH_ITEM /
SEARCH_FILTER) uses a TF-IDF + logistic regression model trained offline with
scikit-learn and exported via skl2onnx, then run through ONNX Runtime. Because
skl2onnx compiles the *entire* pipeline — tokenization and TF-IDF weighting
included — into the ONNX graph, the server never re-implements vectorization:
it hands ONNX Runtime the raw transcript string and reads back a predicted
label and its probabilities. scikit-learn is a dev-only dependency; it is not
installed or imported at runtime.

The model's probabilities are not discarded. Out-of-vocabulary input collapses
to the class prior (~0.30), and even bare nouns top out around 0.40, so a
confidence floor of 0.42 separates a genuine command from noise and routes
low-confidence input to a "try rephrasing" message instead of guessing.

## Entity extraction (deliberately not ML)

Item, quantity, brand, size, and price range are pulled out with regex plus
JSON dictionary lookups. For this narrow, structured, closed-vocabulary task
that is more accurate and far more debuggable than a model, and it keeps the
pipeline free of any generative component. It also handles the arithmetic a
model would get wrong: metric roll-ups (`500 g` + `1 kg` reads back as
`1.5 kg`), multipliers (`two dozen eggs` → 24), and a per-item quantity cap.

## Hindi, offline

Hindi input is normalised by a static alias table (`api/data/aliases_hi.json`),
not a translation service. The previous build round-tripped commands and list
contents through Google Translate on every request — a network call that
contradicted the "no cloud" claim and added unbounded latency. The table now
maps Devanagari items, number words, units, and verbs to their canonical
English tokens and reorders the sentence (Hindi is verb-final; the English-
trained model expects verb-initial) before the same pipeline runs. UI strings
are served from a parallel key/value table (`api/data/ui_hi.json`), so
nothing is translated at request time and identical input always renders
identical output.

## State

List and purchase-history state is **completely stateless on the server** and is persisted entirely in the browser using `localStorage`. The React frontend passes the current items and history in the JSON payload of every API request. The Python backend processes the command, mutates the list, and returns the new state to the client, which then saves it. This solves the "ephemeral state" serverless limitation, requires no database provisioning, and ensures absolute user privacy.
