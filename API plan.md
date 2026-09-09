# Scorpio Octavious Vibe
# API Plan & Integration Specification

Version: 1.0
Backend: Flask / Python
Database: SQLite
Production API:

https://scorpio-octavious-vibe-api.onrender.com

Tapjoy Callback:

https://scorpio-octavious-vibe-api.onrender.com/api/tapjoy/callback


==================================================
1. API PURPOSE
==================================================

The Scorpio Octavious Vibe API is the central backend for:

- User registration
- User login
- JWT authentication
- User profiles
- SOV wallet
- SOV transfers
- 10% platform fees
- Tapjoy rewards
- Offerwall rewards
- Reward history
- Referral rewards
- Withdrawals
- Boost Ads
- Admin dashboard
- Transaction records
- Fraud protection
- Duplicate reward protection

The Android application is the client.

The backend is the source of truth.

The Android application must never be trusted to create or modify money,
SOV balances, rewards, fees, or withdrawals by itself.


==================================================
2. PRODUCTION API
==================================================

Base URL:

https://scorpio-octavious-vibe-api.onrender.com


All Android API requests should use HTTPS.

Example:

https://scorpio-octavious-vibe-api.onrender.com/api/auth/login


==================================================
3. SECURITY
==================================================

Secrets must NEVER be placed inside:

- MainActivity.java
- Android source code
- APK
- GitHub source code
- Public configuration files
- API plan files

Secrets belong in Render Environment Variables.

Required environment variables:

JWT_SECRET=YOUR_PRIVATE_SECRET

TAPJOY_SECRET=YOUR_PRIVATE_TAPJOY_SECRET

OFFERWALL_SECRET=YOUR_PRIVATE_OFFERWALL_SECRET


Never send these values to the Android application.

Never display them in the admin dashboard.

Never commit them to GitHub.


==================================================
4. AUTHENTICATION
==================================================

Authentication uses JWT.

Protected API requests use:

Authorization: Bearer YOUR_JWT_TOKEN


------------------------------------------
REGISTER
------------------------------------------

POST /api/auth/register

Content-Type:

application/json


Request:

{
    "username": "john",
    "email": "john@example.com",
    "password": "StrongPassword123"
}


Success:

{
    "success": true,
    "message": "Account created"
}


The backend must:

1. Validate username.
2. Validate email.
3. Validate password.
4. Prevent duplicate email.
5. Prevent duplicate username.
6. Hash the password.
7. Create the user.
8. Create the user's wallet/account.
9. Return success.


------------------------------------------
LOGIN
------------------------------------------

POST /api/auth/login

Request:

{
    "email": "john@example.com",
    "password": "StrongPassword123"
}


Success:

{
    "success": true,
    "token": "JWT_TOKEN",
    "user": {
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    }
}


Android stores the JWT securely.

The JWT is then sent with protected requests.


------------------------------------------
CURRENT USER
------------------------------------------

GET /api/auth/me

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "user": {
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    }
}


==================================================
5. HEALTH CHECK
==================================================

GET /health


Example:

{
    "status": "ok"
}


Use this endpoint to verify that Render is running.


==================================================
6. API ROOT
==================================================

GET /


Example:

{
    "name": "Scorpio Octavious Vibe API",
    "status": "online"
}


==================================================
7. WALLET
==================================================


------------------------------------------
GET WALLET BALANCE
------------------------------------------

GET /api/wallet/balance

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "balance": 125.50,
    "currency": "SOV"
}


The balance must come from the backend database.

The Android application must not calculate or permanently store
the official wallet balance.


------------------------------------------
SEND SOV
------------------------------------------

POST /api/wallet/send

Header:

Authorization: Bearer JWT_TOKEN

Content-Type:

application/json


Request:

{
    "recipient": "john2",
    "amount": 10.00
}


Backend process:

1. Authenticate user.
2. Find recipient.
3. Validate amount.
4. Check sender balance.
5. Calculate platform fee.
6. Deduct the correct amount.
7. Credit recipient.
8. Create transaction record.
9. Create admin fee record.
10. Return transaction result.


10% fee example:

Amount:

10 SOV

Fee:

1 SOV

Total sender debit:

11 SOV


Recipient receives:

10 SOV


The exact fee presentation must be displayed to the user
before confirmation.


IMPORTANT:

Tapjoy rewards are NOT reduced by this fee.


------------------------------------------
WALLET HISTORY
------------------------------------------

GET /api/wallet/history

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "transactions": [
        {
            "id": 1,
            "type": "send",
            "amount": 10,
            "fee": 1,
            "status": "completed",
            "created_at": "2026-09-09T12:00:00Z"
        }
    ]
}


==================================================
8. TAPJOY
==================================================

Tapjoy is one of the main SOV reward sources.

Application ID:

20c83360-1d38-4acc-bdeb-356931d020af


SOV Placement ID:

e9924a33-8737-44fd-8ba5-22db9dcddc54


These identifiers are not wallet secrets.

The Tapjoy secret/verifier secret must remain on the backend.


------------------------------------------
TAPJOY CALLBACK
------------------------------------------

GET /api/tapjoy/callback


Production URL:

https://scorpio-octavious-vibe-api.onrender.com/api/tapjoy/callback


Expected parameters:

snuid

currency

id

verifier


Example callback:

/api/tapjoy/callback?snuid=123&currency=10&id=reward123&verifier=...


Backend flow:

Tapjoy
   |
   v
SOV API
   |
   v
Verify callback
   |
   v
Check duplicate
   |
   v
Find user
   |
   v
Credit SOV
   |
   v
Save reward
   |
   v
Return HTTP 200


------------------------------------------
TAPJOY VERIFICATION
------------------------------------------

For classic Tapjoy callbacks:

MD5:

id:snuid:currency:TAPJOY_SECRET


The backend calculates the expected verifier.

The backend compares it against the received verifier.

If valid:

HTTP 200


If invalid:

HTTP 403


Do NOT credit the wallet before verification.


==================================================
9. TAPJOY DUPLICATE PROTECTION
==================================================

Every Tapjoy reward must have a unique reward/event ID.

Example:

reward123


Before crediting:

SELECT reward FROM tapjoy_rewards
WHERE reward_id = "reward123"


If already processed:

DO NOT CREDIT AGAIN.


Return success/duplicate handling without creating another wallet credit.


This prevents:

- Double rewards
- Tapjoy retry duplication
- Network retry duplication
- Fraudulent repeated callbacks


==================================================
10. TAPJOY USER IDENTIFICATION
==================================================

The Tapjoy account identifier should map to the SOV user.

Recommended:

SOV user ID


Example:

SOV user ID:

5821


Tapjoy:

snuid=5821


Do not use:

- Phone number
- Private admin information
- Password
- JWT secret
- Random changing device identifiers


The user identifier must remain stable.


==================================================
11. REWARD HISTORY
==================================================

GET /api/rewards/history

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "rewards": [
        {
            "id": 25,
            "provider": "tapjoy",
            "reward_id": "reward123",
            "amount": 25,
            "currency": "SOV",
            "status": "credited",
            "created_at": "2026-09-09T12:00:00Z"
        }
    ]
}


==================================================
12. OFFERWALL ARCHITECTURE
==================================================

The reward architecture is:

USER
 |
 v
OFFERWALL
 |
 v
PROVIDER
 |
 v
SOV BACKEND
 |
 v
VERIFY
 |
 v
DUPLICATE CHECK
 |
 v
SOV WALLET
 |
 v
ANDROID APP


The Android app must NOT directly credit rewards.


Correct:

Provider
    ->
Backend
    ->
Verify
    ->
Wallet


Incorrect:

Android
    ->
Add reward locally


==================================================
13. GENERIC OFFERWALL CALLBACK
==================================================

POST /api/offerwall/callback


Example:

{
    "user_id": "5821",
    "reward_id": "offer123",
    "amount": 50,
    "currency": "SOV"
}


Backend must:

1. Authenticate provider callback.
2. Verify signature.
3. Validate user.
4. Validate amount.
5. Check reward ID.
6. Reject duplicate.
7. Credit wallet.
8. Save event.
9. Return success.


==================================================
14. OFFERWALL EVENTS
==================================================

Database table:

offerwall_events


Recommended fields:

id
provider
user_id
event_id
amount
currency
status
created_at


Possible status values:

pending
verified
credited
rejected
duplicate


==================================================
15. EARNINGS API
==================================================

GET /api/earnings

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "sov_balance": 125.50,
    "today": 8.25,
    "total_earned": 245.75
}


Reward sources:

- Tapjoy
- Offerwalls
- Games
- Referrals
- Daily rewards
- Approved future providers


All reward credits must have backend records.


==================================================
16. REFERRALS
==================================================


GET /api/referrals

Header:

Authorization: Bearer JWT_TOKEN


Example:

{
    "success": true,
    "referral_code": "SOV12345",
    "referral_link": "https://example.com/register?ref=SOV12345",
    "qualified": 5,
    "reward": 25
}


Referral rewards must be verified by the backend.


Never allow:

Android -> Add referral reward


Instead:

Android
   ->
Backend
   ->
Check referral
   ->
Check qualification
   ->
Credit reward


==================================================
17. WITHDRAWALS
==================================================

POST /api/withdrawals


Header:

Authorization: Bearer JWT_TOKEN


Request:

{
    "amount": 100,
    "currency": "USDT",
    "network": "TRC20",
    "destination": "USER_WALLET_ADDRESS"
}


Backend validates:

- Authentication
- Balance
- Minimum withdrawal
- Maximum withdrawal
- Currency
- Network
- Destination
- Fee
- Security checks
- Fraud checks


Possible status:

pending

under_review

approved

sent

completed

rejected


Example:

{
    "success": true,
    "withdrawal": {
        "id": 55,
        "amount": 100,
        "fee": 10,
        "status": "pending"
    }
}


==================================================
18. WITHDRAWAL 10% FEE
==================================================

Configured platform fee:

10%


Example:

Withdrawal:

100


Fee:

10


Depending on the configured accounting model,
the user must clearly see the fee before confirming.


Possible display:

Withdrawal amount: 100 SOV
Platform fee: 10 SOV
Total debit: 110 SOV


OR, if the product intentionally treats 100 as the
maximum total debit:

Requested amount: 100 SOV
Platform fee: 10 SOV
Net payout: 90 SOV


The production implementation must use ONE clearly documented
model and show it before confirmation.


IMPORTANT:

The 10% fee is not a Tapjoy reward fee.


==================================================
19. WITHDRAWAL SECURITY
==================================================

A withdrawal must never be automatically approved merely because
the Android application says it is valid.

Backend must control:

- Balance
- Amount
- Address
- Network
- Fee
- Status
- Approval


Admin/security review may be required.


==================================================
20. BOOST ADS
==================================================

Boost Ads allows users to promote posts/media.


Current packages:


STARTER

2,500 views

$6


GROWTH

4,500 views

$8


PRO

100,000 views

$15


ULTIMATE

300,000 views

$25


==================================================
21. CREATE BOOST CAMPAIGN
==================================================

POST /api/boost


Request:

{
    "package": "starter",
    "post_id": 123
}


Backend creates campaign:

{
    "id": 1001,
    "package": "starter",
    "target_views": 2500,
    "price": 6,
    "status": "pending_payment"
}


Campaign states:

pending_payment
paid
active
paused
completed
rejected


==================================================
22. BOOST CAMPAIGN TRACKING
==================================================

Backend tracks:

campaign_id

user_id

post_id

package

target_views

delivered_views

invalid_views

payment_status

campaign_status

created_at

updated_at


The backend determines when a campaign is completed.


==================================================
23. PAYPAL
==================================================

PayPal credentials remain on the backend.


Correct architecture:

Android
   |
   v
SOV API
   |
   v
Create PayPal order
   |
   v
PayPal
   |
   v
Confirm payment
   |
   v
SOV API
   |
   v
Activate campaign


Never put private PayPal credentials inside the APK.


==================================================
24. ADMIN API
==================================================

Admin endpoints must require:

1. Valid JWT
2. Admin authorization
3. Backend permission check


Admin capabilities:

- Users
- Wallets
- Transactions
- Tapjoy rewards
- Offerwall events
- Withdrawals
- Fees
- Boost campaigns
- Suspicious activity
- Monetization statistics


Example:

GET /api/admin/users


GET /api/admin/transactions


GET /api/admin/rewards


GET /api/admin/withdrawals


GET /api/admin/offerwall/stats


==================================================
25. ADMIN PRIVACY
==================================================

The private admin email must never be displayed to ordinary users.

Admin credentials must never be returned by:

/api/auth/me

or any public endpoint.


Admin information belongs only on protected admin endpoints.


==================================================
26. DATABASE
==================================================

Core tables:

users

transactions

tapjoy_rewards

offerwall_events

admin_fees


Future tables:

withdrawals

referrals

boost_campaigns

payment_orders

notifications

login_activity

security_events


==================================================
27. TRANSACTION RULES
==================================================

Every wallet change must be traceable.


Examples:

Tapjoy reward:

+50 SOV


Send:

-10 SOV

Fee:

-1 SOV


Withdrawal:

-amount

-fee


Admin fee:

+fee


Never change the wallet balance without recording
the corresponding transaction.


==================================================
28. ANDROID API CLIENT
==================================================

Example Java API helper:

```java
public final class ApiConfig {

    private ApiConfig() {}

    public static final String BASE_URL =
            "https://scorpio-octavious-vibe-api.onrender.com/";

    public static final String LOGIN =
            "api/auth/login";

    public static final String REGISTER =
            "api/auth/register";

    public static final String ME =
            "api/auth/me";

    public static final String BALANCE =
            "api/wallet/balance";

    public static final String SEND =
            "api/wallet/send";

    public static final String HISTORY =
            "api/wallet/history";

    public static final String REWARDS =
            "api/rewards/history";

    public static final String EARNINGS =
            "api/earnings";

    public static final String REFERRALS =
            "api/referrals";

    public static final String WITHDRAWALS =
            "api/withdrawals";

    public static final String BOOST =
            "api/boost";
}
==================================================
29. ANDROID HTTP CLIENT

Recommended Android architecture:

MainActivity
|
v
ApiClient
|
v
HTTPS
|
v
Flask API
|
v
SQLite

Example using HttpURLConnection:

public class ApiClient {

    private final String baseUrl =
            "https://scorpio-octavious-vibe-api.onrender.com/";

    public String get(String endpoint, String token)
            throws Exception {

        URL url = new URL(baseUrl + endpoint);

        HttpURLConnection connection =
                (HttpURLConnection) url.openConnection();

        connection.setRequestMethod("GET");

        connection.setRequestProperty(
                "Accept",
                "application/json"
        );

        if (token != null && !token.isEmpty()) {
            connection.setRequestProperty(
                    "Authorization",
                    "Bearer " + token
            );
        }

        int code = connection.getResponseCode();

        InputStream stream;

        if (code >= 200 && code < 300) {
            stream = connection.getInputStream();
        } else {
            stream = connection.getErrorStream();
        }

        BufferedReader reader =
                new BufferedReader(
                        new InputStreamReader(stream)
                );

        StringBuilder response =
                new StringBuilder();

        String line;

        while ((line = reader.readLine()) != null) {
            response.append(line);
        }

        reader.close();
        connection.disconnect();

        return response.toString();
    }
}
==================================================
30. LOGIN REQUEST EXAMPLE
JSONObject body = new JSONObject();

body.put("email", email);
body.put("password", password);

Send:

POST

/api/auth/login

After successful login:

String token =
        responseObject.getString("token");

Store the token securely.

Do not log the token.

==================================================
31. WALLET REQUEST EXAMPLE
ApiClient api = new ApiClient();

String response =
        api.get(
                "api/wallet/balance",
                token
        );

Example response:

{
    "success": true,
    "balance": 250.75,
    "currency": "SOV"
}

Android displays:

SOV Balance

250.75 SOV

==================================================
32. TAPJOY ANDROID SDK

The Tapjoy Android SDK is separate from the SOV backend.

The Android application initializes Tapjoy.

The backend handles verified rewards.

Conceptual flow:

Tapjoy SDK
|
v
Offer completion
|
v
Tapjoy callback
|
v
SOV API
|
v
Wallet credit

Tapjoy SDK dependency should be managed in the Android Gradle project
according to the currently selected Tapjoy SDK version.

Never hardcode the Tapjoy secret in Android.

==================================================
33. NETWORK PERMISSION

AndroidManifest.xml must allow Internet access.

Example:

<uses-permission
    android:name="android.permission.INTERNET" />
==================================================
34. API ERROR FORMAT

Recommended error response:

{
    "success": false,
    "error": "Invalid request"
}

Examples:

401:

{
    "success": false,
    "error": "Authentication required"
}

403:

{
    "success": false,
    "error": "Forbidden"
}

404:

{
    "success": false,
    "error": "Not found"
}

409:

{
    "success": false,
    "error": "Duplicate transaction"
}

500:

{
    "success": false,
    "error": "Internal server error"
}
==================================================
35. API TESTING

Test in this order.

TEST 1

GET:

/health

Expected:

HTTP 200

TEST 2

Register a test account.

TEST 3

Login.

TEST 4

Call:

/api/auth/me

TEST 5

Call:

/api/wallet/balance

TEST 6

Test SOV send.

TEST 7

Verify the 10% fee.

TEST 8

Check wallet history.

TEST 9

Test Tapjoy callback.

TEST 10

Send the same reward ID again.

Expected:

Second reward is NOT credited.

TEST 11

Test withdrawal validation.

TEST 12

Test admin dashboard.

==================================================
36. MONETIZATION FOUNDATION

The monetization foundation is considered functional when:

[ ] Backend deployed
[ ] Render health check works
[ ] Authentication works
[ ] Wallet works
[ ] Tapjoy callback works
[ ] Tapjoy verification works
[ ] Duplicate protection works
[ ] Reward credits wallet
[ ] Reward history works
[ ] 10% platform fee works
[ ] Withdrawal validation works
[ ] Admin can view transactions
[ ] Android connects to API

==================================================
37. COMPLETE MONEY FLOW

TAPJOY:

User
->
Tapjoy
->
Offer completed
->
Tapjoy callback
->
SOV API
->
Verify
->
Duplicate check
->
Credit SOV
->
Wallet

OFFERWALL:

User
->
Offerwall
->
Offer completed
->
Provider callback
->
SOV API
->
Verify
->
Credit SOV
->
Wallet

SEND:

Sender
->
SOV API
->
Check balance
->
Calculate 10% fee
->
Debit sender
->
Credit receiver
->
Record transaction
->
Record fee

WITHDRAWAL:

User
->
Withdrawal request
->
Backend validation
->
Fee calculation
->
Security review
->
Approval
->
Payment processing
->
Completed

BOOST:

User
->
Select package
->
Create campaign
->
PayPal
->
Payment confirmation
->
Campaign active
->
Track views
->
Campaign completed

==================================================
38. IMPORTANT FINANCIAL RULE

The Android application is NOT the authority for balances.

The backend is the authority.

Never do this:

balance += reward;

Instead:

Android requests backend balance:

GET /api/wallet/balance

The backend returns:

{
    "balance": 100
}

Android only displays the result.

==================================================
39. FRAUD PROTECTION

The backend should monitor:

Duplicate reward IDs
Repeated callbacks
Impossible reward amounts
Invalid signatures
Invalid users
Suspicious withdrawal patterns
Multiple accounts abusing referrals
Abnormal boost traffic
Invalid payment confirmations

Suspicious activity should be recorded.

==================================================
40. LOGGING

Never log:

Passwords
JWT secrets
Tapjoy secrets
API keys
Private payment credentials
Full sensitive wallet information

Safe logging:

Tapjoy reward received
Reward ID: reward123
User ID: 5821
Amount: 50
Status: verified
==================================================
41. RENDER DEPLOYMENT

Production service:

https://scorpio-octavious-vibe-api.onrender.com

Render should provide:

PORT

The Flask application should bind to:

0.0.0.0

Example:

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
==================================================
42. GITHUB RULES

GitHub can contain:

app.py
requirements.txt
Android source
API documentation
README
Gradle files

GitHub must NOT contain:

JWT_SECRET
TAPJOY_SECRET
PayPal private credentials
Offerwall private keys
Database passwords
Private admin credentials

Use environment variables instead.

==================================================
43. PRODUCTION CHECKLIST

BACKEND

[ ] app.py complete
[ ] requirements.txt correct
[ ] Render deployed
[ ] /health works
[ ] Database works
[ ] JWT works

TAPJOY

[ ] App configured
[ ] Placement configured
[ ] Callback configured
[ ] Secret configured on Render
[ ] User ID mapping tested
[ ] Reward verification tested
[ ] Duplicate protection tested

WALLET

[ ] Balance works
[ ] Send works
[ ] Fee works
[ ] History works
[ ] Reward credit works

WITHDRAWALS

[ ] Minimum checked
[ ] Maximum checked
[ ] Balance checked
[ ] Network checked
[ ] Address checked
[ ] Fee checked
[ ] Status tracking implemented

ANDROID

[ ] API URL configured
[ ] Login connected
[ ] Register connected
[ ] Wallet connected
[ ] Earnings connected
[ ] Rewards connected
[ ] Withdrawal connected
[ ] Admin separated from normal users

RELEASE

[ ] Release build works
[ ] APK/AAB tested
[ ] Privacy Policy
[ ] Terms
[ ] Offerwall provider requirements
[ ] Payment testing
[ ] Withdrawal testing
[ ] Fraud protection
[ ] Production monitoring

==================================================
44. DEVELOPMENT ORDER

STEP 1

Finish app.py.

STEP 2

Deploy app.py to Render.

STEP 3

Test:

/health

STEP 4

Test authentication.

STEP 5

Test wallet.

STEP 6

Test Tapjoy callback.

STEP 7

Test duplicate protection.

STEP 8

Connect Android application.

STEP 9

Connect earnings screen.

STEP 10

Connect wallet screen.

STEP 11

Connect withdrawal screen.

STEP 12

Connect Boost Ads.

STEP 13

Connect PayPal.

STEP 14

Build release APK/AAB.

STEP 15

Run complete production test.

STEP 16

Publish.

==================================================
45. FINAL ARCHITECTURE
                SCORPIO OCTAVIOUS VIBE
                          |
                Android Application
                          |
                     HTTPS / JSON
                          |
                          v
              SCORPIO SOV BACKEND
                          |
      +-------------------+-------------------+
      |                   |                   |
   AUTH                 WALLET             ADMIN
      |                   |                   |
      |             +-----+-----+             |
      |             |           |             |
      |           Rewards      Fees           |
      |             |           |             |
      |             +-----+-----+             |
      |                   |                   |
      +-------------------+-------------------+
                          |
                     SQLite Database
                          |
      +-------------------+-------------------+
      |                   |                   |
   Tapjoy             Offerwalls          Payments
      |                   |                   |
      +-------------------+-------------------+
                          |
                     Monetization
==================================================
46. GOLDEN RULE

SOV BACKEND = SOURCE OF TRUTH

Android = CLIENT

Tapjoy/Offerwalls = REWARD PROVIDERS

PayPal = PAYMENT PROVIDER

Admin = CONTROL / REVIEW

The backend verifies everything before money or SOV
is credited, transferred, or withdrawn.

==================================================
END OF API PLAN

**This is the file I recommend keeping next to your completed `app.py`.** The next major step is connecting your **new clean Android project** to this API, starting with **login → JWT → wallet balance → Tapjoy/earnings**.
