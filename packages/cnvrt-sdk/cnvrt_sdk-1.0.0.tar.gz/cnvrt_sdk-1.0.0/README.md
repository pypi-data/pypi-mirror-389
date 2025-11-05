# CNVRT Python SDK

Official Python SDK for [CNVRT](https://docs.cnvrt.ing) media conversion API with x402 payment support.

## Installation

```bash
pip install cnvrt
```

## Quick Start

```python
from cnvrt import CNVRT

# Initialize client
client = CNVRT()

# Convert YouTube video to MP3
result = client.convert(
    url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    format="mp3",
    quality="best"
)

print(f"Download: {result['download_url']}")
```

## Features

- ✅ **Universal Media Conversion** - YouTube, TikTok, Instagram, Twitter, and 1000+ platforms
- ✅ **AI Transcription** - 95%+ accuracy with OpenAI Whisper
- ✅ **File Conversion** - Images, documents, PDFs, archives
- ✅ **x402 Payments** - Automatic USDC micropayments on Base & Solana
- ✅ **Agent-Friendly** - Pre-flight validation, cost estimation, batch operations
- ✅ **Type Hints** - Full typing support for better IDE experience
- ✅ **Async Support** - (Coming soon)

## Usage Examples

### Convert Media

```python
# From URL
result = client.convert(
    url="https://youtube.com/watch?v=example",
    format="mp4",
    quality="1080p"
)

# From file
with open("video.mov", "rb") as f:
    result = client.convert(
        file=f,
        format="mp4",
        quality="best"
    )

# Dry run (test without cost)
result = client.convert(
    url="https://youtube.com/watch?v=example",
    format="mp3",
    dry_run=True
)
```

### Transcribe Audio/Video

```python
# Transcribe from URL
result = client.transcribe(
    url="https://youtube.com/watch?v=example",
    language="en"
)

print(result["text"])
print(result["segments"])  # Timestamps

# Transcribe from file
with open("audio.mp3", "rb") as f:
    result = client.transcribe(file=f)
```

### Agent-Friendly Features

```python
# Validate before payment
validation = client.validate(
    url="https://youtube.com/watch?v=example",
    format="mp3",
    quality="best"
)

if validation["valid"]:
    result = client.convert(...)

# Estimate cost
cost = client.estimate_cost(
    url="https://youtube.com/watch?v=example",
    operation="convert",
    format="mp3"
)

print(f"Estimated cost: ${cost['total_usd']}")

# Auto-detect format
suggestion = client.detect_format(
    url="https://youtube.com/watch?v=example"
)

print(f"Suggested: {suggestion['suggested_format']}")

# Get usage stats
usage = client.get_usage()
print(f"Total requests: {usage['total_requests']}")
print(f"Success rate: {usage['success_rate']}%")
```

### Idempotency

Prevent duplicate processing with idempotency keys:

```python
result = client.convert(
    url="https://youtube.com/watch?v=example",
    format="mp3",
    idempotency_key="unique-key-123"
)

# Same request will return cached result
result2 = client.convert(
    url="https://youtube.com/watch?v=example",
    format="mp3",
    idempotency_key="unique-key-123"
)
```

### x402 Protocol Info

```python
# Get supported networks and payment info
x402_info = client.get_x402_info()

print(x402_info["networks"])  # Base, Solana
print(x402_info["facilitator"])  # CDP endpoints
```

### Health Check

```python
health = client.health_check()

if health["healthy"]:
    print("Service is up!")
```

## Configuration

```python
client = CNVRT(
    base_url="https://cnvrt.ing",  # Service URL
    network="base",                 # Payment network (base or solana)
    timeout=120,                    # Request timeout in seconds
)
```

## Error Handling

```python
from cnvrt import CNVRT, CNVRTError, PaymentError, ConversionError

client = CNVRT()

try:
    result = client.convert(
        url="https://youtube.com/watch?v=example",
        format="mp3"
    )
except PaymentError as e:
    print(f"Payment required: {e}")
except ConversionError as e:
    print(f"Conversion failed: {e}")
except CNVRTError as e:
    print(f"API error: {e}")
```

## Supported Formats

### Video Formats
MP4, WebM, MKV, AVI, MOV, FLV, WMV, etc.

### Audio Formats
MP3, WAV, M4A, FLAC, OGG, AAC, etc.

### Image Formats
JPG, PNG, WebP, GIF, BMP, TIFF, etc.

### Document Formats
PDF, DOCX, TXT, etc.

## Requirements

- Python 3.8+
- `requests` library

## Links

- **Documentation:** https://docs.cnvrt.ing
- **GitHub:** https://github.com/iclipz/cnvrt
- **PyPI:** https://pypi.org/project/cnvrt/
- **Support:** support@cnvrt.ing

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

