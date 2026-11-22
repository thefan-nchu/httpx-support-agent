# HTTPX 0.28.1 / _urlparse.py / PATH_SAFE

```python
PATH_SAFE = "".join(
    [
        chr(i)
        for i in range(0x20, 0x7F)
        if i not in (0x20, 0x22, 0x23, 0x3C, 0x3E) + (0x3F, 0x60, 0x7B, 0x7D)
    ]
)
```