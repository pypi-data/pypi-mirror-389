import argparse, json
from . import (
    study_tip, motivate, excuse, study_plan,
    roast, break_idea, pomodoro_schedule, study_playlist, deadline_reminder, pep_talk, affirmation, challenge
)

def main():
    p = argparse.ArgumentParser(prog="studybuddy", description="StudyBuddy CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("tip"); s1.add_argument("--topic", default="math"); s1.add_argument("--seed", type=int)
    s2 = sub.add_parser("motivate"); s2.add_argument("--style", default="sarcastic"); s2.add_argument("--seed", type=int)
    s3 = sub.add_parser("excuse"); s3.add_argument("--reason", default="homework"); s3.add_argument("--seed", type=int)
    s4 = sub.add_parser("plan"); s4.add_argument("--hours", type=int, default=3); s4.add_argument("--caffeine", default="high"); s4.add_argument("--seed", type=int)
    s5 = sub.add_parser("roast"); s5.add_argument("--topic", default="cs"); s5.add_argument("--intensity", type=int, default=5); s5.add_argument("--seed", type=int)
    s6 = sub.add_parser("break"); s6.add_argument("--minutes", type=int, default=5); s6.add_argument("--activity", default="stretch"); s6.add_argument("--seed", type=int)
    s7 = sub.add_parser("pomodoro"); s7.add_argument("--sessions", type=int, default=4); s7.add_argument("--work", type=int, default=25); s7.add_argument("--break", dest="brk", type=int, default=5); s7.add_argument("--long", type=int, default=15)
    s8 = sub.add_parser("playlist"); s8.add_argument("--mood", default="focus"); s8.add_argument("--n", type=int, default=3); s8.add_argument("--seed", type=int)
    s9 = sub.add_parser("deadline"); s9.add_argument("--hours_left", type=int, required=True); s9.add_argument("--tone", default="funny")
    s10 = sub.add_parser("pep"); s10.add_argument("--name", default="friend"); s10.add_argument("--goal", default="study 2 hours"); s10.add_argument("--theme", default="wholesome"); s10.add_argument("--seed", type=int)

    s11 = sub.add_parser("affirm")
    s11.add_argument("--seed", type=int)

    s12 = sub.add_parser("challenge")
    s12.add_argument("--seed", type=int)

    args = p.parse_args()
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

if __name__ == "__main__":
    main()

