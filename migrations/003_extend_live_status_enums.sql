-- Extend live-status enums to cover the volunteer console's full option set:
-- rain "AFFECTING_ENTRY" and entry "RESTRICTED".

ALTER TABLE pandal_live_status
    DROP CONSTRAINT valid_rain_status;

ALTER TABLE pandal_live_status
    ADD CONSTRAINT valid_rain_status
        CHECK (rain_status IN ('CLEAR', 'LIGHT', 'HEAVY', 'AFFECTING_ENTRY'));

ALTER TABLE pandal_live_status
    DROP CONSTRAINT valid_entry_status;

ALTER TABLE pandal_live_status
    ADD CONSTRAINT valid_entry_status
        CHECK (entry_status IN ('OPEN', 'CLOSED', 'RESTRICTED'));
