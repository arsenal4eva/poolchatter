import re, random, math, collections

REFLECT = {
    "i" : "you", "me": "you", "my": "your", "mine": "yours", "myself": "yourself",
    "you": "I", "your": "my", "yours": "mine", "yourself": "myself",
    "am": "are", "are": "am", "was": "were", "were": "was",
    "i'm": "you're", "you're": "i'm", "i've": "you've", "you've": "I've",
    "i'll": "you'll", "you'll": "I'll",
}

def reflect(text):
    return " ".join(REFLECT.get(w.lower(), w) for w in re.findall(r"[\w']+|[^\w\s]", text) for _ in [0]) if False else " ".join(REFLECT.get(w.lower(), w) for w in text.split())

PATTERNS = [
    (r"my name is (\w+)", ["Nice to meet you, {0}! I'll remember that.", "Hey {0}! Good name for a mercenary."]),
    (r"i am (\w+) years old|i'm (\w+) years old", ["{0} huh? Prime mercenary age.", "Noted — {0} years young!"]),
    (r"\bmy (dog|cat|pet|wife|husband|kid|son|daughter| friend)'?s? name is (\w+)",
     ["{1} is a great name for your {0}! How is {1} doing?", "I'll remember {1}! Send my regards to {1}."]),
    (r"i (like|love|hate|enjoy) (.+)", ["What makes you {0} {1}?", "{0} {1}, eh? Tell me more about that."]),
    (r"i feel (.+)", ["How long have you felt {0}?", "Do you often feel {0}?"]),
    (r"i('m| am) (worried|stressed|anxious|sad|nervous) about (.+)",
     ["Why are you {1} about {2}?", "Eat some chimichangas. It always helps."]),
    (r"i('m| am) (.+)", ["Why do you think you're {1}?", "How long have you been {1}?"]),
    (r"you are (.+)", ["Maybe I am {0}... I'm just a depressed guy with cancer."]),
    (r"(joke|funny)", ["Why did the chicken cross the road? It wanted to watch me beat up some criminals!", "Knock knock! Deadpool is here to strike off his targets!"]),
    (r"(weather|rain|sunny|hot|cold)", ["Perfect for chimichangas. Anytime is perfect for chimichangas."]),
    (r"who are you|your name|what are you", ["I'm Deadpool (or just a bot. Yes I know I'm in a browser window.)"]),
    (r"\b(hi|hello|hey|howdy|yo)\b", ["What do you want to talk about?", "Hi!"]),
    (r"\b(bye|goodbye|see you|later)\b", ["See you in the multiverse!", "Bye! Now where did Logan go?"]),
    (r"\b(help|stuck|how do i)\b", ["I can chat, tell jokes, remember your name, or some Deadpool stuff."]),
    (r"thank", ["Anytime, champ!", "You're welcome! Now go sink something tricky."]),
    (r"\b(yes|yeah|yep|sure)\b", ["Great — tell me more!", "Nice. And then what happened?"]),
    (r"\b(no|nope|nah)\b", ["Fair enough. What would you rather talk about?", "No worries. Change of subject? How's your week going?"]),
]



FALLBACKS = [
    "Interesting.",
    "Wasn't listening just now. Bad Deadpool.",
    "Incomprehensible. Go preach to Wolverine.",
    "Come again?",
    "Brain's been fried.",
    "Chimichangas, chimichangas, chimichangas. Huh? Could you repeat that?",
    "Did you hear Wolverine got an adamantium skeleton?",
]

FOLLOWUPS = [
    "So how's your day?",
    "Met your multiverse variants yet?",
    "Do you like chimichangas?",
]


class Markov:
    def __init__(self, order=3):
        self.order = order
        self.model = collections.defaultdict(list)
    def train(self, texts):
        for t in texts:
            w = t.split()
            if len(w) <= self.order: continue
            for i in range(len(w) - self.order):
                self.model[tuple(w[i:i+self.order])].append(w[i+self.order])
    def generate(self, seed=None, maxlen=18):
        if not self.model: return None
        key = random.choice(list(self.model.keys())) if seed is None else None
        if seed:
            sw = seed.split()
            key = tuple(sw[-self.order:]) if len(sw) >= self.order else random.choice(list(self.model.keys()))
            if key not in self.model: key = random.choice(list(self.model.keys()))
        out = list(key)
        for _ in range(maxlen):
            nxt = self.model.get(tuple(out[-self.order]))
            if not nxt: break
            out.append(random.choice(nxt))
            if out[-1].endswith((".", "!", "?")) and len(out) > 6 and random.random() < 0.4: break
        return " ".join(out)


def tfidf_tokens(s):
    return re.findall(r"[a-z']+", s.lower())


class Retrieval:
    def __init__(self, pairs):
        self.pairs = pairs
        df = collections.Counter()
        for q, _ in pairs:
            for t in set(tfidf_tokens(q)): df[t] += 1
        self.idf = {t: math.log((1 + len(pairs)) / (1+c)) + 1 for t, c in df.items()}
    def best(self, query):
        qt = collections.Counter(tfidf_tokens(query))
        best, bests = None, 0.0
        for q, a in self.pairs:
            dt = collections.Counter(tfidf_tokens(q))
            common = set(qt) & set(dt)
            s = sum(qt[t] * dt[t] * self.idf.get(t, 1) ** 2 for t in common)
            n = math.sqrt(sum(v*v for v in qt.values())) * math.sqrt(sum(v*v for v in dt.values())) or 1
            score = s/n
            if score > bests: best, bests = a, score
        return (best, bests)


class PoolChatter:
    def __init__(self, seed=42):
        random.seed(seed)
        self.name = None
        self.facts = {}
        self.turn = 0
        self.markov = Markov()
        self.markov.train(CORPUS_LINES)
        self.retrieval = Retrieval(RETRIEVAL_PAIRS)
        self.last_topic = None

    def reply(self, text):
        self.turn += 1
        t = text.strip()
        low = t.lower()
        m = re.search(r"what (?:'s| is) my (\w+)(?:'s)? name", low)
        if m:
            kind = m.group(1)
            if kind == "my" or kind in ("dog", "cat", "pet", "wife", "husband", "kid", "son", "daughter", "friend"):
                who = self.facts.get("name") if kind == "my" else self.facts.get(kind)
                if who: return f"Your {kind if kind!='my' else ''} name is {who} - Deadpool never forgets.".replace(" ", " ")
                return "You haven't told me yet. What is it?"
            if self.name: return f"You're {self.name}, unless you're hustling me."
            return "You haven't told me your name yet. What should I call you?"
        m = re.search(r"my name is (\w+)", low)
        if m:
            self.name = m.group(1).capitalize()
            self.facts["name"] = self.name
        m2 = re.search(r"\bmy (dog|cat|pet|wife|husband|kid|son|daughter|friend'?s? name is (\w+))", low)
        if m2:
            self.facts[m2.group(1)] = m2.group(2).capitalize()
        for pat, replies in PATTERNS:
            m = re.search(pat, low)
            if m:
                groups = [g for g in m.groups() if g]
                resp = random.choice(replies)
                try:
                    reflected = [reflect(g) for g in groups]
                    resp = resp.format(*reflected, *groups)
                except Exception:
                    pass
                return self._personalize(resp)
        best, score = self.retrieval.best(low)
        if best and score > 1.2:
            return self._personalize(best)
        if random.random() < 0.35:
            g = self.markov.generate()
            if g: return self._personalize(f"That reminds me - {g}")
        fb = random.choice(FALLBACKS)
        if self.name and self.turn > 3 and random.random() < 0.3:
            fb += f"Anyway, {self.name}, what's new?"
        elif random.random() < 0.25:
            fb += " " + random.choice(FOLLOWUPS)
        return fb

    def _personalize(self, s):
        if self.name and random.random() < 0.15 and self.name.lower() not in s.lower():
            s += f" What do you think, {self.name}?"
        return s[0].upper() + s[1:] if s else s


CORPUS_LINES = [
    "Oh look my hand regenerated",
    "Ow! Who shot me?",
    "All the dinosaurs feared the T-Rex.",
    "Bad Deadpool. Good Deadpool.",
    "Oops looks like Juggernaut is charging at us. Run!",
]

RETRIEVAL_PAIRS = [
    ("who is deadpool", "That's me! Basically an immortal mercenary"),
    ("why are you invincible", "I have regenerative abilities. As long as one of my cells are intact, I will grow back."),
    ("how do you regenerate", "Cancerous growth. Sad backstory, really."),
    ("whats your backstory", "I got cancer, signed up for a research program by a mad scientist who gave me these abilities."),
    ("what is your job", "I'm a mercenary. Get paid to kill people."),
]



