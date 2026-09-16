# Video, audio, and timeline editing

Use this reference for editing, reviewing, localizing, captioning, mixing, or exporting video and audio.

## Team shape

- Asset analyst: inspect media, metadata, transcripts, selects, timecodes, rights, and missing assets.
- Story/timeline editor: own narrative structure, pacing, continuity, and timeline changes.
- Audio/captions specialist: review dialogue, music, sound effects, sync, loudness, captions, and accessibility.
- Visual finisher: check graphics, transitions, framing, color, compositing, and artifacts.
- Independent QA reviewer: inspect the rendered output against the brief and delivery specification.

Assign one owner to each timeline or project file. Other workers should produce read-only notes or separate artifacts unless isolated project copies can be merged safely. Keep source media immutable.

## Capability-aware editing and safe fallback

Use only media tools the host actually exposes. A portable adapter may describe available inspection, transcription, scene or silence detection, edit-plan, timeline-mutation, render, and playback-verification capabilities, but must not imply that a named editor, render engine, or delivery integration exists.

Prefer the cheapest reliable evidence path before model judgment:

1. Inspect available media metadata, transcript, waveform, contact sheet, scene boundaries, loudness, or preview with authorized read-only tools.
2. Convert those observations into compact, time-coded edit-relevant notes: hook, story beats, dead air, repetition, filler, continuity, visual variety, dialogue clarity, captions, and rights signals.
3. Use model reasoning for editorial decisions that need taste or synthesis: preserving meaning and creator voice, prioritizing important moments, pacing, emotional cadence, graphics, caption phrasing, and a clear call to action.
4. Let the authorized timeline owner apply changes, then verify the changed timecodes and final render.

If editing or render tools are unavailable, produce a review-ready time-coded EDL, cut list, caption/script change list, or clearly labeled proposed command recipe. State that it is a plan rather than a completed edit; do not claim a render, export, sync, or final-quality verification occurred. Proposed FFmpeg or editor commands are drafts and require the normal mutation authority before they are run.

Do not optimize by mechanically removing every pause, shortening every clip, or following a trend template. Preserve the intended meaning, creator voice, necessary context, accessibility, and significant moments; make each cut traceable to the brief or evidence.

## Efficient workflow

1. Define audience, story goal, target duration, platform, reference style, aspect ratio, frame rate, resolution, codec, audio, captions, and delivery requirements.
2. Build a time-coded edit plan from proxies, contact sheets, waveforms, and transcripts. Parallelize selects, story notes, audio review, captions, graphics, and delivery-spec checks when independent.
3. Have the timeline owner implement approved changes. Review lightweight previews for structure and pacing before expensive renders.
4. After a change, re-check affected timecodes and dependent transitions, overlays, audio, and captions. Reuse unaffected evidence.
5. Render at delivery quality for final verification. Proxy playback cannot prove final image, audio, caption, or encoding quality.

## Quality gate

Verify, as applicable: narrative clarity, pacing, continuity, framing, composition, transitions, graphics, color, visual artifacts, audio/video sync, dialogue intelligibility, music/SFX balance, loudness, captions, spelling, safe areas, accessibility, aspect ratio, frame rate, resolution, codec, duration, start-to-finish playback, media-license provenance, likeness or voice consent, usage restrictions, and required synthetic-media disclosures.

Every issue must include a timecode or artifact location, severity, evidence, and recommended fix. Continue repair and re-render under the core convergence policy until the acceptance matrix passes or the supervisor returns `BLOCKED`. Saving render time or tokens never justifies a known defect. Block all external delivery, distribution, publication, or third-party use while applicable rights, consent, restrictions, or disclosure requirements remain unresolved. Authorized, securely contained internal review may continue only when it does not itself violate those requirements.
