from io import BytesIO
import wave

import numpy as np
import pytest

from audio_engine import AudioSettings, SAMPLE_RATE, generate_samples, generate_wav
from live_player import html_for_player


@pytest.mark.parametrize("sound", ["White noise", "Pink noise", "Brown noise"])
def test_samples_are_finite_and_amplitude_capped(sound):
    config = AudioSettings(sound_type=sound, duration_seconds=15)
    x = generate_samples(config)
    assert x.dtype == np.float32
    assert len(x) == SAMPLE_RATE * 15
    assert np.isfinite(x).all()
    assert np.max(np.abs(x)) <= .05 + 1e-6
    assert np.sqrt(np.mean(x**2)) > .0001
    assert x[0] == 0
    assert x[-1] == 0


def test_tone_mixture_is_capped():
    config = AudioSettings(tone_mix_percent=30, digital_peak_percent=15, duration_seconds=15)
    x = generate_samples(config)
    assert np.max(np.abs(x)) <= .15 + 1e-6


def test_wav_is_valid_mono_pcm():
    wav_bytes = generate_wav(AudioSettings(duration_seconds=15))
    with wave.open(BytesIO(wav_bytes), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() == SAMPLE_RATE * 15
    assert len(wav_bytes) > 44


def test_invalid_values_rejected():
    with pytest.raises(ValueError):
        AudioSettings(low_hz=6000, high_hz=500).validate()
    with pytest.raises(ValueError):
        AudioSettings(digital_peak_percent=90).validate()
    with pytest.raises(ValueError):
        AudioSettings(tone_hz=12000).validate()


def test_live_player_contains_controls_and_config():
    html = html_for_player(AudioSettings(tone_mix_percent=15), 10)
    assert "Start gentle sound" in html
    assert '"tone_mix_percent": 15' in html
    assert '"minutes": 10' in html
    assert "stopSound" in html
