import argparse, json
from . import (
    study_tip, motivate, excuse, study_plan,
    roast, break_idea, pomodoro_schedule, study_playlist, deadline_reminder, pep_talk, affirmation, challenge,
    allocate_time
)
from argparse import RawTextHelpFormatter


def main():
    epilog = (
        "Examples:\n"
        "  studybuddy tip --topic algorithms --seed 3\n"
        "  studybuddy motivate --style genuine --seed 1\n"
        "  studybuddy excuse --reason \"missed deadline\" --seed 2\n"
        "  studybuddy plan --hours 3 --caffeine high --seed 1\n"
        "  studybuddy roast --topic cs --intensity 5 --seed 7\n"
        "  studybuddy break --minutes 5 --activity stretch --seed 0\n"
        "  studybuddy pomodoro --sessions 2 --work 25 --break 5 --long 15\n"
        "  studybuddy playlist --mood focus --n 4 --seed 11\n"
        "  studybuddy deadline --hours_left 10 --tone funny\n"
        "  studybuddy pep --name Gavin --goal \"study 2 hours\" --theme wholesome --seed 9\n"
        "  studybuddy affirm --seed 4\n"
        "  studybuddy challenge --seed 6\n"
        "  studybuddy allocate --minutes 120 --min-chunk 10 --topic DSA:5 --topic OS:3 --topic Math:2\n"
        "\nTip: run `studybuddy <subcommand> -h` for subcommand-specific help.\n"
    )

    p = argparse.ArgumentParser(
        prog="studybuddy",
        description="StudyBuddy CLI",
        epilog=epilog,
        formatter_class=RawTextHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd")

    s1 = sub.add_parser(
        "tip",
        help="Get a study tip",
        description="Return a witty/constructive study tip.\n\nExample:\n  studybuddy tip --topic algorithms --seed 3",
        formatter_class=RawTextHelpFormatter,
    )
    # s1 = sub.add_parser("tip");
    s1.add_argument("--topic", default="math", help="Topic, e.g., algorithms/databases (default: math)")
    s1.add_argument("--seed", type=int, help="Random seed for reproducibility")

    s2 = sub.add_parser(
        "motivate",
        help="Get a motivation line",
        description="Different styles: genuine / sarcastic / toughlove.\n\nExample:\n  studybuddy motivate --style genuine --seed 1",
        formatter_class=RawTextHelpFormatter,
    )
    # s2 = sub.add_parser("motivate");
    s2.add_argument("--style", default="sarcastic", help="Style (default: sarcastic)")
    s2.add_argument("--seed", type=int, help="Random seed")

    s3 = sub.add_parser(
        "excuse",
        help="Generate a cheeky excuse",
        description="Generate a fun excuse for a reason.\n\nExample:\n  studybuddy excuse --reason \"missed deadline\" --seed 2",
        formatter_class=RawTextHelpFormatter,
    )
    # s3 = sub.add_parser("excuse");
    s3.add_argument("--reason", default="homework", help="Reason/context (default: homework)")
    s3.add_argument("--seed", type=int, help="Random seed")

    s4 = sub.add_parser(
        "plan",
        help="Create a study plan",
        description="Plan steps for a number of hours.\n\nExample:\n  studybuddy plan --hours 3 --caffeine high --seed 1",
        formatter_class=RawTextHelpFormatter,
    )
    # s4 = sub.add_parser("plan");
    s4.add_argument("--hours", type=int, default=3, help="Study hours (default: 3)")
    s4.add_argument("--caffeine", default="high", help="low/medium/high (default: high)")
    s4.add_argument("--seed", type=int, help="Random seed")

    s5 = sub.add_parser(
        "roast",
        help="Get a playful roast",
        description="Playful roast (for fun only!).\n\nExample:\n  studybuddy roast --topic cs --intensity 5 --seed 7",
        formatter_class=RawTextHelpFormatter,
    )
    # s5 = sub.add_parser("roast");
    s5.add_argument("--topic", default="cs", help="Topic to roast (default: cs)")
    s5.add_argument("--intensity", type=int, default=5, help="1-10 (default: 5)")
    s5.add_argument("--seed", type=int, help="Random seed")

    s6 = sub.add_parser(
        "break",
        help="Break-time idea",
        description="Suggest a tiny break activity.\n\nExample:\n  studybuddy break --minutes 5 --activity stretch --seed 0",
        formatter_class=RawTextHelpFormatter,
    )
    # s6 = sub.add_parser("break");
    s6.add_argument("--minutes", type=int, default=5, help="Break minutes (default: 5)")
    s6.add_argument("--activity", default="stretch", help="Activity name (default: stretch)")
    s6.add_argument("--seed", type=int, help="Random seed")

    s7 = sub.add_parser(
        "pomodoro",
        help="Generate a pomodoro schedule",
        description="Pomodoro cycles with custom durations.\n\nExample:\n  studybuddy pomodoro --sessions 2 --work 25 --break 5 --long 15",
        formatter_class=RawTextHelpFormatter,
    )
    # s7 = sub.add_parser("pomodoro");
    s7.add_argument("--sessions", type=int, default=4, help="Number of sessions (default: 4)")
    s7.add_argument("--work", type=int, default=25, help="Work minutes per session (default: 25)")
    s7.add_argument("--break", dest="brk", type=int, default=5, help="Short break minutes (default: 5)")
    s7.add_argument("--long", type=int, default=15, help="Long break minutes (default: 15)")

    s8 = sub.add_parser(
        "playlist",
        help="Suggest a study playlist",
        description="Return a small themed playlist.\n\nExample:\n  studybuddy playlist --mood focus --n 4 --seed 11",
        formatter_class=RawTextHelpFormatter,
    )
    # s8 = sub.add_parser("playlist");
    s8.add_argument("--mood", default="focus", help="Mood/genre (default: focus)")
    s8.add_argument("--n", type=int, default=3, help="Number of tracks (default: 3)")
    s8.add_argument("--seed", type=int, help="Random seed")

    s9 = sub.add_parser(
        "deadline",
        help="Deadline reminder",
        description="Generate a fun deadline reminder line.\n\nExample:\n  studybuddy deadline --hours_left 10 --tone funny",
        formatter_class=RawTextHelpFormatter,
    )
    # s9 = sub.add_parser("deadline");
    s9.add_argument("--hours_left", type=int, required=True, help="Hours left to deadline (required)")
    s9.add_argument("--tone", default="funny", help="Tone (default: funny)")

    s10 = sub.add_parser(
        "pep",
        help="Get a short pep talk",
        description="Short pep talk with name/goal/theme.\n\nExample:\n  studybuddy pep --name Gavin --goal \"study 2 hours\" --theme wholesome --seed 9",
        formatter_class=RawTextHelpFormatter,
    )
    # s10 = sub.add_parser("pep");
    s10.add_argument("--name", default="friend", help="Name (default: friend)")
    s10.add_argument("--goal", default="study 2 hours", help="Goal text (default: study 2 hours)")
    s10.add_argument("--theme", default="wholesome", help="Theme (default: wholesome)")
    s10.add_argument("--seed", type=int, help="Random seed")

    s11 = sub.add_parser(
        "affirm",
        help="Get an affirmation",
        description="Short affirmation.\n\nExample:\n  studybuddy affirm --seed 4",
        formatter_class=RawTextHelpFormatter,
    )
    # s11 = sub.add_parser("affirm")
    s11.add_argument("--seed", type=int, help="Random seed")

    s12 = sub.add_parser(
        "challenge",
        help="Get a challenge",
        description="Small challenge.\n\nExample:\n  studybuddy challenge --seed 6",
        formatter_class=RawTextHelpFormatter,
    )
    # s12 = sub.add_parser("challenge")
    s12.add_argument("--seed", type=int, help="Random seed")

    s13 = sub.add_parser(
        "allocate",
        help="Allocate minutes across topics by weight",
        description=(
            "Allocate study minutes across topics by weight; rounds to min-chunk and preserves total.\n\n"
            "Multiple topics via repeated --topic flags in the form NAME:WEIGHT.\n"
            "Example:\n  studybuddy allocate --minutes 120 --min-chunk 10 --topic DSA:5 --topic OS:3 --topic Math:2"
        ),
        formatter_class=RawTextHelpFormatter,
    )
    s13.add_argument("--minutes", type=int, required=True, help="Total minutes to distribute")
    s13.add_argument("--min-chunk", type=int, default=5, dest="min_chunk",
                     help="Round each topic to multiple of this (default: 5)")
    s13.add_argument("--topic", action="append", default=[], metavar="NAME:WEIGHT",
                     help="Repeatable. Example: --topic DSA:5 --topic OS:3")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return

    if args.cmd == "tip": print(study_tip(args.topic, "chaotic", args.seed))
    elif args.cmd == "motivate": print(motivate(args.style, args.seed))
    elif args.cmd == "excuse": print(excuse(args.reason, args.seed))
    elif args.cmd == "plan": print("\n".join(study_plan(args.hours, args.caffeine, args.seed)))
    elif args.cmd == "roast": print(roast(args.topic, args.intensity, args.seed))
    elif args.cmd == "break": print(break_idea(args.minutes, args.activity, args.seed))
    elif args.cmd == "pomodoro": print("\n".join(pomodoro_schedule(args.sessions, args.work, args.brk, args.long)))
    elif args.cmd == "playlist": print(json.dumps(study_playlist(args.mood, args.n, args.seed)))
    elif args.cmd == "deadline": print(deadline_reminder(args.hours_left, args.tone))
    elif args.cmd == "pep": print(pep_talk(args.name, args.goal, args.theme, args.seed))
    elif args.cmd == "affirm":
        print(affirmation(args.seed))
    elif args.cmd == "challenge":
        print(challenge(args.seed))
    elif args.cmd == "allocate":
        topics = {}
        for item in args.topic:
            try:
                name, w = item.split(":", 1)
                topics[name.strip()] = int(w)
            except Exception:
                print(f"Invalid --topic '{item}'. Expected NAME:WEIGHT")
                return
        print(allocate_time(topics, args.minutes, args.min_chunk))


if __name__ == "__main__":
    main()

