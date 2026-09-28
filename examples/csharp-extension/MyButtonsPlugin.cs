using System.Diagnostics;
using BepInEx;
using BepInEx.Unity.IL2CPP;
using FMActionLink;

namespace MyButtons;

/// <summary>
/// Example: buttons added from code instead of FMActionLink.json. Copy this project, build
/// it and drop MyButtons.dll into BepInEx\plugins (next to FMActionLink).
/// </summary>
[BepInPlugin("com.example.mybuttons", "My Buttons (example)", "1.0.0")]
[BepInDependency(Plugin.Guid)]
public class MyButtonsPlugin : BasePlugin
{
    public override void Load()
    {
        // A plain button with your own logic.
        ActionLink.PlayerProfile.Add(new ActionButton
        {
            Id = "code-hello",
            Label = "Hello",
            Tooltip = "Writes the player ID to the BepInEx log",
            OnClick = player => Log.LogInfo($"Hello, player {player.PlayerId?.ToString() ?? "(ID not shown)"}"),
        });

        // A window button handled here instead of sending events to an app.
        ActionLink.PlayerProfile.Add(new WindowButton
        {
            Id = "code-window",
            Label = "Window",
            OpenOnHover = true,
            OnOpen = request => Log.LogInfo($"open {request.Mode} at {request.Anchor} for player {request.Player.PlayerId}"),
            OnPin = request => Log.LogInfo("pinned"),
            OnClose = (request, reason) => Log.LogInfo($"closed: {reason}"),
        });

        // An action that talks to your app with the same events the JSON buttons use.
        ActionLink.PlayerProfile.Add(new ActionButton
        {
            Id = "code-send",
            Label = "Send",
            OnClick = player => ActionLink.SendToApp(new AppEvent
            {
                Event = "button.click", ButtonId = "code-send", Screen = player.ScreenName, PlayerId = player.PlayerId,
            }, startAppIfClosed: true),
        });

        // An embedded area where you decide what to do with its position.
        ActionLink.PlayerProfile.Add(new EmbeddedPanel
        {
            Id = "code-panel",
            AfterLabel = new[] { "Mentais", "Mental" },
            BeforeLabel = new[] { "Sem Bola", "Off The Ball" },
            MinHeight = 60,
            OnShow = update => Debug.WriteLine($"panel at {update.Rect}"),
            OnHide = id => Debug.WriteLine($"panel {id} hidden"),
        });
    }
}
