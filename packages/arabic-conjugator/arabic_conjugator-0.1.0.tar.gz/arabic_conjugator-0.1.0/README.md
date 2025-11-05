# Arabic Conjugator

Small Python package providing functions to parse Arabic three-letter roots with harakat and generate conjugations for past and present tenses.

Usage example

```python
from arabic_conjugator import conjugate_verb

title, forms = conjugate_verb("فَتَحَ", tense="past")
print(title)
for f in forms:
    print(f)
```

License: MIT
