def json_to_prompt(objects: list[dict]) -> str:
    return (
        """The following is a consultation list. Each consultation includes a title,"""
        + """a domain, a summary and contributions. Write a short summary highlighting thei main concerns from contributions."""
        + ":\n"
        + "\n\n".join(objects)
    )
