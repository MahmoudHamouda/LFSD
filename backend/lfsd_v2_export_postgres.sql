-- PostgreSQL Export from SQLite
-- Generated for CloudSQL Import


-- Table: users (2 rows)
INSERT INTO users (id, email, hashed_password, profile_json, viv_preferences, onboarding_status, onboarding_step, onboarding_version, password_reset_token, password_reset_expires, created_at, updated_at) VALUES ('79844847-82b2-418d-9a5d-8206ad0b69db', 'test_gov_79844847@example.com', 'pw', NULL, NULL, 'NOT_STARTED', NULL, 1, NULL, NULL, '2025-12-23 19:23:14.782739', '2025-12-23 19:23:14.782739');
INSERT INTO users (id, email, hashed_password, profile_json, viv_preferences, onboarding_status, onboarding_step, onboarding_version, password_reset_token, password_reset_expires, created_at, updated_at) VALUES ('68b64136-89b4-4035-bf3d-78081cf8754c', 'test_gov_68b64136@example.com', 'pw', NULL, NULL, 'NOT_STARTED', NULL, 1, NULL, NULL, '2025-12-23 19:23:44.064051', '2025-12-23 19:23:44.064051');

-- Table: mobility_trips (2 rows)
INSERT INTO mobility_trips (id, user_id, provider, pickup_time, dropoff_time, cost_amount, currency, trip_type, origin_lat, origin_lon, destination_lat, destination_lon) VALUES ('011808c6-c022-45be-a0f8-cb32640a1ee6', '79844847-82b2-418d-9a5d-8206ad0b69db', 'uber', NULL, NULL, 0.0, 'USD', 'UberX', NULL, NULL, NULL, NULL);
INSERT INTO mobility_trips (id, user_id, provider, pickup_time, dropoff_time, cost_amount, currency, trip_type, origin_lat, origin_lon, destination_lat, destination_lon) VALUES ('a9ed20ea-d48b-48f8-9c6c-a0b5aed21608', '68b64136-89b4-4035-bf3d-78081cf8754c', 'uber', NULL, NULL, 0.0, 'USD', 'UberX', NULL, NULL, NULL, NULL);

-- Table: viv_logs (2 rows)
INSERT INTO viv_logs (id, user_id, timestamp, user_intent, context_snapshot_json, decision_logic, ai_response) VALUES ('c9ab4ad3-f276-45f0-ab13-c10c2e2d2dda', '79844847-82b2-418d-9a5d-8206ad0b69db', '2025-12-23 19:23:14.835762', 'booking', '{"ride_id": "uber_79844847-82b2-418d-9a5d-8206ad0b69db_1766517794", "ride_type": "UberX", "start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "mock": true}', 'uber Interaction', 'Interaction recorded');
INSERT INTO viv_logs (id, user_id, timestamp, user_intent, context_snapshot_json, decision_logic, ai_response) VALUES ('10405345-2a0d-4c7a-b211-6ab04365cad4', '68b64136-89b4-4035-bf3d-78081cf8754c', '2025-12-23 19:23:44.117643', 'booking', '{"ride_id": "uber_68b64136-89b4-4035-bf3d-78081cf8754c_1766517824", "ride_type": "UberX", "start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "mock": true}', 'uber Interaction', 'Interaction recorded');

-- Table: orders (2 rows)
INSERT INTO orders (id, user_id, transaction_id, provider, service_type, status, amount_estimated, amount_final, currency, external_order_id, idempotency_key, details_json, error_message, created_at, updated_at) VALUES ('96fe9186-0a2b-4497-a093-a8262b51a6dc', '79844847-82b2-418d-9a5d-8206ad0b69db', NULL, 'uber', 'mobility', 'CONFIRMED', 0.0, NULL, 'AED', 'uber_79844847-82b2-418d-9a5d-8206ad0b69db_1766517794', 'test_key_6547a0ba-0a39-4924-8d21-f33a740629a5', '{"start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "ride_type": "UberX"}', NULL, '2025-12-23 19:23:14.803770', '2025-12-23 19:23:14.850933');
INSERT INTO orders (id, user_id, transaction_id, provider, service_type, status, amount_estimated, amount_final, currency, external_order_id, idempotency_key, details_json, error_message, created_at, updated_at) VALUES ('34e6de3a-c1c5-49da-8fb6-c34c25b95bdc', '68b64136-89b4-4035-bf3d-78081cf8754c', NULL, 'uber', 'mobility', 'CONFIRMED', 0.0, NULL, 'AED', 'uber_68b64136-89b4-4035-bf3d-78081cf8754c_1766517824', 'test_key_908395e5-ff12-421d-8d34-bfc2898a2a83', '{"start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "ride_type": "UberX"}', NULL, '2025-12-23 19:23:44.083863', '2025-12-23 19:23:44.135144');

-- Export complete
