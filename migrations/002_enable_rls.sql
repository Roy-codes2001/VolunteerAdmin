-- ============================================================
-- Durga Puja Admin API
-- Row Level Security
-- ============================================================


-- ============================================================
-- 1. ENABLE RLS
-- ============================================================

ALTER TABLE public.pandals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_live_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_visitor_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pandal_activity_logs ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- 2. PANDALS
-- A logged-in user can access only their own pandal.
-- ============================================================

CREATE POLICY "Users can view their own pandal"
ON public.pandals
FOR SELECT
TO authenticated
USING (id = auth.uid());


CREATE POLICY "Users can update their own pandal"
ON public.pandals
FOR UPDATE
TO authenticated
USING (id = auth.uid())
WITH CHECK (id = auth.uid());


-- ============================================================
-- 3. PANDAL DEVICES
-- Users can access devices belonging to their pandal.
-- ============================================================

CREATE POLICY "Users can view their pandal devices"
ON public.pandal_devices
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can create devices for their pandal"
ON public.pandal_devices
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can update their pandal devices"
ON public.pandal_devices
FOR UPDATE
TO authenticated
USING (pandal_id = auth.uid())
WITH CHECK (pandal_id = auth.uid());


-- ============================================================
-- 4. LIVE STATUS
-- ============================================================

CREATE POLICY "Users can view their pandal live status"
ON public.pandal_live_status
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can create their pandal live status"
ON public.pandal_live_status
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can update their pandal live status"
ON public.pandal_live_status
FOR UPDATE
TO authenticated
USING (pandal_id = auth.uid())
WITH CHECK (pandal_id = auth.uid());


-- ============================================================
-- 5. PHOTOS
-- ============================================================

CREATE POLICY "Users can view their pandal photos"
ON public.pandal_photos
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can add photos to their pandal"
ON public.pandal_photos
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can delete their pandal photos"
ON public.pandal_photos
FOR DELETE
TO authenticated
USING (pandal_id = auth.uid());


-- ============================================================
-- 6. EVENTS
-- ============================================================

CREATE POLICY "Users can view their pandal events"
ON public.pandal_events
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can create their pandal events"
ON public.pandal_events
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can update their pandal events"
ON public.pandal_events
FOR UPDATE
TO authenticated
USING (pandal_id = auth.uid())
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can delete their pandal events"
ON public.pandal_events
FOR DELETE
TO authenticated
USING (pandal_id = auth.uid());


-- ============================================================
-- 7. VISITOR INFORMATION
-- ============================================================

CREATE POLICY "Users can view their visitor information"
ON public.pandal_visitor_info
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can create visitor information"
ON public.pandal_visitor_info
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can update visitor information"
ON public.pandal_visitor_info
FOR UPDATE
TO authenticated
USING (pandal_id = auth.uid())
WITH CHECK (pandal_id = auth.uid());


-- ============================================================
-- 8. NOTICES
-- ============================================================

CREATE POLICY "Users can view their pandal notices"
ON public.pandal_notices
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());


CREATE POLICY "Users can create pandal notices"
ON public.pandal_notices
FOR INSERT
TO authenticated
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can update pandal notices"
ON public.pandal_notices
FOR UPDATE
TO authenticated
USING (pandal_id = auth.uid())
WITH CHECK (pandal_id = auth.uid());


CREATE POLICY "Users can delete pandal notices"
ON public.pandal_notices
FOR DELETE
TO authenticated
USING (pandal_id = auth.uid());


-- ============================================================
-- 9. ACTIVITY LOGS
-- Users can read their own logs.
-- INSERT will be handled by the backend.
-- ============================================================

CREATE POLICY "Users can view their activity logs"
ON public.pandal_activity_logs
FOR SELECT
TO authenticated
USING (pandal_id = auth.uid());