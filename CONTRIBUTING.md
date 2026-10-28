# Contributing

Thanks for trying Option Prompt. Setup reports and examples of unclear output are useful, especially from apps and Macs beyond the original setup.

## Report a problem

[Open an issue](https://github.com/Lutt999/option-prompt/issues/new/choose) with your macOS version, processor type, destination app, and steps to reproduce. For transcription or cleanup problems, include what you said and what came back using an invented example.

Keep private conversations, credentials, and personal background or glossary files out of issues and pull requests.

## Make a change

Follow the [source installation steps](README.md#get-started). Keep each pull request focused on one problem, explain the resulting behavior, and include how you checked it. For larger changes, an issue first helps establish the scope.

Before opening a pull request, run:

```sh
.venv/bin/python -m compileall -q clean.py config.py context.py dictate.py start.py
git diff --check
```

These commands check syntax and whitespace. They do not verify recording, Accessibility, or paste behavior. For changes to those paths, manually exercise the affected behavior on macOS and describe the app, permissions, and result in the pull request. For prompt changes, provide the transcript, context, and actual output from a small invented example.

Model files and personal configuration stay outside the repository. Application code is contributed under the [MIT license](LICENSE).
