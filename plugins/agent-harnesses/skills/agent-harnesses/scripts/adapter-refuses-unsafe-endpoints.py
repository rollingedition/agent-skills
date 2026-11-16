"""The OpenAI-compatible adapter refuses a redirect, a key over plain http to a remote host, and a non-http scheme. It sends
a remote URL through the environment's proxy and a loopback URL around it. Every request goes to a stub on 127.0.0.1, which
stands in for both the endpoint and the proxy, so no network is used. Each refusal prints one labelled line."""
from lib.models import OpenAICompatibleModel, proxy_env, refusal, stub_endpoint

REMOTE = "http://remote-host.invalid/v1"
MESSAGES = [{"role": "user", "content": "ping"}]

with stub_endpoint(200) as proxy, stub_endpoint(302) as target, proxy_env(proxy):
    loopback = f"{target.url}/v1"
    model = OpenAICompatibleModel(loopback, "model", max_tokens=8, api_key="DUMMY-KEY")
    reason = refusal(lambda: model.reply(MESSAGES, []))
    assert target.seen == ["/v1/chat/completions"], "a redirect was followed"
    print("redirect 302 on loopback:", reason)
    target.code = 307
    reason = refusal(lambda: model.reply(MESSAGES, []))
    print("redirect 307 on loopback:", reason)
    assert target.seen == ["/v1/chat/completions"] * 2, "a redirect was followed"
    print(f"requests to the redirect target: {target.seen.count('/collect')}")
    print(f"loopback requests through the proxy: {len(proxy.seen)}")

    remote = OpenAICompatibleModel(REMOTE, "model", max_tokens=8)
    reply = remote.reply(MESSAGES, [])
    assert reply.text == "ok" and proxy.seen == ["http://remote-host.invalid/v1/chat/completions"]
    print("remote request through the proxy:", proxy.seen[0])
    print("remote reply text:", reply.text)

    reason = refusal(lambda: OpenAICompatibleModel(REMOTE, "model", max_tokens=8, api_key="DUMMY-KEY"))
    print("key over plain http to a remote host:", reason)
    assert len(proxy.seen) == 1, "a request was made for the refused key"
    OpenAICompatibleModel("https://remote-host.invalid/v1", "model", max_tokens=8, api_key="DUMMY-KEY")
    print("key over https to a remote host: accepted, no request made")
    OpenAICompatibleModel(loopback, "model", max_tokens=8, api_key="DUMMY-KEY")
    print("key over http to loopback: accepted")
    reason = refusal(lambda: OpenAICompatibleModel("file:///v1", "model", max_tokens=8))
    print("file URL:", reason)
