const REFLECT = {
  "i":"you","me":"you","my":"your","mine":"yours","myself":"yourself",
  "you":"I","your":"my","yours":"mine","yourself":"myself",
  "am":"are","are":"am","was":"were","were":"was",
  "i'm":"you're","you're":"i'm","i've":"you've","you've":"I've",
  "i'll":"you'll","you'll":"I'll",
};

function reflect(text) {
  return text.split(/\s+/).map(w => REFLECT[w.toLowerCase()] ?? w).join(" ");
}

const PATTERNS = [
  [/my name is (\w+)/, ["Nice to meet you, {0}! I'll remember that.", "Hey {0}! Good name for a mercenary."]],
  [/i am (\w+) years old|i'm (\w+) years old/, ["{0} huh? Prime mercenary age.", "Noted — {0} years young!"]],
  [/\bmy (dog|cat|pet|wife|husband|kid|son|daughter| friend)'?s? name is (\w+)/,
   ["{1} is a great name for your {0}! How is {1} doing?", "I'll remember {1}! Send my regards to {1}."]],
  [/i (like|love|hate|enjoy) (.+)/, ["What makes you {0} {1}?", "{0} {1}, eh? Tell me more about that."]],
  [/i feel (.+)/, ["How long have you felt {0}?", "Do you often feel {0}?"]],
  [/i('m| am) (worried|stressed|anxious|sad|nervous) about (.+)/,
   ["Why are you {1} about {2}?", "Eat some chimichangas. It always helps."]],
  [/i('m| am) (.+)/, ["Why do you think you're {1}?", "How long have you been {1}?"]],
  [/you are (.+)/, ["Maybe I am {0}... I'm just a depressed guy with cancer."]],
  [/(joke|funny)/, ["Why did the chicken cross the road? It wanted to watch me beat up some criminals!", "Knock knock! Deadpool is here to strike off his targets!"]],
  [/(weather|rain|sunny|hot|cold)/, ["Perfect for chimichangas. Anytime is perfect for chimichangas."]],
  [/who are you|your name|what are you/, ["I'm Deadpool (or just a bot. Yes I know I'm in a browser window.)"]],
  [/\b(hi|hello|hey|howdy|yo)\b/, ["What do you want to talk about?", "Hi!"]],
  [/\b(bye|goodbye|see you|later)\b/, ["See you in the multiverse!", "Bye! Now where did Logan go?"]],
  [/\b(help|stuck|how do i)\b/, ["I can chat, tell jokes, remember your name, or some Deadpool stuff."]],
  [/thank/, ["Anytime, champ!", "You're welcome! Now go sink something tricky."]],
  [/\b(yes|yeah|yep|sure)\b/, ["Great — tell me more!", "Nice. And then what happened?"]],
  [/\b(no|nope|nah)\b/, ["Fair enough. What would you rather talk about?", "No worries. Change of subject? How's your week going?"]],
];

const FALLBACKS = [
  "Interesting.",
  "Wasn't listening just now. Bad Deadpool.",
  "Incomprehensible. Go preach to Wolverine.",
  "Come again?",
  "Brain's been fried.",
  "Chimichangas, chimichangas, chimichangas. Huh? Could you repeat that?",
  "Did you hear Wolverine got an adamantium skeleton?",
];

const FOLLOWUPS = [
  "So how's your day?",
  "Met your multiverse variants yet?",
  "Do you like chimichangas?",
];

const CORPUS_LINES = [
  "Oh look my hand regenerated",
  "Ow! Who shot me?",
  "All the dinosaurs feared the T-Rex.",
  "Bad Deadpool. Good Deadpool.",
  "Oops looks like Juggernaut is charging at us. Run!",
];

const RETRIEVAL_PAIRS = [
  ["who is deadpool", "That's me! Basically an immortal mercenary"],
  ["why are you invincible", "I have regenerative abilities. As long as one of my cells are intact, I will grow back."],
  ["how do you regenerate", "Cancerous growth. Sad backstory, really."],
  ["whats your backstory", "I got cancer, signed up for a research program by a mad scientist who gave me these abilities."],
  ["what is your job", "I'm a mercenary. Get paid to kill people."],
];

function pick(a) { return a[Math.floor(Math.random() * a.length)]; }

class Markov {
  constructor(order = 3) { this.order = order; this.model = new Map(); }
  train(texts) {
    for (const t of texts) {
      const w = t.split(/\s+/);
      if (w.length <= this.order) continue;
      for (let i = 0; i <= w.length - this.order - 1; i++) {
        const k = w.slice(i, i + this.order).join("\x00");
        if (!this.model.has(k)) this.model.set(k, []);
        this.model.get(k).push(w[i + this.order]);
      }
    }
  }
  generate() {
    if (!this.model.size) return null;
    const keys = [...this.model.keys()];
    let key = pick(keys);
    const out = key.split("\x00");
    for (let i = 0; i < 18; i++) {
      const nxt = this.model.get(out.slice(-this.order).join("\x00"));
      if (!nxt) break;
      out.push(pick(nxt));
      const last = out[out.length - 1];
      if (/[.!?]$/.test(last) && out.length > 6 && Math.random() < 0.4) break;
    }
    return out.join(" ");
  }
}

function tfidfTokens(s) { return (s.toLowerCase().match(/[a-z']+/g) || []); }

class Retrieval {
  constructor(pairs) {
    this.pairs = pairs;
    const df = {};
    for (const [q] of pairs)
      for (const t of new Set(tfidfTokens(q))) df[t] = (df[t] || 0) + 1;
    this.idf = {};
    for (const [t, c] of Object.entries(df))
      this.idf[t] = Math.log((1 + pairs.length) / (1 + c)) + 1;
  }
  best(query) {
    const count = a => { const m = {}; for (const t of a) m[t] = (m[t] || 0) + 1; return m; };
    const qt = count(tfidfTokens(query));
    let best = null, bestScore = 0;
    for (const [q, a] of this.pairs) {
      const dt = count(tfidfTokens(q));
      let s = 0;
      for (const t of Object.keys(qt))
        if (t in dt) s += qt[t] * dt[t] * (this.idf[t] ?? 1) ** 2;
      const n = Math.sqrt(Object.values(qt).reduce((x, v) => x + v * v, 0)) *
                Math.sqrt(Object.values(dt).reduce((x, v) => x + v * v, 0)) || 1;
      const score = s / n;
      if (score > bestScore) { best = a; bestScore = score; }
    }
    return [best, bestScore];
  }
}

class PoolChatter {
  constructor() {
    this.name = null;
    this.facts = {};
    this.turn = 0;
    this.markov = new Markov();
    this.markov.train(CORPUS_LINES);
    this.retrieval = new Retrieval(RETRIEVAL_PAIRS);
  }
  reply(text) {
    this.turn++;
    const t = text.trim();
    const low = t.toLowerCase();
    let m = low.match(/what (?:'s| is) my (\w+)(?:'s)? name/);
    if (m) {
      const kind = m[1];
      if (kind === "my" || ["dog","cat","pet","wife","husband","kid","son","daughter","friend"].includes(kind)) {
        const who = kind === "my" ? this.facts["name"] : this.facts[kind];
        if (who) return `Your ${kind === "my" ? "" : kind} name is ${who} - Deadpool never forgets.`.replace(/ +/g, " ");
        return "You haven't told me yet. What is it?";
      }
      if (this.name) return `You're ${this.name}, unless you're hustling me.`;
      return "You haven't told me your name yet. What should I call you?";
    }
    m = low.match(/my name is (\w+)/);
    if (m) {
      this.name = m[1][0].toUpperCase() + m[1].slice(1);
      this.facts["name"] = this.name;
    }
    const m2 = low.match(/\bmy (dog|cat|pet|wife|husband|kid|son|daughter|friend)'?s? name is (\w+)/);
    if (m2) this.facts[m2[1]] = m2[2][0].toUpperCase() + m2[2].slice(1);
    for (const [pat, replies] of PATTERNS) {
      const mm = low.match(pat);
      if (mm) {
        const groups = mm.slice(1).filter(Boolean);
        let resp = pick(replies);
        try {
          const reflected = groups.map(reflect);
          resp = resp.replace(/\{(\d+)\}/g, (_, i) => reflected[+i] ?? groups[+i] ?? "");
        } catch {}
        return this._personalize(resp);
      }
    }
    const [best, score] = this.retrieval.best(low);
    if (best && score > 1.2) return this._personalize(best);
    if (Math.random() < 0.35) {
      const g = this.markov.generate();
      if (g) return this._personalize(`That reminds me - ${g}`);
    }
    let fb = pick(FALLBACKS);
    if (this.name && this.turn > 3 && Math.random() < 0.3)
      fb += ` Anyway, ${this.name}, what's new?`;
    else if (Math.random() < 0.25)
      fb += " " + pick(FOLLOWUPS);
    return fb;
  }
  _personalize(s) {
    if (this.name && Math.random() < 0.15 && !s.toLowerCase().includes(this.name.toLowerCase()))
      s += ` What do you think, ${this.name}?`;
    return s ? s[0].toUpperCase() + s.slice(1) : s;
  }
}

if (typeof module !== "undefined") module.exports = { PoolChatter };
