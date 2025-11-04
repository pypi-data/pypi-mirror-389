import random
from typing import Dict, List

# Core data
_TIPS = {
    "math": [
        "If it’s too complex, assume x = 0. Problem solved.",
        "Numbers never lie, but you might when asked if you understand them.",
    ],
    "history": [
        "If you forget the date, just say 'around that time.'",
        "History repeats itself. So if you fail this exam, you’ll get another chance.",
    ],
    "physics": [
        "If it moves, it’s probably physics. If not, hit it again.",
        "Remember: every action has an equal and opposite procrastination.",
    ],
}

_MOTIVATIONS = {
    "sarcastic": [
        "Remember: diamonds are made under pressure. So start panicking.",
        "Dream big, nap often.",
        "You can do anything! Except maybe that.",
    ],
    "genuine": [
        "You’ve got this! Probably. Maybe. Let’s hope.",
        "One page at a time — just keep going.",
        "Even small progress counts. Keep at it.",
    ],
}

_EXCUSES = {
    "homework": [
        "My cat deleted my assignment. She’s learning cybersecurity.",
        "Google Docs went into witness protection.",
    ],
    "late": [
        "My Wi-Fi connected to another dimension.",
        "I was stuck in traffic... on the information highway.",
    ],
    "exam": [
        "I didn’t fail. I just found 99 ways that didn’t work.",
        "The test was multiple guess, and I guessed wrong multiple times.",
    ],
}

_STEPS = [
    "Make coffee.",
    "Open your notes.",
    "Panic productively for 90 minutes.",
    "Reward yourself with a snack break.",
    "Google half the material.",
]

_ROASTS = {
    "cs": [
        "Your code is like your dating life - full of bugs and nobody wants to debug it.",
        "You code like you're trying to solve world hunger... one syntax error at a time.",
        "Your algorithm is so inefficient, it makes bubble sort look like a speed demon.",
        "I've seen more organized code in a toddler's finger painting.",
        "Your variable names are more confusing than IKEA instructions.",
    ],
    "math": [
        "Your math skills are so bad, calculators file restraining orders.",
        "You approach equations like they're written in ancient hieroglyphs.",
        "Your algebra is weaker than decaf coffee on a Monday morning.",
        "You solve problems like you're playing mathematical roulette.",
        "Your geometry is so off, even abstract art looks realistic in comparison.",
    ],
    "physics": [
        "Your understanding of physics violates more laws than a parking ticket collector.",
        "You handle momentum like you handle your life - poorly.",
        "Your grasp of gravity is the only thing keeping your grades down.",
        "You treat thermodynamics like it's thermo-optional-amics.",
        "Your physics solutions defy more laws than they follow.",
    ],
}

_BREAK_ACTIVITIES = {
    "stretch": [
        "Do the 'I've been sitting too long' neck roll dance.",
        "Attempt yoga poses that would make a pretzel jealous.",
        "Stretch like a cat who just discovered the concept of flexibility.",
        "Channel your inner flamingo with some one-legged stretches.",
    ],
    "walk": [
        "Take a victory lap around your room (or building if you're feeling fancy).",
        "Practice your 'deep in thought' stride around the block.",
        "Walk to the kitchen and contemplate the meaning of snacks.",
        "Do the 'I need fresh air but also Wi-Fi' outdoor shuffle.",
    ],
    "snack": [
        "Fuel up with brain food (chips count as brain food, right?).",
        "Have a philosophical discussion with your refrigerator contents.",
        "Practice portion control by eating one cookie... at a time... repeatedly.",
        "Conduct a scientific taste test of available snacks.",
    ],
}

_PLAYLIST_MOODS = {
    "focus": [
        "Lofi Hip Hop Radio - beats to procrastinate/study to",
        "Classical Music for People Who Think They're Sophisticated",
        "Ambient Sounds That Definitely Won't Put You to Sleep",
    ],
    "energetic": [
        "Upbeat Songs to Make You Feel Productive (Even If You're Not)",
        "High-Energy Tracks for Last-Minute Panic Sessions",
        "Songs That Make Cramming Feel Like a Dance Party",
    ],
    "chill": [
        "Mellow Vibes for When You've Given Up on Deadlines",
        "Relaxing Tunes for Stress-Free Procrastination",
        "Calm Music to Help You Accept Your Academic Fate",
    ],
}

_DEADLINE_MESSAGES = {
    "panic": [
        "Time to activate MAXIMUM OVERDRIVE mode!",
        "This is fine. Everything is fine. *nervous laughter*",
        "Remember: pressure makes diamonds... or nervous breakdowns.",
        "It's crunch time! Time to crunch those... study materials.",
    ],
    "funny": [
        "Deadline approaching faster than your motivation to start working!",
        "Time left: {hours} hours. Panic level: Moderate to severe.",
        "Your deadline called - it's running fashionably early.",
        "Breaking news: Local student discovers deadlines don't extend themselves.",
    ],
    "motivational": [
        "You've got this! {hours} hours is plenty of time to work miracles!",
        "Every hour counts - make them work for you!",
        "You're closer to the finish line than you think!",
        "Time to show this deadline who's boss!",
    ],
}

_PEP_TALKS = {
    "wholesome": [
        "Hey {name}, you're doing great! {goal} is totally achievable.",
        "{name}, remember that progress isn't always linear, but you're moving forward!",
        "You've got the determination to reach your goal of {goal}, {name}!",
        "Every small step towards {goal} counts, {name}. Keep it up!",
    ],
    "tough_love": [
        "Listen up {name}, {goal} isn't going to happen by itself!",
        "{name}, stop making excuses and start making progress on {goal}!",
        "You want to achieve {goal}? Then quit talking and start doing, {name}!",
        "Reality check, {name}: {goal} requires actual work, not just wishful thinking!",
    ],
    "funny": [
        "{name}, your goal of {goal} is calling... it wants to know if you're still friends.",
        "Hey {name}, {goal} just texted - it's wondering when you'll take it seriously!",
        "{name}, your future self is judging your current commitment to {goal}.",
        "Breaking news {name}: {goal} is still waiting for you to show up!",
    ],
}

_AFFIRMATIONS = [
    "You are 100% capable of finishing this assignment (eventually).",
    "Progress > perfection.",
    "You’re not behind — you’re just on your own timeline.",
    "Even one line of code counts as productivity!",
    "You’re basically the main character of this study session."
]

_CHALLENGES = [
    "Study 10 pages without checking your phone.",
    "Summarize the last topic in one sentence.",
    "Do a 5-minute rapid-fire recall session.",
    "Write a haiku about your subject.",
    "Quiz yourself out loud — bonus points if you sound confident."
]

# Functions
def _choose(lst, rnd):
    return lst[rnd.randrange(len(lst))]

def study_tip(topic: str = "math", mood: str = "chaotic", seed: int | None = None) -> str:
    """Return a humorous study tip."""
    rnd = random.Random(seed)
    tips = _TIPS.get(topic, _TIPS["math"])
    return _choose(tips, rnd)

def motivate(style: str = "sarcastic", seed: int | None = None) -> str:
    """Return a motivational or sarcastic message."""
    rnd = random.Random(seed)
    msgs = _MOTIVATIONS.get(style, _MOTIVATIONS["sarcastic"])
    return _choose(msgs, rnd)

def excuse(reason: str = "homework", seed: int | None = None) -> str:
    """Return a funny excuse for school mishaps."""
    rnd = random.Random(seed)
    excuses = _EXCUSES.get(reason, _EXCUSES["homework"])
    return _choose(excuses, rnd)

def study_plan(hours: int = 3, caffeine_level: str = "high", seed: int | None = None) -> list[str]:
    """Return a list of 'study plan' steps."""
    rnd = random.Random(seed)
    plan = []
    for i in range(min(hours, 5)):
        step = _choose(_STEPS, rnd)
        if caffeine_level == "high" and "coffee" not in step.lower():
            step = "Drink more coffee. " + step
        plan.append(f"Step {i+1}: {step}")
    return plan

def roast(topic: str = "cs", intensity: int = 5, seed: int | None = None) -> str:
    """Return a humorous roast about an academic topic."""
    rnd = random.Random(seed)
    roasts = _ROASTS.get(topic, _ROASTS["cs"])
    roast_msg = _choose(roasts, rnd)
    
    # Adjust intensity (1-10 scale)
    if intensity <= 3:
        roast_msg = "Gently speaking... " + roast_msg.lower()
    elif intensity >= 8:
        roast_msg = roast_msg.upper() + " 🔥"
    
    return roast_msg

def break_idea(minutes: int = 5, activity: str = "stretch", seed: int | None = None) -> str:
    """Return a break activity suggestion."""
    rnd = random.Random(seed)
    activities = _BREAK_ACTIVITIES.get(activity, _BREAK_ACTIVITIES["stretch"])
    idea = _choose(activities, rnd)
    
    if minutes <= 5:
        return f"Quick {minutes}-minute break: {idea}"
    else:
        return f"Extended {minutes}-minute break: {idea} Take your time!"

def pomodoro_schedule(sessions: int = 4, work_minutes: int = 25, break_minutes: int = 5, long_break: int = 15) -> list[str]:
    """Generate a Pomodoro timer schedule."""
    schedule = []
    
    for i in range(sessions):
        schedule.append(f"Session {i+1}: Work for {work_minutes} minutes")
        
        if (i + 1) % 4 == 0 and i < sessions - 1:
            schedule.append(f"Long break: {long_break} minutes")
        elif i < sessions - 1:
            schedule.append(f"Short break: {break_minutes} minutes")
    
    schedule.append("🎉 Pomodoro session complete! Great work!")
    return schedule

def study_playlist(mood: str = "focus", n: int = 3, seed: int | None = None) -> list[str]:
    """Generate a study playlist based on mood."""
    rnd = random.Random(seed)
    playlists = _PLAYLIST_MOODS.get(mood, _PLAYLIST_MOODS["focus"])
    
    # Return n random playlists (with potential repeats if n > available playlists)
    selected = []
    for _ in range(n):
        selected.append(_choose(playlists, rnd))
    
    return selected

def deadline_reminder(hours_left: int, tone: str = "funny") -> str:
    """Generate a deadline reminder message."""
    messages = _DEADLINE_MESSAGES.get(tone, _DEADLINE_MESSAGES["funny"])
    
    # Choose message based on urgency
    if hours_left <= 2:
        if tone in _DEADLINE_MESSAGES:
            base_msg = _DEADLINE_MESSAGES["panic"][0] if tone != "panic" else messages[0]
        else:
            base_msg = messages[0]
    else:
        rnd = random.Random()
        base_msg = _choose(messages, rnd)
    
    # Format the message with hours if it contains placeholder
    return base_msg.format(hours=hours_left) if "{hours}" in base_msg else base_msg

def pep_talk(name: str = "friend", goal: str = "study 2 hours", theme: str = "wholesome", seed: int | None = None) -> str:
    """Generate a personalized pep talk."""
    rnd = random.Random(seed)
    talks = _PEP_TALKS.get(theme, _PEP_TALKS["wholesome"])
    talk = _choose(talks, rnd)
    
    return talk.format(name=name, goal=goal)

def affirmation(seed: int | None = None) -> str:
    rnd = random.Random(seed)
    return _choose(_AFFIRMATIONS, rnd)


def challenge(seed: int | None = None) -> str:
    rnd = random.Random(seed)
    return _choose(_CHALLENGES, rnd)


def allocate_time(topics: Dict[str, int], total_minutes: int, min_chunk: int = 5) -> Dict[str, int]:
    """
    Allocate study minutes across topics by (non-negative) weight.

    Returns dict[topic -> minutes], sum == total_minutes, each minutes >= 0 and % min_chunk == 0.
    """
    if total_minutes < 0 or min_chunk <= 0:
        raise ValueError("total_minutes must be >= 0 and min_chunk > 0")
    if not topics:
        return {}

    weights = {k: max(0, int(v)) for k, v in topics.items()}
    total_w = sum(weights.values())

    if total_w == 0:
        avg = total_minutes / max(1, len(weights))
        raw = {k: avg for k in weights}
    else:
        raw = {k: (total_minutes * w / total_w) for k, w in weights.items()}

    alloc = {k: max(0, int(round(x / min_chunk) * min_chunk)) for k, x in raw.items()}

    diff = total_minutes - sum(alloc.values())
    if diff != 0:
        keys = sorted(weights, key=lambda k: weights[k], reverse=True)
        step = min_chunk if diff > 0 else -min_chunk
        i = 0
        while diff != 0 and keys:
            k = keys[i % len(keys)]
            if alloc[k] + step >= 0:
                alloc[k] += step
                diff -= step
            i += 1
            if i > 10000:
                break

    return alloc
