"""
Database operations for NeighborTools.
Integrates with Supabase (PostgreSQL, Auth, Storage) and provides safe fallbacks.
Enforces Row Level Security and database-level constraints.
"""

from datetime import datetime, date
import uuid
from typing import Dict, Any, List, Optional, Tuple
import os

from config import get_supabase_credentials, is_supabase_configured, get_storage_buckets

# =============================================================================
# IN-MEMORY DEMO DATA STORAGE (Used when Supabase is not configured yet)
# =============================================================================

MOCK_PROFILES = {
    "u_demo_1": {
        "id": "u_demo_1",
        "display_name": "Maya Lin",
        "neighborhood": "Maplewood Glen",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
        "email": "maya@example.com",
    },
    "u_demo_2": {
        "id": "u_demo_2",
        "display_name": "Marcus Vance",
        "neighborhood": "Oak Ridge",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=250&q=80",
        "email": "marcus@example.com",
    },
    "u_demo_3": {
        "id": "u_demo_3",
        "display_name": "Elena Rostova",
        "neighborhood": "Sunnyvale Heights",
        "avatar_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=250&q=80",
        "email": "elena@example.com",
    },
}

MOCK_TOOLS = [
    {
        "id": "tool_1",
        "owner_id": "u_demo_1",
        "name": "DeWalt 20V Max Cordless Drill & Impact Driver Set",
        "description": "High performance brushless compact drill and impact driver combo with two 2Ah batteries, charger, and sturdy hard case. Perfect for hanging shelves, assembling furniture, and light framing.",
        "category": "Power Tools",
        "condition": "Excellent",
        "neighborhood": "Maplewood Glen",
        "availability_notes": "Available most weekdays and weekends. Please recharge before returning.",
        "status": "active",
        "created_at": "2026-09-15T10:00:00Z",
        "images": [
            "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=700&q=80"
        ],
    },
    {
        "id": "tool_2",
        "owner_id": "u_demo_2",
        "name": "Honda Gas Lawn Mower (Self-Propelled)",
        "description": "Easy-start self-propelled push mower with 21-inch cutting deck and mulching bag. Cuts clean and runs smoothly on regular unleaded fuel.",
        "category": "Lawn & Garden",
        "condition": "Good",
        "neighborhood": "Oak Ridge",
        "availability_notes": "Pick up Saturday or Sunday mornings. Fuel is provided for initial use.",
        "status": "active",
        "created_at": "2026-09-20T14:30:00Z",
        "images": [
            "https://images.unsplash.com/photo-1589254065878-42c9da997008?auto=format&fit=crop&w=700&q=80"
        ],
    },
    {
        "id": "tool_3",
        "owner_id": "u_demo_1",
        "name": "Ryobi 1600 PSI Electric Pressure Washer",
        "description": "Compact and portable pressure washer, ideal for cleaning patio furniture, driveways, siding, and cars. Comes with 25ft hose and 3 nozzle tips (15°, soap, turbo).",
        "category": "Cleaning & Pressure Washers",
        "condition": "Like New",
        "neighborhood": "Maplewood Glen",
        "availability_notes": "Connects to standard garden hose and 120V outdoor outlet.",
        "status": "active",
        "created_at": "2026-09-28T09:15:00Z",
        "images": [
            "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=700&q=80"
        ],
    },
    {
        "id": "tool_4",
        "owner_id": "u_demo_3",
        "name": "Little Giant Multi-Position 22ft Telescoping Ladder",
        "description": "Heavy-duty ladder converts into A-frame, extension, staircase, and 90-degree ladder. Rated for 300 lbs. Fits into SUV trunk when collapsed.",
        "category": "Ladders & Scaffolding",
        "condition": "Like New",
        "neighborhood": "Sunnyvale Heights",
        "availability_notes": "Flexible pickup. Great for gutter cleaning or exterior painting.",
        "status": "active",
        "created_at": "2026-10-01T11:45:00Z",
        "images": [
            "https://upload.wikimedia.org/wikipedia/commons/a/ac/Extension_ladder_leaning_against_a_garage.JPG"
        ],
    },
    {
        "id": "tool_5",
        "owner_id": "u_demo_2",
        "name": "Kreg Pocket-Hole Jig K4 Woodworking System",
        "description": "Essential tool for building sturdy wooden cabinets, tables, bookshelves, and frames. Includes stepped drill bit, stop collar, and starter screws.",
        "category": "Woodworking",
        "condition": "Excellent",
        "neighborhood": "Oak Ridge",
        "availability_notes": "Available all week. Can give quick 5-min demo on pickup.",
        "status": "active",
        "created_at": "2026-10-03T16:00:00Z",
        "images": [
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=700&q=80"
        ],
    },
]

MOCK_RESERVATIONS = [
    {
        "id": "res_1",
        "tool_id": "tool_1",
        "borrower_id": "u_demo_3",
        "start_date": "2026-10-08",
        "end_date": "2026-10-10",
        "note": "Building some bookshelves in my living room this weekend!",
        "status": "pending",
        "created_at": "2026-10-05T08:00:00Z",
    },
    {
        "id": "res_2",
        "tool_id": "tool_2",
        "borrower_id": "u_demo_1",
        "start_date": "2026-09-22",
        "end_date": "2026-09-23",
        "note": "Mowing front and backyard before family visits.",
        "status": "returned",
        "created_at": "2026-09-21T09:30:00Z",
    },
]

MOCK_HANDOVER_LOGS = [
    {
        "id": "log_1",
        "reservation_id": "res_2",
        "event_type": "picked_up",
        "event_time": "2026-09-22T10:00:00Z",
        "condition_note": "Clean, full tank, blades sharp.",
        "recorded_by": "u_demo_2",
    },
    {
        "id": "log_2",
        "reservation_id": "res_2",
        "event_type": "returned",
        "event_time": "2026-09-23T17:30:00Z",
        "condition_note": "Wiped down deck, refilled gas. Thank you Marcus!",
        "recorded_by": "u_demo_1",
    },
]

MOCK_REVIEWS = [
    {
        "id": "rev_1",
        "reservation_id": "res_2",
        "reviewer_id": "u_demo_1",
        "reviewee_id": "u_demo_2",
        "rating": 5,
        "comment": "Marcus was wonderful to coordinate with! The mower started on the very first pull.",
        "created_at": "2026-09-24T12:00:00Z",
    },
    {
        "id": "rev_2",
        "reservation_id": "res_2",
        "reviewer_id": "u_demo_2",
        "reviewee_id": "u_demo_1",
        "rating": 5,
        "comment": "Maya returned the tool promptly and in pristine condition with a full tank of gas. Top tier neighbor!",
        "created_at": "2026-09-24T14:15:00Z",
    },
]


# =============================================================================
# SUPABASE CLIENT SINGLETON
# =============================================================================

_supabase_client = None


def get_client(access_token: Optional[str] = None):
    """
    Returns initialized Supabase client configured with anon key,
    optionally setting the user's JWT access token for RLS execution.
    """
    global _supabase_client
    if not is_supabase_configured():
        return None

    try:
        from supabase import create_client, Client

        url, key = get_supabase_credentials()
        if not url or not key:
            return None

        # Create or reuse client
        client = create_client(url, key)

        if access_token:
            # Attach auth header so PostgREST enforces RLS via auth.uid()
            client.postgrest.auth(access_token)

        return client
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None


# =============================================================================
# AUTHENTICATION FUNCTIONS
# =============================================================================


def sign_up_user(
    email: str, password: str, display_name: str, neighborhood: str
) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[str]]:
    """
    Signs up a new user via Supabase Auth.
    Returns (success, message, user_data, access_token).
    access_token is None when Supabase email confirmation is required.
    """
    client = get_client()
    if not client:
        # Mock mode sign-up
        user_id = f"u_user_{uuid.uuid4().hex[:8]}"
        user_data = {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "neighborhood": neighborhood or "Local Community",
            "avatar_url": None,
        }
        MOCK_PROFILES[user_id] = user_data
        return True, "Account created successfully in preview mode!", user_data, "mock_token"

    try:
        res = client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name,
                        "neighborhood": neighborhood or "Local Community",
                    }
                },
            }
        )
        if res.user:
            user_id = res.user.id
            session = getattr(res, "session", None)
            access_token = session.access_token if session else None

            user_data = {
                "id": user_id,
                "email": email,
                "display_name": display_name,
                "neighborhood": neighborhood or "Local Community",
                "avatar_url": None,
            }

            # If Supabase provided a session immediately (email confirmation disabled)
            if session and access_token:
                # Also try to update profiles table directly with user token
                try:
                    auth_client = get_client(access_token)
                    if auth_client:
                        auth_client.table("profiles").upsert(
                            {
                                "id": user_id,
                                "display_name": display_name,
                                "neighborhood": neighborhood or "Local Community",
                            }
                        ).execute()
                except Exception:
                    pass

                return (
                    True,
                    "Account created and signed in successfully!",
                    user_data,
                    access_token,
                )
            else:
                # Email confirmation is required by Supabase project settings
                return (
                    True,
                    "Account created! Please check your email inbox to confirm your address before signing in.",
                    user_data,
                    None,
                )
        return False, "Failed to create user account.", None, None
    except Exception as e:
        return False, str(e), None, None


def sign_in_user(
    email: str, password: str
) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[str]]:
    """Signs in user with email and password via Supabase Auth."""
    client = get_client()
    if not client:
        # Mock mode sign-in
        for p in MOCK_PROFILES.values():
            if p.get("email") == email:
                return True, "Signed in successfully!", p, "mock_token"
        # If not found, create a mock user session
        user_id = f"u_{abs(hash(email)) % 100000}"
        name = email.split("@")[0].capitalize()
        user_data = {
            "id": user_id,
            "email": email,
            "display_name": name,
            "neighborhood": "Neighborhood Resident",
            "avatar_url": None,
        }
        MOCK_PROFILES[user_id] = user_data
        return True, "Signed in successfully!", user_data, "mock_token"

    try:
        res = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if res.user and res.session:
            user_id = res.user.id
            access_token = res.session.access_token

            # Fetch profile details
            prof_res = (
                client.table("profiles")
                .select("*")
                .eq("id", user_id)
                .execute()
            )
            profile = prof_res.data[0] if prof_res.data else {}

            user_data = {
                "id": user_id,
                "email": res.user.email,
                "display_name": profile.get(
                    "display_name", email.split("@")[0]
                ),
                "neighborhood": profile.get(
                    "neighborhood", "Local Community"
                ),
                "avatar_url": profile.get("avatar_url"),
            }
            return True, "Signed in successfully!", user_data, access_token
        return False, "Invalid email or password.", None, None
    except Exception as e:
        return False, str(e), None, None


def reset_password(email: str) -> Tuple[bool, str]:
    """Sends password reset email via Supabase."""
    client = get_client()
    if not client:
        return True, f"Password reset instructions sent to {email} (preview mode)."
    try:
        client.auth.reset_password_for_email(email)
        return True, f"Password reset email sent to {email}."
    except Exception as e:
        return False, str(e)


# =============================================================================
# PROFILE OPERATIONS
# =============================================================================


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetches user profile by ID."""
    if not user_id:
        return None
    client = get_client()
    if not client:
        return MOCK_PROFILES.get(user_id)

    try:
        res = client.table("profiles").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return None


def update_profile(
    user_id: str,
    display_name: str,
    neighborhood: str,
    avatar_url: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """Updates member profile."""
    client = get_client(access_token)
    if not client:
        if user_id in MOCK_PROFILES:
            MOCK_PROFILES[user_id]["display_name"] = display_name
            MOCK_PROFILES[user_id]["neighborhood"] = neighborhood
            if avatar_url is not None:
                MOCK_PROFILES[user_id]["avatar_url"] = avatar_url
        return True, "Profile updated successfully!"

    try:
        payload = {
            "id": user_id,
            "display_name": display_name,
            "neighborhood": neighborhood,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if avatar_url:
            payload["avatar_url"] = avatar_url

        client.table("profiles").upsert(payload).execute()
        return True, "Profile updated successfully!"
    except Exception as e:
        return False, str(e)


# =============================================================================
# TOOL LISTING OPERATIONS
# =============================================================================


def list_tools(
    category: Optional[str] = None,
    search: Optional[str] = None,
    only_available: bool = False,
    sort_by: str = "newest",
    include_archived_for_owner: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches tools with filters, search, sorting, and attached owner information.
    """
    client = get_client()
    if not client:
        # Filter mock tools
        results = list(MOCK_TOOLS)

        # Filter out archived unless viewing own tools
        if not include_archived_for_owner:
            results = [t for t in results if t.get("status") == "active"]
        else:
            results = [
                t
                for t in results
                if t.get("status") == "active"
                or t.get("owner_id") == include_archived_for_owner
            ]

        # Category filter
        if category and category != "All Categories":
            results = [t for t in results if t.get("category") == category]

        # Search query
        if search:
            q = search.lower().strip()
            results = [
                t
                for t in results
                if q in t.get("name", "").lower()
                or q in t.get("description", "").lower()
                or q in t.get("neighborhood", "").lower()
            ]

        # Availability filter
        if only_available:
            booked_tool_ids = {
                r["tool_id"]
                for r in MOCK_RESERVATIONS
                if r.get("status") in ("approved", "picked_up")
            }
            results = [t for t in results if t["id"] not in booked_tool_ids]

        # Attach owner info & review summary
        for t in results:
            owner = MOCK_PROFILES.get(t["owner_id"], {})
            t["owner"] = owner
            # Check availability status badge
            is_booked = any(
                r["tool_id"] == t["id"]
                and r.get("status") in ("approved", "picked_up")
                for r in MOCK_RESERVATIONS
            )
            t["is_available"] = not is_booked

        # Sort
        if sort_by == "newest":
            results.sort(
                key=lambda x: x.get("created_at", ""), reverse=True
            )
        elif sort_by == "name":
            results.sort(key=lambda x: x.get("name", "").lower())

        return results

    try:
        query = client.table("tools").select(
            "*, owner:profiles(id, display_name, neighborhood, avatar_url), tool_images(image_url, display_order)"
        )

        if not include_archived_for_owner:
            query = query.eq("status", "active")

        if category and category != "All Categories":
            query = query.eq("category", category)

        if search:
            query = query.or_(
                f"name.ilike.%{search}%,description.ilike.%{search}%,neighborhood.ilike.%{search}%"
            )

        if sort_by == "newest":
            query = query.order("created_at", desc=True)
        elif sort_by == "name":
            query = query.order("name", desc=False)

        res = query.execute()
        tools = res.data or []

        # Format image arrays and availability for each tool
        for t in tools:
            # Flatten images
            images = t.get("tool_images", [])
            images.sort(key=lambda x: x.get("display_order", 0))
            t["images"] = [
                img["image_url"] for img in images if img.get("image_url")
            ]
            t["is_available"] = True  # Will be refined if reservations active

        return tools
    except Exception as e:
        print(f"Error querying tools from Supabase: {e}. Falling back to preview tools.")
        results = [dict(t) for t in MOCK_TOOLS]
        if not include_archived_for_owner:
            results = [t for t in results if t.get("status") == "active"]
        if category and category != "All Categories":
            results = [t for t in results if t.get("category") == category]
        if search:
            q = search.lower().strip()
            results = [
                t
                for t in results
                if q in t.get("name", "").lower()
                or q in t.get("description", "").lower()
                or q in t.get("neighborhood", "").lower()
            ]
        for t in results:
            t["owner"] = MOCK_PROFILES.get(t["owner_id"], {})
            t["is_available"] = True
        return results


def get_tool(tool_id: str) -> Optional[Dict[str, Any]]:
    """Fetches single tool with full details and owner info."""
    client = get_client()
    if not client:
        for t in MOCK_TOOLS:
            if t["id"] == tool_id:
                res = dict(t)
                res["owner"] = MOCK_PROFILES.get(res["owner_id"], {})
                return res
        return None

    try:
        res = (
            client.table("tools")
            .select(
                "*, owner:profiles(id, display_name, neighborhood, avatar_url), tool_images(image_url, display_order)"
            )
            .eq("id", tool_id)
            .execute()
        )
        if res.data:
            tool = res.data[0]
            images = tool.get("tool_images", [])
            images.sort(key=lambda x: x.get("display_order", 0))
            tool["images"] = [
                img["image_url"] for img in images if img.get("image_url")
            ]
            return tool
    except Exception as e:
        print(f"Error fetching tool {tool_id} from Supabase: {e}")

    # Fall back to mock tools if tool_id is in MOCK_TOOLS (e.g. tool_4) or Supabase query failed
    for t in MOCK_TOOLS:
        if t["id"] == tool_id:
            res = dict(t)
            res["owner"] = MOCK_PROFILES.get(res["owner_id"], {})
            return res
    return None


def create_tool(
    owner_id: str,
    name: str,
    description: str,
    category: str,
    condition: str,
    neighborhood: str,
    availability_notes: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]:
    """Creates a new tool listing."""
    client = get_client(access_token)
    if not client:
        new_id = f"tool_{uuid.uuid4().hex[:8]}"
        new_tool = {
            "id": new_id,
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "category": category,
            "condition": condition,
            "neighborhood": neighborhood,
            "availability_notes": availability_notes or "",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "images": image_urls
            or [
                "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=700&q=80"
            ],
        }
        MOCK_TOOLS.insert(0, new_tool)
        return True, "Tool listed successfully!", new_id

    try:
        tool_data = {
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "category": category,
            "condition": condition,
            "neighborhood": neighborhood,
            "availability_notes": availability_notes,
            "status": "active",
        }
        res = client.table("tools").insert(tool_data).execute()
        if res.data:
            created_tool_id = res.data[0]["id"]
            if image_urls:
                for idx, img_url in enumerate(image_urls):
                    client.table("tool_images").insert(
                        {
                            "tool_id": created_tool_id,
                            "image_url": img_url,
                            "display_order": idx,
                        }
                    ).execute()
            return True, "Tool listed successfully!", created_tool_id
        return False, "Failed to create tool listing.", None
    except Exception as e:
        return False, str(e), None


def update_tool(
    tool_id: str,
    owner_id: str,
    name: str,
    description: str,
    category: str,
    condition: str,
    neighborhood: str,
    availability_notes: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """Updates an existing tool listing."""
    client = get_client(access_token)
    if not client:
        for t in MOCK_TOOLS:
            if t["id"] == tool_id and t["owner_id"] == owner_id:
                t["name"] = name
                t["description"] = description
                t["category"] = category
                t["condition"] = condition
                t["neighborhood"] = neighborhood
                t["availability_notes"] = availability_notes or ""
                if image_urls:
                    t["images"] = image_urls
                return True, "Listing updated successfully!"
        return False, "Tool not found or unauthorized."

    try:
        payload = {
            "name": name,
            "description": description,
            "category": category,
            "condition": condition,
            "neighborhood": neighborhood,
            "availability_notes": availability_notes,
            "updated_at": datetime.utcnow().isoformat(),
        }
        client.table("tools").update(payload).eq("id", tool_id).eq(
            "owner_id", owner_id
        ).execute()

        if image_urls:
            # Delete old images and insert new
            try:
                client.table("tool_images").delete().eq(
                    "tool_id", tool_id
                ).execute()
                for idx, img in enumerate(image_urls):
                    client.table("tool_images").insert(
                        {
                            "tool_id": tool_id,
                            "image_url": img,
                            "display_order": idx,
                        }
                    ).execute()
            except Exception:
                pass

        return True, "Listing updated successfully!"
    except Exception as e:
        return False, str(e)


def archive_tool(
    tool_id: str, owner_id: str, access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """Archives a tool so it no longer appears in public browsing."""
    client = get_client(access_token)
    if not client:
        for t in MOCK_TOOLS:
            if t["id"] == tool_id and t["owner_id"] == owner_id:
                t["status"] = "archived"
                return True, "Tool has been archived."
        return False, "Tool not found or unauthorized."

    try:
        client.table("tools").update(
            {"status": "archived", "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", tool_id).eq("owner_id", owner_id).execute()
        return True, "Tool has been archived."
    except Exception as e:
        return False, str(e)


def upload_tool_image(
    file_bytes: bytes, file_name: str, access_token: Optional[str] = None
) -> Optional[str]:
    """Uploads photo to Supabase Storage bucket and returns public URL."""
    client = get_client(access_token)
    if not client:
        return None

    try:
        tool_bucket, _ = get_storage_buckets()
        file_ext = file_name.split(".")[-1].lower() if "." in file_name else "jpg"
        unique_name = f"tool_{uuid.uuid4().hex}.{file_ext}"

        # Upload binary
        res = client.storage.from_(tool_bucket).upload(
            unique_name,
            file_bytes,
            file_options={"content-type": f"image/{file_ext}"},
        )
        # Obtain public URL
        public_url = client.storage.from_(tool_bucket).get_public_url(unique_name)
        return public_url
    except Exception as e:
        print(f"Storage upload error: {e}")
        return None


# =============================================================================
# RESERVATIONS & CONCURRENCY
# =============================================================================


def create_reservation(
    tool_id: str,
    borrower_id: str,
    start_date: date,
    end_date: date,
    note: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Submits a reservation request after verifying:
    1. start_date <= end_date
    2. borrower is not the tool owner
    3. no overlapping approved or active bookings
    """
    if start_date > end_date:
        return False, "End date cannot be earlier than start date."

    if start_date < date.today():
        return False, "Start date cannot be in the past."

    client = get_client(access_token)
    if not client:
        # Check mock tool owner
        tool = None
        for t in MOCK_TOOLS:
            if t["id"] == tool_id:
                tool = t
                break
        if not tool:
            return False, "Tool not found."
        if tool["owner_id"] == borrower_id:
            return False, "You cannot borrow your own tool."

        # Check overlapping approved
        s_str = start_date.isoformat()
        e_str = end_date.isoformat()
        for r in MOCK_RESERVATIONS:
            if r["tool_id"] == tool_id and r["status"] in ("approved", "picked_up"):
                if r["start_date"] <= e_str and r["end_date"] >= s_str:
                    return (
                        False,
                        "This tool is already reserved for overlapping dates.",
                    )

        new_res = {
            "id": f"res_{uuid.uuid4().hex[:8]}",
            "tool_id": tool_id,
            "borrower_id": borrower_id,
            "start_date": s_str,
            "end_date": e_str,
            "note": note or "",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }
        MOCK_RESERVATIONS.insert(0, new_res)
        return True, "Reservation request submitted! Waiting for owner approval."

    try:
        # 1. Fetch tool to confirm owner
        t_res = client.table("tools").select("owner_id").eq("id", tool_id).execute()
        if not t_res.data:
            return False, "Tool not found."
        if t_res.data[0]["owner_id"] == borrower_id:
            return False, "You cannot request your own tool."

        # 2. Check for overlapping approved/picked_up reservations
        s_str = start_date.isoformat()
        e_str = end_date.isoformat()
        conflict_query = (
            client.table("reservations")
            .select("id")
            .eq("tool_id", tool_id)
            .in_("status", ["approved", "picked_up"])
            .lte("start_date", e_str)
            .gte("end_date", s_str)
            .execute()
        )
        if conflict_query.data:
            return (
                False,
                "This tool is already reserved or in use during those dates.",
            )

        # 3. Insert reservation
        payload = {
            "tool_id": tool_id,
            "borrower_id": borrower_id,
            "start_date": s_str,
            "end_date": e_str,
            "note": note,
            "status": "pending",
        }
        client.table("reservations").insert(payload).execute()
        return True, "Reservation request submitted! Waiting for owner approval."
    except Exception as e:
        return False, str(e)


def get_borrower_reservations(
    borrower_id: str, access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetches reservations where current user is borrower."""
    client = get_client(access_token)
    if not client:
        res_list = [
            r for r in MOCK_RESERVATIONS if r["borrower_id"] == borrower_id
        ]
        # Attach tool & owner
        for r in res_list:
            tool = next((t for t in MOCK_TOOLS if t["id"] == r["tool_id"]), None)
            if tool:
                r["tool"] = tool
                r["owner"] = MOCK_PROFILES.get(tool["owner_id"], {})
        return res_list

    try:
        res = (
            client.table("reservations")
            .select(
                "*, tool:tools(*, owner:profiles(id, display_name, neighborhood))"
            )
            .eq("borrower_id", borrower_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching borrower reservations: {e}")
        return []


def get_owner_reservations(
    owner_id: str, access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetches reservations requested on tools owned by the user."""
    client = get_client(access_token)
    if not client:
        owned_tool_ids = {
            t["id"] for t in MOCK_TOOLS if t["owner_id"] == owner_id
        }
        res_list = [
            r for r in MOCK_RESERVATIONS if r["tool_id"] in owned_tool_ids
        ]
        for r in res_list:
            tool = next((t for t in MOCK_TOOLS if t["id"] == r["tool_id"]), None)
            if tool:
                r["tool"] = tool
            r["borrower"] = MOCK_PROFILES.get(r["borrower_id"], {})
        return res_list

    try:
        # Join reservations where tool owner_id is owner_id
        res = (
            client.table("reservations")
            .select("*, tool:tools!inner(*), borrower:profiles(*)")
            .eq("tool.owner_id", owner_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching owner reservations: {e}")
        return []


def approve_reservation(
    reservation_id: str, owner_id: str, access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Approves a reservation using the database function approve_reservation
    to guarantee safe concurrency and prevent double bookings.
    Never uses direct table update fallback in live Supabase mode.
    """
    client = get_client(access_token)
    if not client:
        # Mock mode approval
        for r in MOCK_RESERVATIONS:
            if r["id"] == reservation_id:
                # Check conflict
                for other in MOCK_RESERVATIONS:
                    if (
                        other["id"] != r["id"]
                        and other["tool_id"] == r["tool_id"]
                        and other["status"] in ("approved", "picked_up")
                        and other["start_date"] <= r["end_date"]
                        and other["end_date"] >= r["start_date"]
                    ):
                        return (
                            False,
                            "Cannot approve: overlapping reservation already approved.",
                        )
                r["status"] = "approved"
                return True, "Reservation approved successfully!"
        return False, "Reservation not found."

    try:
        rpc_res = client.rpc(
            "approve_reservation", {"p_reservation_id": reservation_id}
        ).execute()
        if rpc_res.data and isinstance(rpc_res.data, dict):
            if rpc_res.data.get("success"):
                return True, rpc_res.data.get("message", "Reservation approved!")
            return False, rpc_res.data.get("error", "Failed to approve reservation.")
        return False, "Failed to approve reservation: database function did not return a valid response."
    except Exception as e:
        return False, f"Failed to approve reservation: {e}"


def decline_reservation(
    reservation_id: str, owner_id: str, access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """Declines a pending reservation."""
    client = get_client(access_token)
    if not client:
        for r in MOCK_RESERVATIONS:
            if r["id"] == reservation_id:
                r["status"] = "declined"
                return True, "Reservation declined."
        return False, "Reservation not found."

    try:
        # Attempt RPC first if present
        try:
            rpc_res = client.rpc(
                "decline_reservation", {"p_reservation_id": reservation_id}
            ).execute()
            if rpc_res.data and isinstance(rpc_res.data, dict):
                if rpc_res.data.get("success"):
                    return True, rpc_res.data.get("message", "Reservation declined.")
                return False, rpc_res.data.get("error", "Failed to decline reservation.")
        except Exception:
            pass

        client.table("reservations").update(
            {"status": "declined", "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", reservation_id).execute()
        return True, "Reservation declined."
    except Exception as e:
        return False, str(e)


def cancel_reservation(
    reservation_id: str, borrower_id: str, access_token: Optional[str] = None
) -> Tuple[bool, str]:
    """Borrower cancels their pending reservation request."""
    client = get_client(access_token)
    if not client:
        for r in MOCK_RESERVATIONS:
            if (
                r["id"] == reservation_id
                and r["borrower_id"] == borrower_id
                and r["status"] == "pending"
            ):
                r["status"] = "cancelled"
                return True, "Reservation request cancelled."
        return False, "Unable to cancel reservation."

    try:
        # Attempt RPC first if present
        try:
            rpc_res = client.rpc(
                "cancel_reservation", {"p_reservation_id": reservation_id}
            ).execute()
            if rpc_res.data and isinstance(rpc_res.data, dict):
                if rpc_res.data.get("success"):
                    return True, rpc_res.data.get("message", "Reservation request cancelled.")
                return False, rpc_res.data.get("error", "Unable to cancel reservation.")
        except Exception:
            pass

        client.table("reservations").update(
            {"status": "cancelled", "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", reservation_id).eq("borrower_id", borrower_id).eq(
            "status", "pending"
        ).execute()
        return True, "Reservation request cancelled."
    except Exception as e:
        return False, str(e)


# =============================================================================
# HANDOVER & RETURN TRACKING
# =============================================================================


def mark_handover_pickup(
    reservation_id: str,
    user_id: str,
    condition_note: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Marks tool as picked up and creates handover log entry via record_pickup RPC.
    Never uses direct table update fallback in live Supabase mode.
    """
    client = get_client(access_token)
    if not client:
        for r in MOCK_RESERVATIONS:
            if r["id"] == reservation_id and r["status"] == "approved":
                r["status"] = "picked_up"
                MOCK_HANDOVER_LOGS.append(
                    {
                        "id": f"log_{uuid.uuid4().hex[:8]}",
                        "reservation_id": reservation_id,
                        "event_type": "picked_up",
                        "event_time": datetime.utcnow().isoformat(),
                        "condition_note": condition_note or "",
                        "recorded_by": user_id,
                    }
                )
                return True, "Tool pickup confirmed!"
        return False, "Reservation not eligible for pickup."

    try:
        rpc_res = client.rpc(
            "record_pickup",
            {
                "p_reservation_id": reservation_id,
                "p_condition_note": condition_note,
            },
        ).execute()
        if rpc_res.data and isinstance(rpc_res.data, dict):
            if rpc_res.data.get("success"):
                return True, rpc_res.data.get(
                    "message", "Tool pickup confirmed!"
                )
            return False, rpc_res.data.get(
                "error", "Pickup transition failed."
            )
        return False, "Failed to record pickup: database function did not return a valid response."
    except Exception as e:
        return False, f"Failed to record pickup: {e}"


def mark_handover_return(
    reservation_id: str,
    user_id: str,
    condition_note: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Records return of tool and logs condition note via record_return RPC.
    Never uses direct table update fallback in live Supabase mode.
    """
    client = get_client(access_token)
    if not client:
        for r in MOCK_RESERVATIONS:
            if r["id"] == reservation_id and r["status"] in (
                "picked_up",
                "approved",
                "overdue",
            ):
                r["status"] = "returned"
                MOCK_HANDOVER_LOGS.append(
                    {
                        "id": f"log_{uuid.uuid4().hex[:8]}",
                        "reservation_id": reservation_id,
                        "event_type": "returned",
                        "event_time": datetime.utcnow().isoformat(),
                        "condition_note": condition_note or "",
                        "recorded_by": user_id,
                    }
                )
                return True, "Tool return recorded successfully!"
        return False, "Reservation not in borrowed state."

    try:
        rpc_res = client.rpc(
            "record_return",
            {
                "p_reservation_id": reservation_id,
                "p_condition_note": condition_note,
            },
        ).execute()
        if rpc_res.data and isinstance(rpc_res.data, dict):
            if rpc_res.data.get("success"):
                return True, rpc_res.data.get("message", "Tool returned successfully!")
            return False, rpc_res.data.get(
                "error", "Return transition failed."
            )
        return False, "Failed to record return: database function did not return a valid response."
    except Exception as e:
        return False, f"Failed to record return: {e}"


def get_handover_logs(
    reservation_id: str, access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves handover logs (pickup/return events) for a reservation."""
    client = get_client(access_token)
    if not client:
        return [
            h
            for h in MOCK_HANDOVER_LOGS
            if h["reservation_id"] == reservation_id
        ]

    try:
        res = (
            client.table("handover_logs")
            .select("*, recorder:profiles(display_name)")
            .eq("reservation_id", reservation_id)
            .order("event_time", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching handover logs: {e}")
        return []


# =============================================================================
# REVIEWS & RATINGS
# =============================================================================


def create_review(
    reservation_id: str,
    reviewer_id: str,
    reviewee_id: str,
    rating: int,
    comment: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Submits a review (1 to 5 stars) after a reservation is returned.
    Ensures one review per reviewer, reviewee, and reservation.
    """
    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 and 5."

    client = get_client(access_token)
    if not client:
        # Check if already reviewed in mock
        for rev in MOCK_REVIEWS:
            if (
                rev["reservation_id"] == reservation_id
                and rev["reviewer_id"] == reviewer_id
                and rev["reviewee_id"] == reviewee_id
            ):
                return False, "You have already submitted a review for this transaction."

        MOCK_REVIEWS.append(
            {
                "id": f"rev_{uuid.uuid4().hex[:8]}",
                "reservation_id": reservation_id,
                "reviewer_id": reviewer_id,
                "reviewee_id": reviewee_id,
                "rating": rating,
                "comment": comment or "",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return True, "Review posted! Thank you for supporting the community."

    try:
        payload = {
            "reservation_id": reservation_id,
            "reviewer_id": reviewer_id,
            "reviewee_id": reviewee_id,
            "rating": rating,
            "comment": comment,
        }
        client.table("reviews").insert(payload).execute()
        return True, "Review posted! Thank you for supporting the community."
    except Exception as e:
        err_msg = str(e)
        if "unique" in err_msg.lower():
            return False, "You have already submitted a review for this reservation."
        return False, err_msg


def get_user_reviews(user_id: str) -> List[Dict[str, Any]]:
    """Fetches reviews received by a user."""
    client = get_client()
    if not client:
        reviews = [r for r in MOCK_REVIEWS if r["reviewee_id"] == user_id]
        for r in reviews:
            r["reviewer"] = MOCK_PROFILES.get(r["reviewer_id"], {})
        return reviews

    try:
        res = (
            client.table("reviews")
            .select("*, reviewer:profiles(id, display_name, avatar_url, neighborhood)")
            .eq("reviewee_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        reviews = [r for r in MOCK_REVIEWS if r["reviewee_id"] == user_id]
        for r in reviews:
            r["reviewer"] = MOCK_PROFILES.get(r["reviewer_id"], {})
        return reviews


def get_user_rating_summary(user_id: str) -> Tuple[float, int]:
    """Calculates average rating and total review count for a user."""
    reviews = get_user_reviews(user_id)
    if not reviews:
        return 0.0, 0
    total = sum(r["rating"] for r in reviews)
    avg = round(total / len(reviews), 1)
    return avg, len(reviews)


def has_user_reviewed_reservation(
    reservation_id: str, reviewer_id: str
) -> bool:
    """Checks if reviewer has already reviewed this reservation."""
    client = get_client()
    if not client:
        return any(
            r["reservation_id"] == reservation_id
            and r["reviewer_id"] == reviewer_id
            for r in MOCK_REVIEWS
        )

    try:
        res = (
            client.table("reviews")
            .select("id")
            .eq("reservation_id", reservation_id)
            .eq("reviewer_id", reviewer_id)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False
