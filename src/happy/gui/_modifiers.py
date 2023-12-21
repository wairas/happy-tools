def remove_modifiers(state):
    """
    Removes NUMLOCK and CAPSLOCK from the keyboard state.
    # modifiers: https://tkdocs.com/shipman/event-handlers.html

    :param state: the keyboard state to "clean"
    :return: the cleaned staet
    """
    state = state
    # remove NUMLOCK
    state &= ~0x0010
    # remove CAPSLOCK
    state &= ~0x0002
    return state
