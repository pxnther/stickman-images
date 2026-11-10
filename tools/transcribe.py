"""Transcribe narration audio into an SRT plus word-level timings (runs in GitHub Actions)."""
import json, os, sys
from faster_whisper import WhisperModel

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"

model = WhisperModel(os.environ.get("WHISPER_MODEL", "medium.en"), device="cpu", compute_type="int8")
for path in sys.argv[1:]:
    base, _ = os.path.splitext(path)
    prompt = None
    sp = os.path.join(os.path.dirname(path), "script.txt")
    if os.path.exists(sp):
        prompt = open(sp, encoding="utf-8").read()[-800:]
    segs, info = model.transcribe(path, language="en", word_timestamps=True, beam_size=5,
                                  initial_prompt=prompt, vad_filter=False)
    segs = list(segs)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    aligner = "faster-whisper"
    try:   # WhisperX forced alignment (wav2vec2) for tighter word timings; falls back to whisper's own times
        import whisperx
        from faster_whisper.audio import decode_audio
        audio = decode_audio(path, sampling_rate=16000)
        model_a, meta = whisperx.load_align_model(language_code="en", device="cpu")
        res = whisperx.align([{"start": s.start, "end": s.end, "text": s.text} for s in segs], model_a, meta, audio, "cpu",
                             return_char_alignments=False)
        wx = [{"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
              for seg in res["segments"] for w in seg.get("words", []) if "start" in w and "end" in w]
        if len(wx) >= 0.9 * len(words):
            words, aligner = wx, "whisperx"
    except Exception as e:
        print("whisperx alignment skipped:", e)
    json.dump({"duration": info.duration, "aligner": aligner, "words": words}, open(base + "_words.json", "w"), indent=1)
    # captions: up to 6 words, break at sentence ends or gaps over 0.35 s
    caps, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_sent = w["word"].endswith((".", "?", "!", ","))
        gap = nxt is not None and nxt["start"] - w["end"] > 0.35
        if nxt is None or len(cur) >= 6 or end_sent or gap:
            caps.append(cur); cur = []
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for n, c in enumerate(caps, 1):
            f.write(f"{n}\n{ts(c[0]['start'])} --> {ts(c[-1]['end'])}\n{' '.join(w['word'] for w in c)}\n\n")
    print(path, len(words), "words,", len(caps), "captions,", round(info.duration, 2), "s")
