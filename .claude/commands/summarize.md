Run the AI summarize CLI command with the user's input.

Use the project's CLI tool located at `backend/.venv/bin/ai-app` to summarize text.

The command pattern is:
```
backend/.venv/bin/ai-app summarize --text "<text>" --max-points <n>
```

Options:
- `--text` (required): The text to summarize
- `--max-points`: Number of key points (default: 3)
- `--word-limit`: Word limit, 0 means unlimited (default: 0)
- `--tone`: Tone style (Professional/Conversational/Technical/Academic/Creative), default: Professional

The user's message after /summarize is the input. Parse it to extract the text and options.

If the backend isn't running, remind them to run `npm run sidecar` first.

Example: `/summarize 很长的文本内容... --max-points 5`
