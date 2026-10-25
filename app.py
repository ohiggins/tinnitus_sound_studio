"""Tinnitus Sound Studio: sound-enrichment prototype, not a tinnitus cure.

Run: streamlit run app.py
"""

from dataclasses import asdict
from datetime import datetime
from io import StringIO
import csv

import streamlit as st
import streamlit.components.v1 as components

from audio_engine import AudioSettings, SOUND_TYPES, generate_wav
from live_player import html_for_player

st.set_page_config(
    page_title="Tinnitus Sound Studio",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.7rem; max-width: 1170px;}
h1,h2,h3 {color:#173c4b;}
.intro {color:#4d6874;font-size:1.06rem;}
.note {border-left:3px solid #176e75;padding:.3rem .85rem;background:#f1f8f8;
       border-radius:0 8px 8px 0;margin:.7rem 0 1rem;}
.small {font-size:.86rem;color:#556c78;}
</style>
    """,
    unsafe_allow_html=True,
)

st.title("🎧 Tinnitus Sound Studio")
st.markdown(
    '<p class="intro">Personalised, low-level sound enrichment for comfort, '
    'relaxation and self-care.</p>',
    unsafe_allow_html=True,
)
st.warning(
    "No sound or frequency has been proven to cure tinnitus. This app is a "
    "self-care prototype, not a medical device or a substitute for assessment. "
    "Benefits are individual and uncertain."
)

with st.sidebar:
    st.header("Sound settings")
    sound_type = st.selectbox(
        "Background sound",
        SOUND_TYPES,
        index=0,
        help="Pink and brown noise contain more low-frequency energy than white noise. "
        "No type is established as best for tinnitus.",
    )
    st.subheader("Frequency balance")
    low_hz, high_hz = st.slider(
        "Pass-band (Hz)",
        min_value=80,
        max_value=8000,
        value=(150, 4500),
        step=10,
        help="Only changes timbre. This does not match or treat your tinnitus pitch.",
    )
    if high_hz - low_hz < 100:
        st.warning("Choose a wider frequency range (at least 100 Hz).")
        high_hz = min(8000, low_hz + 100)
        if high_hz == low_hz:
            low_hz = high_hz - 100

    st.subheader("Optional soft tone")
    st.caption("A low-level sound texture, not a therapeutic tinnitus frequency.")
    tone_mix = st.slider(
        "Tone proportion (%)", 0, 30, 0, 5,
        help="0% means noise only. Tone volume is limited to a minority of the mixture.",
    )
    tone_hz = st.slider(
        "Tone frequency (Hz)", 125, 2000, 440, 5,
        disabled=(tone_mix == 0),
        help="Select for comfort only. Do not attempt tinnitus pitch matching.",
    )
    st.subheader("Digital output")
    level = st.slider(
        "Peak signal level (% of full-scale)",
        1, 15, 5, 1,
        help="This limits the digital audio sample amplitude, not sound pressure at "
        "your ears. Your device volume can still be harmful.",
    )
    st.caption(
        "Start with the device volume at its minimum. Increase only until "
        "the sound is just audible and comfortable. Do not try to drown out tinnitus."
    )

settings = AudioSettings(
    sound_type=sound_type,
    low_hz=int(low_hz),
    high_hz=int(high_hz),
    tone_hz=int(tone_hz),
    tone_mix_percent=int(tone_mix),
    digital_peak_percent=int(level),
    duration_seconds=30,
)

player_tab, export_tab, diary_tab, evidence_tab = st.tabs(
    ["▶ Live player", "↓ WAV download", "◷ Symptom diary", "Clinical evidence and safety"]
)

with player_tab:
    left, right = st.columns([1.75, 1], gap="large")
    with left:
        st.subheader("Play sound continuously")
        session_minutes = st.select_slider(
            "Automatic stop after", options=[5, 10, 15, 30, 60], value=10,
            format_func=lambda n: f"{n} minutes",
        )
        components.html(html_for_player(settings, session_minutes), height=170)
        st.info(
            "Audio runs in your browser after you press Start. It stops at the selected "
            "time or when you press Stop. Changing a Streamlit control resets the player."
        )
    with right:
        st.subheader("Suggested approach")
        st.markdown(
            "1. Turn your speakers or headphones down first.\n"
            "2. Start with the default soft pink noise.\n"
            "3. Keep the sound at a gentle background level.\n"
            "4. Try different noise types only if comfortable.\n"
            "5. Stop if it causes discomfort or worsening symptoms."
        )
        st.caption(
            "The 5–60 minute timer is a user convenience. It is not an "
            "evidence-based treatment dose."
        )

with export_tab:
    st.subheader("Generate an offline audio file")
    st.write(
        "Create a mono, 44.1 kHz, 16-bit WAV with the selected sound settings. "
        "Your audio is generated on the application server."
    )
    duration = st.radio(
        "File length", options=[15, 30, 60, 120], index=1,
        format_func=lambda s: f"{s} seconds",
        horizontal=True,
    )
    target_settings = AudioSettings(
        **{**asdict(settings), "duration_seconds": duration}
    )
    if st.button("Generate audio", type="primary", key="generate_audio"):
        with st.spinner("Generating WAV file..."):
            try:
                st.session_state["wav_data"] = generate_wav(target_settings)
                st.session_state["wav_config"] = target_settings
            except Exception as exc:
                st.error(f"Could not generate audio: {exc}")

    if "wav_data" in st.session_state:
        if st.session_state.get("wav_config") != target_settings:
            st.warning("The generated file uses earlier settings. Generate audio again to update it.")
        st.audio(st.session_state["wav_data"], format="audio/wav")
        st.download_button(
            "Download WAV file",
            data=st.session_state["wav_data"],
            file_name="tinnitus_sound_enrichment.wav",
            mime="audio/wav",
            key="download_wav",
        )
    st.caption(
        "Audio files do not contain clinical calibration. Playback volume depends "
        "on the receiving device. WAV generation may take a few seconds."
    )

with diary_tab:
    st.subheader("Optional self-reported comfort diary")
    st.write(
        "Track whether a listening session felt helpful. This is descriptive self-report "
        "and cannot establish clinical effectiveness or a causal treatment effect."
    )
    if "diary" not in st.session_state:
        st.session_state["diary"] = []
    with st.form("comfort_entry", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            before = st.slider("Tinnitus-related distress before (0–10)", 0, 10, 5)
        with col2:
            after = st.slider("Tinnitus-related distress after (0–10)", 0, 10, 5)
        helped = st.selectbox(
            "Overall experience", ["Neutral", "Helpful", "Unhelpful", "Stopped due to discomfort"]
        )
        notes = st.text_input(
            "Optional notes", max_chars=180,
            placeholder="For example, pink noise made reading easier",
        )
        saved = st.form_submit_button("Save diary entry")
    if saved:
        st.session_state["diary"].append(
            {
                "timestamp_local": datetime.now().astimezone().isoformat(timespec="seconds"),
                "distress_before_0_10": before,
                "distress_after_0_10": after,
                "experience": helped,
                "sound": sound_type,
                "notes": notes,
            }
        )
        st.success("Entry saved in this Streamlit session.")
    if st.session_state["diary"]:
        st.dataframe(st.session_state["diary"], use_container_width=True, hide_index=True)
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(st.session_state["diary"][0]))
        writer.writeheader()
        writer.writerows(st.session_state["diary"])
        st.download_button(
            "Export diary as CSV", output.getvalue().encode("utf-8-sig"),
            file_name="tinnitus_comfort_diary.csv", mime="text/csv"
        )
        if st.button("Clear diary in this session"):
            st.session_state["diary"] = []
            st.rerun()
    st.caption(
        "Privacy: entries reside in the Streamlit server's temporary session memory, "
        "not in a database created by this app. Whoever hosts the app controls the "
        "server. Do not enter identifying health information on an untrusted deployment."
    )

with evidence_tab:
    st.subheader("What clinical guidelines support")
    st.markdown(
        "**Sound for self-care.** The 2024 VA/DoD guideline suggests therapeutic "
        "sound for tinnitus self-care (weak recommendation). The same guideline "
        "suggests sound enrichment alongside ongoing tinnitus education delivered "
        "by an audiologist. The evidence does not identify a curative frequency. "
        "(Department of Veterans Affairs & Department of Defense, 2024)."
    )
    st.markdown(
        "**Strength of evidence.** NICE did not recommend a particular stand-alone "
        "sound therapy because available evidence was insufficient. A Cochrane "
        "review likewise found low-certainty evidence and no clear superiority "
        "of sound generators over comparison options (NICE, 2020; Sereda et al., 2018)."
    )
    st.markdown(
        "**Approaches with greater support.** Cognitive behavioural therapy can "
        "reduce tinnitus-related distress. An audiologist can assess hearing and "
        "advise on hearing aids if hearing loss is present (Fuller et al., 2020; "
        "NICE, 2020)."
    )
    st.markdown(
        "**Techniques not claimed here.** There is insufficient evidence to "
        "recommend for or against notched or spectrally altered music as a tinnitus "
        "treatment. This app does not offer pitch matching, notched-music therapy "
        "or 'healing frequencies' (Department of Veterans Affairs & Department of "
        "Defense, 2024; NICE, 2020)."
    )
    st.subheader("When to seek clinical advice")
    st.error(
        "Seek urgent medical assessment for tinnitus with sudden hearing loss, "
        "new facial weakness or other acute neurological symptoms. "
        "Seek clinical assessment for heartbeat-synchronous (pulsatile) tinnitus, "
        "persistent one-sided tinnitus, vertigo, ear pain or new tinnitus."
    )
    st.write(
        "A GP or audiologist can assess hearing, potential reversible causes, "
        "and whether treatment or referral is appropriate. Review any suspected "
        "medication-related tinnitus with the prescriber; do not stop prescribed "
        "medicines without advice."
    )
    st.markdown("#### References (APA 7th)")
    st.markdown(
        "Department of Veterans Affairs, & Department of Defense. (2024). "
        "*VA/DoD clinical practice guideline for tinnitus*. "
        "https://www.healthquality.va.gov/guidelines/CD/tinnitus/\n\n"
        "Fuller, T., Cima, R., Langguth, B., Mazurek, B., Vlaeyen, J. W. S., "
        "& Hoare, D. J. (2020). Cognitive behavioural therapy for tinnitus. "
        "*Cochrane Database of Systematic Reviews*, *2020*(1), CD012614. "
        "https://doi.org/10.1002/14651858.CD012614.pub2\n\n"
        "National Institute for Health and Care Excellence. (2020). "
        "*Tinnitus: Assessment and management (NICE guideline NG155)*. "
        "https://www.nice.org.uk/guidance/ng155\n\n"
        "Sereda, M., Xia, J., El Refaie, A., Hall, D. A., & Hoare, D. J. (2018). "
        "Sound therapy (using amplification devices and/or sound generators) "
        "for tinnitus. *Cochrane Database of Systematic Reviews*, *2018*(12), "
        "CD013094. https://doi.org/10.1002/14651858.CD013094.pub2"
    )

st.divider()
st.caption(
    "Tinnitus Sound Studio, educational prototype. No claims of cure, "
    "no clinical calibration, no individually prescribed dose. "
    "Do not use while driving or when you need to hear environmental warnings."
)
