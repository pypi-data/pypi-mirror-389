import argparse
import json
import zlib

import requests
from flask import Flask, Response, request

try:
    import brotli
except ImportError:
    try:
        import brotlicffi as brotli
    except ImportError:  # pragma: no cover - optional dependency
        brotli = None


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

EXCLUDED_REQUEST_HEADERS = {
    "host",
    "connection",
    "content-length",
    "transfer-encoding",
}

RESPONSE_PREVIEW_BYTES = 4096
REQUEST_LOG_PREVIEW_BYTES = 4096


def _infer_charset(content_type: str) -> str:
    if not content_type:
        return "utf-8"
    lower = content_type.lower()
    if "charset=" in lower:
        charset = lower.split("charset=", 1)[1].split(";", 1)[0].strip()
        if charset:
            return charset
    return "utf-8"


def _bytes_to_text(payload: bytes, charset: str) -> str:
    try:
        return payload.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return payload.decode("utf-8", errors="replace")

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path=""):
    base_target = args.target.rstrip("/")
    target_url = f"{base_target}/{path}" if path else base_target
    if request.query_string:
        target_url = f"{target_url}?{request.query_string.decode('utf-8', errors='ignore')}"

    payload = request.get_data(cache=True, as_text=False)
    request_charset = _infer_charset(request.headers.get("Content-Type", ""))

    # Print request information
    print(f"\n{'='*50}")
    print(f"Request Method: {request.method}")
    print(f"Target URL: {target_url}")
    print(f"Request Headers: {dict(request.headers)}")

    if payload:
        body_repr = None
        try:
            parsed = json.loads(payload)
            body_repr = json.dumps(parsed, ensure_ascii=False, indent=2)
        except (ValueError, TypeError):
            pass

        if body_repr is None:
            snippet = payload[:REQUEST_LOG_PREVIEW_BYTES]
            text_preview = _bytes_to_text(bytes(snippet), request_charset)
            suffix = "..." if len(payload) > len(snippet) else ""
            print(
                f"Request Body Preview ({len(snippet)} bytes): {text_preview}{suffix}"
            )
        else:
            truncated = (
                body_repr[:REQUEST_LOG_PREVIEW_BYTES] + "..."
                if len(body_repr) > REQUEST_LOG_PREVIEW_BYTES
                else body_repr
            )
            print("Request JSON Body:")
            print(truncated)

    # Forward request
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={
                key: value
                for key, value in request.headers
                if key.lower() not in EXCLUDED_REQUEST_HEADERS
            },
            data=payload,
            cookies=request.cookies,
            allow_redirects=True,
            stream=True,
            timeout=args.timeout,
        )
    except requests.exceptions.RequestException as exc:
        print(f"Request failed: {exc}")
        return Response(str(exc), status=502)

    if resp.history:
        print("Redirect history:")
        for previous in resp.history:
            location = previous.headers.get("Location", "<unknown>")
            print(f"  {previous.status_code} -> {location}")
        print(f"Final URL: {resp.url}")

    # Print response information
    print(f"\nResponse Status: {resp.status_code}")
    print(f"Response Headers: {dict(resp.headers)}")

    resp.raw.decode_content = False
    encoding = resp.headers.get("Content-Encoding", "").lower()
    charset = _infer_charset(resp.headers.get("Content-Type", ""))

    if request.method != "HEAD":
        print(
            "Response Body: <captured in-memory; preview logged up to "
            f"{RESPONSE_PREVIEW_BYTES} bytes>"
        )

    raw_body = bytearray()
    preview = bytearray()
    preview_truncated = False

    if request.method != "HEAD":
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue

            raw_body.extend(chunk)

            if len(preview) < RESPONSE_PREVIEW_BYTES:
                limit = RESPONSE_PREVIEW_BYTES - len(preview)
                preview.extend(chunk[:limit])
                if len(chunk) > limit:
                    preview_truncated = True
            else:
                preview_truncated = True

        body_bytes = bytes(raw_body)

        decoded_preview_bytes = None
        decoded_truncated = False
        decompress_error = None

        if encoding and encoding != "identity":
            try:
                if encoding == "gzip":
                    decompressed = zlib.decompress(body_bytes, 16 + zlib.MAX_WBITS)
                elif encoding == "deflate":
                    try:
                        decompressed = zlib.decompress(body_bytes)
                    except zlib.error:
                        decompressed = zlib.decompress(body_bytes, -zlib.MAX_WBITS)
                elif encoding == "br" and brotli is not None:
                    decompressed = brotli.decompress(body_bytes)
                else:
                    decompressed = None

                if decompressed is not None:
                    decoded_preview_bytes = decompressed[:RESPONSE_PREVIEW_BYTES]
                    decoded_truncated = len(decompressed) > RESPONSE_PREVIEW_BYTES
            except Exception as err:  # pragma: no cover - diagnostics only
                decompress_error = str(err)

        if decoded_preview_bytes is not None:
            preview_bytes = decoded_preview_bytes
            truncated = decoded_truncated
        else:
            preview_bytes = bytes(preview)
            truncated = preview_truncated

        if preview_bytes:
            body_preview = _bytes_to_text(preview_bytes, charset)
            suffix = "..." if truncated else ""
        else:
            body_preview = "<empty>"
            suffix = ""

        print(
            "Response Body Preview ({} bytes captured of up to {}): {}{}".format(
                len(preview_bytes), RESPONSE_PREVIEW_BYTES, body_preview, suffix
            )
        )
        if decompress_error and encoding and encoding != "identity":
            print(f"[decode note] Failed to decode {encoding}: {decompress_error}")
        elif encoding == "br" and brotli is None:
            print(
                f"[decode note] Install 'brotli' (or 'brotlicffi') to decode {encoding} bodies"
            )

        print(f"{'='*50}\n")
    else:
        body_bytes = b""
        print("Response Body: <not forwarded for HEAD request>")
        print(f"{'='*50}\n")

    resp.close()

    response = Response(
        body_bytes,
        status=resp.status_code,
    )

    for key, value in resp.headers.items():
        lower = key.lower()
        if lower in HOP_BY_HOP_HEADERS or lower == "content-length":
            continue
        response.headers[key] = value

    if request.method == "HEAD" and "Content-Length" in resp.headers:
        response.headers["Content-Length"] = resp.headers["Content-Length"]
    else:
        response.headers["Content-Length"] = str(len(body_bytes))

    response.headers.pop("Transfer-Encoding", None)

    if request.method == "HEAD":
        resp.close()

    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
HTTP proxy service for debugging API requests
Forwards requests to the specified API address and prints request and response information.
usage:
    python -m mxlm.api_proxy -t 127.0.0.1:58080
"""
    )
    parser.add_argument(
        "-t",
        "--target",
        required=True,
        help="Target API address, e.g. http://api.example.com:[port]",
    )
    parser.add_argument("--port", type=int, default=8000, help="Proxy server port")
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Upstream request timeout in seconds",
    )
    args = parser.parse_args()
    if "http" not in args.target:
        args.target = "http://" + args.target
    print(f"API proxy service started at http://localhost:{args.port}")
    print(f"Target API: {args.target}")
    app.run(host="0.0.0.0", port=args.port)
