"""Romantic Risk Assessment — browser game logic.

The original game was a deeply nested input()/print() decision tree.
This refactor keeps the story outcomes and most question wording intact,
but exposes a small JSON API that JavaScript can call through Pyodide.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


def choice(label: str, value: str, next_node: str) -> dict[str, str]:
    return {"label": label, "value": value, "next": next_node}


NODES: dict[str, dict[str, Any]] = {
    "start": {
        "messages": [
            "So, you're experiencing the terribly embarrassing feeling of having a crush on somebody, and now you're faced with the dilemma of whether you should tell them...",
            "My condolences.",
            "First things first: Is your crush seeing someone?",
        ],
        "choices": [
            choice("Yes", "A", "seeing_type"),
            choice("No", "B", "how_know"),
            choice("I don't know", "C", "end_find_out"),
        ],
    },
    "seeing_type": {
        "messages": ["Define 'seeing'..."],
        "choices": [
            choice("They're casually dating somebody", "A", "same_or_multiple"),
            choice("They're in a relationship", "B", "end_dont_tell"),
            choice("They're casually hooking up with somebody", "C", "actually_casual"),
        ],
    },
    "actually_casual": {
        "messages": ["Is it actually casual?"],
        "choices": [
            choice("yes", "yes", "same_or_multiple"),
            choice("no", "no", "end_dont_tell"),
        ],
    },
    "same_or_multiple": {
        "messages": ["Same person, or multiple people?"],
        "choices": [
            choice("Same person", "same", "situationship_role"),
            choice("Multiple people", "multiple", "end_depends_what_you_want"),
        ],
    },
    "situationship_role": {
        "messages": [
            "So you're crushing on somebody who's in a situationship. What's their role in the situationship?"
        ],
        "choices": [
            choice(
                "They're the one who won't commit and is dragging the other person along",
                "A",
                "end_situationship_no",
            ),
            choice(
                "They're the one being dragged along by the other person who won't commit",
                "B",
                "end_situationship_yes",
            ),
        ],
    },
    "how_know": {
        "messages": ["How do you know your crush?"],
        "choices": [
            choice("Online", "A", "celebrity"),
            choice("Through in-person circumstances", "B", "in_person_context"),
        ],
    },
    "celebrity": {
        "messages": ["Are they a celebrity?"],
        "choices": [
            choice("yes", "yes", "end_celebrity"),
            choice("no", "no", "dating_app"),
        ],
    },
    "dating_app": {
        "messages": ["Did you meet this person on a dating app?"],
        "choices": [
            choice("yes", "yes", "end_dating_app"),
            choice("no", "no", "met_in_real_life"),
        ],
    },
    "met_in_real_life": {
        "messages": ["Have you ever met this person in real life?"],
        "choices": [
            choice("yes", "yes", "end_tell"),
            choice("no", "no", "end_online_unmet"),
        ],
    },
    "in_person_context": {
        "messages": ["Do you know your crush..."],
        "choices": [
            choice("Through friends", "A", "friends_or_met_through"),
            choice("Through school", "B", "see_often"),
            choice("Through work", "C", "fear_fired"),
            choice("A chance meeting in the wild", "D", "end_tell_exclaim"),
        ],
    },
    "friends_or_met_through": {
        "messages": ["Which one?"],
        "choices": [
            choice("You are friends with your crush", "A", "friend_type"),
            choice("You met your crush through friends", "B", "friend_connection"),
        ],
    },
    "friend_connection": {
        "messages": ["How do you know your crush?"],
        "choices": [
            choice("You and your crush have a mutual friend", "A", "friend_type"),
            choice("Your crush is related to your friend", "B", "friend_relative"),
        ],
    },
    "friend_type": {
        "messages": ["Are you and your crush..."],
        "choices": [
            choice("One-on-one friends", "A", "end_prepared"),
            choice("In a friend group together", "B", "group_seeing"),
        ],
    },
    "group_seeing": {
        "messages": ["Was your crush seeing somebody else in the friend group?"],
        "choices": [
            choice("yes", "yes", "group_seeing_type"),
            choice("no", "no", "someone_else_likes"),
        ],
    },
    "group_seeing_type": {
        "messages": ["Define 'seeing'"],
        "choices": [
            choice(
                "Your crush was casually hooking up with somebody else in the friend group",
                "A",
                "end_friend_group_dynamic",
            ),
            choice(
                "Your crush was dating somebody else in the friend group",
                "B",
                "seriousness",
            ),
        ],
    },
    "seriousness": {
        "messages": ["How serious was it? On a scale of 0-5"],
        "choices": [
            choice("0", "0", "end_low_seriousness"),
            choice("1", "1", "end_low_seriousness"),
            choice("2", "2", "end_low_seriousness"),
            choice("3", "3", "ex_duration"),
            choice("4", "4", "ex_duration"),
            choice("5", "5", "ex_duration"),
        ],
    },
    "ex_duration": {
        "messages": [
            "Is it f***ed up for you to ask out your friend's ex?",
            "What is the time in months that your friend and their ex dated?",
        ],
        "input": {
            "type": "number",
            "key": "ex_duration",
            "placeholder": "months",
            "min": 0,
            "step": 1,
            "button": "send",
        },
    },
    "friendship_level": {
        "messages": ["What is the friendship level between you and your friend on a scale of 1-10?"],
        "input": {
            "type": "number",
            "key": "friendship_level",
            "placeholder": "1–10",
            "min": 1,
            "max": 10,
            "step": 1,
            "button": "send",
        },
    },
    "months_since_breakup": {
        "messages": [
            "What is the time in months between the break up and you hypothetically telling your crush you like them?"
        ],
        "input": {
            "type": "number",
            "key": "months_since_breakup",
            "placeholder": "months",
            "min": 0,
            "step": 1,
            "button": "send",
        },
    },
    "still_like_each_other": {
        "messages": [
            "MIGHT be okay, proceed to the next step with extreme caution.",
            "Do your friend and your crush still like each other?",
        ],
        "choices": [
            choice("Yes / I don't know", "A", "worth_group_risk"),
            choice("No", "B", "end_friend_group_dynamic"),
        ],
    },
    "worth_group_risk": {
        "messages": [
            "Does the potential of getting together with your crush and/or potentially breaking up outweight the risk of potentially changing the dynamic of the friend group forever?"
        ],
        "choices": [
            choice("yes", "yes", "end_tell"),
            choice("no", "no", "end_dont_tell"),
        ],
    },
    "someone_else_likes": {
        "messages": ["Does anybody else in your friend group like your crush?"],
        "choices": [
            choice("yes", "yes", "chance_likes_you"),
            choice("no", "no", "worth_group_risk"),
        ],
    },
    "chance_likes_you": {
        "messages": ["Is there any change of your crush liking YOU back?"],
        "choices": [
            choice("yes", "yes", "worth_group_risk"),
            choice("no", "no", "end_wouldnt"),
        ],
    },
    "friend_relative": {
        "messages": ["Are they your friend's sibling?"],
        "choices": [
            choice("yes", "yes", "sibling_reason"),
            choice("no", "no", "friend_parent"),
        ],
    },
    "sibling_reason": {
        "messages": ["Do you think you like them just because they're your friend's sibling?"],
        "choices": [
            choice("yes", "yes", "end_dont_tell_no_period"),
            choice("no", "no", "sibling_risk"),
        ],
    },
    "sibling_risk": {
        "messages": [
            "Does the prospect of being with your crush outweight the fact that you may ruin/make awkward (at least for a time) your relationship wiht your friend?"
        ],
        "choices": [
            choice("yes", "yes", "end_sibling_chaos"),
            choice("no", "no", "end_dont_tell_no_period"),
        ],
    },
    "friend_parent": {
        "messages": ["Are they your friend's parent?"],
        "choices": [
            choice("yes", "yes", "end_too_much_drama"),
            choice("no", "no", "end_too_much_drama"),
        ],
    },
    "see_often": {
        "messages": ["Do you see your crush often?"],
        "choices": [
            choice("yes", "yes", "actually_like"),
            choice("no", "no", "end_tell"),
        ],
    },
    "actually_like": {
        "messages": [
            "Do you actually like them, or do you only have a crush on them because you're in close proximity to them?"
        ],
        "choices": [
            choice("Yes — I actually like them", "yes", "end_close_proximity_yes"),
            choice("No — it's probably proximity", "no", "end_close_proximity_no"),
        ],
    },
    "fear_fired": {
        "messages": ["Do you fear being fired?"],
        "choices": [
            choice("yes", "yes", "end_hr_rules"),
            choice("no", "no", "same_work_level"),
        ],
    },
    "same_work_level": {
        "messages": ["Is your crush in the same level as you in the work hierarchy?"],
        "choices": [
            choice("yes", "yes", "actually_like"),
            choice("no", "no", "work_superior"),
        ],
    },
    "work_superior": {
        "messages": ["Who's the superior in the hierarchy?"],
        "choices": [
            choice("Me", "Me", "power_play"),
            choice("My crush", "crush", "authority_figures"),
        ],
    },
    "power_play": {
        "messages": [
            "Is there any chance that your crush likes you or is this some sick power play that will make your crush incredibly uncomfortable for the rest of their limited time working there before they inevitably resign?"
        ],
        "choices": [
            choice("yes", "yes", "end_hr_hears"),
            choice("no", "no", "end_dont_tell"),
        ],
    },
    "authority_figures": {
        "messages": ["Do you really like them or do you just have a weird thing for authority figures?"],
        "choices": [
            choice("I really like them", "like", "end_promotion"),
            choice("Maybe I have a thing for authority figures", "authority", "end_promotion"),
        ],
    },

    # Endings
    "end_situationship_no": {
        "messages": ["Don't tell them, unless you also want to be in a situationship with this person."],
        "ending": True,
    },
    "end_situationship_yes": {
        "messages": [
            "You should tell them, but it's likely that they'll be too blinded by the other person to reciprocate your feelings."
        ],
        "ending": True,
    },
    "end_depends_what_you_want": {
        "messages": ["You can tell them, but it depends what you want out of this."],
        "ending": True,
    },
    "end_dont_tell": {"messages": ["Don't tell them."], "ending": True},
    "end_find_out": {"messages": ["Find out and come back later."], "ending": True},
    "end_celebrity": {
        "messages": ["You can tell them, but they're never going to know about it."],
        "ending": True,
    },
    "end_dating_app": {
        "messages": [
            "Yeah you should tell them but I assume they already know you like them (assuming you matched)."
        ],
        "ending": True,
    },
    "end_tell": {"messages": ["Tell them."], "ending": True},
    "end_tell_exclaim": {"messages": ["Tell them!"], "ending": True},
    "end_online_unmet": {
        "messages": ["I mean, you CAN tell them, but there's a chance you won't be attracted to them in real life."],
        "ending": True,
    },
    "end_prepared": {
        "messages": ["You should tell them, but be mentally prepared for the answer."],
        "ending": True,
    },
    "end_friend_group_dynamic": {
        "messages": ["Yeaaah, do it. Be aware that it may change the dynamic of your friend group forever."],
        "ending": True,
    },
    "end_low_seriousness": {
        "messages": [
            "Sure, tell them, as long as you're okay with the fact that the outcome of this may change the dynamic of your friend group forever."
        ],
        "ending": True,
    },
    "end_too_soon": {"messages": ["Don't even think about it."], "ending": True},
    "end_danger_zone": {"messages": ["You're in the danger zone, wait it out."], "ending": True},
    "end_wouldnt": {"messages": ["I meaannnn, I wouldn't."], "ending": True},
    "end_dont_tell_no_period": {"messages": ["Don't tell them"], "ending": True},
    "end_sibling_chaos": {
        "messages": ["Tell them, but it will be a f***ing s*** show."],
        "ending": True,
    },
    "end_too_much_drama": {
        "messages": ["This is too much drama for me I'm not getting involved.", "Good luck, babe."],
        "ending": True,
    },
    "end_close_proximity_yes": {
        "messages": [
            "Tell them; it'll either be the best relationship of your life or it will make things incredibly awkward and uncomfortable everyday when you're forced to see them."
        ],
        "ending": True,
    },
    "end_close_proximity_no": {
        "messages": ["Don't tell them, it's only going to ruin the prurpose they serve in your life right now."],
        "ending": True,
    },
    "end_hr_rules": {
        "messages": ["Don't tell them. It's probably against HR rules."],
        "ending": True,
    },
    "end_hr_hears": {"messages": ["HR will hear about this."], "ending": True},
    "end_promotion": {
        "messages": ["If you do it there is a 1% chance you'll get a promotion and a 99% chance you'll be immediately fired."],
        "ending": True,
    },
}


@dataclass
class GameEngine:
    current: str = "start"
    state: dict[str, Any] = field(default_factory=dict)

    def restart(self) -> dict[str, Any]:
        self.current = "start"
        self.state.clear()
        return self.payload()

    def payload(self, *, error: str | None = None) -> dict[str, Any]:
        node = NODES[self.current]
        return {
            "node": self.current,
            "messages": node.get("messages", []),
            "choices": node.get("choices", []),
            "input": node.get("input"),
            "ended": bool(node.get("ending")),
            "error": error,
        }

    def choose(self, value: str) -> dict[str, Any]:
        node = NODES[self.current]
        options = node.get("choices", [])
        selected = next((item for item in options if item["value"] == value), None)

        if selected is None:
            return self.payload(error="That choice isn't available right now.")

        self.current = selected["next"]
        return self.payload()

    def submit(self, raw_value: str) -> dict[str, Any]:
        node = NODES[self.current]
        input_config = node.get("input")
        if not input_config:
            return self.payload(error="This part of the game isn't expecting typed input.")

        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            return self.payload(error="Send me a whole number.")

        minimum = input_config.get("min")
        maximum = input_config.get("max")
        if minimum is not None and value < minimum:
            return self.payload(error=f"Use a number of at least {minimum}.")
        if maximum is not None and value > maximum:
            return self.payload(error=f"Use a number no higher than {maximum}.")

        key = input_config["key"]
        self.state[key] = value

        if self.current == "ex_duration":
            self.current = "friendship_level"
        elif self.current == "friendship_level":
            self.current = "months_since_breakup"
        elif self.current == "months_since_breakup":
            if value < 2:
                self.current = "end_too_soon"
            else:
                months_dated = self.state["ex_duration"]
                friendship_level = self.state["friendship_level"]
                appropriateness = (months_dated * friendship_level) / value
                self.state["appropriateness"] = appropriateness
                self.current = (
                    "end_danger_zone"
                    if appropriateness > value
                    else "still_like_each_other"
                )

        return self.payload()


engine = GameEngine()


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def start_game() -> str:
    return _json(engine.restart())


def choose(value: str) -> str:
    return _json(engine.choose(str(value)))


def submit_value(value: str) -> str:
    return _json(engine.submit(str(value)))


def restart_game() -> str:
    return _json(engine.restart())
