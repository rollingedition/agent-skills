---
title: "Model Context Protocol in Practice"
chapter: "Authorize clients with OAuth"
chapter_id: authorization
book: model-context-protocol-in-practice
edition: 2026.11.10
verified: 2026-11-10
edition_code: H239-A01C
canonical: https://rollingedition.com/model-context-protocol-in-practice/authorization
license: CC BY 4.0
attribution: "“Authorize clients with OAuth,” chapter 8 of Model Context Protocol in Practice, Edition 2026.11.10, examples passed Nov 10, 2026. By Rolling Edition, https://rollingedition.com/model-context-protocol-in-practice/authorization. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Authorize clients with OAuth

By the end of this chapter you can protect the shop's Model Context Protocol server with OAuth. You publish the metadata that leads a client to the authorization server, identify the support team's host with a Client ID Metadata Document, get tokens with PKCE, accept only tokens issued for the shop's server, catch a mix-up attack through the issuer of each response, and require a scope per tool, with step-up when a refund needs more. Everything holds for the specification at revision 2026-07-28 and the Python SDK, `mcp` 2.3.0.

This book follows one case study throughout: a small online shop for kitchen and garden goods, which we call **the shop**, and whose support team answers customer tickets through a host. [Meet the shop and its API](#the-shop) introduces it. [Serve over Streamable HTTP](#streamable-http) moved the shop's server, `shop-support`, onto an HTTP address so that the support team's hosts could share it. Its Origin check keeps out web pages and nothing else: any program that reaches the port can read orders and issue refunds ([Reject requests from other origins](#validate-origin)). The shop needs to know which host is calling, for which person, and what that person may do. Support staff may read orders and stock; only a support lead may refund.

The Model Context Protocol (MCP) answers with OAuth 2.1. Authorization is optional in MCP and belongs to HTTP transports: a stdio server takes its credentials from the environment instead ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). A protected MCP server is an OAuth resource server, the host's client for it is an OAuth client, and tokens come from an authorization server, which may run beside the MCP server or apart from it. You know this flow from the client side of other APIs. What MCP changes is that a client knows nothing about a server in advance. It starts from a URL, so discovery, the client's identity and the token's audience all have to work with no setup between the two.

Four shared modules in `examples/lib/` carry this chapter's setup, so each example shows only its idea:

- `lib.auth_server` is the shop's authorization server, on loopback: metadata, the authorization code grant with PKCE, `iss` on every answer, and JWT access tokens bound to one server. Consent is scripted, standing in for the person at the browser. It is a teaching server for these loopback examples, and you must never deploy it: it signs no one in, and its signing key derives from the book's public seed, so anyone with the book can mint tokens it accepts. A deployment uses an established authorization server that meets this chapter's checks. The Python SDK has an authorization server of its own, but its documentation discourages it for new servers, and its metadata advertises neither `iss` nor Client ID Metadata Documents ([SDK authorization docs](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/docs/run/authorization.md)).
- `lib.oauth_client` is the host's side: the SDK's `OAuthClientProvider` with in-memory token storage, and a scripted browser that follows the authorization server's redirects and hands the answer back to the SDK.
- `lib.tool_scopes` adds the scope check per tool that the SDK doesn't have.
- `lib.protected_shop` puts them together: chapter 3's five tools behind OAuth, as this chapter leaves them.

Everything runs on 127.0.0.1 over plain HTTP. That is acceptable for local development only: in production, every authorization server endpoint MUST be served over HTTPS ([security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations)).

## Find the authorization server from the resource {#protected-resource-metadata}

A client that has only a server's URL must learn from the server where to get a token. The pinned revision does this in two steps. First, MCP servers MUST publish Protected Resource Metadata (RFC 9728), a JSON document that names the resource and lists at least one authorization server ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). A request without a token gets 401, and its `WWW-Authenticate` header points to that document in a `resource_metadata` parameter. A client that finds no such parameter tries the well-known URI, `/.well-known/oauth-protected-resource` with the server's path inserted, and then without the path ([authorization server discovery](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery)). Second, the client fetches the authorization server's own metadata (RFC 8414), which lists its endpoints and what it supports.

Two values must match along the way. The `resource` in the server's metadata must be identical to the URL the client used, or the client must not use the metadata ([RFC 9728, section 3.3](https://www.rfc-editor.org/rfc/rfc9728.txt)). And the `issuer` in the authorization server's metadata must be identical to the issuer the client built the well-known URL from ([RFC 8414, section 3.3](https://www.rfc-editor.org/rfc/rfc8414.txt)). Both checks stop a client from trusting a document that describes some other server.

In the shop, the server states its own URL and the authorization server states its issuer. The SDK does the server's half when you give `MCPServer` an `AuthSettings` and a token verifier: `issuer_url` names the authorization server, `resource_server_url` is the server's own endpoint URL, and `required_scopes` lists the scopes every request needs. The shop's server requires `orders:read` and `stock:read`, because every ticket needs one or both. `refunds:write` comes later, and only when a refund needs it. The token verifier is `lib.auth_server.JwtVerifier`, which checks a token's signature, issuer and expiry. On loopback the port, and so the resource URL, is known only once the socket is open, so the example builds the server in a function of its base URL, and `serve_built` from `lib.auth_server` opens the socket first. Then the example does what a client does: it sends `tools/list` with no token and follows the answer.

Example `discover-the-authorization-server` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""Protect the shop's server with OAuth, then follow its 401 to the authorization server, as a client does."""
from urllib.parse import urlsplit

import httpx2
from mcp.server.auth.settings import AuthSettings

from lib import auth_server, http_mcp, shop_tools


def protected(issuer: str):
    def build(base_url: str):                                   # the server must know its own URL: the resource
        settings = AuthSettings(issuer_url=issuer, resource_server_url=base_url + "/mcp",
                                required_scopes=["orders:read", "stock:read"], validate_token_resource=True)
        verifier = auth_server.JwtVerifier(issuer)
        return shop_tools.create_server(version="0.8.0", auth=settings, token_verifier=verifier).streamable_http_app()
    return build


with auth_server.serve() as issuer, auth_server.serve_built(protected(issuer.url)) as base_url:
    first = http_mcp.post(base_url + "/mcp", "tools/list")                     # no token
    print("status:", first.status_code)
    challenge = dict(part.split("=", 1) for part in first.headers["www-authenticate"][7:].split(", "))
    print("challenge parameters:", ", ".join(challenge))
    print("challenge error:", challenge["error"].strip('"'))
    metadata_url = challenge["resource_metadata"].strip('"')
    print("resource metadata path:", urlsplit(metadata_url).path)
    resource = httpx2.get(metadata_url).json()
    print("resource is the endpoint's URL:", resource["resource"] == base_url + "/mcp")
    print("authorization servers:", len(resource["authorization_servers"]))
    print("scopes_supported:", " ".join(resource["scopes_supported"]))
    found = resource["authorization_servers"][0]
    metadata = httpx2.get(found + "/.well-known/oauth-authorization-server").json()
    print("metadata issuer is the URL it came from:", metadata["issuer"] == found)
    for key in ("code_challenge_methods_supported", "client_id_metadata_document_supported",
                "authorization_response_iss_parameter_supported"):
        print(f"{key}:", metadata[key])
```

Output:

```text
status: 401
challenge parameters: error, error_description, resource_metadata
challenge error: invalid_token
resource metadata path: /.well-known/oauth-protected-resource/mcp
resource is the endpoint's URL: True
authorization servers: 1
scopes_supported: orders:read stock:read
metadata issuer is the URL it came from: True
code_challenge_methods_supported: ['S256']
client_id_metadata_document_supported: True
authorization_response_iss_parameter_supported: True
```

The first request got 401, with a challenge carrying `error, error_description, resource_metadata` and the error `invalid_token`. That error is the SDK's choice, and a departure from RFC 6750, which says a server SHOULD NOT include an error code when a request carries no credentials at all ([RFC 6750, section 3.1](https://www.rfc-editor.org/rfc/rfc6750.txt)). The `resource_metadata` URL's path is `/.well-known/oauth-protected-resource/mcp`: the well-known prefix with the server's path inserted, as RFC 9728 asks. The metadata names the endpoint's own URL as its resource (True), lists 1 authorization server, and gives `scopes_supported` as `orders:read stock:read`, which the SDK fills from `required_scopes`.

The challenge has no `scope` parameter, because the SDK's 401 never sends one (`mcp/server/auth/middleware/bearer_auth.py`). So a client falls back to `scopes_supported`. The specification's order is the challenge's `scope` first, then every scope in `scopes_supported`, then no `scope` at all ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). That is why `scopes_supported` should be the smallest set that works, not every scope the server knows: whatever it lists, every host asks every user for.

The authorization server's metadata passes the issuer check (True) and states three things the rest of this chapter relies on: PKCE methods `['S256']`, support for Client ID Metadata Documents (True) and `iss` on authorization responses (True). The SDK's client makes both matching checks for you. It raises `OAuthFlowError` when the metadata's `issuer` differs from the expected one, compared as plain strings ([SDK migration guide](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/docs/migration.md)). Its resource check is laxer than RFC 9728: it accepts metadata whose `resource` is a same-origin path prefix of the server's URL (`mcp/shared/auth_utils.py`), and a `validate_resource_url` callback on `OAuthClientProvider` replaces the check with your own.

**Working rule:** Give every protected server an `AuthSettings` with its endpoint's URL as `resource_server_url`, exactly as clients will type it, and the smallest `required_scopes` that every request needs. Check the chain with one request that carries no token: a 401, a `resource_metadata` URL, metadata whose `resource` is the endpoint, and authorization server metadata whose `issuer` is the URL you fetched it from. When a value differs by a trailing slash or a port, fix the configuration rather than relaxing the client.

## Identify the client with a metadata document {#client-id-metadata-documents}

[Find the authorization server from the resource](#protected-resource-metadata) tells the host where to get a token. The authorization server still has to know which client is asking, and a host meets MCP servers it has never seen, so it can't have registered with each one's authorization server in advance. The pinned revision ranks the ways to get a client ID: use pre-registered client information if there is any; otherwise a Client ID Metadata Document, if the authorization server advertises `client_id_metadata_document_supported`; otherwise Dynamic Client Registration; otherwise ask the user ([client registration](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration)).

A Client ID Metadata Document makes the client ID a URL. The client publishes a JSON document at an `https://` URL with a path, and that URL is its `client_id`. The document must contain at least `client_id`, equal to the URL exactly, `client_name` and `redirect_uris` ([client registration](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration)). The authorization server fetches the document when the client first appears, checks the ID and the redirect URI against it, and may cache it by its HTTP headers. It must not follow redirects while fetching, and must not cache an error ([metadata document draft -02](https://www.ietf.org/archive/id/draft-ietf-oauth-client-id-metadata-document-02.txt)). A document can't carry a shared secret: `client_secret` is forbidden, so a client identified this way is public and relies on PKCE, or proves itself with a key pair through `private_key_jwt` ([metadata document draft -02, section 4.1](https://www.ietf.org/archive/id/draft-ietf-oauth-client-id-metadata-document-02.txt)). The MCP specification links draft -00 of that document; we cite draft -02, the later text. A client ID from a document also works with any authorization server, where a pre-registered or registered client ID is bound to the server that issued it, and the pinned revision forbids reusing it with another ([client registration](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration)).

Dynamic Client Registration is deprecated at the pinned revision and kept as a fallback for authorization servers without metadata document support; its earliest removal is the first revision released on or after 2027-07-28 ([deprecated features](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)). [Replace dynamic client registration](#replace-dynamic-registration) moves a client off it.

The support team's host publishes its document at `https://support.fernhill.example/oauth/client.json`. The examples have no network, and `fernhill.example` never resolves, so the shop's authorization server can't fetch it. Rather than give the host an `http://` client ID that a loopback server could fetch, `lib.auth_server` keeps the document in a mapping from client ID URL to document, which stands in for the fetch, and applies to it the checks it would apply to a fetched one. That is pre-registration of the URL, which the draft allows as associating a client ID URL with its metadata "through other means" ([metadata document draft -02, section 5](https://www.ietf.org/archive/id/draft-ietf-oauth-client-id-metadata-document-02.txt)). It is a test-only stand-in: a deployed authorization server fetches the document over HTTPS. The example prints the document's key values, runs the server's checks on it and on three broken copies, gives the SDK an `http://` client ID, and then connects twice, to an authorization server that supports metadata documents and to one that doesn't.

Example `publish-client-metadata` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""The support host's Client ID Metadata Document, the checks an authorization server makes on it, and the SDK's
client using its URL as the client ID, with and without the authorization server's support."""
import asyncio

from mcp.client.auth import OAuthRegistrationError

from lib import auth_server, oauth_client, protected_shop

document = auth_server.client_document()                      # served at auth_server.CLIENT_ID
print("client_id:", document["client_id"])
print("redirect_uris:", ", ".join(document["redirect_uris"]))
print("token_endpoint_auth_method:", document["token_endpoint_auth_method"])
for label, url, candidate in [
        ("as published", auth_server.CLIENT_ID, document),
        ("with a secret", auth_server.CLIENT_ID, auth_server.client_document(client_secret="not-a-secret")),
        ("another client_id", auth_server.CLIENT_ID, auth_server.client_document(client_id="https://partner.example/")),
        ("on http", "http://support.fernhill.example/oauth/client.json", document)]:
    print(f"document {label}:", auth_server.document_problem(url, candidate) or "accepted")
try:
    oauth_client.provider("http://127.0.0.1/mcp", browser=oauth_client.ScriptedBrowser(),
                          client_metadata_url="http://localhost:4280/client.json")
except ValueError:
    print("SDK given an http client ID: ValueError")


async def connect(**server_options) -> None:
    with auth_server.serve(**server_options) as issuer, protected_shop.serve(issuer.url) as url:
        browser = oauth_client.ScriptedBrowser()
        try:
            async with oauth_client.connect(url, browser=browser) as client:
                await client.list_tools()
            print("client_id sent:", browser.requests[0]["client_id"])
        except* OAuthRegistrationError as group:                 # the SDK fell back to registration
            print("without metadata document support:", group.exceptions[0])


asyncio.run(connect())
asyncio.run(connect(advertise_cimd=False))
```

Output:

```text
client_id: https://support.fernhill.example/oauth/client.json
redirect_uris: http://localhost:4280/callback
token_endpoint_auth_method: none
document as published: accepted
document with a secret: document carries a shared secret
document another client_id: document client_id differs from its URL
document on http: client_id must be an https URL with a path
SDK given an http client ID: ValueError
client_id sent: https://support.fernhill.example/oauth/client.json
without metadata document support: Registration failed: 404 Not Found
```

The document names `https://support.fernhill.example/oauth/client.json` as its own ID, one redirect URI, `http://localhost:4280/callback`, and `none` as its token endpoint authentication method: the host holds no secret. The published document is accepted. A copy with a secret fails with "document carries a shared secret", one whose `client_id` names another site with "document client_id differs from its URL", and a client ID on `http` with "client_id must be an https URL with a path". The SDK makes the same `https` check on its side: given an `http://` client ID, `OAuthClientProvider` raises ValueError as soon as it's built (`mcp/client/auth/utils.py`).

Against the shop's authorization server, the SDK sent `https://support.fernhill.example/oauth/client.json` as the client ID and made no registration request. Against a server that doesn't advertise support, it fell back to Dynamic Client Registration without a word, and the flow ended with "Registration failed: 404 Not Found", because the shop's authorization server has no registration endpoint. The SDK's documentation calls this fallback silent ([OAuth clients](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/docs/client/oauth-clients.md)). For the host, that means an authorization server configured without metadata document support shows up as a registration error, not as a missing feature.

**Working rule:** Give every host one Client ID Metadata Document at a stable `https://` URL, with only the redirect URIs it uses and no secret, and pass that URL to the SDK as `client_metadata_url`. Use pre-registered credentials where an authorization server has issued them, since they rank first, and keep Dynamic Client Registration only for authorization servers that support nothing else. In tests on loopback, keep the client ID an `https://` URL and associate it with a local copy of the document in the test authorization server, rather than giving the client an `http://` ID that no production server accepts.

## Get a token with PKCE {#authorization-code-with-pkce}

With its client ID from [Identify the client with a metadata document](#client-id-metadata-documents), the host can ask for a token. MCP uses the authorization code grant. The host sends the user's browser to the authorization server's authorization endpoint, the user signs in and consents, and the browser returns to the host's redirect URI with a code, which the host exchanges for a token at the token endpoint. Three parameters of that exchange carry most of its security.

PKCE binds the code to the client that asked for it. The client makes a random `code_verifier`, sends its SHA-256 hash as `code_challenge` with `code_challenge_method=S256`, and reveals the verifier only in the token request, so someone who intercepts the code doesn't have it. MCP clients MUST use PKCE with `S256`, and MUST refuse to go on if the authorization server's metadata has no `code_challenge_methods_supported` ([security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations)). The `plain` method, where the challenge is the verifier itself, is "explicitly forbidden" in OAuth 2.1 since draft-16 ([OAuth 2.1 draft-16, section 7.5.2](https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-16.txt)). The MCP specification cites draft-13, which still allowed it ([OAuth 2.1 draft-13](https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-13.txt)).

The `resource` parameter (RFC 8707) names the server the token is for, by the server's canonical URI. MCP clients MUST send it in both the authorization request and the token request, whether or not the authorization server supports it ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). And `state`, which the client checks when the browser returns, ties the answer to the request.

In the shop, the SDK's client does all of this for the host. `lib.oauth_client.connect` gives it an `OAuthClientProvider` with the host's metadata document URL and a scripted browser in place of a person. The browser opens the authorization URL, follows the authorization server's redirects, and stops at the first one addressed to the redirect URI. The person's consent is scripted at the authorization server: the signed-in user grants every requested scope that their role allows. The example calls `get_order_status`, reads what the authorization server logged, and then sends the authorization server three requests the SDK never would.

Example `token-with-pkce` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""The SDK's client gets a token for the shop's server: authorization code with PKCE S256 and the resource parameter,
then what the authorization server does with a code sent twice, a wrong verifier and the plain method."""
import asyncio
import os

import httpx2

from lib import auth_server, loopback, oauth_client, protected_shop, shop_api


async def main() -> None:
    with auth_server.serve() as issuer, loopback.serve(shop_api.create_app()) as api_url:
        os.environ.update(shop_api.server_env(api_url))                  # the server runs in this process
        with protected_shop.serve(issuer.url) as url:
            browser, storage = oauth_client.ScriptedBrowser(), oauth_client.MemoryStorage()
            async with oauth_client.connect(url, browser=browser, storage=storage) as client:
                result = await client.call_tool("get_order_status", {"order_id": "O-1873"})
            print("O-1873 status:", result.structured_content["status"])
            asked, exchanged = issuer.events                              # /authorize, then /token
            print("authorization request:", ", ".join(key for key in asked if key != "endpoint"))
            print("code_challenge_method:", asked["code_challenge_method"])
            print("challenge is S256 of the verifier:",
                  oauth_client.s256(exchanged["code_verifier"]) == asked["code_challenge"])
            print("same resource in both requests:", asked["resource"] == exchanged["resource"] == url)
            claims = auth_server.claims(storage.tokens.access_token)
            for claim, expected in [("aud", url), ("iss", issuer.url)]:            # the server; the issuer
                print(f"token {claim} as expected:", claims[claim] == expected)
            print("token sub:", claims["sub"])
            print("token scope:", claims["scope"])
            print("refresh token:", storage.tokens.refresh_token)
            again = httpx2.post(issuer.url + "/token", data=exchanged)      # the same code a second time
            print("code sent twice:", again.status_code, again.json()["error"])
            code = oauth_client.authorize_by_hand(issuer.url, url, challenge=oauth_client.s256("the-real-verifier"))
            stolen = {**exchanged, "code": code["code"], "code_verifier": "a-guessed-verifier"}
            print("wrong verifier:", httpx2.post(issuer.url + "/token", data=stolen).json()["error"])
            plain = oauth_client.authorize_by_hand(issuer.url, url, challenge="the-real-verifier", method="plain")
            print("plain method:", plain["error"], "/", plain["error_description"])


asyncio.run(main())
```

Output:

```text
O-1873 status: delivered
authorization request: response_type, client_id, redirect_uri, state, code_challenge, code_challenge_method, resource, scope
code_challenge_method: S256
challenge is S256 of the verifier: True
same resource in both requests: True
token aud as expected: True
token iss as expected: True
token sub: staff-0007
token scope: orders:read stock:read
refresh token: None
code sent twice: 400 invalid_grant
wrong verifier: invalid_grant
plain method: invalid_request / PKCE with S256 is required
```

The call worked, and order O-1873 is delivered. The authorization request carried `response_type, client_id, redirect_uri, state, code_challenge, code_challenge_method, resource, scope`, with the method S256. Its challenge is the hash of the verifier that the token request revealed (True), and both requests named the same resource, the endpoint's URL (True). The access token is a JWT whose `aud` is the server's URL (True) and whose `iss` is the authorization server (True). Its scope is `orders:read stock:read`, the server's `scopes_supported`, because the 401 named no scope.

The token's `sub`, `staff-0007`, names the member of the support staff the host acts for, not a customer, and a server reads it from the SDK's `get_access_token().subject`. So a staff token can't by itself replace `SHOP_CUSTOMER_ID`, which the order completion in [Complete arguments for the user](#argument-completion) read from its environment over stdio. For a support host, the customer comes from the record of the ticket the staff member is working on, which the server looks up and checks, never from a tool argument. Only where customers sign in to a host themselves is `sub` the customer, the case [Keep the server from acting as a confused deputy](#confused-deputy) takes up. There is no refresh token (None): the shop's authorization server issues none, and the specification tells clients not to assume one ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).

The three requests the SDK never sends show what PKCE and single-use codes stop. The same code sent a second time got 400 invalid_grant: a code works once. A fresh code sent with a guessed verifier got invalid_grant, so a stolen code alone is worth nothing. A request with `plain` got "invalid_request / PKCE with S256 is required", because the shop's authorization server accepts only `S256`.

One check falls to the host. The SDK's client always sends `S256`, but it never reads `code_challenge_methods_supported`, so it goes ahead with an authorization server whose metadata leaves the field out (`mcp/client/auth/oauth2.py`). A host that must meet the specification fetches each authorization server's metadata itself before it connects, and refuses one that doesn't list `S256`.

**Working rule:** Let the SDK's `OAuthClientProvider` run the authorization code flow, and check once, from the authorization server's side, what it sends: `S256`, `state`, and a `resource` equal to the server's URL in both requests. Add the check the SDK skips, and refuse an authorization server whose metadata doesn't list `S256`. On an authorization server you run, accept only `S256`, make codes single-use and short-lived, and bind each code to its client, its redirect URI and its resource.

## Bind each token to one server {#token-audience}

The token from [Get a token with PKCE](#authorization-code-with-pkce) names the shop's server in `aud`, because the host sent `resource`. That protects no one unless the server checks it. An access token is a bearer credential: whoever holds it can present it. Suppose the support host also connects to a partner's MCP server that trusts the same authorization server. The partner's server receives the tokens the host gets for it, and if the shop's server accepted them, the partner's operator could replay them at the shop. RFC 8707 says the authorization server SHOULD restrict each token's audience to the requested resource, so that a token "legitimately presented to a resource cannot then be taken by that resource and presented elsewhere" ([RFC 8707](https://www.rfc-editor.org/rfc/rfc8707.txt)). The other half belongs to the server: MCP servers MUST validate that a token was issued for them as its audience, and MUST NOT accept or pass on any other token ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).

In the Python SDK at 2.3.0, the server's half is off by default. `AuthSettings.validate_token_resource` decides whether the server refuses a token whose `AccessToken.resource` isn't `resource_server_url`. Left unset, it warns with `MCPDeprecationWarning` and behaves as `False`, and version 3.0 makes `True` the default (`mcp/server/auth/settings.py`). The SDK compares the two as URLs, so the case of the scheme and host, a default port or a trailing slash makes no difference (`mcp/server/auth/middleware/bearer_auth.py`), and it compares whatever your token verifier puts in `AccessToken.resource`. The other way is a verifier that checks `aud` itself.

The example signs two tokens with the key of the shop's authorization server, one for the shop's server and one for the partner's, `https://partner.example/mcp`. It presents each to the shop's server in three configurations: the SDK's default, `validate_token_resource=True`, and a verifier that passes the shop's URL to the JWT library as the expected audience.

Example `wrong-audience-rejected` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""A token issued for another server, presented to the shop's server: accepted by the SDK's default, refused once the
server checks the audience, either through AuthSettings or in its own token verifier."""
import warnings

from mcp.server.auth.settings import AuthSettings

from lib import auth_server, http_mcp, shop_tools

PARTNER = "https://partner.example/mcp"                  # another MCP server, with the same authorization server
SCOPES = ["orders:read", "stock:read"]


def shop(issuer: str, validate_token_resource: bool | None, verifier_checks_aud: bool):
    def build(base_url: str):
        resource = base_url + "/mcp"
        verifier = auth_server.JwtVerifier(issuer, audience=resource if verifier_checks_aud else None)
        settings = AuthSettings(issuer_url=issuer, resource_server_url=resource, required_scopes=SCOPES,
                                validate_token_resource=validate_token_resource)
        return shop_tools.create_server(auth=settings, token_verifier=verifier).streamable_http_app()
    return build


with auth_server.serve() as issuer:
    for label, validate, in_verifier in [("SDK default", None, False), ("validate_token_resource=True", True, False),
                                         ("verifier checks aud", False, True)]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with auth_server.serve_built(shop(issuer.url, validate, in_verifier)) as base_url:
                url = base_url + "/mcp"
                own = auth_server.mint(issuer.url, url, SCOPES)
                foreign = auth_server.mint(issuer.url, PARTNER, SCOPES)
                for name, token in [("own token", own), ("partner's token", foreign)]:
                    response = http_mcp.post(url, "tools/list", headers={"Authorization": f"Bearer {token}"})
                    print(f"{label}, {name}:", response.status_code)
        print(f"{label}, warnings:", ", ".join(sorted({w.category.__name__ for w in caught})) or "none")
```

Output:

```text
SDK default, own token: 200
SDK default, partner's token: 200
SDK default, warnings: MCPDeprecationWarning
validate_token_resource=True, own token: 200
validate_token_resource=True, partner's token: 401
validate_token_resource=True, warnings: none
verifier checks aud, own token: 200
verifier checks aud, partner's token: 401
verifier checks aud, warnings: none
```

With the SDK's default, the shop's server answered the partner's token with 200: it listed its tools for a token issued to someone else. The only sign was a warning at startup, MCPDeprecationWarning. With `validate_token_resource=True`, the partner's token got 401, and with the audience check in the verifier it got 401. The shop's own token got 200 in all three configurations, and neither fix warned. Both fixes refuse with 401 and `invalid_token`, the answer the specification gives for a token that isn't valid for the server.

We recommend `validate_token_resource=True`, set in `lib.protected_shop`. It states the decision beside the server's other authorization settings, and it survives a change of token verifier. Check `aud` in the verifier as well when the verifier decodes the token anyway, since the second check costs nothing.

**Working rule:** Set `validate_token_resource=True` on every protected server, and make the token verifier fill `AccessToken.resource` from the token's `aud`. Treat an `MCPDeprecationWarning` from `AuthSettings` as a failed deployment, not as noise. Test the check with a token for another resource from the same authorization server, which must get 401. A server that calls another service on a client's behalf gets its own token for that service and never passes the client's token on ([Never pass a client's token through](#no-token-passthrough)).

## Validate the issuer of each response {#validate-the-issuer}

Binding the audience, as [Bind each token to one server](#token-audience) does, keeps a token from working at the wrong server. A mix-up attack strikes earlier, at the authorization code. A host that talks to several authorization servers sends each code to whichever server it believes answered. In a mix-up, an attacker's authorization server gets the host to start a flow with it, then sends the user's browser on to an honest authorization server. The honest server's code arrives at the host's redirect URI, and the host, still believing it is talking to the attacker, sends the code to the attacker's token endpoint. PKCE alone doesn't stop this, "because the client transmits the `code_verifier` to the attacker's token endpoint" ([security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)). Nor does `resource`, which the attacker rewrites in the request it forwards.

The defence is the `iss` parameter of RFC 9207: the authorization server names itself in its redirect, and the client compares that name with the server it sent the user to. The pinned revision introduced this check ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)). Before redirecting, the client records the issuer from the authorization server's validated metadata, and it compares `iss` with that record by exact string comparison, with no normalisation of case, ports or slashes ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)).

The rules are conditional. Authorization servers SHOULD include `iss`, and one that does MUST advertise `authorization_response_iss_parameter_supported`. A client MUST compare an `iss` that is present, whatever the metadata says, and MUST reject a response without `iss` only when the server advertised support; otherwise it proceeds. On a mismatch, the client must not act on or display any `error` in the response. The specification expects a later revision to make `iss` a MUST for authorization servers ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). Comparing a present `iss` that wasn't advertised uses the latitude RFC 9207 leaves to local policy; its default is that clients SHOULD discard such a response ([RFC 9207, section 2.4](https://www.rfc-editor.org/rfc/rfc9207.txt)).

In the shop's case, the attacker is the partner. The example sets up the attack with `MixUp` from `lib.auth_server`. The partner's MCP server names the attacker's authorization server, which copies the metadata of the shop's authorization server without `iss` support. Its authorization endpoint forwards the browser to the shop's authorization server with the host's own request, rewritten to ask for the shop's server and every scope. The host's client ID is a metadata document URL, which works with any authorization server, so the shop's authorization server sees a request from the real support host. The example runs the attack twice: against a shop authorization server that sends `iss`, and against one that doesn't.

Example `mix-up-attack-blocked` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""A mix-up attack on the support host: the partner's server names an attacker's authorization server, which sends the
user on to the shop's. The `iss` in the shop's answer gives it away; without `iss`, the attacker gets a token."""
import asyncio

from mcp.client.auth import OAuthFlowError, OAuthTokenError

from lib import auth_server, oauth_client, protected_shop


async def attempt(label: str, **shop_options) -> None:
    with auth_server.serve(**shop_options) as shop_issuer, protected_shop.serve(shop_issuer.url) as shop_url:
        with auth_server.serve_mix_up(shop_issuer.url, target=shop_url) as attacker, \
                protected_shop.serve(attacker.url) as partner_url:          # the partner's server names the attacker
            browser = oauth_client.ScriptedBrowser()
            try:
                async with oauth_client.connect(partner_url, browser=browser) as client:
                    await client.list_tools()
            except* (OAuthFlowError, OAuthTokenError) as group:
                error = group.exceptions[0]
                print(f"{label}, host stopped:", type(error).__name__, str(error).split(":")[0])
            print(f"{label}, user consented at the shop's server:", "code" in browser.arrived)
            print(f"{label}, iss in the answer:", "shop's" if browser.arrived.get("iss") == shop_issuer.url else "none")
            print(f"{label}, codes the attacker received:", len(attacker.stolen))
            for loot in attacker.stolen:
                claims = auth_server.claims(loot["access_token"])
                print(f"{label}, attacker's token is for the shop's server:", claims["aud"] == shop_url)
                print(f"{label}, attacker's token scope:", claims["scope"])


asyncio.run(attempt("shop sends iss"))
asyncio.run(attempt("shop omits iss", send_iss=False, advertise_iss=False))
```

Output:

```text
shop sends iss, host stopped: OAuthFlowError Authorization response iss mismatch
shop sends iss, user consented at the shop's server: True
shop sends iss, iss in the answer: shop's
shop sends iss, codes the attacker received: 0
shop omits iss, host stopped: OAuthTokenError Token exchange failed (400)
shop omits iss, user consented at the shop's server: True
shop omits iss, iss in the answer: none
shop omits iss, codes the attacker received: 1
shop omits iss, attacker's token is for the shop's server: True
shop omits iss, attacker's token scope: orders:read stock:read refunds:write
```

In both runs the user consented at the shop's authorization server (True), because the request in front of them came from the real support host. When the shop sends `iss`, the answer carried the shop's issuer, the SDK stopped with `OAuthFlowError Authorization response iss mismatch`, and the attacker received 0 codes. When the shop omits `iss`, the answer carried none, and the SDK went on, as the specification says it should for a server that never advertised `iss`. The attacker received 1 code with its verifier, redeemed it at the shop's authorization server, and holds a token for the shop's server (True) with the scope `orders:read stock:read refunds:write`, refunds included. The host saw only `OAuthTokenError Token exchange failed (400)`.

So the check protects a host only when the honest server sends `iss`; the security best practices say it "provides no protection against an honest server that does not" ([security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)). The SDK follows the specification's table exactly (`validate_authorization_response_iss` in `mcp/client/auth/utils.py`), so whether the shop's tokens can be stolen this way depends on the shop's authorization server, not on the host. The other defence RFC 9700 describes, a distinct redirect URI for each authorization server, doesn't help this host: it "cannot be used in scenarios where clients only register once for the use of many different issuers", and should be used only when nothing else is available ([RFC 9700, section 4.4.2.2](https://www.rfc-editor.org/rfc/rfc9700.txt)). A client identified by a metadata document is that case, with one `client_id` and one list of redirect URIs for every authorization server, so the honest server accepts whichever listed URI the attacker forwards. What a host can do without the server's help is limit which authorization servers it uses at all: an attacker's server that isn't on the host's allow-list never starts a flow.

**Working rule:** Send `iss` from every authorization server you run, and advertise it with `authorization_response_iss_parameter_supported: true`, so that clients reject an answer without it. In a host, keep the SDK's check, add no normalisation around it, and treat a mismatch as an attack: show the user none of that response's error text. When a host must use an authorization server that doesn't send `iss`, keep the host to an allow-list of authorization servers, and refuse or warn the user about any server not on it. Don't count on a separate redirect URI per server when the host is identified by a metadata document.

## Scope tools by what the token allows {#scopes-per-tool}

With a token checked as [Bind each token to one server](#token-audience) and [Validate the issuer of each response](#validate-the-issuer) describe, the shop's server knows who is calling. It still has to decide what each caller may do. The token lists the scopes the user granted, and the shop has three: `orders:read` for finding, reading and quoting orders, `stock:read` for checking stock, and `refunds:write` for issuing a refund, which only support leads may grant.

The SDK checks scopes per endpoint, not per tool: `AuthSettings.required_scopes` applies to every request, and the SDK's own 403 names no `scope` (`mcp/server/auth/middleware/bearer_auth.py`). The specification asks for a challenge a client can act on: 403 with `WWW-Authenticate: Bearer error="insufficient_scope"`, the `scope` the operation needs and `resource_metadata`, with "all scopes required for the current operation in a single challenge" ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). An HTTP middleware can send that. At the pinned revision each `tools/call` names its tool in the `Mcp-Name` header, but servers MUST decode its `=?base64?...?=` form before comparing it with the body ([Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)), so a check on the raw header lets an encoded `issue_refund` through. And a client at revision 2025-11-25, which the SDK's server still accepts on the same endpoint, sends no `Mcp-Name` at all.

So `lib.tool_scopes.require` decides on what the server will execute, with the credential the SDK will use. It checks the tool in the parsed body's `params.name`. `Mcp-Name`, decoded as the SDK decodes it, must match, or the request gets -32020, `HeaderMismatch`, and a body that isn't one JSON object, or repeats a key, is refused. The SDK authenticates with the first `Authorization` header (`mcp/server/auth/middleware/bearer_auth.py`), so the middleware refuses two of them with 400 `invalid_request`, and reads the token through the SDK's own `BearerAuthBackend`, answering 401 to a tool call whose token doesn't verify. It denies by default: a tool missing from the map is refused, methods that name nothing, such as `tools/list`, need only the endpoint's scopes, and any other method, such as `prompts/get`, `resources/read` or `tasks/get`, gets 403. `lib.protected_shop` maps all five tools, and `lib.tool_scopes.hide_unscoped` can hide the tools a token can't call ([Keep the tool list small](#keep-the-tool-list-small)). The example signs a token with `orders:read` and `stock:read`, lists the tools with hiding off and on, then sends hand-written calls.

Example `refund-needs-a-scope` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""Scopes per tool: the shop's server refuses a refund without `refunds:write` with a 403 challenge, decided on the
parsed JSON-RPC body however `Mcp-Name` is spelled or left out and with the one token the SDK reads, refuses
methods no scope maps, and can hide the tools a token can't call."""
import json
import os

from lib import auth_server, http_mcp, loopback, protected_shop, shop_api

REFUND = {"name": "issue_refund", "arguments": {"quote_id": "Q-00000000aa"}}
IN_BASE64 = "=?base64?aXNzdWVfcmVmdW5k?="                                   # "issue_refund", as the spec encodes it


def bearer(token: str, **headers: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", **headers}


with auth_server.serve() as issuer, loopback.serve(shop_api.create_app()) as api_url:
    os.environ.update(shop_api.server_env(api_url))                       # the server runs in this process
    for hide in (False, True):
        with protected_shop.serve(issuer.url, hide_tools=hide) as url:
            token = auth_server.mint(issuer.url, url, ["orders:read", "stock:read"])
            listed = http_mcp.post(url, "tools/list", headers=bearer(token)).json()["result"]
            print(f"hide_tools={hide}, tools listed:", ", ".join(tool["name"] for tool in listed["tools"]))
    print("tools/list cacheScope:", listed["cacheScope"])
    with protected_shop.serve(issuer.url) as url:
        token = auth_server.mint(issuer.url, url, ["orders:read", "stock:read"])
        status = http_mcp.post(url, "tools/call", {"name": "get_order_status", "arguments": {"order_id": "O-1873"}},
                               headers=bearer(token))
        print("get_order_status:", status.status_code)
        refused = http_mcp.post(url, "tools/call", REFUND, headers=bearer(token))
        print("issue_refund:", refused.status_code)
        print("challenge:", refused.headers["www-authenticate"].split(", resource_metadata")[0])
        print("challenge has resource_metadata:", "resource_metadata=" in refused.headers["www-authenticate"])
        lying = http_mcp.post(url, "tools/call", REFUND, headers=bearer(token, **{"Mcp-Name": "get_order_status"}))
        print("issue_refund named get_order_status in Mcp-Name:", lying.status_code, lying.json()["error"]["code"])
        encoded = http_mcp.post(url, "tools/call", REFUND, headers=bearer(token, **{"Mcp-Name": IN_BASE64}))
        print("issue_refund with Mcp-Name in base64:", encoded.status_code)
        print("issue_refund at 2025-11-25:", protected_shop.call_at_2025_11_25(url, token, REFUND).status_code)
        twice = protected_shop.call_with_headers(url, REFUND, [("Authorization", f"Bearer {token}"),
                                                               ("Authorization", "Bearer x")])    # read-only, then junk
        print("issue_refund with two Authorization headers:", twice.status_code, twice.json()["error"])
        unmapped = http_mcp.post(url, "prompts/get", {"name": "review_refund"}, headers=bearer(token))
        print("prompts/get, which no scope maps:", unmapped.status_code)
        lead = auth_server.mint(issuer.url, url, ["orders:read", "stock:read", "refunds:write"])
        allowed = http_mcp.post(url, "tools/call", REFUND, headers=bearer(lead))
        print("issue_refund with a lead token:", allowed.status_code, json.loads(allowed.text)["result"]["isError"])
```

Output:

```text
hide_tools=False, tools listed: find_orders, get_order_status, quote_refund, issue_refund, check_stock
hide_tools=True, tools listed: find_orders, get_order_status, quote_refund, check_stock
tools/list cacheScope: private
get_order_status: 200
issue_refund: 403
challenge: Bearer error="insufficient_scope", scope="refunds:write"
challenge has resource_metadata: True
issue_refund named get_order_status in Mcp-Name: 400 -32020
issue_refund with Mcp-Name in base64: 403
issue_refund at 2025-11-25: 403
issue_refund with two Authorization headers: 400 invalid_request
prompts/get, which no scope maps: 403
issue_refund with a lead token: 200 True
```

With hiding off, the token sees `find_orders, get_order_status, quote_refund, issue_refund, check_stock`; with hiding on, `find_orders, get_order_status, quote_refund, check_stock`. Either way the list's cache scope is `private`, the SDK's default, which suits a list that depends on the token ([Cache list results](#cache-list-results)). `get_order_status` got 200. `issue_refund` got 403, with the challenge `Bearer error="insufficient_scope", scope="refunds:write"` and a `resource_metadata` URL (True). A refund whose `Mcp-Name` claimed `get_order_status` got 400 -32020. Two requests that pass a check on the header alone were refused for scope: the refund with `Mcp-Name` in Base64 got 403, and the refund from a client at 2025-11-25 got 403. A refund with the read-only token and then a junk second `Authorization` header got 400 invalid_request; a check that read the last header would have let the SDK refund on the read-only token. An unmapped `prompts/get` got 403. With `refunds:write`, the call reached the tool, which answered 200 True: the status, then the result's `isError`, true because the example's quote ID doesn't exist.

**Working rule:** Map every tool to its scopes, and authorize on the parsed request with exactly the credential the SDK authenticates, never on a header alone: refuse two `Authorization` headers, and any method your map doesn't cover. Treat `Mcp-Name` as a hint that must match the body once decoded, and refuse any body you can't parse exactly as the server does. Answer a missing scope with a 403 `insufficient_scope` challenge that names all of the tool's scopes, and keep `required_scopes` to what every request needs.

### Ask for more scope when a call needs it {#step-up-scopes}

The 403 in [Scope tools by what the token allows](#scopes-per-tool) is half of step-up; the client does the other half. On `insufficient_scope`, the client authorizes again with the union of the scopes it asked for before and the scopes in the challenge, retries, and limits how many times it tries ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). The union rule is in the pinned revision's text and not in revision 2025-11-25's ([2025-11-25 authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)). Without it, a client that asked for `refunds:write` alone would lose `orders:read`, and its next order lookup would start the cycle again. The SDK's client steps up on 403 and unions the scopes (`mcp/client/auth/oauth2.py`).

In the shop, a support lead and a member of the support staff without the lead role each refund order O-1004 through the SDK's client. The refund, €24.98, is within the policy limit, so no confirmation is involved. The scripted consent lets the lead grant all three scopes and the other user only the two read scopes.

Example `step-up-for-refunds` (Python 3.12.15 · cryptography 50.0.2 · httpx2 2.16.0 · jsonschema 4.26.0 · mcp 2.3.0 · mcp-types 2.3.0 · pydantic 2.14.3 · pyjwt 2.15.1 · starlette 1.10.0 · uvicorn 0.54.0), passing in Edition 2026.11.10:

```python
"""Step-up: the SDK's client meets the refund's 403, asks the user again for the union of its scopes and
`refunds:write`, and retries. A user who may not grant `refunds:write` gets a token without it, and the refund fails."""
import asyncio
import os

from lib import auth_server, loopback, oauth_client, protected_shop, shop_api


async def refund(label: str, user_scopes: tuple[str, ...]) -> None:
    with auth_server.serve(user_scopes=user_scopes) as issuer, protected_shop.serve(issuer.url) as url:
        browser, storage = oauth_client.ScriptedBrowser(), oauth_client.MemoryStorage()
        async with oauth_client.connect(url, browser=browser, storage=storage) as client:
            quote = await client.call_tool("quote_refund", {"order_id": "O-1004", "reason": "arrived cracked"})
            print(f"{label}, quote amount:", quote.structured_content["amount"])
            print(f"{label}, quote within limit:", quote.structured_content["within_limit"])
            try:
                result = await client.call_tool("issue_refund", {"quote_id": quote.structured_content["quote_id"]})
                print(f"{label}, refund status:", result.structured_content["status"])
            except Exception as error:
                print(f"{label}, refund failed:", type(error).__name__, error)
        for number, asked in enumerate(browser.requests, start=1):
            print(f"{label}, authorization {number} asked for:", asked["scope"])
        print(f"{label}, token scope:", auth_server.claims(storage.tokens.access_token)["scope"])


async def main() -> None:
    with loopback.serve(shop_api.create_app()) as api_url:
        os.environ.update(shop_api.server_env(api_url))                    # the server runs in this process
        await refund("lead", auth_server.SCOPES)
        await refund("non-lead", ("orders:read", "stock:read"))


asyncio.run(main())
```

Output:

```text
lead, quote amount: 24.98
lead, quote within limit: True
lead, refund status: requested
lead, authorization 1 asked for: orders:read stock:read
lead, authorization 2 asked for: orders:read stock:read refunds:write
lead, token scope: orders:read stock:read refunds:write
non-lead, quote amount: 24.98
non-lead, quote within limit: True
non-lead, refund failed: MCPError Server returned an error response
non-lead, authorization 1 asked for: orders:read stock:read
non-lead, authorization 2 asked for: orders:read stock:read refunds:write
non-lead, token scope: orders:read stock:read
```

For the lead, the first authorization asked for `orders:read stock:read`. The refund's 403 started a second, which asked for `orders:read stock:read refunds:write`, the union, although the challenge named only `refunds:write`. The retry went through, and the refund's status is `requested`. For the other user, the second authorization asked for the same union, the user could grant only `orders:read stock:read`, and the retried call failed with `MCPError Server returned an error response`. The SDK stepped up once and stopped, so there was no loop. But the host got a generic error, not "this needs a lead".

**Working rule:** Let the SDK step up, and keep its union of scopes. List every tool a caller could gain by step-up, since a hidden tool never gets the 403 that starts it. In the host, compare the scope the token response granted with the scope the challenge asked for, and when they differ, treat it as a decision, not a fault: tell the user which scope the call needs and pass the ticket to someone who holds it. Never let an authorization server grant by step-up what a user's role doesn't allow; the client only asks, and the authorization server decides.

## What goes wrong in production {#authorization-in-production}

The shop's server, its authorization server and its host all work on loopback. In production they meet other people's authorization servers, gateways and clients, and each of these failures has a sign you can watch for.

**An authorization server that doesn't send `iss`.** It is a SHOULD at the pinned revision, so some authorization servers leave it out, and the SDK then proceeds without any defence against mix-up ([Validate the issuer of each response](#validate-the-issuer)). The sign is metadata without `authorization_response_iss_parameter_supported`. Check the metadata of each authorization server your host meets, and keep the host to an allow-list of authorization servers while any of them leaves `iss` out.

**The silent fallback to registration.** When an authorization server doesn't advertise Client ID Metadata Document support, the SDK registers dynamically without saying so ([OAuth clients](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/docs/client/oauth-clients.md)). The sign is registration errors, or a growing list of registered clients at the authorization server. Log which kind of client ID each connection used.

**The audience check is off.** A server without `validate_token_resource` accepts tokens issued for other servers, and the only sign is `MCPDeprecationWarning` at startup ([Bind each token to one server](#token-audience)). Make warnings from `AuthSettings` fail the deployment.

**An issuer with a trailing slash.** The issuer comparison is by exact string, so `https://auth.fernhill.example` and `https://auth.fernhill.example/` are different issuers, and the SDK raises "Authorization server metadata issuer mismatch". The SDK's metadata models keep a URL without a path as it was sent, but an `AnyHttpUrl` object built in Python still gains the slash, so pass URLs to the SDK as strings ([SDK migration guide](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v2.3.0/docs/migration.md)). The sign is `OAuthFlowError` on the first connection to a server, from every host.

**No PKCE check in the host.** The SDK's client never reads `code_challenge_methods_supported` ([Get a token with PKCE](#authorization-code-with-pkce)). Nothing fails, so the only sign is an audit: fetch each authorization server's metadata and look for `S256`.

**A `localhost` redirect taken over.** A metadata document proves which domain a client belongs to, not which program listens on a `localhost` redirect URI, and any local program can bind the port first. The specification says that metadata documents "cannot prevent `localhost` URL impersonation by themselves", and asks authorization servers to show the redirect's host name to the user and warn about redirects to `localhost` only ([security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations)). The sign is a consent screen that names the real host for a request no one at that machine made.

**An authorization server used to probe the network.** A server that fetches any client ID URL can be pointed at internal addresses. The draft says authorization servers MUST NOT fetch from special-use addresses, with a loopback exception only for development servers that themselves run on loopback ([metadata document draft -02, section 8.6](https://www.ietf.org/archive/id/draft-ietf-oauth-client-id-metadata-document-02.txt)). The sign is metadata fetches to private addresses in the authorization server's logs.

**Consent every few minutes.** The shop's authorization server issues no refresh token, so the host runs the whole flow again whenever a token expires, and the user consents again. If you issue refresh tokens to hosts, which are public clients, the authorization server MUST rotate them, and MCP servers SHOULD NOT list `offline_access` in their challenges or `scopes_supported` ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). The sign is authorization requests from one host at the token lifetime's interval.

**Step-up that can never succeed.** A server whose 403 names a scope the authorization server doesn't know, or one the user's role can't grant, sends every such call through a second authorization that fails. The sign is authorization requests in pairs for one tool call, followed by a generic error in the host ([Ask for more scope when a call needs it](#step-up-scopes)).

**Working rule:** Before the shop's server takes traffic, run three probes against the deployment: a request without a token gets 401 with a `resource_metadata` URL, a token for another resource gets 401, and a refund with a read-only token gets 403 with `scope="refunds:write"`, and the same refund with a second `Authorization` header gets 400. Then check the metadata of every authorization server your hosts use for `S256`, `iss` support and metadata document support, and watch 401s, 403s and authorization requests per host.

## Decisions this chapter made {#authorization-decisions}

- **The shop's server is an OAuth resource server** over Streamable HTTP, configured with the SDK's `AuthSettings`: its endpoint's URL as `resource_server_url`, `orders:read` and `stock:read` as `required_scopes`, and `validate_token_resource=True`.
- **The examples use a teaching authorization server,** `lib.auth_server`, not the SDK's built-in one: S256 only, `resource` required, `iss` sent and advertised, single-use codes, JWT access tokens with `aud` and `scope`, and no refresh tokens. It signs no one in, and its key derives from the book's public seed, so it must never be deployed. A deployment uses an established authorization server that offers S256 only, honours `resource`, sends and advertises `iss`, and supports Client ID Metadata Documents.
- **The support host is identified by a Client ID Metadata Document** at an `https://` URL on `support.fernhill.example`. In the examples the authorization server holds a local copy of the document in place of fetching it; Dynamic Client Registration isn't offered.
- **Hosts use the SDK's `OAuthClientProvider`** with `client_metadata_url`, and add the PKCE support check the SDK leaves out.
- **Tokens are checked for audience** by `AuthSettings`, and the token verifier reports `aud` as `AccessToken.resource`.
- **Scopes are per tool:** `orders:read` for finding, reading and quoting orders, `stock:read` for stock, and `refunds:write`, which only support leads can grant, for refunds. An HTTP middleware decides on the parsed JSON-RPC body, with `Mcp-Name` only as a hint that must match it, and with the one token the SDK authenticates, refusing a second `Authorization` header. It answers a missing scope with a 403 challenge, and refuses tools and named methods that it doesn't map.
- **`refunds:write` arrives by step-up,** never by default: it isn't in `scopes_supported`, and the SDK's client asks for the union of scopes when a refund needs it.
- **Every tool stays in `tools/list`,** so that step-up can start. Hiding tools by scope is available in `lib.tool_scopes` and unused.
- **Who the host acts for comes from the verified token's `sub`,** through `get_access_token()`, never from a tool argument: for the support host, a member of the staff. The customer a ticket concerns comes from the ticket record, which the server looks up and checks, not from the token or an argument. Only where customers sign in is `sub` the customer.
