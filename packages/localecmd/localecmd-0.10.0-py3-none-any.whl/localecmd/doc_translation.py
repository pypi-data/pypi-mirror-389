#!/usr/bin/env python3

import re

from localecmd.localisation import _, d_, f_


def _translate_parameter(match: re.Match, fullname: str = "") -> str:
    """
    Translate parameter info into other language

    :param match re.Match: Object containing the expression match with the example
    :param str fullname: Full function name
    """
    s = match[0].strip(":").split()

    new_param_string = ":"
    for typ in s[0:-1]:
        new_param_string += d_(typ) + " "
    new_param_string += f_(fullname, s[-1]) + ":"

    return new_param_string


def translate_parameters(s: str, fullname: str = ""):
    """
    Translate parameters and types in the parameters section of a doctring

    :param str s: docstring to translate
    :type s: str
    :param str fullname: Full name of function. Used to call
    {py:func}`~zfp.cli.localisation.f_`. defaults to ""
    :return: Translated docstring
    :rtype: str

    """
    out = re.sub(r":param.*:", lambda x: _translate_parameter(x, fullname), s)
    return out


def _translate_example(match: re.Match, translated_name: str, fullname: str) -> str:
    """Translates python code example to prgram script in correct language

    :param match re.Match: Object containing the expression match with the example
    :param str translated_name: Translated name of function
    :param str fullname: Full function name

    """
    s = match[0].strip("").strip(")").split("(")[1].split(",")

    new_param_string = _("¤ ") + translated_name
    for arg in s:
        arg = arg.strip()
        if re.fullmatch(r"^\S+\s*=\s*\S+$", arg):
            # Keyword argument
            key, val = (s.strip() for s in arg.split("="))
            key = f_(fullname, key)
            new_param_string += " " + "-" + key + " " + val
        else:  # Positional argument. Not checked for bad or wrong style.
            val = arg.strip()
            new_param_string += " " + val

    return new_param_string + ""


def _translate_examples(match: re.Match, translated_name: str, fullname: str) -> str:
    """Translates python code block to program script

    :param match re.Match: Object containing the expression match with the code block
    :param str translated_name: Translated name of function
    :param str fullname: Full name of function. Used to translate keyword arguments
    {py:func}`~zfp.translate.translate.f_`.
    """
    # Replace python with nothing
    sub = re.sub(r":::{code}\s*python", ":::{code}", match[0])

    def sub_func(x):
        return _translate_example(x, translated_name, fullname)

    return re.sub(r">>> .*", sub_func, sub)


def translate_examples(doc: str, translated_name: str, fullname: str) -> str:
    """Translates python code block to program script

    :param match re.Match: Object containing the expression match with the code block
    :param str translated_name: Translated name of function
    :param str fullname: Full name of function. Used to translate keyword arguments
    {py:func}`~zfp.translate.translate.f_`.
    """

    def sub_func(x):
        return _translate_examples(x, translated_name, fullname)

    out = re.sub(r":::{code}[\w\W]*python[\w\W]*\n[^\n]*:::", sub_func, doc)
    return out
