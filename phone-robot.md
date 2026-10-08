# 📱 Bonus: The Phone Robot

**Rock Paper Scissors against a robot that lives in a web page.** Open a link on the iPhone, allow the camera, tap Start, and the phone becomes the robot: it **sees** your hand with the same Google AI from Chapter 3 and **speaks** with Safari's built-in voice. Nothing to install, no app, no wires.

| | |
|---|---|
| **Builders** | Two kids, plus a parent |
| **Time** | One evening |
| **Before this** | Chapter 3 (they've seen hand gestures recognized on the Mac) |
| **Needs** | An iPhone or iPad with Safari, the GitHub Pages site (it must be **https**), and the Mac for building and testing |
| **Cost** | $0 |

---

## Notes for the builder (Claude Code)

Please create:

1. **`phone-robot/index.html`**: the whole app. Plain HTML, CSS and JavaScript, **no build step, no frameworks**. It must work by just being served as a static file.
2. **`phone-robot/game.js`**: the game rules as a small ES module with pure functions, so they can be tested (see [Testing](#testing)).
3. **`phone-robot/game.test.mjs`**: tests runnable with `node --test`.
4. **`phone-robot.html`**: a short kid-facing guide page in the same style as the chapter pages (how to open it, how to play, challenges, troubleshooting). Link it from `index.html`, the README chapter table and `roadmap.md` as a **Bonus**.

Ground rules:

- **The app page is an app, not a guide.** Full screen, portrait first, huge buttons, readable from arm's length. Use the site's colors and rounded font so it feels like part of Build-a-Bot.
- **Everything runs on the phone.** The camera picture never leaves the device. The page only *downloads* the AI files; it never uploads anything.
- **No real names** in committed files. Player names are typed on the phone and saved only in that phone's browser storage.
- **Kid-readable code** with plain-English comments, like every chapter.

---

## How it works

```
 📷 iPhone camera ──► 🧠 Google AI (running inside Safari, on the phone) ──► 🎮 game rules ──► 📱 screen + 🔊 voice
```

Same idea as Chapter 3, with one big difference: there's no MacBook and no Arduino. The phone is the eyes, the brain, the screen and the voice, all in one.

**Kid version:** *"A web page is a program too. This one asks the phone for its camera, borrows a small AI brain from Google, and uses the phone's own voice to talk."*

---

## How it plays

1. **Start screen:** a giant **"Tap to start 🤖"** button. That one tap does three things: lets the robot speak, turns on the camera, and starts downloading the AI (with a "Loading the robot's brain..." progress message).
2. **Pick a player:** big buttons for **Player 1 / Player 2 / Guest**. Tap and hold a name to rename it. Names are stored only on this phone.
3. **The robot commits first:** it secretly picks its move **before** seeing yours and shows a sealed envelope 🔒. It can't cheat (the same fair-play idea as Chapter 7).
4. **Countdown:** the robot says *"Rock... Paper... Scissors... SHOOT!"* with a beep on each word and big words on screen.
5. **Reading your move:** for about half a second after "SHOOT!", the AI checks every camera frame and takes a **majority vote**. ✊ `Closed_Fist` = rock, ✋ `Open_Palm` = paper, ✌️ `Victory` = scissors. If it's unclear, the robot says *"I couldn't see that. Again!"*
6. **Reveal:** the envelope opens, both moves appear big, and the robot announces the result with a voice line ("Ha! Paper covers rock!", "You got me!", "Tie! Great minds...").
7. **Match:** first to 3 wins, with the score always visible.
8. **Leaderboard:** best win streak per player, saved on this phone.

The live camera picture shows in a corner, **mirrored like a selfie**, with the hand's skeleton drawn on it so kids can see what the AI sees.

---

## iPhone rules the page must follow

These are the things that make or break it on iPhone Safari.

### 1. The page must be https

iPhones only allow the camera on secure pages. **GitHub Pages is https**, so publish there. For testing on the Mac, `http://localhost` also counts as secure. The iPhone **can't** use the Mac's address over plain `http://`. Test on the Mac first, then push to GitHub and test on the phone.

If GitHub Pages isn't on yet: repo **Settings → Pages**, deploy from the `main` branch, root folder. The app would then live at `https://keep-code-simple.github.io/build-a-bot/phone-robot/`.

### 2. Camera only, never the microphone

- Ask for video only: `getUserMedia({ video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: false })`.
- **Never request the microphone.** On iPhone, an open microphone can switch audio into a "recording" mode that makes speech quiet or silent.
- The `<video>` element needs `playsinline`, `muted` and `autoplay`, or iPhone tries to open it full screen.

### 3. The robot can only talk after a tap

- iPhone Safari ignores speech until the page has spoken **during a tap**.
- So inside the Start button's tap handler, **before any `await`**, speak a first utterance (the greeting *"Hi! I'm the Phone Robot!"* works) and create or resume the `AudioContext` used for beeps.
- If speech ever seems stuck, `speechSynthesis.cancel()` and speak again on the next tap.
- Voices load in the background, so listen for `voiceschanged` and pick an English voice. A settings panel lets kids choose the voice and change its speed and pitch.

### 4. The AI

- Load **`@mediapipe/tasks-vision` version 1.1.0** from jsDelivr as an ES module: `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0`. Get the WebAssembly files with `FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0/wasm")`.
- Use the **same gesture model as Chapter 3**: `https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task`.
- Create it with `GestureRecognizer.createFromOptions(...)`, `runningMode: "VIDEO"`, `numHands: 1`. Try `delegate: "GPU"` first, and **fall back to `"CPU"` automatically** if that fails.
- Call `recognizeForVideo(video, performance.now())` from a `requestAnimationFrame` loop, skipping frames where the video hasn't changed. Results: `result.gestures[0][0].categoryName` and `.score`, and `result.landmarks[0]` (21 hand points) for drawing the skeleton.
- **Don't commit the model files** (`*.task` is already gitignored). The page downloads them each time, so it needs internet. After the first visit, Safari's cache usually makes it faster.

### 5. Be a good phone app

- **Keep the screen on** while playing: `navigator.wakeLock.request("screen")` if it's available. Ask again when the page becomes visible again.
- **Save battery:** when the page is hidden (`visibilitychange`), stop the AI loop and the camera. Restart them when it comes back.
- **Friendly errors** instead of blank screens:
  - Camera blocked: show how to allow it (in Safari, tap **aA → Website Settings → Camera → Allow**, then reload).
  - AI can't download: "The robot needs internet the first time. Check Wi-Fi."
  - No hand found: "Show me your hand! Not too close, not too far."
- **Rotation:** portrait first. Landscape should still work.
- **Optional:** iPhone's **Share → Add to Home Screen** for a full-screen, app-like icon. Include the icon and home-screen meta tags, but test the camera in that mode. If it misbehaves, play in a normal Safari tab.

---

## Code layout

```
phone-robot/
├── index.html         the app: screens, camera, AI, voice, sounds, game loop
├── game.js            pure game rules (no camera, no AI, no screen), exported functions
└── game.test.mjs      node --test
phone-robot.html       the kid guide page (site style)
```

`game.js` exports at least:

- `gestureToMove(categoryName, score)` returns `"rock" | "paper" | "scissors" | null` (score must be at least 0.5)
- `majorityMove(movesSeenDuringWindow)` returns the winning move, or `null` if it's unclear (fewer than half the frames agree, or too few frames)
- `winner(playerMove, robotMove)` returns `"player" | "robot" | "tie"`
- `pickRobotMove(randomFn)` (takes the random function as an argument, so tests can fix it)
- `updateMatch(state, result)` returns the new score and whether the match is over (first to 3)

`index.html` is organized as clearly labeled sections: settings, camera, AI, voice, sounds, game screens, and a simple **state machine** with states `START → LOADING → PICK_PLAYER → COMMIT → COUNTDOWN → READ → REVEAL → (next round or MATCH_OVER)`.

---

## Testing

**Automatic (`node --test phone-robot/`):**

- `winner` for all 9 combinations.
- `gestureToMove`: the three gestures; low scores; other gestures like `Thumb_Up` and `None` give `null`.
- `majorityMove`: clear majority, a 50/50 split (`null`), an empty window (`null`), and mixed frames with `null`s.
- `pickRobotMove` with a fixed random function; it's called **before** the read window (test the order with a fake clock or call log).
- `updateMatch`: first to 3, and ties don't count.

**On the Mac:** open `http://localhost:8000/phone-robot/` (any simple static server) in Safari or Chrome with the webcam. Everything should work.

**On the iPhone (the family's checklist on the guide page):**

- The camera permission prompt appears once, and the video is mirrored.
- The robot speaks right after the Start tap, and keeps speaking every round.
- 9 of 10 held gestures are read correctly in normal room light.
- Locking the phone and coming back resumes the game, with the camera and AI working.
- Rotating the phone doesn't break the layout.
- No microphone permission is ever requested.

---

## Kid challenges

- **Give it a personality:** write your own win, lose and tie lines in the settings section. Pick the funniest voice and speed.
- **Secret gestures:** the AI also knows 👍 `Thumb_Up`, 👎 `Thumb_Down`, ☝️ `Pointing_Up` and 🤟 `ILoveYou`. Make 👍 do a victory dance on screen, or make 🤟 say something nice.
- **The cheat switch:** turn on the hidden setting where the robot waits to see your move first. The envelope shows "?" instead of 🔒. Can you tell it's cheating? (Chapter 3's lesson, in your pocket.)
- **Play a friend:** send the link to a cousin. The robot runs on their phone too.

---

## Privacy

- The camera picture is processed **on the phone, inside Safari**. The page never sends pictures anywhere.
- The page only downloads two things: the AI's code (jsDelivr) and the gesture model (Google).
- Player names and scores stay in that phone's browser storage, and nothing personal goes in the repo.
- No analytics and no tracking scripts.

---

## Facts checked (October 2026)

| Fact | Source |
|---|---|
| `@mediapipe/tasks-vision` 1.1.0 is the current release (Oct 6, 2026). It exports an ES module and ships its WebAssembly files in `/wasm`. `GestureRecognizer.createFromOptions`, `recognizeForVideo`, `delegate: "CPU" \| "GPU"`; results have `gestures`, `landmarks`, `handedness` | npm package contents, checked |
| Gesture model URL (same as Chapter 3) | [MediaPipe web samples](https://github.com/google-ai-edge/mediapipe-samples-web/blob/main/src/tasks/gesture-recognizer.ts) |
| A live web demo of the MediaPipe gesture recognizer exists | [MediaPipe CodePen demo](https://codepen.io/mediapipe-preview/pen/zYamdVd) |
| iPhone Safari ignores `speechSynthesis.speak()` until the page has spoken during a tap | [knowledge_press fix for iOS speech](https://github.com/Flux-Frontiers/knowledge_press/pull/42) |
| On iPhone, an open microphone can switch audio to a recording mode that demotes speech, and audio must start inside a tap | [iOS Safari audio sessions](https://samueleddy.com/writing/ios-safari-audio-sessions/) |

**Not verified on a real iPhone yet:** GPU vs CPU speed in Safari, the wake lock on this phone's iOS version, and camera behavior in Add to Home Screen mode. The on-device checklist covers these.
