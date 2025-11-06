__all__ = ["LearningMode", "DevMode", "cmps"]

cmps = {
    "browser": {
        "acceptichars",  # should we accept or ignore invisible completions like ("" or "\n", "\n    ")?
        "scon",  # should we enable shell completions?
        "triggerc", # characters or words that will trigger an inline completion.
        "triggeronaccept", # should we trigger another inline completion after accepting the current completion?
    },
}

LearningMode = {
    "name": "Learning Mode",
    # code message variables
    "c_acceptichars": False,
    "c_scon": True,
    "c_triggerc": ['#'],
    "c_triggeronaccept": True,
    # prose message variables (i.e. notes and prompts)
    "p_acceptichars": False,
    "p_scon": True,
    "p_triggerc": ['#'],
    "p_triggeronaccept": True,
}

DevMode = {
    "name": "Dev Mode",
    # code message variables
    "c_acceptichars": False,
    "c_scon": True,
    "c_triggerc": [' ', '\n', '.', ':', '(', ')', '[', ']', '{', '}', ',', ';', '"', "'", "_", '=', '+', '-', '*', '/', '%', '<', '>', '!', '|', '&', '^', '~', '#', '@', '`', '\\'],
    "c_triggeronaccept": True,
    # prose message variables (i.e. notes and prompts)
    "p_acceptichars": False,
    "p_scon": True,
    "p_triggerc": [' '],
    "p_triggeronaccept": True,
}

