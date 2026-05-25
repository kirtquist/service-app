# WhatsApp demo setup (Phase 1a)

Send a **job note** via WhatsApp → get a **structured summary + JSON** back. Two supported providers:

| Provider | Best for | Webhook path |
|----------|----------|--------------|
| **Twilio sandbox** | Fastest first SME demo | `POST /webhook/whatsapp/twilio` |
| **Meta Cloud API** | Production-like pilot | `GET/POST /webhook/whatsapp` |

Cloud Run service URL (after deploy):

```bash
gcloud run services describe service-app-api \
  --region us-west1 \
  --project kgs-service-app \
  --format 'value(status.url)'
```

---

## Option A: Twilio WhatsApp sandbox (recommended first)

### 1. Twilio account

1. Sign up at [twilio.com](https://www.twilio.com/)
2. Open **Messaging → Try it out → Send a WhatsApp message**
3. Join the sandbox from your phone (send the join code to the sandbox number)

### 2. Configure Cloud Run

Set env vars on the Cloud Run service (replace with your values):

```bash
export SERVICE_URL="https://service-app-api-XXXX.us-west1.run.app"

gcloud run services update service-app-api \
  --region us-west1 \
  --project kgs-service-app \
  --set-env-vars="PUBLIC_BASE_URL=${SERVICE_URL},TWILIO_VALIDATE_SIGNATURES=true" \
  --set-secrets="TWILIO_AUTH_TOKEN=twilio-auth-token:latest"
```

Create the Twilio auth token secret (once):

```bash
echo -n "YOUR_TWILIO_AUTH_TOKEN" | gcloud secrets create twilio-auth-token \
  --data-file=- --project=kgs-service-app --replication-policy=automatic

gcloud secrets add-iam-policy-binding twilio-auth-token \
  --member="serviceAccount:service-app-api@kgs-service-app.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=kgs-service-app
```

For **local testing only**, you can skip signature validation:

```bash
TWILIO_VALIDATE_SIGNATURES=false
```

### 3. Point Twilio webhook

In Twilio Console → sandbox settings → **When a message comes in**:

```
https://YOUR-CLOUD-RUN-URL/webhook/whatsapp/twilio
```

Method: **POST**

### 4. Test

Send a WhatsApp message to the sandbox number:

```
Baker residence, replaced P-trap under sink, 2 hours
```

You should get a summary + JSON reply.

---

## Option B: Meta WhatsApp Cloud API

### 1. Meta developer setup

1. [developers.facebook.com](https://developers.facebook.com/) → create app → add **WhatsApp** product
2. Get **Phone number ID** and **temporary access token** (API setup page)
3. Choose a **Verify token** (any string you invent, e.g. `service-app-verify-2026`)

### 2. Configure Cloud Run

```bash
gcloud run services update service-app-api \
  --region us-west1 \
  --project kgs-service-app \
  --set-env-vars="WHATSAPP_VERIFY_TOKEN=service-app-verify-2026" \
  --set-secrets="WHATSAPP_ACCESS_TOKEN=whatsapp-access-token:latest"
```

Create secret:

```bash
echo -n "YOUR_META_ACCESS_TOKEN" | gcloud secrets create whatsapp-access-token \
  --data-file=- --project=kgs-service-app --replication-policy=automatic
```

Also set phone number ID (env var, not highly sensitive):

```bash
gcloud run services update service-app-api \
  --region us-west1 \
  --project=kgs-service-app \
  --set-env-vars="WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID"
```

### 3. Configure webhook in Meta

**Callback URL:**

```
https://YOUR-CLOUD-RUN-URL/webhook/whatsapp
```

**Verify token:** same as `WHATSAPP_VERIFY_TOKEN`

Subscribe to **messages** field.

### 4. Test

Add your phone as a test recipient in Meta dashboard, then send a job note.

---

## Local dev

Add to `.env` (see [`.env.example`](../.env.example)):

```bash
# Twilio (local — disable signature check unless using ngrok + PUBLIC_BASE_URL)
TWILIO_VALIDATE_SIGNATURES=false
TWILIO_AUTH_TOKEN=...

# Meta
WHATSAPP_VERIFY_TOKEN=test-verify
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
```

Run API and expose with ngrok if testing webhooks locally:

```bash
service-app-api
ngrok http 8090
```

---

## Example plumber prompts (SME demos)

```
Smith house — kitchen sink leak, new P-trap and two fittings, about 2 hours
```

```
Johnson — water heater install, 3/4 copper fittings, 4 hours on site
```

```
Replaced toilet and supply line at Garcia, 1.5 hours
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Meta verify fails | `WHATSAPP_VERIFY_TOKEN` must match Meta dashboard exactly |
| Twilio 403 signature | Set `PUBLIC_BASE_URL` to exact Cloud Run URL (no trailing slash) |
| No reply / 503 on parse | Check `OPENROUTER_API_KEY` secret on Cloud Run |
| Meta message ignored | Only **text** messages supported in Phase 1a (no voice yet) |
