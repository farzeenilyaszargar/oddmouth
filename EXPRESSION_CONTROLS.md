# Oddmouth delivery scope

Updated 21 November 2026. **Explicit emotion controls have been removed at the user's request.** This replaces the previous emotion-tag specification; Git history retains that superseded proposal.

Oddmouth learns one speaker's natural narration and conversational delivery directly from recordings. Preserve phrasing, emphasis, pauses and variation in pace without emotion labels or user-selectable performance categories.

Do not implement emotion tags, emotion embeddings, emotion annotation, emotion-balanced sampling or emotion-specific tests. Naturalness and engaging delivery remain listening criteria. There is no special tag parser or span-control requirement.

Every deployed neural component is trained from random initialization on this one speaker, including the vocoder. See [the current model plan](VOICE_MODEL_PLAN.md) and [Mac training system](MAC_TRAINING_SYSTEM.md).
