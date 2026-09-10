# Run state

Goal: 100 additional sets, each with a 36-frame sheet, 36 PNG frames, and a 3-second GIF. Different styles and action ideas. User emphasizes action with a little story. Do not use HyperFrames.

Live generation handles when this note was written: functions exec cell 27 owns IDs 001–020; functions exec cell 31 owns IDs 021–100. Cell 27 is now completed: 20 successes, zero failures. Cell 31 remains the generation worker for IDs 021–100 with six workers, retries up to three times, and saves each case immediately. Revalidate these exact handles with functions.wait after resuming; do not infer termination from silence.

Assembler: exec_command session 78225 runs watch_build.py. It waits for generated sheets and encodes/verifies each. Revalidate with write_stdin. It exits after 100 technical audits exist.

Authoritative progress: case generation.json, storyboard.png, animation.gif and audit.json, plus qa/visual-reviews.json. Manifest may lag a newly recorded visual review until pipeline.py status is called. Do not treat stale manifest alone as process state.

Need before final: visually inspect every generated sheet, record honest approvals or regenerate poor cases; verify all files and exact 100 count; copy package to ~/Downloads/stop-motion-100-20260910; verify copies; update_goal complete only once all requirements are proven.
