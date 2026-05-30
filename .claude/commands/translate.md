Run the AI translate CLI command with the user's input.

Use the project's CLI tool located at `backend/.venv/bin/ai-app` to translate text.

The command pattern is:
```
backend/.venv/bin/ai-app translate --text "<text>" --from <source_lang> --to <target_lang>
```

Options:
- `--text` (required): The text to translate
- `--from` (required): Source language code (e.g. zh, en, ja)
- `--to` (required): Target language code
- `--tone`: Tone style (Professional/Conversational/Technical/Academic/Creative), default: Professional

The user's message after /translate is the input. Parse it to extract:
1. The text to translate
2. Source and target languages

If the user doesn't specify --from/--to, ask them. If the backend isn't running, remind them to run `npm run sidecar` first.

Example: `/translate Hello --from en --to zh`
