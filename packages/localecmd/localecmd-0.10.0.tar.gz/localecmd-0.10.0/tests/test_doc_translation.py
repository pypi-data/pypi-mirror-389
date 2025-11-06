#!/usr/bin/env python3
import inspect

from localecmd.doc_translation import translate_examples, translate_parameters


def test_doc_translation():
    doc = inspect.cleandoc("""
    :::{code} python
    >>> func2(1, 2, 3, 4)

    >>> func2(1, b=4)
    :::
    """)
    tdoc = translate_examples(doc, "bla", "test.bla")
    assert tdoc == inspect.cleandoc("""
    :::{code}
    ¤ bla 1 2 3 4
    
    ¤ bla 1 -b 4
    :::
    """)


def test_parameter_translation():
    # A correct string
    s = ":param many words that must be translated name:"
    assert translate_parameters(s, "test.bla") == s  # Nothing to really translate...

    # Wrong string. Did not write param out. Should not translate, but not give error
    assert translate_parameters(":pa types name:") == ":pa types name:"

    # Wrong string. Forgot second colon. Should not translate, but not give error
    assert translate_parameters(":pa types name") == ":pa types name"
