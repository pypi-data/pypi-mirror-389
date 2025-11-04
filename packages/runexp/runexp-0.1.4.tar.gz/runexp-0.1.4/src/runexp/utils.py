def unexpected_error(identifier: str, /):
    return AssertionError(
        f"unexpected error ({identifier}), please file an issue at "
        "https://github.com/maxime915/runexp/issues"
    )
