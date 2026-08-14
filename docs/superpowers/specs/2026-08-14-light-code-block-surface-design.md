# Light Code-Block Surface Design

## Goal

Make code blocks easier to distinguish from the page background in Flatnotes'
light theme.

## Behavior

Apply the neutral `#e7e5e4` background to Toast UI rendered `pre` blocks in
the light theme. The rule covers reader and WYSIWYG views, which both render
their code blocks through Toast UI contents markup.

The Markdown source editor and all dark-theme styling remain unchanged.

## Verification

Extend the existing frontend stylesheet test to assert the light-theme code
block selector and its exact background color. Run the frontend test suite and
production build after the CSS change.
