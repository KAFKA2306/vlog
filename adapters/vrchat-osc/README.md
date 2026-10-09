# VRChat OSC adapter

Replaceable UDP OSC output for companion projections.

Default target: `127.0.0.1:9000`.

Parameters emitted by `VrchatOsc.speak`:

- `PetChar0` ... `PetChar7`: integer character IDs
- `PetMood`: integer 0-255
- `PetSpeak`: boolean pulse

This adapter does not persist evidence or memory. VRChat client reception, Animator behavior, and avatar parameter wiring require separate runtime verification.
