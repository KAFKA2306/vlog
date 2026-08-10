# Companion projection

`vlog_companion` is a storage-agnostic projection for a deliberately simple VRChat companion.

It does not create or accept human memory claims. It consumes already-selected terms and produces ephemeral companion state:

```text
observed term + reading
  -> count + last_seen
  -> weighted sampling
  -> 8 kana parameter slots
```

Sampling weight:

```text
w_i = (count_i + 0.5)^0.8 * exp(-0.035 * age_days_i)
```

The default VRChat parameter shape is eight 8-bit character slots, one 8-bit mood value, and one boolean speak pulse: 73 synced bits in total.

This package contains no persistence, transcription, publication decision, or network I/O. Raw transcripts and private memory remain outside the public companion projection according to the repository privacy boundaries.
