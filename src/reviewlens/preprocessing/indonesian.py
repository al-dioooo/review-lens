from __future__ import annotations

from functools import lru_cache

from Sastrawi.Stemmer.Stemmer import Stemmer
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

from reviewlens.config import PreprocessingConfig
from reviewlens.preprocessing.cleaner import _TOKEN
from reviewlens.preprocessing.slang import load_slang_map


@lru_cache(maxsize=1)
def default_stopwords() -> frozenset[str]:
    factory = StopWordRemoverFactory()
    return frozenset(word.lower() for word in factory.get_stop_words())


@lru_cache(maxsize=1)
def default_stemmer() -> Stemmer:
    return StemmerFactory().create_stemmer()


def model_tokens(text: str, config: PreprocessingConfig) -> list[str]:
    slang = load_slang_map(config.extra_slang) if config.normalize_slang else {}
    tokens = [slang.get(token, token) for token in _TOKEN.findall(text)]
    if config.remove_stopwords:
        protected = set(config.protected_negations)
        stopwords = (set(default_stopwords()) | set(config.extra_stopwords)) - protected
        tokens = [token for token in tokens if token not in stopwords]
    if config.stem:
        stemmer = default_stemmer()
        tokens = [stemmer.stem(token) for token in tokens]
    return [token for token in tokens if token]
