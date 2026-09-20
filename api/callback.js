// Step 2 of Decap CMS's GitHub OAuth flow: exchange the code for a token and
// relay it back to the /admin popup via postMessage, per Decap's documented
// handshake (window.opener.postMessage("authorizing:github", "*") then
// "authorization:github:success:<payload>").
module.exports = async function handler(req, res) {
  const { code, error, error_description } = req.query;
  const clientId = process.env.OAUTH_CLIENT_ID;
  const clientSecret = process.env.OAUTH_CLIENT_SECRET;

  if (error) {
    res.status(400).send(`GitHub authorization error: ${error_description || error}`);
    return;
  }
  if (!clientId || !clientSecret) {
    res.status(500).send("Missing OAUTH_CLIENT_ID/OAUTH_CLIENT_SECRET environment variables.");
    return;
  }

  const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret, code }),
  });
  const data = await tokenRes.json();

  if (data.error) {
    res.status(400).send(`GitHub token exchange error: ${data.error_description || data.error}`);
    return;
  }

  const payload = JSON.stringify({ token: data.access_token, provider: "github" });
  res.setHeader("Content-Type", "text/html");
  res.status(200).send(`<!doctype html>
<html><body>
<script>
(function () {
  function receiveMessage(e) {
    window.opener.postMessage(
      "authorization:github:success:" + ${JSON.stringify(payload)},
      e.origin
    );
    window.removeEventListener("message", receiveMessage, false);
  }
  window.addEventListener("message", receiveMessage, false);
  window.opener.postMessage("authorizing:github", "*");
})();
</script>
</body></html>`);
}
