// Step 1 of Decap CMS's GitHub OAuth flow: send the browser to GitHub to authorize.
// GitHub OAuth App callback URL must be set to https://gevix.in/api/callback.
module.exports = function handler(req, res) {
  const clientId = process.env.OAUTH_CLIENT_ID;
  if (!clientId) {
    res.status(500).send("Missing OAUTH_CLIENT_ID environment variable.");
    return;
  }
  const redirectUri = `https://${req.headers.host}/api/callback`;
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: "repo,user",
  });
  res.writeHead(302, { Location: `https://github.com/login/oauth/authorize?${params}` });
  res.end();
}
