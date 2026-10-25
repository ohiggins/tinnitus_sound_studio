# Tinnitus Sound Studio

An evidence-informed Streamlit application for **optional tinnitus sound enrichment**, rather than a treatment or cure. It produces low-level background sounds for personal comfort and illustrates how clinical evidence can be presented transparently in a digital health prototype.

> **Medical notice**: No sound or specific frequency is proven to cure tinnitus. The app is not a medical device. The signal level is a digital amplitude cap, **not a safe sound pressure level (dB SPL)**. Start with your actual device's volume at minimum. Stop for discomfort or worsening symptoms. Seek audiological assessment, and urgent assessment when tinnitus accompanies sudden hearing loss or acute neurological symptoms.

## Features

- Continuous browser player using the Web Audio API, Start/Stop controls, 5–60-minute automatic stop.
- White, pink and brown noise, adjustable 80–8,000 Hz noise filtering.
- Optional low-level 125–2,000 Hz sine texture mixed into noise, explicitly **not a therapeutic frequency**.
- Conservative default signal setting, 5% peak full-scale and a capped 1–15% adjustment.
- WAV preview/export, 15, 30, 60 or 120 seconds, mono 44.1 kHz 16-bit PCM.
- Optional self-rated before/after distress diary with CSV export, no database included.
- In-app evidence summary and APA 7th references.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit will provide a local URL, typically http://localhost:8501. Use a modern browser. Click the Start button **inside** the Live Player panel; browsers block audio that starts without user interaction. If the player is blocked, use the downloadable WAV player. Adjusting app settings while playing causes the embedded player to reload and stop.

To run unit tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Evidence and intentional omissions

See [EVIDENCE.md](EVIDENCE.md). Sound enrichment may help some people temporarily by reducing the prominence or intrusiveness of tinnitus. Benefits are variable and intervention-specific evidence remains uncertain. The US VA/DoD guideline offers a **weak** suggestion for sound self-care. NICE could not recommend stand-alone sound therapy from the available evidence. CBT has stronger evidence for managing tinnitus-related distress. Audiological assessment is important, with hearing aids appropriate in certain cases of hearing loss.

The app does **not** implement pitch matching, notched music, binaural beats, subliminal audio, neuromodulation or curative frequency presets. A selectable sine tone is an optional auditory texture and makes no therapeutic claim.

## Technical notes and limitations

- Audio is generated on the **browser** for live playback and on the **Streamlit server** for WAV files. The two generators use distinct algorithms and therefore sound similar rather than identical.
- Generated colour noises are approximate spectra. The band-pass filter alters timbre only.
- A 5% digital waveform on one phone or set of headphones can produce a different actual sound pressure level from 5% on another. No listening duration or dB SPL is medically certified.
- The automatic timer is a user convenience, **not** a validated treatment schedule.
- Diary changes are not evidence of efficacy. They are uncontrolled, subjective observations.
- Diary records are kept in Streamlit server session memory while available and can be exported by the user. Host infrastructure may log connections and retains ultimate responsibility for security. No user or audio data is intentionally sent to an external service by this code.
- Avoid making the app publicly accessible without appropriate cybersecurity review, privacy notices and clinical governance.

## Appropriate use

Use alongside, not instead of, a qualified assessment. Seek urgent medical care when tinnitus accompanies sudden hearing loss, facial weakness or other acute neurological symptoms. Arrange assessment for pulse-synchronous or one-sided persistent tinnitus, dizziness, ear pain or other concerning changes. If tinnitus began after a medication change, review this with the prescribing clinician rather than stopping medicines independently.

## Running on Streamlit Community Cloud

Connect a repository containing `app.py`, `audio_engine.py`, `live_player.py` and `requirements.txt`. Set the main file to `app.py`. This app does not require API keys, microphones or internet audio services, but audio runs only after a user clicks Start.

## Licence

MIT (see [LICENSE](LICENSE)). Third-party Python dependencies are installed separately under their own respective licences.
