-- =============================================================================
-- NeighborTools - Complete Supabase PostgreSQL Schema & Security Policies
-- =============================================================================
-- Run this script in the Supabase SQL Editor (Dashboard > SQL Editor > New query).
-- It establishes all tables, constraints, indexes, triggers, database functions,
-- and Row Level Security (RLS) policies.
-- =============================================================================

-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. PROFILES TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text not null,
    neighborhood text not null default 'Neighborhood Local',
    avatar_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Trigger to automatically create a profile row when a new user registers
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, display_name, neighborhood, avatar_url)
    values (
        new.id,
        coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1), 'Neighbor'),
        coalesce(new.raw_user_meta_data->>'neighborhood', 'Local Community'),
        new.raw_user_meta_data->>'avatar_url'
    )
    on conflict (id) do update set
        display_name = coalesce(excluded.display_name, profiles.display_name),
        neighborhood = coalesce(excluded.neighborhood, profiles.neighborhood),
        avatar_url = coalesce(excluded.avatar_url, profiles.avatar_url),
        updated_at = now();
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- -----------------------------------------------------------------------------
-- 2. TOOLS TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.tools (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    description text not null,
    category text not null,
    condition text not null check (condition in ('Like New', 'Excellent', 'Good', 'Fair')),
    neighborhood text not null,
    availability_notes text,
    status text not null default 'active' check (status in ('active', 'archived')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_tools_owner_id on public.tools(owner_id);
create index if not exists idx_tools_status on public.tools(status);
create index if not exists idx_tools_category on public.tools(category);
create index if not exists idx_tools_created_at on public.tools(created_at desc);

-- -----------------------------------------------------------------------------
-- 3. TOOL IMAGES TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.tool_images (
    id uuid primary key default gen_random_uuid(),
    tool_id uuid not null references public.tools(id) on delete cascade,
    image_url text not null,
    display_order integer not null default 0,
    created_at timestamptz not null default now()
);

create index if not exists idx_tool_images_tool_id on public.tool_images(tool_id);

-- -----------------------------------------------------------------------------
-- 4. RESERVATIONS TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.reservations (
    id uuid primary key default gen_random_uuid(),
    tool_id uuid not null references public.tools(id) on delete cascade,
    borrower_id uuid not null references public.profiles(id) on delete cascade,
    start_date date not null,
    end_date date not null,
    note text,
    status text not null default 'pending' check (status in ('pending', 'approved', 'declined', 'cancelled', 'picked_up', 'returned', 'overdue')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint check_reservation_dates check (start_date <= end_date)
);

create index if not exists idx_reservations_tool_id on public.reservations(tool_id);
create index if not exists idx_reservations_borrower_id on public.reservations(borrower_id);
create index if not exists idx_reservations_status on public.reservations(status);
create index if not exists idx_reservations_dates on public.reservations(start_date, end_date);

-- -----------------------------------------------------------------------------
-- 5. HANDOVER LOGS TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.handover_logs (
    id uuid primary key default gen_random_uuid(),
    reservation_id uuid not null references public.reservations(id) on delete cascade,
    event_type text not null check (event_type in ('picked_up', 'returned')),
    event_time timestamptz not null default now(),
    condition_note text,
    recorded_by uuid not null references public.profiles(id) on delete cascade,
    created_at timestamptz not null default now()
);

create index if not exists idx_handover_logs_reservation_id on public.handover_logs(reservation_id);

-- -----------------------------------------------------------------------------
-- 6. REVIEWS TABLE
-- -----------------------------------------------------------------------------
create table if not exists public.reviews (
    id uuid primary key default gen_random_uuid(),
    reservation_id uuid not null references public.reservations(id) on delete cascade,
    reviewer_id uuid not null references public.profiles(id) on delete cascade,
    reviewee_id uuid not null references public.profiles(id) on delete cascade,
    rating integer not null check (rating >= 1 and rating <= 5),
    comment text,
    created_at timestamptz not null default now(),
    constraint unique_review_per_party unique (reservation_id, reviewer_id, reviewee_id)
);

create index if not exists idx_reviews_reservation_id on public.reviews(reservation_id);
create index if not exists idx_reviews_reviewee_id on public.reviews(reviewee_id);
create index if not exists idx_reviews_reviewer_id on public.reviews(reviewer_id);

-- -----------------------------------------------------------------------------
-- 7. DATABASE TRIGGER: STRICT RESERVATION INTEGRITY & TRANSITION RULES
-- -----------------------------------------------------------------------------
-- Prevents updating protected fields (tool, borrower, dates, created_at)
-- and strictly controls status transitions at the database level.
create or replace function public.validate_reservation_update()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    v_tool_owner uuid;
    v_conflict_count integer;
begin
    -- 1. Enforce immutability of protected fields
    if NEW.id <> OLD.id then
        raise exception 'Reservation id cannot be changed';
    end if;
    if NEW.tool_id <> OLD.tool_id then
        raise exception 'Reservation tool_id cannot be changed';
    end if;
    if NEW.borrower_id <> OLD.borrower_id then
        raise exception 'Reservation borrower_id cannot be changed';
    end if;
    if NEW.start_date <> OLD.start_date then
        raise exception 'Reservation start_date cannot be changed';
    end if;
    if NEW.end_date <> OLD.end_date then
        raise exception 'Reservation end_date cannot be changed';
    end if;
    if NEW.created_at <> OLD.created_at then
        raise exception 'Reservation created_at cannot be changed';
    end if;

    -- 2. Validate status transitions
    if NEW.status <> OLD.status then
        -- A. Borrower cancelling pending request
        if NEW.status = 'cancelled' then
            if OLD.status <> 'pending' then
                raise exception 'Only pending reservations can be cancelled';
            end if;
            if auth.uid() is not null and auth.uid() <> OLD.borrower_id then
                raise exception 'Only the borrower can cancel this reservation';
            end if;

        -- B. Owner declining pending request
        elsif NEW.status = 'declined' then
            if OLD.status <> 'pending' then
                raise exception 'Only pending reservations can be declined';
            end if;
            select owner_id into v_tool_owner from public.tools where id = OLD.tool_id;
            if auth.uid() is not null and auth.uid() <> v_tool_owner then
                raise exception 'Only the tool owner can decline this reservation';
            end if;

        -- C. Owner approving pending request (with per-tool lock and overlap prevention)
        elsif NEW.status = 'approved' then
            if OLD.status <> 'pending' then
                raise exception 'Only pending reservations can be approved';
            end if;
            select owner_id into v_tool_owner from public.tools where id = OLD.tool_id;
            if auth.uid() is not null and auth.uid() <> v_tool_owner then
                raise exception 'Only the tool owner can approve this reservation';
            end if;

            -- Row-lock tool to serialize concurrent approval checks
            perform 1 from public.tools where id = OLD.tool_id for update;

            select count(*) into v_conflict_count
            from public.reservations
            where tool_id = OLD.tool_id
              and id <> OLD.id
              and status in ('approved', 'picked_up')
              and start_date <= NEW.end_date
              and end_date >= NEW.start_date;

            if v_conflict_count > 0 then
                raise exception 'Conflict: Tool is already booked or active for overlapping dates';
            end if;

        -- D. Marking tool as picked up
        elsif NEW.status = 'picked_up' then
            if OLD.status <> 'approved' then
                raise exception 'Reservation must be in approved status before pickup';
            end if;

        -- E. Marking tool as returned
        elsif NEW.status = 'returned' then
            if OLD.status not in ('picked_up', 'approved', 'overdue') then
                raise exception 'Reservation must be picked up or approved before return';
            end if;

        else
            raise exception 'Invalid reservation status transition from % to %', OLD.status, NEW.status;
        end if;
    end if;

    NEW.updated_at = now();
    return NEW;
end;
$$;

drop trigger if exists trg_validate_reservation_update on public.reservations;
create trigger trg_validate_reservation_update
    before update on public.reservations
    for each row execute function public.validate_reservation_update();

-- -----------------------------------------------------------------------------
-- 8. DATABASE FUNCTIONS FOR SAFE CONCURRENCY & WORKFLOWS
-- -----------------------------------------------------------------------------

-- A. Safe Reservation Approval (Per-tool lock prevents simultaneous overlapping approvals)
create or replace function public.approve_reservation(p_reservation_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_res record;
    v_tool record;
    v_conflict_count integer;
begin
    -- 1. Fetch and row-lock the target reservation
    select * into v_res
    from public.reservations
    where id = p_reservation_id
    for update;

    if not found then
        return jsonb_build_object('success', false, 'error', 'Reservation not found');
    end if;

    -- 2. Concurrency Lock: Row-lock the parent TOOL for UPDATE to serialize all approvals on this tool
    select * into v_tool
    from public.tools
    where id = v_res.tool_id
    for update;

    if not found then
        return jsonb_build_object('success', false, 'error', 'Associated tool not found');
    end if;

    -- 3. Verify caller is the tool owner
    if v_tool.owner_id != auth.uid() then
        return jsonb_build_object('success', false, 'error', 'Unauthorized: Only the tool owner can approve requests');
    end if;

    if v_res.status != 'pending' then
        return jsonb_build_object('success', false, 'error', 'Only pending reservations can be approved');
    end if;

    -- 4. Check for overlapping approved or active picked_up reservations on the same tool
    select count(*) into v_conflict_count
    from public.reservations
    where tool_id = v_res.tool_id
      and id != v_res.id
      and status in ('approved', 'picked_up')
      and start_date <= v_res.end_date
      and end_date >= v_res.start_date;

    if v_conflict_count > 0 then
        return jsonb_build_object(
            'success', false,
            'error', 'Conflict: This tool is already booked or active for overlapping dates.'
        );
    end if;

    -- 5. Update status to approved
    update public.reservations
    set status = 'approved',
        updated_at = now()
    where id = p_reservation_id;

    return jsonb_build_object('success', true, 'message', 'Reservation approved successfully');
end;
$$;

-- B. Safe Reservation Decline
create or replace function public.decline_reservation(p_reservation_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_res record;
    v_owner_id uuid;
begin
    select * into v_res from public.reservations where id = p_reservation_id for update;
    if not found then
        return jsonb_build_object('success', false, 'error', 'Reservation not found');
    end if;

    select owner_id into v_owner_id from public.tools where id = v_res.tool_id;
    if v_owner_id != auth.uid() then
        return jsonb_build_object('success', false, 'error', 'Unauthorized: Only the tool owner can decline requests');
    end if;

    if v_res.status != 'pending' then
        return jsonb_build_object('success', false, 'error', 'Only pending reservations can be declined');
    end if;

    update public.reservations
    set status = 'declined', updated_at = now()
    where id = p_reservation_id;

    return jsonb_build_object('success', true, 'message', 'Reservation declined');
end;
$$;

-- C. Safe Reservation Cancellation by Borrower
create or replace function public.cancel_reservation(p_reservation_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_res record;
begin
    select * into v_res from public.reservations where id = p_reservation_id for update;
    if not found then
        return jsonb_build_object('success', false, 'error', 'Reservation not found');
    end if;

    if v_res.borrower_id != auth.uid() then
        return jsonb_build_object('success', false, 'error', 'Unauthorized: Only the borrower can cancel this request');
    end if;

    if v_res.status != 'pending' then
        return jsonb_build_object('success', false, 'error', 'Only pending reservations can be cancelled');
    end if;

    update public.reservations
    set status = 'cancelled', updated_at = now()
    where id = p_reservation_id;

    return jsonb_build_object('success', true, 'message', 'Reservation request cancelled');
end;
$$;

-- D. Safe Handover Transition (Picked Up)
create or replace function public.record_pickup(
    p_reservation_id uuid,
    p_condition_note text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_res record;
    v_owner_id uuid;
begin
    select * into v_res from public.reservations where id = p_reservation_id for update;
    if not found then
        return jsonb_build_object('success', false, 'error', 'Reservation not found');
    end if;

    select owner_id into v_owner_id from public.tools where id = v_res.tool_id;

    -- Owner initiates pickup handover
    if auth.uid() != v_owner_id then
        return jsonb_build_object('success', false, 'error', 'Unauthorized: Only the tool owner can mark the tool as picked up');
    end if;

    if v_res.status != 'approved' then
        return jsonb_build_object('success', false, 'error', 'Tool must be in approved status to record pickup');
    end if;

    update public.reservations
    set status = 'picked_up', updated_at = now()
    where id = p_reservation_id;

    insert into public.handover_logs (reservation_id, event_type, condition_note, recorded_by)
    values (p_reservation_id, 'picked_up', p_condition_note, auth.uid());

    return jsonb_build_object('success', true, 'message', 'Tool marked as picked up');
end;
$$;

-- E. Safe Handover Transition (Returned)
create or replace function public.record_return(
    p_reservation_id uuid,
    p_condition_note text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_res record;
    v_owner_id uuid;
begin
    select * into v_res from public.reservations where id = p_reservation_id for update;
    if not found then
        return jsonb_build_object('success', false, 'error', 'Reservation not found');
    end if;

    select owner_id into v_owner_id from public.tools where id = v_res.tool_id;

    -- Either owner or borrower can register the return
    if auth.uid() != v_owner_id and auth.uid() != v_res.borrower_id then
        return jsonb_build_object('success', false, 'error', 'Unauthorized: Only the borrower or tool owner can record return');
    end if;

    if v_res.status not in ('picked_up', 'approved', 'overdue') then
        return jsonb_build_object('success', false, 'error', 'Tool must be currently borrowed or approved to record return');
    end if;

    update public.reservations
    set status = 'returned', updated_at = now()
    where id = p_reservation_id;

    insert into public.handover_logs (reservation_id, event_type, condition_note, recorded_by)
    values (p_reservation_id, 'returned', p_condition_note, auth.uid());

    return jsonb_build_object('success', true, 'message', 'Tool returned successfully');
end;
$$;

-- F. Helper function to calculate user reputation/rating
create or replace function public.get_user_rating_summary(p_user_id uuid)
returns jsonb
language sql
security definer
set search_path = public
as $$
    select jsonb_build_object(
        'average_rating', coalesce(round(avg(rating)::numeric, 1), 0.0),
        'total_reviews', count(*)
    )
    from public.reviews
    where reviewee_id = p_user_id;
$$;

-- -----------------------------------------------------------------------------
-- 9. ROW LEVEL SECURITY (RLS) POLICIES
-- -----------------------------------------------------------------------------

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.tools enable row level security;
alter table public.tool_images enable row level security;
alter table public.reservations enable row level security;
alter table public.handover_logs enable row level security;
alter table public.reviews enable row level security;

-- PROFILES POLICIES
-- Publicly readable (safe fields: display_name, neighborhood, avatar_url)
drop policy if exists "Public profiles are viewable by everyone" on public.profiles;
create policy "Public profiles are viewable by everyone"
    on public.profiles for select
    using (true);

drop policy if exists "Users can insert their own profile" on public.profiles;
create policy "Users can insert their own profile"
    on public.profiles for insert
    with check (auth.uid() = id);

drop policy if exists "Users can update their own profile" on public.profiles;
create policy "Users can update their own profile"
    on public.profiles for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

-- TOOLS POLICIES
-- Public can view active tools; owners can view all their tools (including archived)
drop policy if exists "Active tools are viewable by everyone" on public.tools;
create policy "Active tools are viewable by everyone"
    on public.tools for select
    using (status = 'active' or auth.uid() = owner_id);

drop policy if exists "Members can create tools" on public.tools;
create policy "Members can create tools"
    on public.tools for insert
    with check (auth.uid() = owner_id);

drop policy if exists "Owners can update their own tools" on public.tools;
create policy "Owners can update their own tools"
    on public.tools for update
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Owners can delete their own tools" on public.tools;
create policy "Owners can delete their own tools"
    on public.tools for delete
    using (auth.uid() = owner_id);

-- TOOL IMAGES POLICIES
drop policy if exists "Images of visible tools are readable" on public.tool_images;
create policy "Images of visible tools are readable"
    on public.tool_images for select
    using (
        exists (
            select 1 from public.tools
            where tools.id = tool_images.tool_id
              and (tools.status = 'active' or tools.owner_id = auth.uid())
        )
    );

drop policy if exists "Owners can insert images for their tools" on public.tool_images;
create policy "Owners can insert images for their tools"
    on public.tool_images for insert
    with check (
        exists (
            select 1 from public.tools
            where tools.id = tool_images.tool_id
              and tools.owner_id = auth.uid()
        )
    );

drop policy if exists "Owners can delete images of their tools" on public.tool_images;
create policy "Owners can delete images of their tools"
    on public.tool_images for delete
    using (
        exists (
            select 1 from public.tools
            where tools.id = tool_images.tool_id
              and tools.owner_id = auth.uid()
        )
    );

-- RESERVATIONS POLICIES
-- Only the borrower and the tool owner can see a reservation
drop policy if exists "Participants can view their reservations" on public.reservations;
create policy "Participants can view their reservations"
    on public.reservations for select
    using (
        auth.uid() = borrower_id or
        exists (
            select 1 from public.tools
            where tools.id = reservations.tool_id
              and tools.owner_id = auth.uid()
        )
    );

-- Borrowers can insert requests, but CANNOT request their own tool
drop policy if exists "Borrowers can create reservation requests" on public.reservations;
create policy "Borrowers can create reservation requests"
    on public.reservations for insert
    with check (
        auth.uid() = borrower_id and
        status = 'pending' and
        not exists (
            select 1 from public.tools
            where tools.id = reservations.tool_id
              and tools.owner_id = auth.uid()
        )
    );

-- Updates:
-- 1. Borrower update: restricted to cancellation of their own pending requests
drop policy if exists "Borrowers can cancel pending reservations" on public.reservations;
create policy "Borrowers can cancel pending reservations"
    on public.reservations for update
    using (
        auth.uid() = borrower_id and status = 'pending'
    )
    with check (
        auth.uid() = borrower_id and status = 'cancelled'
    );

-- 2. Owner update: restricted to approval and decline transitions of pending requests
drop policy if exists "Owners can manage reservation status" on public.reservations;
create policy "Owners can manage reservation status"
    on public.reservations for update
    using (
        status = 'pending' and
        exists (
            select 1 from public.tools
            where tools.id = reservations.tool_id
              and tools.owner_id = auth.uid()
        )
    )
    with check (
        status in ('approved', 'declined') and
        exists (
            select 1 from public.tools
            where tools.id = reservations.tool_id
              and tools.owner_id = auth.uid()
        )
    );

-- HANDOVER LOGS POLICIES
-- Readable by borrower and owner
drop policy if exists "Participants can view handover logs" on public.handover_logs;
create policy "Participants can view handover logs"
    on public.handover_logs for select
    using (
        exists (
            select 1 from public.reservations r
            join public.tools t on t.id = r.tool_id
            where r.id = handover_logs.reservation_id
              and (r.borrower_id = auth.uid() or t.owner_id = auth.uid())
        )
    );

-- Handover logs insert: only authorized participant for the matching transition
drop policy if exists "Participants can insert handover logs" on public.handover_logs;
create policy "Participants can insert handover logs"
    on public.handover_logs for insert
    with check (
        recorded_by = auth.uid() and
        exists (
            select 1 from public.reservations r
            join public.tools t on t.id = r.tool_id
            where r.id = handover_logs.reservation_id
              and (
                  (handover_logs.event_type = 'picked_up' and t.owner_id = auth.uid())
                  or
                  (handover_logs.event_type = 'returned' and (t.owner_id = auth.uid() or r.borrower_id = auth.uid()))
              )
        )
    );

-- REVIEWS POLICIES
-- Reviews are publicly readable to foster neighborhood trust
drop policy if exists "Reviews are viewable by everyone" on public.reviews;
create policy "Reviews are viewable by everyone"
    on public.reviews for select
    using (true);

-- Eligible participants can write a review once reservation is returned
drop policy if exists "Eligible participants can write reviews" on public.reviews;
create policy "Eligible participants can write reviews"
    on public.reviews for insert
    with check (
        reviewer_id = auth.uid() and
        reviewer_id != reviewee_id and
        exists (
            select 1 from public.reservations r
            join public.tools t on t.id = r.tool_id
            where r.id = reviews.reservation_id
              and r.status = 'returned'
              and (
                  (r.borrower_id = auth.uid() and reviews.reviewee_id = t.owner_id)
                  or
                  (t.owner_id = auth.uid() and reviews.reviewee_id = r.borrower_id)
              )
        )
    );

-- -----------------------------------------------------------------------------
-- 10. SUPABASE STORAGE BUCKETS SETUP (OPTIONAL / RECOMMENDED)
-- -----------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('tool-photos', 'tool-photos', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

-- Allow public reads on tool-photos
create policy "Public Access Tool Photos"
on storage.objects for select
using ( bucket_id = 'tool-photos' );

-- Allow authenticated users to upload tool photos
create policy "Authenticated Users Can Upload Tool Photos"
on storage.objects for insert
with check ( bucket_id = 'tool-photos' and auth.role() = 'authenticated' );

-- Allow public reads on avatars
create policy "Public Access Avatars"
on storage.objects for select
using ( bucket_id = 'avatars' );

-- Allow authenticated users to upload avatars
create policy "Authenticated Users Can Upload Avatars"
on storage.objects for insert
with check ( bucket_id = 'avatars' and auth.role() = 'authenticated' );
