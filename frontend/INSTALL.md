# Installing this drop-in into your frontend/ folder

This zip holds the real PipelinePilot UI. The `npm create vite` scaffold you
ran gave you a working toolchain and a demo page - this replaces the demo
page with the actual app.

## 1. Stop the dev server

In the terminal running `npm run dev`, press `Ctrl+C`.

## 2. Extract this zip over your `frontend/` folder

Unzip it so its contents land directly inside `frontend/` (not inside a
nested `frontend/frontend/`). It will add/replace:

```
frontend/
  index.html          (replaced)
  vite.config.js       (new)
  INSTALL.md            (this file - safe to delete after reading)
  src/
    main.jsx           (replaced)
    styles.css          (new)
    config.js            (new)
    App.jsx               (new)
    Dashboard.jsx          (new)
    api/client.js           (new)
    hooks/useSession.js      (new)
    components/...            (new - 7 files)
```

## 3. Delete the files the Vite scaffold made that we no longer use

These came from `npm create vite` and nothing imports them anymore:

```powershell
cd frontend
Remove-Item src\App.css, src\index.css -ErrorAction SilentlyContinue
Remove-Item src\assets -Recurse -ErrorAction SilentlyContinue
```

(`public\vite.svg` can stay or go - it's unused but harmless.)

## 4. No new packages needed

Everything here is built on plain `react` and `react-dom`, which the
scaffold already installed. No `npm install` of anything new.

## 5. Start the backend, then the frontend

In one terminal (your `.venv-sdk`), from the repo root:

```powershell
uvicorn web.app:app --port 8001
```

In a second terminal, from `frontend/`:

```powershell
npm run dev
```

Open `http://localhost:5173`. The chat app should load, with your live
pipeline in the left sidebar (pulled from `/pipeline` through the dev
proxy). Open `http://localhost:5173/dashboard` for the metrics page.

## 6. Two things to confirm with me before this is "done"

1. **The exact shape of `jd_breakdown` and `approval_required` events.**
   I wrote `JdPanel.jsx` and `ApprovalCard.jsx` against the field names I
   have from our spec conversation (`company`, `role`, `must_have_skills`,
   `nice_to_have_skills`, `red_flags`, `work_authorization`,
   `work_authorization_quote`, and a `tool_name` / `arguments` pair for
   approvals). Send me one real `jd_breakdown` payload and one real
   `approval_required` payload from your browser dev tools (Network tab,
   the `/chat` request, EventStream view) and I'll correct any mismatch.
2. **Where the "Pitch Note" text comes from.** Right now `PitchNote.jsx`
   only renders if `jd_breakdown.note` exists, which may not match your
   actual agent output. Tell me where that text actually comes from (a
   separate field on JDBreakdown, or just part of the assistant's chat
   reply) and I'll wire it correctly.
