============================================================================================
FM ACTIONLINK
============================================================================================

Puts your own buttons on the Football Manager 26 player profile and connects them to
your own software (a website, an app, a 3D viewer).

[Imagem/Image: docs/exemplo.webp]

What it can do: three buttons right after "Actions" (here with a custom look; by default
they copy the game's own style) and a 3D stadium inside the Physical column, shown by an app
running outside the game.

Guia em português: LEIA-ME.txt

For developers and AI assistants: INTEGRATION.md (complete technical reference).

WHO NEEDS WHAT
--------------

  - You are...: Player: just uses buttons someone else set up
  - You need: FM26 with BepInEx 6 and the plugin folder. If the creator says so, their app installed.
  - You do NOT need: Python, coding, editing files

  - You are...: Creator without an app: buttons that open websites or programs
  - You need: The above, plus Notepad to edit one file
  - You do NOT need: Python, coding

  - You are...: Creator with an app: buttons that send things to your own app
  - You need: The above, plus an app that receives messages over the local network (any language)
  - You do NOT need: Python, unless your app is written in Python

About Python: it is only needed to run the example app in the examples folder,
which is there for creators to study. Players never need Python.

PART 1: INSTALL (EVERYONE)
--------------------------

1. BepInEx 6. If you already use other FM26 plugins, you have it. Otherwise install
   BepInEx 6 for IL2CPP (build be.755 or newer) and start the game once.
2. Copy the FMActionLink folder (inside the zip's plugins folder) into your game's
   BepInEx\plugins. For example:
   - Steam: ...\steamapps\common\Football Manager 26\BepInEx\plugins
   - Epic: ...\Epic Games\<FM26 folder>\BepInEx\plugins
   - Xbox / Game Pass: ...\XboxGames\Football Manager 26\Content\BepInEx\plugins
3. Run the game windowed or borderless. In "exclusive" full screen, app windows cannot
   appear over the game.
4. Turn on the game's ID option. In FM's preferences, tick "Show screen IDs in Title Bar to
   assist skinning". That is how the plugin knows which player is open. With the option off,
   the buttons only work for players who have a photo.
5. Open any player's profile. The buttons appear right after "Actions".

If nothing shows up, see Part 6.

PART 2: RECIPES (CREATORS)
--------------------------

Everything is set up in FMActionLink.json, in the plugin folder.

- Open it with Notepad (right click > Open with > Notepad).
- Each button is a block between { and } inside the "buttons" list, with a comma
  between blocks.
- Save and look at the game: it updates within 2 seconds, no restart. If a comma or a
  quote is wrong, the game keeps the previous version and the log says where the error is.
- Wherever {playerId} appears, the plugin puts the ID of the player on screen.

>> Recipe 1: a button that opens a website

No app needed. Inside "buttons", paste:

    {
      "id": "my-site",
      "label": "My site",
      "action": { "type": "openUrl", "url": "https://mysite.com/player/{playerId}" }
    }

1. Change "My site" to the button's text.
2. Change the address to yours. Keep {playerId} where the ID goes.
3. Save. Click the button in the game: the browser opens that player's page.

>> Recipe 2: a button that runs a program

No app needed. Paste:

    {
      "id": "my-program",
      "label": "Open program",
      "action": { "type": "runProgram", "path": "C:\\Program Files\\MyProgram\\MyProgram.exe", "arguments": "--player {playerId}" }
    }

1. path is the full path of the .exe. Note: every \ in the path is written twice
   (\\) in this file.
2. arguments is what the program receives (can be "").
3. Save and test.

>> Recipe 3: a button that opens the player in YOUR app

The button does not open anything by itself: it tells your app, and your app decides.

In FMActionLink.json:

1. At the top, in "app", set the address your app listens on:
    "app": { "eventsUrl": "http://127.0.0.1:8767/fm-events" }
   Any port works (the number after 127.0.0.1:), as long as your app uses the same one.
2. In "buttons", paste:
    { "id": "open-in-app", "label": "Open in app", "action": { "type": "sendToApp" } }
3. Optional: to have the game start your app when it is closed, add to "app" the path of
   its .exe: "startIfClosed": "C:\\Program Files\\MyApp\\MyApp.exe".

In your app: three things.

1. Listen on the eventsUrl address for POST requests.
2. Read the message. Every click arrives like this:
    {"event":"button.click","buttonId":"open-in-app","playerId":29179241,"screen":"playerProfile","gamePid":4876}
   buttonId says which button; playerId, which player.
3. Answer right away (any success code, like 200 or 204), then show the player. The
   plugin already allows your app to come in front of the game: use the usual "bring window
   to front" call.

Minimal example in Python (any language works the same: a local web server receiving JSON):

    from http.server import BaseHTTPRequestHandler, HTTPServer
    import json
    
    class Messages(BaseHTTPRequestHandler):
        def do_POST(self):
            message = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(204)            # answer first
            self.end_headers()
            if message["event"] == "button.click" and message["buttonId"] == "open-in-app":
                print("open player", message.get("playerId"))   # replace with your code
    
    HTTPServer(("127.0.0.1", 8767), Messages).serve_forever()

>> Recipe 4: a window that appears on mouse over (hover)

The plugin draws the button; the window belongs to your app. How it works:

- The mouse rests on the button: your app gets window.open and shows the window.
- The mouse leaves: it gets window.close and closes it.
- A click on the button: it gets window.pin, and the window stays until a click
  elsewhere, Esc or a second click on the button (then window.close arrives).

In FMActionLink.json (set the app address as in Recipe 3, step 1):

    {
      "id": "preview",
      "icon": "icons/radar.png",
      "tooltip": "Player preview",
      "action": { "type": "window", "openOnHover": true, "hoverDelayMs": 250 }
    }

hoverDelayMs is how long the mouse must rest before it opens (250 = a quarter of a
second). Without label, the button is a square icon.

In your app, on window.open:

    {"event":"window.open","buttonId":"preview","playerId":29179241,"mode":"hover",
     "anchor":{"x":1180,"y":262,"width":38,"height":38},"gamePid":4876}

1. Create a borderless, always on top window that does not take focus.
2. Put it next to the button: anchor is where the button is on screen (pixels). For
   example, right below it: x = anchor.x, y = anchor.y + anchor.height + 6.
3. Show the preview of player playerId in it.
4. On window.close with the same buttonId, close it.

The rules in Part 3 avoid the usual problems (window in the wrong place, game no longer
responding to the mouse). The example app does all of it: see show_overlay,
hide_overlay and next_to in examples\python-app\app.py.

>> Recipe 5: a 3D preview on click

Recipe 4 with "openOnHover": false: the window opens only on a click and stays until
closed.

    {
      "id": "preview-3d",
      "icon": "icons/cube.png",
      "tooltip": "View in 3D",
      "action": { "type": "window", "openOnHover": false }
    }

In your app, the window shows a page with the 3D model. The simplest way is
<model-viewer> with a GLB file (the most practical 3D format for this):

    <script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js"></script>
    <model-viewer src="my-model.glb" camera-controls auto-rotate style="width:100vw;height:100vh"></model-viewer>

The example app has this page ready: examples\python-app\pages\model3d.html.

>> Recipe 6: 3D (or anything else) embedded in the screen itself

The plugin opens an empty area inside the profile and keeps reporting where it is. Your
app places a window exactly over it, so it looks part of the game (the stadium in the
picture above).

In FMActionLink.json, in the "embeddedPanels" list:

    {
      "id": "my-3d",
      "afterLabel": ["Físicos", "Physical"],
      "beforeLabel": ["Guarda-Redes", "Goleiro", "Goalkeeping", "Goalkeeper"],
      "minHeight": 110
    }

- The area goes below the afterLabel text and above the beforeLabel text. Both
  must be in the same column, one above the other.
- Write each text exactly as the game shows it, in every language you want to support.
- The spot above (Physical column, before Goalkeeping) is only a suggestion for testing:
  it exists for outfield players only.
- The area only uses the column's spare room: it never squeezes the game's content. If
  there is less than minHeight, it does not appear.

In your app:

1. On panel.show, put your window (borderless, on top, no focus) exactly on rect:
    {"event":"panel.show","panelId":"my-3d","playerId":29179241,
     "rect":{"x":1283,"y":820,"width":342,"height":141},"gamePid":4876}
   It repeats when the area moves or resizes, when the player changes, and every 2 seconds.
   If rect did not change, do nothing.
2. On panel.hide (another tab or screen), hide the window without closing it, so the 3D
   does not load again when the user comes back.

>> Recipe 7: quick tweaks

- Another icon: put a PNG in the icons folder and use "icon": "icons/your-icon.png".
  Best: 64x64 pixels, white drawing on a transparent background.
- Keyboard shortcut: add "hotkey": "ctrl+shift+o" to the button. Works while the
  profile is open, outside text fields.
- Turn a button off without deleting it: add "enabled": false.
- Text on mouse over: "tooltip": "...".
- Order: buttons appear in list order.

PART 3: THE 5 RULES FOR YOUR APP'S WINDOWS
------------------------------------------

They make the window feel part of the game. The example app follows all of them.

1. Never take focus. Create windows without activating them (pywebview: focus=False).
   If your window steals focus, the game stops receiving mouse and keyboard.
2. Use "physical" pixels. Make your app "DPI aware (per monitor v2)" and use the numbers
   as received. Otherwise, with Windows scaling at 125% or 150%, the window lands in the
   wrong place.
3. Borderless and always on top, but hidden while another program is in front:
   compare the foreground window's process with gamePid and with your app's own.
4. On panel.hide, hide; do not close. The content stays loaded.
5. On window.close, close, even if the window is still opening (the mouse can leave
   the button before that).

PART 4: TRY IT WITH THE EXAMPLE APP (NEEDS PYTHON)
--------------------------------------------------

To see everything working before building your own app.

1. Install Python 3.10 or newer (python.org), ticking "Add Python to PATH".
2. Open a Command Prompt and run: pip install pywebview
3. Run: python examples\python-app\app.py and leave it open.
4. Open a player profile in FM. The FMActionLink.json in the package adds: Search
   (website), Open in app (message to the app, also Ctrl+Shift+O), the radar icon
   (hover preview), the cube icon (3D on click) and a 3D area in the Physical column.
5. To try your own pages, replace the files in examples\python-app\pages, or the
   addresses in WINDOWS and PANELS at the top of app.py.

PART 5: FOR PROGRAMMERS (C#), OPTIONAL
--------------------------------------

Instead of FMActionLink.json (or together with it), a BepInEx plugin of yours can create
buttons in code and handle them without any app. Full example: examples\csharp-extension;
complete API reference: INTEGRATION.md, section 7.

    [BepInPlugin("com.you.buttons", "Your buttons", "1.0.0")]
    [BepInDependency(FMActionLink.Plugin.Guid)]
    public class YourPlugin : BasePlugin
    {
        public override void Load()
        {
            ActionLink.PlayerProfile.Add(new ActionButton
            {
                Id = "hello", Label = "Hello",
                OnClick = player => Log.LogInfo($"player {player.PlayerId}"),
            });
            ActionLink.PlayerProfile.Add(new WindowButton
            {
                Id = "preview", IconPath = "icons/radar.png", OpenOnHover = true,
                OnOpen = r => { /* r.Anchor, r.Mode, r.Player.PlayerId */ },
                OnClose = (r, reason) => { },
            });
            ActionLink.PlayerProfile.Add(new EmbeddedPanel
            {
                Id = "area", AfterLabel = new[] { "Physical" }, BeforeLabel = new[] { "Goalkeeping" },
                OnShow = u => { /* u.Rect */ }, OnHide = id => { },
            });
        }
    }

- Leave OnOpen, OnPin, OnClose, OnShow, OnHide empty for the default: the same JSON
  messages sent to eventsUrl. ActionLink.SendToApp(...) sends any message yourself.
- Callbacks run on the game's main thread: return quickly; move network or disk work to
  Task.Run.
- Add with an existing id replaces it; Remove(id) removes it. The screen updates by
  itself.

To build the plugin from source: dotnet build src -c Release -p:GameDir="<FM26 folder>",
or tools\build-package.ps1 -GameDir "<FM26 folder>" for the full package. GameDir is a
game folder where BepInEx already ran once.

PART 6: WHEN SOMETHING DOES NOT WORK
------------------------------------

Everything the plugin does is written to BepInEx\LogOutput.log, on lines starting with
[ActionLink].

  - What happens: The buttons do not appear
  - What to do: Check the folder is in BepInEx\plugins and the log has [ActionLink] ... loaded.

  - What happens: I edited the file and nothing changed
  - What to do: The log should say FMActionLink.json has an error: a missing or extra comma or quote.

  - What happens: I click the app button and nothing happens
  - What to do: Your app is not running or listens on another address. The log says the app is not answering at ....

  - What happens: The windows do not appear over the game
  - What to do: The game is in exclusive full screen. Switch to windowed or borderless.

  - What happens: The window lands in the wrong place
  - What to do: Your app is not using physical pixels (Part 3, rule 2).

  - What happens: A button says it did not find the ID
  - What to do: Turn on "Show screen IDs in Title Bar to assist skinning" in FM's preferences (Part 1, step 4).

  - What happens: The embedded area does not appear
  - What to do: The two texts are not in the same column, or there is not enough spare height (minHeight).

REFERENCE: EVERY OPTION
-----------------------

>> Top of the file

  - Key: app.eventsUrl
  - What it does: Your app's address, where messages go.

  - Key: app.startIfClosed
  - What it does: Path of your app's .exe, started on a click if it is closed.

  - Key: app.startArguments
  - What it does: What to pass to the .exe when starting it.

  - Key: app.startTimeoutSeconds
  - What it does: How long to wait for the app to start (default 45).

  - Key: debug.logScreenTree
  - What it does: true writes the screen structure around the buttons and areas to the log.

>> Buttons

  - Key: id
  - Required: yes
  - What it does: Unique name. Sent with the messages.

  - Key: label
  - Required: no
  - What it does: Button text. Without it, a square icon.

  - Key: icon
  - Required: no
  - What it does: PNG or JPG image, relative to the plugin folder.

  - Key: tooltip
  - Required: no
  - What it does: Text on mouse over.

  - Key: hotkey
  - Required: no
  - What it does: Shortcut, like ctrl+shift+o or alt+f5.

  - Key: enabled
  - Required: no
  - What it does: false turns it off without deleting it.

  - Key: action.type
  - Required: yes
  - What it does: openUrl (Recipe 1), runProgram (Recipe 2), sendToApp (Recipe 3) or window (Recipes 4 and 5).

>> Embedded areas

  - Key: id
  - What it does: Unique name. Sent with the messages.

  - Key: afterLabel / beforeLabel
  - What it does: The texts the area sits between (Recipe 6).

  - Key: minHeight
  - What it does: Minimum height to appear (default 110).

  - Key: placeholderText
  - What it does: Text shown in the area until the app's window covers it.

>> Messages your app receives

All by POST to eventsUrl, in JSON, one at a time and in order.

  - event: button.click
  - When: Click on a sendToApp button
  - Main fields: buttonId, playerId

  - event: window.open
  - When: Open the window of a window button
  - Main fields: buttonId, playerId, mode (hover or pinned), anchor

  - event: window.pin
  - When: A hover window became pinned by a click
  - Main fields: same as window.open

  - event: window.close
  - When: Close the window
  - Main fields: buttonId, reason (mouseLeft, clickOutside, escape, clickedAgain, screenChanged)

  - event: panel.show
  - When: The embedded area appeared, changed or shows another player (and every 2 s)
  - Main fields: panelId, playerId, rect

  - event: panel.hide
  - When: The area is no longer visible
  - Main fields: panelId

All of them also carry screen (today always playerProfile) and gamePid (the game's
process). anchor and rect are physical screen pixels: x, y, width, height.

>> Player ID

It comes from two places: the player's photo in the header and the "ID: 12345678" text the game
shows when the option "Show screen IDs in Title Bar to assist skinning" is on (Part 1, step 4).
With the option on it works for every player; off, only for players with a photo. Without an
ID, messages go without playerId and buttons that use {playerId} do nothing (the log explains).

>> Current limits

- Player profile only; other screens will come later.
- The buttons sit next to the "Actions" box (#FrameActions), which stays in place across
  skins. A skin that renames it hides the buttons.
- The app's windows sit over the game: a game menu opened over the embedded area stays
  behind them.
- Version 1.0, tested on the Steam and Epic versions.
