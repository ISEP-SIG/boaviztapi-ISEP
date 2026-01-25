## 🔒 OAuth2 One-Button Login Setup

## Google Sign-on
<p>Our application uses Google's Identity services to provide secure authentication and authorisation
between the backend and frontend applications.</p>

<p>Each deployment requires a separate <a href="https://developers.google.com/workspace/guides/create-project"> Google Cloud Project</a>. Please create
one for your deployment before proceeding.
</p>

### Step 1. Get your Google API client ID by setting up a GCP project
In our `.env.sample` file, you will find two environment variables:
```yaml
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_SECRET_ID
```
These environment variables are used by the authentication code to identify the correct deployment for
which the authentication request is being made.

<p>The first step is therefore to get your own <b>GOOGLE_CLIENT_ID</b> and <b>GOOGLE_CLIENT_SECRET</b> values.
To do so, please follow the steps illustrated <a href="https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid#get_your_google_api_client_id"> here</a>, under step 1.
Make sure to correctly set your <b>Authorized JavaScript origins</b> to match your frontend deployment domain, otherwise the
authentication requests will be rejected.</p>

### Step 2. Copy-paste the ID and Secret to your environment
<p>Once the project is set-up, the CLIENT_ID and CLIENT_SECRET tokens will be displayed on the page. Please
add them to your environment <b>(and do not commit the secret under any circumstances!)</b></p>


### Step 3. Add a redirect callback URL for the frontend
<p>Since most users will authenticate through the frontend website, it is necessary to add a redirect URL that
tells Google at what address our authentication callback is located in the backend domain. To do so, please identify
the following environment variables in the <a href="https://github.com/ISEP-SIG/ISEP-Frontend"> frontend project</a>:</p>

```bash
NEXT_PUBLIC_GOOGLE_LOGIN_URI=YOUR_BACKEND_DOMAIN/auth/google/callback
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
```

<p>The <b>GOOGLE_LOGIN_URI</b> is the callback at which the backend expects each authentication request to land. Please
replace the domain placeholder with your backend domain. The <b>NEXT_PUBLIC_GOOGLE_CLIENT_ID</b> is the client ID that was
created at step 1.</p>


<p>Authentication with Google should now work under the new deployment.</p>


## Discord Sign-on
<p> For Discord, please identify the same environment variables discussed in the Google tutorial,
and modify them accordingly. Each Discord-related variable is explicitly appended with the "DISCORD" prefix.</p>
You can find a tutorial on how to obtain your client ID, secret and redirect url <a href="https://discord.com/developers/docs/topics/oauth2"> here</a>.