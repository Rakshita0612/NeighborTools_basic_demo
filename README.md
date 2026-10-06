# 🌱 NeighborTools — Community Tool Library

**NeighborTools** is a full-stack community tool library application built with **Python**, **Streamlit**, and **Supabase (PostgreSQL, Auth & Storage)**. It empowers neighbors to lend and borrow tools they only need occasionally — such as power drills, lawn mowers, telescoping ladders, pressure washers, and woodworking jigs — saving money, reducing clutter, and building neighbourhood trust.

---

## 🚀 Key Features

1. **🏡 Home & Community Showcase:**
   - Friendly landing page explaining the 3-step tool sharing flow.
   - Live showcase of recently added community tools.
   - Quick action triggers to browse or list tools.

2. **🔍 Tool Discovery & Details:**
   - Search by tool name, description, or neighborhood.
   - Filter by category and real-time availability.
   - Sort by newest listings or alphabetical order.
   - Rich tool cards displaying photos, condition badges, neighborhood, and owner info.
   - Tool Detail modal with full descriptions, owner ratings/reviews, and reservation date picker.
   - Self-borrowing protection (members cannot reserve their own tools).

3. **➕ Tool Listing Management:**
   - List tools with name, category, condition, neighborhood, description, and availability notes.
   - Upload photos directly to Supabase Storage with preview and fallback image URL support.
   - Owners can edit listing details or archive tools (archived tools are removed from public browsing).

4. **📅 Reservations & Concurrency Safety:**
   - Borrowers select start and end dates with custom project notes.
   - Date validation: enforces `start_date <= end_date` and prevents booking past dates.
   - Safe database-level concurrency: prevents overlapping approved reservations on the same tool via PostgreSQL row locking (`approve_reservation` stored procedure).
   - Borrower view: track upcoming, pending, and completed reservations; cancel pending requests with confirmation.

5. **🤝 Handover & Return Tracking:**
   - Owners can confirm tool pickup with condition notes.
   - Either borrower or owner can record returns with timestamp and condition notes.
   - Timeline log tracking every handover event (`handover_logs`).

6. **⭐ 5-Star Reviews & Reputation:**
   - After a tool is returned, borrower can review owner and owner can review borrower.
   - 1 to 5 star ratings and written feedback.
   - Database constraint guarantees one review per party per completed reservation.
   - Average reputation scores and review counts displayed on member profiles.

7. **👤 Member Profiles & Privacy:**
   - Edit display name, neighborhood, and profile avatar.
   - View your active listings and reviews received.
   - Safe privacy: email addresses and private street addresses are never exposed publicly.

---

## 🛠️ Technology Stack

- **Frontend & App Logic:** Python 3.12 + Streamlit
- **Database:** Supabase PostgreSQL with UUID primary keys and timestamps
- **Authentication:** Supabase Auth (Email & Password, session tokens)
- **Object Storage:** Supabase Storage (`tool-photos` and `avatars` buckets)
- **Database Security:** Row Level Security (RLS) enabled on all tables
- **Styling:** Custom CSS design system with forest-green palette (`#1b4332`, `#2d6a4f`) and warm neutral background (`#fbfaf7`).

---

## 📁 Project Structure

```
NeighborTools/
├── .streamlit/
│   └── config.toml          # Streamlit theme configuration
├── components/
│   ├── __init__.py
│   ├── auth_modal.py        # Sign-in, sign-up, password reset
│   ├── header.py            # Wordmark and user status header
│   └── tool_card.py         # Reusable tool card component
├── pages_ui/
│   ├── __init__.py
│   ├── home_view.py         # Landing page and how-it-works
│   ├── browse_view.py       # Tool discovery and detail/reservation
│   ├── list_tool_view.py    # List new tool with photo upload
│   ├── my_reservations_view.py  # Borrower reservation management
│   ├── tool_requests_view.py    # Owner requests & handover tracking
│   └── profile_view.py      # Member profile & listing editor
├── app.py                   # Main Streamlit application entry point
├── config.py                # Environment configuration and constants
├── database.py              # Supabase API client & database queries
├── styles.py                # Custom CSS styling tokens
├── setup.sql                # Complete PostgreSQL schema, RLS & functions
├── requirements.txt         # Python package dependencies
├── .env.example             # Template environment variables
└── README.md                # Documentation and setup guide
```

---

## ⚙️ Setup & Installation Instructions

### 1. Clone & Install Dependencies

Ensure Python 3.10+ is installed:

```bash
# Navigate to directory
cd d:/Rakshii/NeighborTools

# Install requirements
pip install -r requirements.txt
```

### 2. Set Up Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create a new project.
2. Go to **Project Settings > API** to copy:
   - **Project URL**
   - **anon / public key** (Do NOT use the service_role key in frontend/client code).

### 3. Configure Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase credentials:

```ini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_TOOL_BUCKET=tool-photos
SUPABASE_AVATAR_BUCKET=avatars
```

### 4. Run SQL Schema in Supabase

1. Open your Supabase Dashboard and go to the **SQL Editor**.
2. Click **New query**.
3. Copy the entire contents of [`setup.sql`](file:///d:/Rakshii/NeighborTools/setup.sql) and paste it into the editor.
4. Click **Run**.

This script sets up:
- `profiles`, `tools`, `tool_images`, `reservations`, `handover_logs`, `reviews` tables.
- Foreign key constraints, unique constraints, and indexes.
- Row Level Security (RLS) policies for each table.
- Trigger `handle_new_user()` to auto-create profiles on registration.
- Trigger `trg_validate_reservation_update` ensuring protected reservation fields (tool, borrower, dates) are immutable and verifying status transitions.
- PostgreSQL function `approve_reservation()` with per-tool row locking (`FOR UPDATE` on `public.tools`) to guarantee simultaneous approval requests on the same tool cannot produce double bookings.
- Functions `decline_reservation()`, `cancel_reservation()`, `record_pickup()`, and `record_return()`.
- Storage buckets `tool-photos` and `avatars` with public access policies.

### 5. Storage Buckets (If not created by SQL)

In your Supabase Dashboard, go to **Storage**:
- Create a bucket named `tool-photos` with **Public bucket** enabled.
- Create a bucket named `avatars` with **Public bucket** enabled.

### 6. Start the Application

Run Streamlit:

```bash
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`.

---

## 🔒 Database Security & Row Level Security (RLS)

All tables in `setup.sql` enforce strict PostgreSQL RLS policies and trigger guards:

| Table | Policy Highlights |
|---|---|
| `profiles` | Publicly readable safe fields (display_name, neighborhood, avatar_url); editable only by `auth.uid() = id`. |
| `tools` | Public can view `status = 'active'`; owners can view and manage their own tools (including archived). |
| `tool_images`| Publicly viewable for active tools; insertable/deletable only by tool owners. |
| `reservations` | Viewable only by the borrower (`borrower_id = auth.uid()`) and tool owner; borrower can only cancel their own pending requests; owner can only approve or decline pending requests; protected fields (tool, borrower, dates) are immutable via trigger; pickups and returns require RPC functions. |
| `handover_logs` | Viewable by participants; insertable only by the tool owner for `picked_up` events and borrower/owner for `returned` events. |
| `reviews` | Publicly readable; insertable only by verified borrower or owner after reservation is `returned`; one review per party enforced. |

---

## 🧪 Interactive Preview Mode

If Supabase credentials are not configured yet, NeighborTools automatically runs in **Interactive Preview Mode**. You can freely explore the landing page, search through curated tools, test the reservation request flow, inspect handover logs, and try listing new tools. When you're ready, simply add your Supabase credentials into `.env` to connect live!
