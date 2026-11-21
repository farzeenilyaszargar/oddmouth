"""Deterministic text -> IPA -> token frontend. No learned weights.

The symbol table is fixed (not fitted to a corpus) so token ids stay stable
across data preparation runs, checkpoints and browser export.
"""
import os
from pathlib import Path
import re

import torch

PAD, BLANK, UNK = 0, 1, 2
_PUNCTUATION = ';:,.!?¡¿—…"«»“”\'-() '
_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
_IPA = ('ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃ'
        'ˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘̩ᵻ')
SYMBOLS = list(dict.fromkeys(_PUNCTUATION + _LETTERS + _IPA))
SYMBOL_VERSION = 'oddmouth-ipa-v1'
INDEX = {s: i + 3 for i, s in enumerate(SYMBOLS)}
VOCAB_SIZE = len(SYMBOLS) + 3


def _espeak():
    lib = Path('/opt/homebrew/opt/espeak-ng/lib/libespeak-ng.dylib')
    if lib.exists():
        os.environ.setdefault('PHONEMIZER_ESPEAK_LIBRARY', str(lib))


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


def phonemize(texts):
    """List of strings -> list of IPA strings (espeak-ng en-us, stress kept)."""
    _espeak()
    from phonemizer import phonemize as run
    from phonemizer.separator import Separator
    return run([clean(t) for t in texts], language='en-us', backend='espeak', strip=True,
               preserve_punctuation=True, with_stress=True, njobs=1,
               separator=Separator(phone='', word=' ', syllable=''))


def encode(ipa, unknown=None):
    """IPA string -> token ids with a blank between every symbol."""
    ids = [BLANK]
    for char in ipa:
        token = INDEX.get(char, UNK)
        if token == UNK and unknown is not None:
            unknown[char] = unknown.get(char, 0) + 1
        ids += [token, BLANK]
    return torch.tensor(ids, dtype=torch.long)
