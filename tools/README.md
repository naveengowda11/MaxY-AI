# Stage 4 — Safe Actions

This milestone adds a registered local tool set and an explicit approval boundary.

## Available actions
- `launch_app`: Notepad, Calculator, Paint, or File Explorer (fixed Windows executable mapping).
- `list_files`: list names in the MAXY workspace.
- `search_files`: find names inside the workspace.
- `read_text_file`: UTF-8 text files, selected extensions, maximum 1 MB.

Place files to inspect inside the `workspace/` folder. MAXY cannot browse your entire drive in this stage.

## Approval flow
1. Select an action in the Safe actions panel.
2. MAXY prepares a preview; nothing is executed.
3. Review the target and type `APPROVE`.
4. Approval is exact, single-use, and expires in 90 seconds.
5. The execution result is written to SQLite's local audit table.

API routes are `GET /api/tools`, `POST /api/tools/proposals`, and `POST /api/tools/proposals/{id}/approve`.

Never add an unrestricted shell tool or execute model-generated commands. The API must remain bound to localhost. Browser automation, conversational tool routing, and Android access are future work.
