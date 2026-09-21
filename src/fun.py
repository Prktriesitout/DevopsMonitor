"""Fun demo endpoints and interactive landing page (additive only)."""

import random
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter()

# In-memory session counter for fun requests.
_fun_counter = 0

JOKES = [
    "Why do programmers prefer dark mode?"
    " Because light attracts bugs.",
    "A SQL query walks into a bar, sees two"
    " tables and asks: Can I join you?",
    "Why was the JavaScript developer sad?"
    " Because he didn't Node how to Express"
    " himself.",
    "How many programmers does it take to"
    " change a light bulb? None, that's a"
    " hardware problem.",
    "Why do Java developers wear glasses?"
    " Because they can't C#.",
    "A programmer's wife tells him: Go to"
    " the store and buy a loaf of bread."
    " If they have eggs, buy a dozen."
    " He comes home with 12 loaves.",
    "What's a programmer's favorite hangout"
    " place? Foo Bar.",
    "Why do programmers hate nature?"
    " It has too many bugs.",
    "What do you call a computer that sings?"
    " A-Dell.",
    "Why did the developer go broke?"
    " Because he used up all his cache.",
]

QUOTES = [
    ("The only way to do great work is to"
     " love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a"
     " leader and a follower.", "Steve Jobs"),
    ("Stay hungry, stay foolish.",
     "Stewart Brand"),
    ("Talk is cheap. Show me the code.",
     "Linus Torvalds"),
    ("Programs must be written for people"
     " to read.", "Harold Abelson"),
    ("Simplicity is prerequisite for"
     " reliability.", "Edsger W. Dijkstra"),
    ("First, solve the problem. Then, write"
     " the code.", "John Johnson"),
    ("Any fool can write code that a computer"
     " can understand. Good programmers write"
     " code that humans can understand.",
     "Robert C. Martin"),
    ("The best error message is the one that"
     " never shows up.", "Thomas Fuchs"),
    ("Make it work, make it right, make it"
     " fast.", "Kent Beck"),
]

FORTUNES = [
    "A bug in your code will become a feature"
    " in production.",
    "The code you write today will be"
    " maintained by you tomorrow.",
    "A well-placed comment saves a thousand"
    " words of confusion.",
    "Your next deployment will be flawless.",
    "The best optimization is the one you"
    " don't need.",
    "A clean codebase brings peace of mind.",
    "Your tests will catch the bug before"
    " the users do.",
    "The documentation you skip writing will"
    " haunt you later.",
    "A refactored function will bring"
    " unexpected joy.",
    "Your CI pipeline will turn green on the"
    " first try.",
]

_LANDING_HTML_PATH = Path(__file__).parent / "templates" / "landing.html"


def _bump_fun_counter():
    """Increment the in-memory fun request counter."""
    global _fun_counter  # noqa: PLW0603
    _fun_counter += 1
    return _fun_counter


# ---- Routes ----


@router.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the interactive landing page."""
    html = _LANDING_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@router.get("/api/joke")
async def get_joke():
    """Return a random joke."""
    _bump_fun_counter()
    return {"joke": random.choice(JOKES)}


@router.get("/api/quote")
async def get_quote():
    """Return a random quote with author."""
    _bump_fun_counter()
    text, author = random.choice(QUOTES)
    return {"quote": text, "author": author}


@router.get("/api/dice")
async def roll_dice(sides: int = Query(default=6)):
    """Roll a die with the given number of sides (2-100)."""
    if sides < 2 or sides > 100:
        return HTMLResponse(
            content='{"detail":'
                    '"sides must be between 2 and 100"}',
            status_code=422,
        )
    _bump_fun_counter()
    return {"sides": sides, "result": random.randint(1, sides)}


@router.get("/api/coinflip")
async def flip_coin():
    """Flip a coin and return heads or tails."""
    _bump_fun_counter()
    return {"result": random.choice(["heads", "tails"])}


@router.get("/api/fortune")
async def get_fortune():
    """Return a random fortune cookie message."""
    _bump_fun_counter()
    return {"fortune": random.choice(FORTUNES)}


@router.get("/api/fun-stats")
async def fun_stats():
    """Return the in-memory fun request counter."""
    return {"fun_requests_served": _fun_counter}
