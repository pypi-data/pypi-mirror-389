import os
import sys

# Ensure `src` directory is on sys.path for imports when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from arabic_conjugator_hmolavi import conjugate_verb, BABS


def test_past_conjugation_length():
    title, forms = conjugate_verb("فَتَحَ", tense="past")
    assert isinstance(title, str)
    assert isinstance(forms, list)
    assert len(forms) == 14
    assert all(isinstance(f, str) for f in forms)


def test_present_conjugation_length():
    # Use one of the BABS keys for present haraka
    bab_key = list(BABS.keys())[0]
    title, forms = conjugate_verb("فَتَحَ", tense="present", bab_key=bab_key)
    assert isinstance(title, str)
    assert len(forms) == 14
