-- ============================================================
-- 1. PANDALS
-- ============================================================

CREATE TABLE public.pandals (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 2. PANDAL DEVICES
-- ============================================================

CREATE TABLE public.pandal_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pandal_id UUID NOT NULL REFERENCES public.pandals(id) ON DELETE CASCADE,
    device_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_pandal_device
        UNIQUE (pandal_id, device_id)
);


-- ============================================================
-- 3. LIVE STATUS
-- ============================================================

CREATE TABLE public.pandal_live_status (
    pandal_id UUID PRIMARY KEY REFERENCES public.pandals(id) ON DELETE CASCADE,

    crowd_level TEXT NOT NULL DEFAULT 'LOW',
    rain_status TEXT NOT NULL DEFAULT 'CLEAR',
    entry_status TEXT NOT NULL DEFAULT 'OPEN',
    wait_time_minutes SMALLINT NOT NULL DEFAULT 0,

    updated_by_device_id UUID REFERENCES public.pandal_devices(id)
        ON DELETE SET NULL,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_crowd_level
        CHECK (crowd_level IN ('LOW', 'MODERATE', 'HIGH', 'VERY_HIGH')),

    CONSTRAINT valid_rain_status
        CHECK (rain_status IN ('CLEAR', 'LIGHT', 'HEAVY')),

    CONSTRAINT valid_entry_status
        CHECK (entry_status IN ('OPEN', 'CLOSED')),

    CONSTRAINT valid_wait_time
        CHECK (wait_time_minutes >= 0)
);


-- ============================================================
-- 4. PANDAL PHOTOS
-- ============================================================

CREATE TABLE public.pandal_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pandal_id UUID NOT NULL REFERENCES public.pandals(id) ON DELETE CASCADE,

    storage_path TEXT NOT NULL,
    display_order SMALLINT NOT NULL,

    uploaded_by_device_id UUID REFERENCES public.pandal_devices(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_display_order
        CHECK (display_order BETWEEN 1 AND 5),

    CONSTRAINT unique_pandal_photo_order
        UNIQUE (pandal_id, display_order)
);


-- ============================================================
-- 5. PANDAL EVENTS
-- ============================================================

CREATE TABLE public.pandal_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pandal_id UUID NOT NULL REFERENCES public.pandals(id) ON DELETE CASCADE,

    title TEXT NOT NULL,
    description TEXT,

    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,

    created_by_device_id UUID REFERENCES public.pandal_devices(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_event_time
        CHECK (end_at > start_at)
);


-- ============================================================
-- 6. VISITOR INFORMATION
-- ============================================================

CREATE TABLE public.pandal_visitor_info (
    pandal_id UUID PRIMARY KEY REFERENCES public.pandals(id) ON DELETE CASCADE,

    entry_information TEXT,
    parking_information TEXT,
    accessibility_information TEXT,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 7. NOTICES
-- ============================================================

CREATE TABLE public.pandal_notices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pandal_id UUID NOT NULL
        REFERENCES public.pandals(id)
        ON DELETE CASCADE,

    message TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_by_device_id UUID
        REFERENCES public.pandal_devices(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 8. ACTIVITY LOG
-- ============================================================

CREATE TABLE public.pandal_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    pandal_id UUID NOT NULL REFERENCES public.pandals(id)
        ON DELETE CASCADE,

    device_id UUID REFERENCES public.pandal_devices(id)
        ON DELETE SET NULL,

    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,

    old_value JSONB,
    new_value JSONB,

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_pandal_devices_pandal_id
    ON public.pandal_devices(pandal_id);

CREATE INDEX idx_pandal_events_pandal_id
    ON public.pandal_events(pandal_id);

CREATE INDEX idx_pandal_events_start_at
    ON public.pandal_events(start_at);

CREATE INDEX idx_pandal_notices_pandal_id
    ON public.pandal_notices(pandal_id);

CREATE INDEX idx_pandal_notices_expires_at
    ON public.pandal_notices(expires_at);

CREATE INDEX idx_pandal_activity_logs_pandal_id
    ON public.pandal_activity_logs(pandal_id);

CREATE INDEX idx_pandal_activity_logs_created_at
    ON public.pandal_activity_logs(created_at);