# Traeger API Authentication Analysis

## Summary

Based on analysis of your mitmproxy flows, here's what was discovered about the authentication system:

## Authentication Token Structure

### There is ONLY ONE token type in use:

**AWS Cognito ID Token (JWT)**
- This is the ONLY token you need for API authentication
- There is NO separate "session token" - the JWT IS the session token
- There is NO separate "user token" vs "session token" distinction

### Token Details

```json
{
  "token_type": "JWT (JSON Web Token)",
  "token_use": "id",
  "issuer": "AWS Cognito User Pool",
  "algorithm": "RS256",
  "duration": "3600 seconds (1 hour)",
  "format": "eyJraWQiOi...header.eyJzdWIiOi...payload.signature"
}
```

### Token Contains:

**User Identity Information:**
- `sub`: Cognito User ID (unique identifier)
- `custom:v2_user_id`: Traeger User ID (unique identifier)
- `email`: user email address
- `cognito:username`: typically the email address
- `given_name`: user's first name
- `family_name`: user's last name

**Token Metadata:**
- `iss`: Token issuer (AWS Cognito User Pool URL)
- `aud`: Client ID (application identifier)
- `iat`: Issued at timestamp (Unix epoch)
- `exp`: Expiration timestamp (Unix epoch, typically iat + 3600)
- `auth_time`: Authentication time (Unix epoch)
- `token_use`: "id" (ID token type)

## What the Flows DON'T Show

❌ **The initial authentication flow was NOT captured** because:
1. You were already logged into the Traeger app
2. The app had a valid token stored locally
3. The app simply reused that existing token

### What's Missing:
- No AWS Cognito login API calls
- No username/password submission
- No token exchange or refresh token calls
- No initial authentication challenge/response

## How AWS Cognito Authentication Works

### Standard AWS Cognito Authentication Flow (not captured):

```
1. User enters email/password in app
   ↓
2. App sends credentials to AWS Cognito
   POST https://cognito-idp.us-west-2.amazonaws.com/
   Action: InitiateAuth or AdminInitiateAuth
   ↓
3. Cognito validates credentials
   ↓
4. Cognito returns THREE tokens:
   - ID Token (JWT) ← This is what you have
   - Access Token (JWT)
   - Refresh Token (used to get new tokens)
   ↓
5. App stores tokens locally
   ↓
6. App uses ID Token for API calls (in Authorization header)
```

### What You Captured:

```
1. App already has valid ID Token stored
   ↓
2. App includes token in Authorization header
   ↓
3. API validates token signature with Cognito
   ↓
4. API returns requested data
```

## Token Usage in API Calls

Every API call includes the JWT token in the Authorization header:

```http
Authorization: eyJraWQiOiI6Y0dhUVRibHhBVzc2NCtQT2pWUGxmbjJq...
```

### This token is used for:
- Traeger REST API (`mobile-iot-api.iot.traegergrills.io`)
- Traeger GraphQL API (`api.kube-gql.prod.traegergrills.io`)
- MQTT connection authorization
- All grill control commands
- User profile access

## Token Derivation

### Is the session token derived from a user token? 

**NO** - There is no "derivation" happening. Here's the actual flow:

1. **User authenticates with AWS Cognito** (username/password)
2. **Cognito issues ID Token directly** (this is your "session token")
3. **That same ID Token is used for all subsequent API calls**

The ID Token IS the session token. It's not derived from anything - it's issued directly by AWS Cognito upon successful authentication.

## How to Get a Fresh Token

Since the login flow wasn't captured, here are your options:

### Option 1: Continue Using mitmproxy (Current Method)
```bash
1. Wait for token to expire (1 hour)
2. Open Traeger app while mitmproxy is running
3. App will automatically re-authenticate with Cognito
4. Capture the new token from API calls
```

### Option 2: Reverse Engineer the Login Flow (Advanced)
To capture the actual login, you would need to:
```bash
1. Logout of Traeger app
2. Start mitmproxy
3. Login to Traeger app
4. Capture the AWS Cognito authentication calls
```

This would reveal:
- Cognito User Pool details
- Client ID and Client Secret (if any)
- Authentication flow specifics
- How to programmatically get tokens

### Option 3: Implement AWS Cognito Authentication (Most Robust)
```python
import boto3
from warrant import Aws  # Python library for Cognito

# You would need to capture:
# - User Pool ID: us-west-2_1FC3aJuC3
# - Client ID: 4id473dsrcq4kevlgrikukqn2a
# - Client Secret (if required)

# Then authenticate programmatically:
aws = Aws(
    username='your_email@example.com',
    password='your_password',
    pool_id='us-west-2_1FC3aJuC3',
    client_id='4id473dsrcq4kevlgrikukqn2a',
    client_secret=None  # May or may not be required
)
tokens = aws.authenticate()
id_token = tokens['AuthenticationResult']['IdToken']
```

## Token Types in AWS Cognito (For Reference)

AWS Cognito typically issues THREE token types:

### 1. ID Token (JWT) ← **This is what you have**
- **Purpose**: Identifies the user
- **Contains**: User attributes (email, name, custom fields)
- **Use**: Sent to APIs to prove user identity
- **In your case**: Used for ALL Traeger API calls

### 2. Access Token (JWT) ← **Not used by Traeger**
- **Purpose**: Grants access to resources
- **Contains**: Scopes and permissions
- **Use**: Typically for accessing AWS resources
- **In your case**: Traeger doesn't seem to use this

### 3. Refresh Token ← **Not captured in flows**
- **Purpose**: Get new ID/Access tokens without re-authenticating
- **Contains**: Long-lived opaque token
- **Use**: Exchange for fresh tokens when current ones expire
- **In your case**: App probably has this stored, uses it automatically

## Why Your Current Approach Works

Your current approach of extracting tokens from mitmproxy flows works because:

1. ✅ The Traeger app already authenticated with Cognito
2. ✅ The app stores the ID Token locally
3. ✅ The app uses that ID Token for API calls
4. ✅ You capture those API calls with the token
5. ✅ You can reuse that token until it expires (1 hour)

## Limitations

❌ **You can't get tokens programmatically** (yet)
- You don't have the login flow details
- You don't know if there's a client secret
- You can't automate token refresh

❌ **Tokens expire after 1 hour**
- Must recapture from mitmproxy flows
- No automated refresh mechanism

❌ **Requires the Traeger app**
- Can't authenticate independently
- Dependent on app having valid credentials

## Recommendations

### For Production Use:
1. **Capture the login flow** - Logout and re-login while capturing with mitmproxy
2. **Implement proper Cognito auth** - Use AWS SDK or Cognito libraries
3. **Store refresh tokens** - Automatically get new tokens when expired
4. **Secure token storage** - Use keyring/keychain for token storage

### For Current Development:
Your current method is fine for:
- Testing and development
- Learning the API
- Building proof-of-concept tools
- Personal use where you can manually refresh tokens

## Firebase Token (Separate from Auth)

Note: The flows also show Firebase token registration:
```http
PUT /users/self/firebase-tokens
```

This is **NOT** an authentication token. It's a push notification token:
- Used for Firebase Cloud Messaging (FCM)
- Allows the server to send push notifications to your iPhone
- Separate from authentication
- Optional for API functionality

## Conclusion

### To answer your questions:

**Q: Does the mitmproxy flow show how the token was achieved?**
**A:** NO - The actual login/authentication flow was not captured. You only captured API calls that used an already-issued token.

**Q: Is there a separate user token and session token?**
**A:** NO - There is only ONE token: the AWS Cognito ID Token (JWT). This serves as both the user identity token AND the session token.

**Q: Is the session token derived from a user token?**
**A:** NO - The ID Token is issued directly by AWS Cognito upon successful authentication. It's not "derived" from anything - it's the primary authentication credential issued by Cognito.

### The Authentication Flow is:
```
Username/Password → AWS Cognito → ID Token (JWT) → API Calls
```

Not:
```
User Token → Session Token → API Calls  ❌
```
