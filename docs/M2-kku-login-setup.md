# M2 — KKU login setup

"Sign in with Google", restricted to @kku.ac.th. The restriction is one server-side
domain check — that single check is the whole gate.

## 0. Confirm first (ask KKU IT — digital.kku.ac.th)
- [ ] Do faculty @kku.ac.th sign in via GOOGLE or MICROSOFT?
      Google -> follow this as written. Microsoft -> identical shape, swap provider
      to Entra ID and restrict to the KKU tenant; keep the same domain check.

## 1. Your part — register the app (Google Cloud Console)
Only you can do this; it produces two secrets the code needs.
1. console.cloud.google.com -> create / select a project.
2. OAuth consent screen:
   - BEST: set it to "Internal" within KKU's Workspace -> auto-limits to KKU accounts
     (needs the project inside KKU's org; usually an IT admin). Keep the code check too.
   - FALLBACK: "External" + rely on the server-side domain check below.
3. Credentials -> Create OAuth client ID -> "Web application".
4. Authorized redirect URIs:
   - dev:  http://localhost:8000/auth/callback
   - prod: https://<your-domain>/auth/callback   (add later)
5. Copy Client ID + Client Secret into .env (never commit):
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   SESSION_SECRET=...            # random string for signing the session cookie
   ALLOWED_EMAIL_DOMAIN=kku.ac.th

## 2. Claude Code's part — the build prompt
"Build M2. Add 'Sign in with Google' using OAuth (Authlib on the FastAPI backend).
On the callback, verify the Google ID token, reject any email whose domain isn't
kku.ac.th, then issue a signed HTTP-only session cookie. Add a dependency that guards
every /api route so unauthenticated or non-KKU users get 401. Read client id/secret
and the allowed domain from env. Write the test first using a mocked Google response."

## 3. Security checklist (verify after the build)
- [ ] Domain check runs on the BACKEND, against the token Google signed — never the browser.
- [ ] hd=kku.ac.th is sent to Google (UX hint only; the server check is the real gate).
- [ ] email_verified == true is required.
- [ ] Session is a signed, HTTP-only cookie; only email + name stored.
- [ ] Non-KKU and logged-out requests to /api/* get 401.
- [ ] Secrets come from .env only; .env is gitignored.

## The flow (for reference)
click -> Google login (KKU account) -> approve -> Google returns a one-time code
 -> backend swaps code for verified email+name -> domain == kku.ac.th?
 -> yes: set session cookie   |   no: reject
Every protected route checks the session cookie.
