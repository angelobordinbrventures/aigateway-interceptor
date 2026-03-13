# ADR 001: Proxy Technology Selection

**Status:** Accepted
**Date:** 2026-03-13
**Decision Makers:** Engineering Team

## Context

The AIGateway Interceptor requires a transparent HTTPS proxy capable of intercepting, inspecting, and modifying traffic between users and AI provider APIs. The proxy must:

1. Perform TLS interception (man-in-the-middle) to inspect HTTPS request bodies
2. Be scriptable to integrate custom DLP logic
3. Support high throughput with low latency overhead
4. Handle WebSocket and streaming responses (for AI chat APIs)
5. Be maintainable by a Python-focused team

## Options Considered

### Option A: mitmproxy (Python)

- Mature, well-documented HTTPS proxy with built-in TLS interception
- Python scripting API (`addon` system) for request/response modification
- Active open-source community, regularly updated
- Supports HTTP/1.1, HTTP/2, WebSocket
- Can run in regular, transparent, or reverse proxy modes
- ~15 years of development history

### Option B: NGINX + Lua (OpenResty)

- High-performance reverse proxy
- Lua scripting via OpenResty for request inspection
- Excellent for traditional reverse proxy workloads
- TLS interception requires complex configuration and is not a primary use case
- Lua ecosystem is smaller than Python for DLP/NLP libraries

### Option C: Envoy Proxy + WASM

- Cloud-native proxy with extensibility via WebAssembly filters
- Strong performance characteristics
- WASM filter development is more complex (Go/Rust/C++)
- TLS interception (SDS) is possible but configuration-heavy
- Overkill for a single-purpose interception proxy

### Option D: Custom Go Proxy

- Full control over implementation
- High performance with Go's concurrency model
- Requires implementing TLS interception from scratch
- Significant development effort for a solved problem
- Testing and edge case handling would take months

### Option E: Squid Proxy + ICAP

- Traditional enterprise proxy with ICAP protocol for content inspection
- Well-suited for corporate environments
- ICAP server must be written separately
- Adds architectural complexity (two services for one function)
- Less flexible scripting compared to mitmproxy

## Decision

**We chose mitmproxy (Option A).**

## Rationale

1. **TLS interception is a first-class feature.** mitmproxy was built for exactly this purpose. The CA certificate management, certificate generation, and TLS handling are battle-tested and work out of the box.

2. **Python addon system aligns with our DLP stack.** Our DLP detector, anonymizer, and policy engine are all Python. mitmproxy's addon API allows us to plug these directly into the request pipeline without network hops or serialization overhead.

3. **Rapid development.** With mitmproxy handling the proxy infrastructure, we focused entirely on DLP logic. The initial proxy implementation was completed in days, not weeks.

4. **Streaming support.** AI APIs increasingly use Server-Sent Events (SSE) for streaming responses. mitmproxy handles these correctly, and our addons can inspect streamed content.

5. **Operational simplicity.** A single Python process handles proxying, DLP, and policy evaluation. No inter-process communication, no additional services.

## Trade-offs Accepted

- **Performance ceiling.** mitmproxy (Python) will not match the raw throughput of Go or C++ proxies. For our use case (intercepting AI API calls, not general web traffic), this is acceptable. AI API calls are relatively infrequent and high-latency by nature.

- **Resource usage.** Python processes use more memory than equivalent Go services. We mitigate this with container resource limits.

- **Single-threaded processing.** mitmproxy uses asyncio but runs in a single process. If throughput becomes a bottleneck, we can scale horizontally (multiple proxy instances behind a load balancer).

## Consequences

- All proxy-layer code is Python 3.11+
- The proxy service depends on the `mitmproxy` package
- Custom CA certificate generation and distribution is required for TLS interception
- Clients must trust the custom CA or use explicit proxy configuration
- Future performance optimization may require moving to a Go-based proxy (unlikely given the use case)

## References

- [mitmproxy Documentation](https://docs.mitmproxy.org/)
- [mitmproxy Addon API](https://docs.mitmproxy.org/stable/addons-overview/)
- [Envoy WASM Filters](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/wasm_filter)
- [Squid ICAP](http://www.squid-cache.org/Doc/config/icap_enable/)
