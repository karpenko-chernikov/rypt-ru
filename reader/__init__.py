"""Telegram reader service.

Reads a public Telegram channel via MTProto, converts posts to a small HTML
dialect, downloads media, and serves them over a small authenticated HTTP API
for the website to pull from. Runs on a server outside Russia where Telegram is
reachable; the website only talks HTTPS to this service.
"""

__version__ = "1.0.0"
