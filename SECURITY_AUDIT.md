# ANALYTIX CLUB WEBSITE – COMPREHENSIVE APPLICATION SECURITY AUDIT & HARDENING REPORT

**Audit Date:** November 25, 2026  
**Auditor:** Application Security & Cybersecurity Engineering  
**Application Target:** Analytix Club Web Platform  
**Production Deployment URL:** https://analytix-lvij.onrender.com  
**Stack:** FastAPI (Python), Supabase (PostgreSQL, Auth, Storage), HTML5/CSS3/Vanilla ES6 JavaScript  

---

## Executive Summary

A comprehensive application security audit of the entire codebase was conducted across backend routes, authentication dependencies, role-based access control, database operations, file storage, CORS, HTTP response headers, and frontend client scripts.

A total of **10 vulnerabilities and configuration weaknesses** were identified across critical, high, medium, and low severity tiers. **All identified vulnerabilities have been remediated, patched, and verified.**

---

## Vulnerability Summary Matrix

| ID | Vulnerability Title | Severity | Affected Component | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Insecure Fallback JWT Secret & Unvalidated Token Claims | **Critical** | `backend/services/auth_service.py` | ✅ **Fixed & Verified** |
| **SEC-002** | Sensitive PII (Email & Phone) Leakage via Public Teams API | **High** | `backend/routers/members.py`, `backend/models/user.py` | ✅ **Fixed & Verified** |
| **SEC-003** | Missing Authentication Endpoint Rate Limiting (Brute Force Risk) | **High** | `backend/routers/auth.py` | ✅ **Fixed & Verified** |
| **SEC-004** | Stored XSS Risk via Unvalidated Image/Profile URLs in DOM | **High** | `backend/models/*.py`, `frontend/js/*.js` | ✅ **Fixed & Verified** |
| **SEC-005** | Missing Standard HTTP Security Headers (Clickjacking / MIME Sniffing) | **Medium** | `backend/main.py` | ✅ **Fixed & Verified** |
| **SEC-006** | Incomplete Server-Side Session Revocation on Logout | **Medium** | `backend/routers/auth.py` | ✅ **Fixed & Verified** |
| **SEC-007** | Unrestricted Storage Bucket Parameter in Storage Service | **Medium** | `backend/services/storage_service.py` | ✅ **Fixed & Verified** |
| **SEC-008** | Unbounded Field Lengths and Point Bounds in Pydantic Models | **Medium** | `backend/models/*.py` | ✅ **Fixed & Verified** |
| **SEC-009** | Flash of Unauthorized Content (FOUC) on Admin Dashboard | **Low** | `frontend/admin-dashboard.html`, `frontend/js/admin.js` | ✅ **Fixed & Verified** |
| **SEC-010** | Production CORS Allowed Origin Mismatch | **Low** | `backend/config.py` | ✅ **Fixed & Verified** |

---

## Detailed Vulnerability Analysis & Remediation

### 1. SEC-001: Insecure Fallback JWT Secret & Unvalidated Token Claims
- **Severity:** Critical
- **Affected File & Function:** `backend/services/auth_service.py` -> `AuthService.verify_token`, `AuthService.create_access_token`
- **Explanation:** 
  The token verification routine allowed decoding JWTs using a hardcoded development secret string (`"dev-only-secret-do-not-use-in-production-12345678"`) whenever running in non-production environments or if the production environment flag was omitted. Furthermore, audience validation was completely bypassed (`verify_aud: False`).
- **Potential Impact:** 
  Authentication bypass and privilege escalation. An attacker could forge an arbitrary JWT with `sub` pointing to an administrator and obtain complete unauthorized access to admin endpoints.
- **Recommended Fix:** 
  Strictly forbid fallback secrets in production. Prioritize authoritative verification via Supabase Auth API (`auth.get_user(token)`). Require token expiration and audience validation (`aud: "authenticated"`).
- **Fix Implemented & Verified:** 
  ✅ **Yes.** In `backend/services/auth_service.py`, `verify_token` enforces authoritative Supabase Auth verification. If Supabase fails or rejects the token, production rejects the token immediately. Fallback secrets are barred when running in production mode or when Supabase credentials are configured.

---

### 2. SEC-002: Sensitive PII (Email & Phone) Leakage via Public Teams API
- **Severity:** High
- **Affected File & Function:** `backend/routers/members.py` -> `get_teams_overview()`, `backend/models/user.py`
- **Explanation:** 
  The public endpoint `GET /api/members/teams` returned full `UserProfileOut` models for members of Tech, Design, and MOC teams. This included private email addresses and mobile numbers to any unauthenticated web visitor.
- **Potential Impact:** 
  Scraping and bulk collection of student emails and personal phone numbers for phishing, spam, or social engineering.
- **Recommended Fix:** 
  Create a dedicated public projection model (`PublicTeamMemberOut`) that omits `email`, `phone`, and private identifiers.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Created `PublicTeamMemberOut` in `backend/models/user.py` and applied it to `get_teams_overview()`. Unauthenticated requests only receive safe display metadata (`id`, `full_name`, `team`, `role`, `department`, `year`, `skills`, `bio`, `profile_photo`).

---

### 3. SEC-003: Missing Authentication Endpoint Rate Limiting (Brute Force Risk)
- **Severity:** High
- **Affected File & Function:** `backend/routers/auth.py` -> `login()`, `register()`, `forgot_password()`
- **Explanation:** 
  The authentication endpoints lacked rate limiting at the application layer, permitting unlimited automated attempts per second.
- **Potential Impact:** 
  Credential stuffing, password brute-forcing, registration spam, and denial of service via Supabase email quota exhaustion.
- **Recommended Fix:** 
  Implement an in-memory sliding-window IP rate limiter to throttle login, registration, and password recovery attempts.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Implemented `SlidingWindowRateLimiter` in `backend/routers/auth.py` with sliding-window thresholds (10 login attempts/min, 5 registration attempts/2 min, 5 password reset requests/2 min per IP). Exceeded limits return `429 Too Many Requests`.

---

### 4. SEC-004: Stored XSS Risk via Unvalidated Image/Profile URLs in DOM
- **Severity:** High
- **Affected File & Function:** `backend/models/user.py`, `backend/models/event.py`, `frontend/js/api.js`, `frontend/js/admin.js`, `frontend/js/events.js`, `frontend/js/member.js`, `frontend/js/profile.js`
- **Explanation:** 
  Profile photos, poster URLs, and links were accepted without URL protocol validation. Injected strings such as `javascript:alert(1)` or unescaped HTML attributes in templates like `<img src="${m.profile_photo}">` could execute arbitrary JavaScript in victim browsers (specifically administrators reviewing the member directory).
- **Potential Impact:** 
  Stored Cross-Site Scripting (XSS), administrator session hijacking, and unauthorized state changes.
- **Recommended Fix:** 
  Validate and sanitize URLs at both backend model level (requiring `https://`, `http://`, or `/assets/`) and frontend rendering layer via `API.sanitizeUrl()`.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Added `validate_safe_url` validators to `UserProfileUpdate`, `EventBase`, `HackathonBase`, and `AnnouncementBase`. Added `API.sanitizeUrl()` in `frontend/js/api.js` and applied it across all image tags in `admin.js`, `events.js`, `member.js`, and `profile.js`.

---

### 5. SEC-005: Missing Standard HTTP Security Headers (Clickjacking / MIME Sniffing)
- **Severity:** Medium
- **Affected File & Function:** `backend/main.py` -> `security_headers_middleware`
- **Explanation:** 
  FastAPI by default does not set defensive HTTP headers, leaving responses without `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, or `Permissions-Policy`.
- **Potential Impact:** 
  Clickjacking attacks (framing sensitive admin or member pages inside malicious parent sites), MIME confusion attacks, and browser feature abuse.
- **Recommended Fix:** 
  Implement an HTTP middleware that injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and HSTS.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Added `security_headers_middleware` in `backend/main.py` applying all standard defensive headers on every HTTP response.

---

### 6. SEC-006: Incomplete Server-Side Session Revocation on Logout
- **Severity:** Medium
- **Affected File & Function:** `backend/routers/auth.py` -> `logout()`
- **Explanation:** 
  The `/api/auth/logout` endpoint merely returned a static JSON message, failing to notify Supabase Auth to invalidate the session token on the server side.
- **Potential Impact:** 
  If an access token is intercepted or copied before logout, it remains valid for API calls until natural expiration even after the user logged out.
- **Recommended Fix:** 
  Forward the caller's Bearer token to Supabase Auth's `/auth/v1/logout` endpoint to formally terminate the session server-side.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Updated `logout()` in `backend/routers/auth.py` to invoke Supabase `/auth/v1/logout` with the active bearer credentials.

---

### 7. SEC-007: Unrestricted Storage Bucket Parameter in Storage Service
- **Severity:** Medium
- **Affected File & Function:** `backend/services/storage_service.py` -> `StorageService.upload_file`
- **Explanation:** 
  The storage upload service accepted an arbitrary string for the `bucket` parameter without checking against authorized buckets.
- **Potential Impact:** 
  If internal or future endpoints expose this parameter, an attacker could attempt writing into unauthorized or unintended storage buckets.
- **Recommended Fix:** 
  Enforce a strict whitelist of allowed buckets (`{"posters", "avatars", "event-photos"}`).
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Added `ALLOWED_BUCKETS = {"posters", "avatars", "event-photos"}` check in `backend/services/storage_service.py`. Any other bucket request raises `400 Bad Request`.

---

### 8. SEC-008: Unbounded Field Lengths and Point Bounds in Pydantic Models
- **Severity:** Medium
- **Affected File & Function:** `backend/models/user.py`, `backend/models/registration.py`, `backend/models/event.py`
- **Explanation:** 
  Text fields such as `full_name`, `bio`, `skills`, `description`, and `instructions` had no upper character bounds. In addition, `LeaderboardAward.points` had no upper limit, allowing arbitrary integers.
- **Potential Impact:** 
  Database memory bloat, DoS via giant payload submission, and illogical point awards.
- **Recommended Fix:** 
  Add `max_length` constraints on all string attributes and `le=1000` upper limit on point awards.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Implemented length bounds across all Pydantic models (`full_name`: 100, `bio`: 1000, `skills`: 500, `description`: 5000, `points`: 1..1000).

---

### 9. SEC-009: Flash of Unauthorized Content (FOUC) on Admin Dashboard
- **Severity:** Low
- **Affected File & Function:** `frontend/admin-dashboard.html`, `frontend/js/admin.js`, `frontend/js/auth.js`
- **Explanation:** 
  `admin-dashboard.html` rendered the DOM tree immediately before `Auth.requireAdmin()` verified permissions asynchronously via API, and waited 1 full second (`setTimeout`) before redirecting non-admins.
- **Potential Impact:** 
  Unauthorized visitors or members could briefly see admin interface structures, metrics, and tab names before the redirect fired.
- **Recommended Fix:** 
  Hide body visibility initially via CSS until `Auth.requireAdmin()` confirms authorization, and perform immediate redirect using `window.location.replace()`.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Added `<style>body { visibility: hidden; }</style>` in `admin-dashboard.html`, which is revealed only after `requireAdmin()` succeeds. Redirects now use immediate `window.location.replace()` with no delay.

---

### 10. SEC-010: Production CORS Allowed Origin Mismatch
- **Severity:** Low / Configuration
- **Affected File & Function:** `backend/config.py` -> `Settings.cors_origins`
- **Explanation:** 
  The default `ALLOWED_ORIGINS` was configured with an older Render URL (`https://analytix-644w.onrender.com`) instead of the current production domain (`https://analytix-lvij.onrender.com`).
- **Potential Impact:** 
  Legitimate browser requests from the live production site could fail with CORS preflight errors if environment variables are not set on Render.
- **Recommended Fix:** 
  Include `https://analytix-lvij.onrender.com` in the default allowed origins list in `config.py`.
- **Fix Implemented & Verified:** 
  ✅ **Yes.** Updated `ALLOWED_ORIGINS` in `backend/config.py` to include `https://analytix-lvij.onrender.com`.

---

## Role-Based Access Control (RBAC) Verification Matrix

| Role | Browse Events & Notices | Register for Events | Update Own Profile | View Team Directory | Manage Events / Hackathons | Award Points | Manage Member Roles | Access Admin Dashboard |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Public Visitor** | ✅ | ❌ | ❌ | ✅ (Safe PII) | ❌ | ❌ | ❌ | ❌ |
| **Club Member** | ✅ | ✅ | ✅ (Non-privileged) | ✅ (Safe PII) | ❌ | ❌ | ❌ | ❌ |
| **Administrator** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Conclusion & Verification Sign-Off

All identified vulnerabilities have been remediated across the application layer, authentication pipeline, model validation layer, and frontend client. Automated test suites verify that all endpoints, authorization guards, and security boundaries function as intended.
