from pathlib import Path, PurePosixPath


INVALID_SEGMENT_CHARACTERS = set('<>:"\\|?*')


def workspace_note_path(root: Path, title: str) -> Path:
    """Return safe Markdown path for workspace-relative note title."""
    relative = PurePosixPath(title)
    if (
        not title
        or relative.is_absolute()
        or any(
            not segment
            or segment in {".", ".."}
            or any(char in INVALID_SEGMENT_CHARACTERS for char in segment)
            for segment in relative.parts
        )
    ):
        raise ValueError("note path must remain inside workspace")

    resolved_root = root.resolve()
    candidate = (resolved_root / Path(*relative.parts)).with_suffix(".md")
    resolved_candidate = candidate.resolve(strict=False)
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError("note path must remain inside workspace")
    return candidate
