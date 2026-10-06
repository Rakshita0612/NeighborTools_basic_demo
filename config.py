"""
Configuration module for NeighborTools.
Handles environment variables, Supabase connection settings, and app constants.
"""

import os
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# App Brand Constants
APP_NAME = "NeighborTools"
APP_TAGLINE = "Your friendly neighborhood tool-sharing library"
APP_ICON = "🌱"

# Tool Categories
CATEGORIES = [
    "All Categories",
    "Power Tools",
    "Lawn & Garden",
    "Hand Tools",
    "Woodworking",
    "Painting & Drywall",
    "Plumbing & Electrical",
    "Automotive",
    "Cleaning & Pressure Washers",
    "Ladders & Scaffolding",
    "Other",
]

# Tool Conditions
CONDITIONS = ["Like New", "Excellent", "Good", "Fair"]

# Reservation Statuses
RESERVATION_STATUSES = [
    "pending",
    "approved",
    "declined",
    "cancelled",
    "picked_up",
    "returned",
    "overdue",
]

# Universal resilient fallback image (inline SVG data URI, 0 network requests, never breaks)
FALLBACK_TOOL_IMAGE = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgMzAwIiB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCI+CiAgPHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNmNGYxZWEiLz4KICA8cmVjdCB4PSIyMCIgeT0iMjAiIHdpZHRoPSIzNjAiIGhlaWdodD0iMjYwIiByeD0iMTIiIGZpbGw9IiNlOGU0ZGEiIHN0cm9rZT0iI2Q1Y2ViZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtZGFzaGFycmF5PSI2IDYiLz4KICA8ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxNjAsIDkwKSIgc3Ryb2tlPSIjMmQ2YTRmIiBzdHJva2Utd2lkdGg9IjMuNSIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj4KICAgIDxwYXRoIGQ9Ik0xNC43IDYuM2ExIDEgMCAwIDAgMCAxLjRsMS42IDEuNmExIDEgMCAwIDAgMS40IDBsMy43Ny0zLjc3YTYgNiAwIDAgMS03Ljk0IDcuOTRsLTYuOTEgNi45MWEyLjEyIDIuMTIgMCAwIDEtMy0zbDYuOTEtNi45MWE2IDYgMCAwIDEgNy45NC03Ljk0bC0zLjc2IDMuNzZ6Ii8+CiAgICA8cGF0aCBkPSJNNDUgMTUgTDY1IDM1Ii8+CiAgICA8cmVjdCB4PSIxMCIgeT0iNDUiIHdpZHRoPSI2MCIgaGVpZ2h0PSIzMiIgcng9IjQiIGZpbGw9IiMyZDZhNGYiIGZpbGwtb3BhY2l0eT0iMC4xNSIgc3Ryb2tlPSIjMmQ2YTRmIi8+CiAgICA8cGF0aCBkPSJNMjUgNDUgVjM1IEg1NSBWNDUiLz4KICAgIDxjaXJjbGUgY3g9IjQwIiBjeT0iNjEiIHI9IjMiIGZpbGw9IiMyZDZhNGYiLz4KICA8L2c+CiAgPHRleHQgeD0iMjAwIiB5PSIxOTAiIGZvbnQtZmFtaWx5PSItYXBwbGUtc3lzdGVtLCBCbGlua01hY1N5c3RlbUZvbnQsICdTZWdvZSBVSScsIFJvYm90bywgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNiIgZm9udC13ZWlnaHQ9IjYwMCIgZmlsbD0iIzJkNmE0ZiIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TmVpZ2hib3JUb29sczwvdGV4dD4KICA8dGV4dCB4PSIyMDAiIHk9IjIxNSIgZm9udC1mYW1pbHk9Ii1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgUm9ib3RvLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiBmaWxsPSIjNmI3MjgwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5ObyBwaG90byBhdmFpbGFibGU8L3RleHQ+Cjwvc3ZnPg=="
)


def get_supabase_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves Supabase URL and Anon/Publishable Key from environment variables,
    Streamlit secrets, or session state. Never uses service-role keys.
    """
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    # Avoid default placeholder values
    if "your-project-id" in url or "your-anon-public-key" in key:
        return None, None

    if not url or not key:
        return None, None

    return url, key


def is_supabase_configured() -> bool:
    """Returns True if valid Supabase URL and Anon key are available."""
    url, key = get_supabase_credentials()
    return bool(url and key)


def get_storage_buckets() -> Tuple[str, str]:
    """Returns the bucket names for tool images and profile avatars."""
    tool_bucket = os.getenv("SUPABASE_TOOL_BUCKET", "tool-photos").strip()
    avatar_bucket = os.getenv("SUPABASE_AVATAR_BUCKET", "avatars").strip()
    return tool_bucket, avatar_bucket
