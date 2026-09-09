# Scorpio Octavious Vibe (SOV)

Scorpio Octavious Vibe (SOV) is a social and rewards platform designed to combine social features, user accounts, an SOV wallet, verified offerwall rewards, referrals, withdrawals, and advertising/boost campaigns.

The project is built around a mobile Android application and a backend API. The backend is responsible for authentication, wallet operations, reward verification, transaction records, fees, withdrawals, and administrative controls.

> **Important:** This README documents the intended production architecture. Provider credentials, signing secrets, private keys, and administrator credentials must never be committed to GitHub.

---

## 1. Project Goals

Scorpio Octavious Vibe is designed to provide:

- User registration and login
- User profiles
- Social feed
- Photos and videos
- Likes, comments, views, and interactions
- Friends and direct messaging
- SOV wallet
- SOV send and receive
- Transaction history
- Verified earning opportunities
- Tapjoy offerwall integration
- Referral rewards
- Withdrawal requests
- A 10% transaction/withdrawal fee where configured
- Admin fee tracking
- Boost Ads
- Payment verification
- Notifications
- Security controls
- Backend-controlled reward verification

The primary monetization flow is:

```text
Offer Provider
     ↓
Tapjoy / Offerwall
     ↓
SOV Backend
     ↓
Verify Callback
     ↓
Prevent Duplicate Reward
     ↓
Credit User Wallet
     ↓
User Sees Verified SOV Balance
     ↓
Withdrawal / Transfer
     ↓
Configured Fee → Admin Account
```

---

# 2. High-Level Architecture

```text
┌───────────────────────────────┐
│       SOV Android App         │
│                               │
│ Login / Signup                │
│ Profile / Feed                │
│ Wallet / Earnings             │
│ Offerwall / Rewards           │
│ Send / Receive                │
│ Withdrawal                    │
│ Boost Ads                     │
└───────────────┬───────────────┘
                │ HTTPS
                ▼
┌───────────────────────────────┐
│       SOV Backend API         │
│          Flask                │
│                               │
│ Authentication               │
│ JWT                           │
│ Wallet                        │
│ Transactions                  │
│ Tapjoy Callback               │
│ Reward Verification           │
│ Withdrawals                   │
│ Admin                         │
│ Offerwall Statistics          │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          Database             │
│          SQLite*              │
│                               │
│ Users                         │
│ Transactions                  │
│ Rewards                       │
│ Offerwall Events              │
│ Admin Fees                    │
└───────────────────────────────┘

*Use a production database such as PostgreSQL when scaling beyond a
small/test deployment.
```

---

# 3. Repository Structure

A recommended repository layout is:

```text
Scorpio-Octavious-Vibe/
│
├── android/
│   ├── app/
│   │   ├── src/
│   │   │   └── main/
│   │   │       ├── java/
│   │   │       ├── res/
│   │   │       └── AndroidManifest.xml
│   │   ├── build.gradle.kts
│   │   └── proguard-rules.pro
│   │
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   └── gradlew
│
├── backend/
│   ├── sovbackendserver.py
│   ├── requirements.txt
│   ├── offerwall.py
│   ├── offerwall_route.py
│   ├── auth.py
│   ├── withdrawal.py
│   ├── admin.py
│   ├── SOV_network.py
│   ├── SOV_transactions.py
│   └── database/
│
├── README.md
└── .gitignore
```

The exact names can differ from the current working project. Keep only one production entry point for the backend to avoid accidentally deploying an obsolete server file.

---

# 4. Android Application

The Android application is the client layer.

It should communicate with the backend over HTTPS rather than directly modifying wallet balances.

## Main application areas

### Authentication

- Signup
- Login
- Logout
- Session/token handling
- Account restoration

### Profile

- Username
- Profile information
- Profile media
- Account settings

### Social

- Feed
- Posts
- Photos
- Videos
- Likes
- Comments
- Views
- Friends
- Direct messages

### Wallet

- SOV balance
- Send
- Receive
- Transaction history
- Withdrawal request

### Earnings

- Offerwalls
- Games
- Referral rewards
- Daily rewards where configured

### Advertising

- Boost Ads
- Campaign selection
- Campaign payment
- Campaign status

### Security

Possible controls include:

- Email verification
- Phone verification
- Two-factor authentication
- Wallet PIN
- Biometric authentication
- Login activity
- Device management

Security features should only be presented as active when their backend implementation is actually complete.

---

# 5. Backend API

The backend is a Flask API.

Production deployment is intended for a service such as Render.

Example production base URL:

```text
https://scorpio-octavious-vibe-api.onrender.com
```

Do not hardcode secrets into the Android application.

---

# 6. Health Check

The backend should provide a health endpoint:

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

Use this endpoint to confirm that the deployed backend is responding.

---

# 7. Authentication

Authentication should be handled by the backend.

Typical endpoints:

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

The backend should issue a JWT after successful authentication.

The Android app should store the token securely and send it using:

```http
Authorization: Bearer <JWT>
```

Never put JWT signing secrets inside the Android APK.

---

# 8. Wallet

The SOV wallet is controlled by the backend.

Typical operations include:

```text
GET  /api/wallet/balance
POST /api/wallet/send
GET  /api/wallet/history
POST /api/wallet/withdraw
```

The client must not be trusted to calculate or authorize wallet balances.

Example:

```text
Android App
     ↓
POST /api/wallet/send
     ↓
Backend validates:
- JWT
- sender
- recipient
- amount
- balance
- fee
     ↓
Database transaction
     ↓
Wallet balances updated
     ↓
Transaction recorded
```

---

# 9. 10% Fee

The configured SOV transaction/withdrawal fee is intended to be:

```text
10%
```

Example:

```text
User requests: 100 SOV

Fee:           10 SOV
Net amount:    90 SOV
```

The exact fee rules should be controlled by the backend.

The fee must never be calculated only by the Android client.

The backend should record:

```text
gross amount
fee
net amount
transaction type
sender/user
recipient/destination
timestamp
status
```

---

# 10. Tapjoy Offerwall

Tapjoy is intended to provide earning opportunities.

The general flow is:

```text
User opens Earnings
        ↓
Tapjoy Offerwall
        ↓
User completes eligible offer
        ↓
Tapjoy sends server callback
        ↓
SOV Backend verifies callback
        ↓
Backend checks duplicate reward
        ↓
Reward is credited
        ↓
Transaction/reward record created
        ↓
Android app refreshes wallet
```

The user should never be able to create a reward simply by sending a request from the Android application.

---

# 11. Tapjoy Callback

The intended production callback endpoint is:

```text
GET /api/tapjoy/callback
```

Full callback URL:

```text
https://scorpio-octavious-vibe-api.onrender.com/api/tapjoy/callback
```

The callback should be configured in the Tapjoy dashboard using the actual production URL.

The backend must verify the callback before crediting a reward.

---

# 12. Tapjoy Security

Tapjoy credentials and callback secrets are private.

Use environment variables such as:

```text
JWT_SECRET
TAPJOY_SECRET
OFFERWALL_SECRET
```

Do not commit:

```text
.env
```

or real secret values to GitHub.

A secret should look like this in documentation:

```text
TAPJOY_SECRET=<your-private-secret>
```

not:

```text
TAPJOY_SECRET=real-secret-value
```

---

# 13. Duplicate Reward Protection

A reward callback may be delivered more than once.

The backend must therefore identify previously processed rewards.

A reward record should contain a provider transaction/event identifier where available.

The logic should be:

```text
Receive callback
       ↓
Verify signature/verifier
       ↓
Find reward/event ID
       ↓
Already processed?
   ┌───────┴───────┐
   │               │
  YES              NO
   │               │
Return success     Credit reward
without credit     Record event
again               ↓
                    Return success
```

This prevents accidental double-crediting.

---

# 14. Tapjoy Reward Verification

The backend should verify the provider's callback before changing a user's balance.

For the classic Tapjoy self-managed currency callback, the verifier is based on the callback values and the private Tapjoy secret.

Conceptually:

```text
verifier =
MD5(id + ":" + snuid + ":" + currency + ":" + secret)
```

The exact implementation must match the current Tapjoy configuration and documentation.

Never expose the secret to the Android app.

---

# 15. Stable User Identification

The Tapjoy user identifier should correspond to a stable SOV user/account identifier.

Do not use:

- Phone number
- Random ID generated every launch
- Password
- Private API key
- Backend secret

The goal is for:

```text
SOV user
     ↕
Tapjoy user identity
```

to remain consistent.

---

# 16. Reward Accounting

Tapjoy rewards should be credited separately from the normal SOV transfer/withdrawal fee.

Example:

```text
Tapjoy reward:
+100 SOV

Wallet:
+100 SOV
```

The 10% fee should not automatically reduce the incoming Tapjoy reward unless a specific reward policy says otherwise.

When the user later performs a fee-bearing transfer or withdrawal:

```text
100 SOV
10% fee
90 SOV net
```

---

# 17. Reward History

The application should display verified reward history.

Recommended fields:

```text
Provider
Offer/Event
Reward
Currency
Status
Transaction ID
Date
```

Possible statuses:

```text
verified
pending
rejected
duplicate
```

Only verified rewards should increase the spendable wallet balance.

---

# 18. Referral System

The platform can support referral rewards.

Example:

```text
User A
   ↓
Referral link/code
   ↓
User B registers
   ↓
User B completes qualifying activity
   ↓
Backend validates referral
   ↓
Referral reward credited
```

Referral rewards should be protected against:

- Self-referrals
- Duplicate accounts
- Repeated rewards
- Fraudulent activity

Referral balances should be controlled by the backend.

---

# 19. Withdrawals

The withdrawal process should be backend controlled.

Recommended flow:

```text
User selects Withdraw
        ↓
Select amount
        ↓
Select cryptocurrency/network
        ↓
Enter destination address
        ↓
Backend validates request
        ↓
Check balance
        ↓
Calculate fee
        ↓
Create withdrawal record
        ↓
Admin/security review
        ↓
Approved
        ↓
Payment sent
        ↓
Completed
```

Possible withdrawal statuses:

```text
pending
under_review
approved
sent
completed
rejected
```

The backend should validate:

- Minimum amount
- Maximum amount
- Available balance
- Fee
- Network
- Destination address
- User account
- Fraud/security conditions

---

# 20. Withdrawal Security

Do not allow the Android application to directly mark a withdrawal as completed.

Only trusted backend/admin/payment systems should be able to change payment status.

A withdrawal should have a unique ID.

Example:

```text
WD-2026-000001
```

The exact ID format can be different.

---

# 21. Admin Dashboard

The administrator area should provide controlled access to management functions.

Possible features:

```text
Users
Wallets
Transactions
Rewards
Offerwall events
Withdrawals
Fees
Boost campaigns
Payments
Statistics
Security logs
```

Admin-only endpoints should require authentication and authorization.

---

# 22. Administrator Privacy

The administrator's private email/account credentials must never be displayed to ordinary users.

Do not expose admin credentials in:

- Android source code
- API responses
- Public GitHub files
- Logs
- Screenshots
- Client-side JavaScript
- README files

Use environment variables and backend authorization.

---

# 23. Offerwall Providers

The platform can later support additional offerwall providers.

Recommended architecture:

```text
Provider
   ↓
Provider Callback
   ↓
Verification Layer
   ↓
Reward Service
   ↓
SOV Wallet
```

Each provider should have its own:

```text
callback verification
provider event ID
duplicate protection
reward mapping
logging
```

Do not trust a provider callback until its authenticity has been verified.

---

# 24. Boost Ads

The platform can offer paid Boost Ads.

Example packages:

| Package | Views | Price |
|---|---:|---:|
| Starter | 2,500 | $6 |
| Growth | 4,500 | $8 |
| Pro | 100,000 | $15 |
| Ultimate | 300,000 | $25 |

These are configuration examples and should be changed according to the actual business pricing.

The backend should track:

```text
Campaign ID
User
Post/media
Requested views
Delivered views
Price
Payment status
Campaign status
Start time
End time
Invalid traffic
Completion
```

---

# 25. Boost Payment Flow

Recommended payment architecture:

```text
User chooses Boost package
        ↓
Backend creates campaign
        ↓
Payment checkout
        ↓
Payment provider confirms payment
        ↓
Backend verifies payment
        ↓
Campaign activated
        ↓
Views delivered
        ↓
Campaign completed
```

Do not activate a paid campaign based only on a client-side success message.

---

# 26. PayPal

If PayPal is used for Boost Ads or other payments:

```text
Android App
     ↓
Backend creates checkout/order
     ↓
PayPal
     ↓
User approves
     ↓
Backend verifies/captures payment
     ↓
Campaign activated
```

The PayPal secret must remain on the backend.

Never put PayPal private credentials inside the APK.

---

# 27. Database

The development backend may use SQLite.

Typical tables include:

```text
users
transactions
tapjoy_rewards
offerwall_events
admin_fees
```

As the application grows, use a production database such as PostgreSQL rather than relying on a local SQLite file on an ephemeral hosting service.

Important production rule:

> Do not assume a local filesystem database on a cloud service is permanent.

---

# 28. Environment Variables

The backend should use environment variables for secrets and configuration.

Example:

```text
JWT_SECRET=<private-jwt-secret>
TAPJOY_SECRET=<private-tapjoy-secret>
OFFERWALL_SECRET=<private-offerwall-secret>
PORT=5000
```

Additional provider credentials can be added later:

```text
PAYPAL_CLIENT_ID
PAYPAL_CLIENT_SECRET
PAYPAL_WEBHOOK_SECRET
```

Never commit real values.

---

# 29. Python Requirements

A typical `requirements.txt` may include:

```text
Flask
PyJWT
gunicorn
```

Add only the packages actually used by the deployed backend.

Install with:

```bash
pip install -r requirements.txt
```

---

# 30. Running the Backend Locally

From the backend directory:

```bash
python sovbackendserver.py
```

or, for a production-style Flask deployment:

```bash
gunicorn sovbackendserver:app
```

The local API can normally be tested at:

```text
http://127.0.0.1:5000
```

The exact port is controlled by the application's configuration.

---

# 31. Render Deployment

The backend can be deployed to Render.

Typical setup:

```text
Build Command:
pip install -r requirements.txt

Start Command:
gunicorn sovbackendserver:app
```

Set environment variables in Render rather than committing them to GitHub.

After deployment, test:

```text
GET /health
```

The service should return a successful health response.

---

# 32. Android Build Environment

The clean Android project was generated with a modern Gradle setup.

The known clean project configuration includes:

```text
Gradle:       8.12.0
Kotlin:       1.9.24
compileSdk:   35
targetSdk:    35
minSdk:       27
```

The clean project is located in the working environment at:

```text
/storage/internal_new/project/octavious
```

This clean project is preferable to continuing with an outdated Gradle 6.1.1 setup.

---

# 33. Android Build

From the Android project:

```bash
cd /storage/internal_new/project/octavious
```

Check Gradle:

```bash
./gradlew --version
```

Build debug APK:

```bash
./gradlew assembleDebug
```

The generated APK is normally under:

```text
app/build/outputs/apk/debug/
```

For a release build, configure signing before distributing it publicly.

---

# 34. Tapjoy Android SDK

When integrating the current Tapjoy Android SDK, use the SDK version and installation instructions supported by Tapjoy at the time of integration.

The dependency previously targeted for this project was:

```text
com.tapjoy:tapjoy-android-sdk:14.4.0
```

The Android application also requires internet access:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

Do not assume an SDK version remains current forever. Check Tapjoy's official documentation before production release.

---

# 35. Android → Backend Security

The Android application is an untrusted client.

Never trust:

```text
wallet amount
reward amount
admin status
withdrawal approval
payment success
offer completion
```

when those values originate from the client.

The backend must independently verify important operations.

---

# 36. API Authentication Example

A protected request should look conceptually like:

```http
GET /api/wallet/balance
Authorization: Bearer YOUR_JWT
```

The Android app should not send:

```text
admin=true
```

and expect the backend to trust it.

Authorization must be determined from the authenticated server-side account.

---

# 37. Error Handling

The API should return useful HTTP status codes.

Example:

```text
200  Success
201  Created
400  Invalid request
401  Authentication required
403  Forbidden / invalid verification
404  Not found
409  Duplicate/conflict
429  Rate limited
500  Server error
```

Avoid returning private implementation details or secrets in error messages.

---

# 38. Logging

Backend logs should help diagnose:

- Authentication failures
- Reward callbacks
- Duplicate callbacks
- Wallet transactions
- Withdrawal requests
- Payment events
- Server errors

Never log:

```text
passwords
JWT secrets
Tapjoy secrets
PayPal secrets
private keys
wallet private keys
```

---

# 39. Rate Limiting and Abuse Protection

Before large-scale public launch, add protection against automated abuse.

Recommended areas:

```text
Login
Signup
Password reset
Reward callbacks
Withdrawal requests
Wallet transfers
Referral creation
Boost creation
```

Provider callbacks should also be verified before being accepted.

---

# 40. Production Checklist

Before monetizing with real users:

### Backend

- [ ] Production backend deployed
- [ ] HTTPS enabled
- [ ] Health endpoint working
- [ ] JWT secret configured
- [ ] Tapjoy secret configured
- [ ] Database persistence configured
- [ ] Reward duplicate protection tested
- [ ] Wallet transactions tested
- [ ] Fee calculation tested
- [ ] Withdrawal validation tested
- [ ] Admin authorization tested
- [ ] Error handling tested
- [ ] Rate limiting/security reviewed

### Android

- [ ] App builds successfully
- [ ] Login works
- [ ] Signup works
- [ ] Wallet connects to backend
- [ ] Balance refresh works
- [ ] Send works
- [ ] Receive works
- [ ] History works
- [ ] Earnings screen works
- [ ] Tapjoy SDK integrated
- [ ] Correct SOV user ID supplied to Tapjoy
- [ ] Offer completion tested
- [ ] Backend reward callback tested
- [ ] Reward appears in wallet
- [ ] Duplicate reward test passes
- [ ] Withdrawal request works
- [ ] 10% fee is displayed correctly
- [ ] Admin cannot be exposed to normal users

### Publishing

- [ ] App name finalized
- [ ] Icon finalized
- [ ] Privacy policy
- [ ] Terms of service
- [ ] App screenshots
- [ ] Store description
- [ ] Content rating
- [ ] Data safety declarations
- [ ] Release signing
- [ ] Production API URL
- [ ] Real provider credentials configured

---

# 41. Testing the Monetization Foundation

A safe test sequence is:

```text
1. Create test user
2. Log in
3. Open wallet
4. Confirm zero/starting balance
5. Open offerwall
6. Complete a test/eligible offer
7. Wait for provider callback
8. Backend verifies callback
9. Backend creates reward record
10. Wallet balance increases
11. Repeat same callback
12. Balance must NOT increase again
13. Request withdrawal
14. Backend calculates fee
15. Confirm transaction record
16. Check admin fee record
```

This is the minimum end-to-end path that should be proven before calling the monetization foundation production-ready.

---

# 42. What the Monetization Foundation Does

The monetization foundation is not just an offerwall screen.

It consists of:

```text
Provider
   ↓
Verified callback
   ↓
Reward processing
   ↓
Duplicate protection
   ↓
Wallet credit
   ↓
Transaction record
   ↓
User balance
   ↓
Withdrawal/transfer
   ↓
Fee tracking
```

If one of these critical parts is missing, monetization is not fully production-ready.

---

# 43. Scaling Toward 5,000+ Users/Callbacks

The backend can be designed to process thousands of callback events, but the application cannot force an offer provider to generate a specific number of offers or completed offers.

For higher traffic:

- Use PostgreSQL
- Add database indexes
- Use atomic wallet updates
- Add idempotency
- Add rate limiting
- Add structured logging
- Add monitoring
- Use background jobs where appropriate
- Keep provider callbacks fast
- Separate reward processing from heavy work
- Back up production data
- Monitor failed callbacks

---

# 44. Security Rules

### Never commit

```text
.env
*.pem
*.key
private credentials
provider secrets
database passwords
signing keys
```

### Never trust the client

The backend must verify:

```text
identity
balance
reward
fee
withdrawal
payment
admin authorization
```

### Never expose

```text
JWT_SECRET
TAPJOY_SECRET
PAYPAL_CLIENT_SECRET
database credentials
admin credentials
private keys
```

---

# 45. GitHub `.gitignore`

Recommended entries:

```gitignore
# Environment
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/

# Databases
*.db
*.sqlite
*.sqlite3

# Android
.gradle/
build/
**/build/
local.properties
*.apk
*.aab

# IDE
.idea/
*.iml

# Secrets
*.pem
*.key
*.jks

# Logs
*.log
```

Do not ignore files that are required for the source repository.

---

# 46. Example `.env.example`

Create a template containing names only:

```text
JWT_SECRET=CHANGE_ME
TAPJOY_SECRET=CHANGE_ME
OFFERWALL_SECRET=CHANGE_ME
PORT=5000
```

This file is safe to commit because it contains no real secrets.

---

# 47. API Development Principles

The backend should follow these principles:

1. Validate every input.
2. Authenticate protected requests.
3. Authorize admin operations.
4. Verify external provider callbacks.
5. Prevent duplicate rewards.
6. Use atomic wallet updates.
7. Record transactions.
8. Keep secrets server-side.
9. Use HTTPS in production.
10. Log important events without logging secrets.

---

# 48. Current Monetization Architecture

The intended SOV monetization architecture is:

```text
                 ┌──────────────┐
                 │   Tapjoy     │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ SOV Backend  │
                 │ Verification│
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ SOV Wallet   │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌─────────────┐     ┌─────────────┐
       │   Transfer  │     │ Withdrawal  │
       └──────┬──────┘     └──────┬──────┘
              │                   │
              └─────────┬─────────┘
                        ▼
                 ┌──────────────┐
                 │  10% Fee     │
                 │ Admin Record │
                 └──────────────┘
```

---

# 49. Development Roadmap

## Phase 1 — Foundation

- [x] Android project
- [x] Backend foundation
- [x] Authentication foundation
- [x] Wallet foundation
- [x] Transaction foundation
- [x] Admin foundation
- [x] Render deployment foundation

## Phase 2 — Monetization

- [ ] Final Android/backend connection
- [ ] Tapjoy SDK integration
- [ ] Tapjoy placement configuration
- [ ] Callback verification
- [ ] Duplicate protection
- [ ] Reward-to-wallet testing
- [ ] Reward history
- [ ] Withdrawal end-to-end testing

## Phase 3 — Payments

- [ ] Payment provider integration
- [ ] Boost Ads checkout
- [ ] Payment verification
- [ ] Campaign activation
- [ ] Campaign tracking

## Phase 4 — Production

- [ ] Production database
- [ ] Security audit
- [ ] Rate limiting
- [ ] Monitoring
- [ ] Backup strategy
- [ ] Privacy policy
- [ ] Terms
- [ ] Store release
- [ ] Production testing

---

# 50. Troubleshooting

## Backend does not start

Check:

```bash
python --version
pip install -r requirements.txt
python sovbackendserver.py
```

Check the Render logs if deployed.

---

## Health endpoint fails

Verify:

```text
https://scorpio-octavious-vibe-api.onrender.com/health
```

If it fails:

1. Check Render deployment logs.
2. Check the start command.
3. Check Python dependencies.
4. Check environment variables.
5. Confirm the Flask app variable is named correctly.

---

## Tapjoy reward does not appear

Check in order:

```text
Tapjoy offer completed
        ↓
Correct SOV user ID
        ↓
Callback sent
        ↓
Callback reaches Render
        ↓
Verifier valid
        ↓
Reward not already processed
        ↓
User exists
        ↓
Wallet credit succeeds
```

Check backend logs for the callback.

Do not manually add rewards to the production wallet to hide a callback problem.

---

## Reward appears twice

Check the provider event/transaction ID and ensure the backend has a unique/idempotent reward check.

The same provider event must never credit the wallet twice.

---

## Android cannot connect

Check:

- API base URL
- HTTPS
- Internet permission
- Render service status
- JWT token
- endpoint path
- JSON request format

---

# 51. Production Philosophy

Scorpio Octavious Vibe should treat the Android application as the user interface and the backend as the authority.

```text
Android:
Display + user interaction

Backend:
Trust + verification + accounting

Database:
Persistent records
```

The most important rule is:

> **Never allow the client to decide how much money or SOV a user has.**

---

# 52. License

Choose and add an appropriate license before making the repository public.

If the project is intended to remain proprietary, do not add an open-source license that grants rights you do not intend to grant.

---

# 53. Disclaimer

Scorpio Octavious Vibe is a software project. Availability, rewards, advertising revenue, offerwall earnings, payment processing, cryptocurrency transfers, and withdrawal services depend on the relevant providers, applicable rules, account eligibility, fraud checks, geographic availability, and production configuration.

No particular amount of revenue or rewards is guaranteed.

---

# 54. Final Production Goal

The final production system should look like:

```text
                    SCORPIO OCTAVIOUS VIBE
                             │
             ┌───────────────┼────────────────┐
             │               │                │
          Social          Earnings          Wallet
             │               │                │
       Feed/Profile      Tapjoy/Offers    Send/Receive
       Photos/Videos      Referrals       Transactions
       Likes/Comments     Rewards          Withdraw
             │               │                │
             └───────────────┼────────────────┘
                             │
                        SOV BACKEND
                             │
              ┌──────────────┼──────────────┐
              │              │              │
          Security        Accounting      Admin
              │              │              │
          JWT/Auth       Rewards/Fee     Dashboard
          Verification   Transactions    Monitoring
                             │
                         DATABASE
```

The objective is to make every money/reward-changing operation verifiable, traceable, and controlled by the backend.
