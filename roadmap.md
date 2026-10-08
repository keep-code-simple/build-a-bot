# 🗺️ Build-a-Bot Roadmap

Where the series is, and what's next. One chapter at a time, fun first, and no rushing the risky parts.

## The chapters

| # | Gadget | New idea | Spec | Built page | Status |
|---|---|---|---|---|---|
| 1 | 🤖 Door Greeter Bot | Input → brain → output | (in the page) | `door-greeter-build-guide.html` | ✅ Built and working |
| 2 | 🔐 Secret Code Bot | A remote as an input | (in the page) | `chapter-2-secret-code-bot.html` | ✅ Built and working |
| 3 | 👀 Robot Eyes | AI vision as an input (faces, fingers, Rock Paper Scissors) | `chapter-3-ai-vision.md` + `chapter-3-code/` | `chapter-3-robot-eyes.html` | Page ready, not built on hardware yet |
| 4 | 🗣️ The Talking Robot | Speech, phone ↔ robot round trip, schedules, greeting by name | `chapter-4-talking-robot.md` + `chapter-4-code/` | `chapter-4-talking-robot.html` | Page and code ready, not built on hardware yet |
| 5 | 🚪 The Auto Door | Moving things safely in the real world | this file, below | not yet | **Parked on purpose** |
| 6 | 🦖 Dino Bot | A robot that uses a computer like a person; beating latency | `chapter-6-dino-bot.md` + `chapter-6-code/` | `chapter-6-dino-bot.html` | Page and code ready, not built on hardware yet |
| 7 | 📦 The Robot Box | A robot with its own body; apps as folders, so the same box becomes new gadgets | `chapter-7-robot-box_v2.md` + `robot-box/` (app ideas: `robot-box-ideas.md`) | `chapter-7-robot-box.html` | Page and code ready and tested on the Mac; not built on a Raspberry Pi yet |
| Bonus | 🔬 Inside the Robot | How boards, chips and silicon work | `inside-the-robot.md` | `inside-the-robot.html` | ✅ Built |
| Bonus | 📱 The Phone Robot | A web page is a program too: the AI runs in the phone's browser | `phone-robot.md` + `phone-robot/` | `phone-robot.html` | Page and app ready and tested in a Mac browser; not tried on an iPhone yet |

`chapter-2-remote-control.md` (Guard Mode) is an earlier draft of Chapter 2. Its remote piano and greeter modes could become a Chapter 2 bonus later.

Order matters: Chapter 4 needs Chapter 3's Python setup, and its name-greeting finale reuses Chapter 3's camera skills. Chapter 7 moves Chapter 3's Rock Paper Scissors onto a Raspberry Pi.

`chapter-7-robot-box.md` is the first draft of Chapter 7; `chapter-7-robot-box_v2.md` is the one that was built.

---

## Chapter 5: The Auto Door (parked)

**The real problem:** the door from the garage into the kitchen swings shut by itself. The kids keep asking for it to stay open while they carry things in.

**Read this before anything else:** that door closes itself **on purpose**. In much of the US, the model building code (IRC R302.5.1) requires the door between an attached garage and the house to have **self-closing, self-latching hardware**. It's a barrier against **car exhaust (carbon monoxide) and garage fires**. Local rules vary, but the reason doesn't. So the goal is never "keep the door open". It's "**open it for you, then always let it close and latch**", even if the power fails or the robot crashes.

That makes it a perfect lesson for the boys: real engineering starts with the safety requirement, and the annoying door is protecting them.

### Part A: the tabletop model (do this first, whenever ready)

A cardboard door on the kit's servo, built on the table where nobody can get hurt.

- **Input:** the ultrasonic sensor sees someone coming (Chapter 1 logic).
- **Output:** the servo swings the door open **slowly**.
- **The brain is a state machine:** CLOSED → OPENING → OPEN (while someone is near) → WARNING (beep and blink for 3 seconds) → CLOSING → CLOSED. If someone appears during WARNING or CLOSING, go back to OPENING.
- **Safety rules, even on the model:**
  - It moves slowly.
  - A second check makes sure the doorway is clear before closing.
  - A big **manual button** always wins.
  - **Fail-safe:** a rubber band or gravity closes the door if power is cut, so losing power means closed, never stuck open.
- **Grown-up corner:** a state machine is the same idea as a Step Functions workflow, and "fail closed" is the same thinking as a circuit breaker defaulting to the safe state.

### Part B: the real door (no rush, maybe never DIY)

A "how real engineers think about it" guide, not a weekend build. Topics to cover when the time comes:

- **Code first:** the door must still self-close and self-latch. Check the local code before buying anything.
- **Use a listed product:** real automatic swing-door operators (sometimes called low-energy operators) come with force limits, slow speeds, obstruction sensing and safety certifications. A DIY motor pushing a heavy fire-rated door near kids is a hard no.
- **Fail-safe:** on power loss or a smoke/CO alarm, the door must close.
- **Pinch and force limits:** fingers at the hinge side, and kids, pets and bags in the way.
- **Where the Arduino could still fit:** as a *signal* to a certified operator (for example "someone is approaching"), never as the thing holding force or safety.
- **When to call a pro:** anything mounted on the actual door, wired to mains power, or replacing the door's closer.

---

## Ideas waiting in the wings

- **Wi-Fi robot:** an ESP32 replaces the Mac as the bridge in Chapter 4, so there's no laptop needed.
- **Robot car:** send Chapter 3's gestures to the ELEGOO Smart Robot Car (point left, it turns left).
- **Speedometer with interrupts:** a spinning wheel where checking "in the loop" misses beats, and an interrupt doesn't. The perfect demo of polling vs interrupts.
- **Room weather station:** the DHT11 from the kit, plus Chapter 4's phone notifications.

## Sources

- [IRC 2021 R302.5.1: garage-to-house door requirements](https://www.jaspector.com/codes/irc-2021/ch03-building-planning/garage-to-house-door-requirements/)
