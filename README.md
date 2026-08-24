# Scorpio Octavious Vibe Backend V1

This is the backend foundation for the APK + website.

## Included
- Account registration/login
- JWT authentication
- User profiles
- Wallet ledger (USD cents + BTC/ETH/USDT fields)
- Feed/posts
- Reels
- Likes/comments database tables
- Transaction history
- PayPal/bank payout REQUESTS
- Admin summary endpoint

## Important
This backend does NOT move real crypto or real money yet.
Google OAuth, blockchain transactions, PayPal payouts and bank payouts must be
connected through their official provider APIs and verified server-side.

Do not put private keys, PayPal secrets, bank credentials or JWT_SECRET in the APK.

## Run locally
1. Install Python 3.
2. `pip install -r requirements.txt`
3. Set a strong `JWT_SECRET`.
4. `python app.py`
5. Test: `/api/health`

Default local server: http://127.0.0.1:8080

## Next integration
The APK should call this server over HTTPS:
POST /api/auth/register
POST /api/auth/login
POST /api/auth/google
GET  /api/me
GET  /api/wallet
GET  /api/feed
POST /api/posts
GET  /api/reels
POST /api/reels
GET  /api/transactions
POST /api/payouts
GET  /api/admin/summary

