# Chapter 4, Steps 2 to 5: the Robot Bridge (the robot's BIG brain)
#
#   phone -> cloud -> THIS PROGRAM -> USB cable -> Arduino -> screen, buzzer, voice
#   phone <- cloud <- THIS PROGRAM <- USB cable <- Arduino    ("EVENT VISITOR 3")
#
# Start it:   caffeinate -i python robot_bridge.py
# With faces: caffeinate -i python robot_bridge.py --faces
# No robot?   python robot_bridge.py --fake-arduino
# Stop it:    Control + C   (or Q in the camera window)
#
# Helpers each do one job and drop what they hear into ONE inbox:
#   the USB link, the cloud listener, the alarm clock and (with --faces) the camera.
# The brain takes things out of the inbox one at a time and decides what to do.

import argparse
import queue
import threading
import time
from datetime import datetime

from bridge import cloud, protocol, rules
from bridge.arduino_link import ArduinoLink, FakeArduino
from bridge.scheduler import Scheduler
from bridge.settings import load_config
from bridge.speech import SpeechQueue

HEARTBEAT_SECONDS = 20      # how often we tell the Arduino "the Mac is still here"


def stamp_log(text):
    print(datetime.now().strftime("%H:%M:%S") + " " + text, flush=True)


def how_long(seconds):
    """ 3725 -> "1 h 2 min" """
    minutes = int(seconds) // 60
    return f"{minutes // 60} h {minutes % 60} min" if minutes >= 60 else f"{minutes} min"


class Brain:
    def __init__(self, config, link, speech, notifier=None, faces_on=False,
                 clock=time.monotonic, now=datetime.now, log=stamp_log):
        self.config = config
        self.link = link                  # the USB link to the Arduino
        self.speech = speech              # the voice
        self.notifier = notifier          # texts the phone (None = phone features are off)
        self.faces_on = faces_on
        self.clock = clock                # a stopwatch (seconds)
        self.now = now                    # the wall clock (date and time)
        self.log = log

        self.inbox = queue.Queue()        # everything that happens lands here
        self.started = clock()
        self.visitors = 0
        self.last_heartbeat = None

        face_rules = config.get("faces", {})
        self.phone_line = rules.WaitingLine(config.get("seconds_between_messages", 3),
                                            config.get("messages_that_can_wait", 5), clock)
        self.visitor_texts = rules.Cooldown(config.get("visitor_text_cooldown_seconds", 60), clock)
        self.person_greetings = rules.Cooldown(face_rules.get("person_cooldown_seconds", 120), clock)
        self.friend_greetings = rules.Cooldown(face_rules.get("friend_cooldown_seconds", 60), clock)

    # ---- the helpers call these (from their own threads) ----

    def from_arduino(self, message):
        self.inbox.put(("arduino", message))

    def from_phone(self, text):
        self.inbox.put(("phone", text))

    def from_clock(self, item):
        self.inbox.put(("clock", item))

    def from_camera(self, person):
        self.inbox.put(("face", person))

    # ---- the brain's loop: call step() again and again ----

    def step(self):
        while True:
            try:
                kind, thing = self.inbox.get_nowait()
            except queue.Empty:
                break
            if kind == "arduino":
                self.on_arduino(thing)
            elif kind == "phone":
                self.on_phone(thing)
            elif kind == "clock":
                self.on_alarm(thing)
            elif kind == "face":
                self.on_face(thing)

        message = self.phone_line.next()          # at most one phone message every 3 seconds
        if message is not None:
            self.do_phone_message(message)

        if self.last_heartbeat is None or self.clock() - self.last_heartbeat >= HEARTBEAT_SECONDS:
            self.last_heartbeat = self.clock()
            self.link.send(protocol.ping())

    def quiet(self):
        return rules.quiet_now(self.config, self.now())

    def show_and_say(self, text, speak=True, then=None):
        """Put text on the screen and say it, starting at the same moment."""
        def update_screen():
            self.link.send(protocol.show_wrapped(text))
            if then:
                self.link.send(then)
        self.speech.say(text if speak else "", first=update_screen)

    def text_phone(self, message):
        if self.notifier:
            self.notifier.send(self.config.get("robot_name", "Robot"), message)

    # ---- news from the Arduino ----

    def on_arduino(self, message):
        kind = message["kind"]
        if kind == "READY":
            self.log("🤖 Robot: I'm awake!")
        elif kind == "VISITOR":
            self.visitors = message["count"]
            self.log(f"🤖 Robot: visitor #{self.visitors}")
            self.greet_visitor()
        elif kind == "LEFT":
            self.log("🤖 Robot: they walked away")
        elif kind == "ERR":
            self.log(f"🤖 Robot didn't like a note: {message['reason']}")
        elif kind == "JUNK":
            self.log(f"🤖 Robot said something odd: {message['text']}")
        # PONG and OK answers are normal, so we stay quiet about them

    def greet_visitor(self):
        if not self.faces_on:                     # with --faces, the camera does the greeting
            hello = self.config.get("visitor_greeting", "Hello, human!")
            line = protocol.show(hello, f"Visitor #{self.visitors}")
            words = f"{hello} You are visitor number {self.visitors}."
            self.speech.say("" if self.quiet() else words, first=lambda: self.link.send(line))
        if not self.notifier:
            return
        if self.visitor_texts.ready():
            self.text_phone(f"🤖 Visitor #{self.visitors} at the door")
        else:
            self.log("🔕 Not texting again so soon (cooldown)")

    # ---- messages from the phone ----

    def on_phone(self, text):
        text = text.strip()
        if not text:
            return
        if len(text) > protocol.MAX_SPOKEN:
            self.log("✂️  That message was long, so I cut it to 100 letters")
            text = text[:protocol.MAX_SPOKEN]
        if self.phone_line.add(text):
            self.log(f"📱 Phone said: {text}")
        else:
            self.log(f"🚫 Too many messages at once! Dropped: {text}")

    def do_phone_message(self, text):
        if text.startswith("!"):
            self.do_phone_command(text[1:].lower().split())
        elif self.quiet():
            self.log("🤫 Quiet hours: showing it, not saying it")
            self.show_and_say(text, speak=False)
        else:
            self.show_and_say(text)

    def do_phone_command(self, words):
        try:
            if words == ["beep"]:
                self.link.send(protocol.beep())
            elif len(words) == 2 and words[0] == "tune":
                self.link.send(protocol.tune(words[1]))
            elif len(words) == 2 and words[0] == "led":
                self.link.send(protocol.led(words[1]))
            elif words == ["status"]:
                status = f"Awake for {how_long(self.clock() - self.started)}. Visitors: {self.visitors}."
                self.log("📊 " + status)
                self.text_phone("📊 " + status)
            else:
                self.log("❓ I don't know that command: !" + " ".join(words))
        except ValueError as problem:
            self.log(f"❓ {problem}")

    # ---- the alarm clock ----

    def on_alarm(self, item):
        self.log(f"⏰ Alarm: {item['say']}")
        tune = protocol.tune(item["tune"]) if item["tune"] in protocol.TUNES else None
        self.show_and_say(item["say"], then=tune)   # alarms are NOT stopped by quiet hours

    # ---- faces (Step 5) ----

    def on_face(self, person):
        """person is a dictionary from people.json, or None for "friend"."""
        if person is None:
            if not self.friend_greetings.ready():
                return
            self.log("🧑 Hello, friend! (not sure who that is)")
            line, tune, words = protocol.show("Hello, friend!", "Nice to see you"), protocol.tune("HELLO"), "Hello, friend!"
        else:
            if not self.person_greetings.ready(person["name"]):
                return
            self.log(f"🧑 I see {person['name']}!")
            line = protocol.show(f"Hi {person['name']}!", person.get("catchphrase", ""))
            try:
                tune = protocol.notes(person.get("tune") or [523, 659, 784, 1047])
            except ValueError:
                tune = protocol.tune("HELLO")
            words = f"Hi {person.get('say_as') or person['name']}! {person.get('catchphrase', '')}"
            # PRIVACY: the name only leaves the house if notify_names is true in config.json
            who = person["name"] if self.config.get("faces", {}).get("notify_names") else "Someone"
            self.text_phone(f"🏠 {who} is home")

        def update_screen():
            self.link.send(line)
            self.link.send(tune)
        self.speech.say("" if self.quiet() else words, first=update_screen)


# ---------- the camera loop (must run on the main thread on a Mac) ----------

def watch_faces(brain, config, keep_going):
    import cv2
    from bridge import faces

    face_rules = config.get("faces", {})
    details, samples = faces.load_people()
    if not details:
        stamp_log("🧑 Nobody is enrolled yet, so everyone is a friend. Run enroll_face.py first.")
    engine = faces.FaceEngine()
    camera = faces.open_camera(face_rules.get("camera", 0))
    doorman = faces.Doorman(face_rules.get("frames_needed", 3), face_rules.get("frames_window", 5))
    stamp_log("📷 Camera on. Click the camera window and press Q to quit.")

    while keep_going():
        ok, frame = camera.read()
        if not ok:
            stamp_log("📷 Can't read the camera. See 'Camera won't open' in Troubleshooting.")
            break
        frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
        found = engine.find_faces(frame)
        answer = None
        if found:
            numbers = engine.embedding(frame, found[0])  # the closest face
            scores = faces.all_scores(numbers, samples, engine.compare)
            answer = faces.decide(scores, face_rules.get("sure_enough", faces.SURE_ENOUGH),
                                  face_rules.get("beat_second_by", faces.BEAT_SECOND_BY))
            x, y, w, h = faces.box(found[0])
            label = details[answer]["name"] if answer in details else "friend?"
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
            cv2.putText(frame, label, (x, y - 12), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        winner = doorman.see(answer)                     # the same answer in 3 of the last 5 frames
        if winner is not None:
            brain.from_camera(details.get(winner))       # None means "friend"

        brain.step()
        cv2.imshow("Talking Robot - press Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


# ---------- start everything ----------

def main():
    parser = argparse.ArgumentParser(description="The Talking Robot's big brain.")
    parser.add_argument("--faces", action="store_true", help="turn on the camera and greet people by name")
    parser.add_argument("--fake-arduino", action="store_true", help="use a pretend Arduino (no robot needed)")
    parser.add_argument("--fake-visitor-every", type=int, default=20, metavar="SECONDS",
                        help="with --fake-arduino: a pretend visitor this often (0 = never)")
    args = parser.parse_args()

    config = load_config()
    stopping = threading.Event()
    speech = SpeechQueue(config.get("voice", ""), config.get("speech_rate", 0), log=stamp_log)

    # The cloud needs the two secret topics that setup_cloud.py makes.
    notifier = None
    cloud_on = (cloud.is_real_topic(config.get("to_robot_topic"))
                and cloud.is_real_topic(config.get("from_robot_topic")))
    if cloud_on:
        notifier = cloud.PhoneNotifier(config["ntfy_server"], config["from_robot_topic"], log=stamp_log)
    else:
        stamp_log("☁️  No secret topics yet, so phone features are off. A parent runs: python setup_cloud.py")

    fake = FakeArduino(args.fake_visitor_every) if args.fake_arduino else None
    link = ArduinoLink(fake=fake, log=stamp_log)
    brain = Brain(config, link, speech, notifier, faces_on=args.faces)
    link.on_message = brain.from_arduino
    link.start()

    if cloud_on:
        listener = cloud.PhoneListener(config["ntfy_server"], config["to_robot_topic"],
                                       brain.from_phone, log=stamp_log)
        threading.Thread(target=listener.run, daemon=True).start()

    scheduler = Scheduler(config.get("schedule"), log=stamp_log)
    threading.Thread(target=scheduler.run, args=(stopping, brain.from_clock), daemon=True).start()
    stamp_log(f"⏰ {len(scheduler.items)} alarms set")
    stamp_log("🧠 Bridge is running. Press Control + C to stop.")

    try:
        if args.faces:
            watch_faces(brain, config, lambda: not stopping.is_set())
        else:
            while True:
                brain.step()
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        stamp_log("👋 Shutting down...")
        stopping.set()
        link.send(protocol.idle())
        time.sleep(0.3)                  # give the last note time to leave
        link.stop()
        speech.stop()


if __name__ == "__main__":
    main()
