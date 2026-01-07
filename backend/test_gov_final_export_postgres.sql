-- PostgreSQL Export from SQLite
-- Generated for CloudSQL Import

-- Schema for users
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
	id VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	hashed_password VARCHAR NOT NULL, 
	profile_json JSON, 
	viv_preferences JSON, 
	onboarding_status VARCHAR, 
	onboarding_step VARCHAR, 
	onboarding_version INTEGER, 
	password_reset_token VARCHAR, 
	password_reset_expires TIMESTAMP, 
	created_at TIMESTAMP, 
	updated_at TIMESTAMP, 
	PRIMARY KEY (id)
);


-- Table: users (2 rows)
INSERT INTO users (id, email, hashed_password, profile_json, viv_preferences, onboarding_status, onboarding_step, onboarding_version, password_reset_token, password_reset_expires, created_at, updated_at) VALUES ('79844847-82b2-418d-9a5d-8206ad0b69db', 'test_gov_79844847@example.com', 'pw', NULL, NULL, 'NOT_STARTED', NULL, 1, NULL, NULL, '2025-12-23 19:23:14.782739', '2025-12-23 19:23:14.782739');
INSERT INTO users (id, email, hashed_password, profile_json, viv_preferences, onboarding_status, onboarding_step, onboarding_version, password_reset_token, password_reset_expires, created_at, updated_at) VALUES ('68b64136-89b4-4035-bf3d-78081cf8754c', 'test_gov_68b64136@example.com', 'pw', NULL, NULL, 'NOT_STARTED', NULL, 1, NULL, NULL, '2025-12-23 19:23:44.064051', '2025-12-23 19:23:44.064051');
-- Schema for system_logs
DROP TABLE IF EXISTS system_logs CASCADE;
CREATE TABLE system_logs (
	id INTEGER NOT NULL, 
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
	level VARCHAR, 
	message TEXT NOT NULL, 
	module VARCHAR, 
	function_name VARCHAR, 
	line_number INTEGER, 
	request_id VARCHAR, 
	user_id INTEGER, 
	extra_data JSON, 
	PRIMARY KEY (id)
);

-- Schema for bug_reports
DROP TABLE IF EXISTS bug_reports CASCADE;
CREATE TABLE bug_reports (
	id INTEGER NOT NULL, 
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
	updated_at TIMESTAMP, 
	error_type VARCHAR, 
	error_message TEXT NOT NULL, 
	severity VARCHAR, 
	status VARCHAR, 
	stack_trace TEXT NOT NULL, 
	source_file VARCHAR, 
	line_number INTEGER, 
	request_id VARCHAR, 
	endpoint VARCHAR, 
	method VARCHAR, 
	user_id INTEGER, 
	system_info JSON, 
	request_headers JSON, 
	request_payload JSON, 
	resolution_notes TEXT, 
	PRIMARY KEY (id)
);

-- Schema for audit_logs
DROP TABLE IF EXISTS audit_logs CASCADE;
CREATE TABLE audit_logs (
	id VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	actor_id VARCHAR, 
	actor_type VARCHAR, 
	action VARCHAR NOT NULL, 
	entity_type VARCHAR NOT NULL, 
	entity_id VARCHAR NOT NULL, 
	changes_json JSON, 
	metadata_json JSON, 
	PRIMARY KEY (id)
);

-- Schema for conversations
DROP TABLE IF EXISTS conversations CASCADE;
CREATE TABLE conversations (
	id VARCHAR NOT NULL, 
	title VARCHAR, 
	date TIMESTAMP, 
	PRIMARY KEY (id)
);

-- Schema for notifications
DROP TABLE IF EXISTS notifications CASCADE;
CREATE TABLE notifications (
	id VARCHAR NOT NULL, 
	PRIMARY KEY (id)
);

-- Schema for onboarding_sessions
DROP TABLE IF EXISTS onboarding_sessions CASCADE;
CREATE TABLE onboarding_sessions (
	id VARCHAR NOT NULL, 
	data_json JSON, 
	created_at TIMESTAMP, 
	PRIMARY KEY (id)
);

-- Schema for connections
DROP TABLE IF EXISTS connections CASCADE;
CREATE TABLE connections (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	provider VARCHAR NOT NULL, 
	status VARCHAR, 
	credentials_json TEXT, 
	metadata_json TEXT, 
	created_at TIMESTAMP, 
	updated_at TIMESTAMP, 
	access_token VARCHAR, 
	refresh_token VARCHAR, 
	expires_at TIMESTAMP, 
	token_type VARCHAR, 
	scope VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for health_data_samples
DROP TABLE IF EXISTS health_data_samples CASCADE;
CREATE TABLE health_data_samples (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	source VARCHAR NOT NULL, 
	date TIMESTAMP NOT NULL, 
	steps INTEGER, 
	distance_m FLOAT, 
	active_minutes INTEGER, 
	calories_kcal FLOAT, 
	resting_hr_bpm INTEGER, 
	avg_hr_bpm INTEGER, 
	sleep_minutes INTEGER, 
	metadata_json JSON, 
	created_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for viv_indexes
DROP TABLE IF EXISTS viv_indexes CASCADE;
CREATE TABLE viv_indexes (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	financial_score FLOAT, 
	health_score FLOAT, 
	time_score FLOAT, 
	confidence FLOAT, 
	snapshot_reason TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for life_goals
DROP TABLE IF EXISTS life_goals CASCADE;
CREATE TABLE life_goals (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	title VARCHAR NOT NULL, 
	target_amount FLOAT NOT NULL, 
	saved_amount FLOAT, 
	target_date TIMESTAMP, 
	type VARCHAR, 
	monthly_contribution_target FLOAT, 
	impact_vector_json JSON, 
	priority VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for financial_accounts
DROP TABLE IF EXISTS financial_accounts CASCADE;
CREATE TABLE financial_accounts (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	institution_name VARCHAR NOT NULL, 
	account_type VARCHAR NOT NULL, 
	current_balance FLOAT, 
	"limit" FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for statements
DROP TABLE IF EXISTS statements CASCADE;
CREATE TABLE statements (
	id VARCHAR NOT NULL, 
	user_id VARCHAR, 
	bank_name VARCHAR, 
	period_start DATE, 
	period_end DATE, 
	total_credits FLOAT, 
	total_debits FLOAT, 
	uploaded_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for recurring_bills
DROP TABLE IF EXISTS recurring_bills CASCADE;
CREATE TABLE recurring_bills (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	amount FLOAT NOT NULL, 
	cadence VARCHAR, 
	next_due_date DATE, 
	category VARCHAR, 
	is_verified BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for health_daily_summaries
DROP TABLE IF EXISTS health_daily_summaries CASCADE;
CREATE TABLE health_daily_summaries (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	date DATE NOT NULL, 
	sleep_duration_minutes INTEGER, 
	sleep_quality_score FLOAT, 
	hrv_average FLOAT, 
	resting_heart_rate INTEGER, 
	steps_count INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for sleep_sessions
DROP TABLE IF EXISTS sleep_sessions CASCADE;
CREATE TABLE sleep_sessions (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	start_time TIMESTAMP NOT NULL, 
	end_time TIMESTAMP NOT NULL, 
	deep_sleep_minutes INTEGER, 
	rem_sleep_minutes INTEGER, 
	wake_count INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for workouts
DROP TABLE IF EXISTS workouts CASCADE;
CREATE TABLE workouts (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	start_time TIMESTAMP NOT NULL, 
	end_time TIMESTAMP NOT NULL, 
	activity_type VARCHAR NOT NULL, 
	calories_burned INTEGER, 
	average_heart_rate INTEGER, 
	perceived_exertion FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for calendar_events
DROP TABLE IF EXISTS calendar_events CASCADE;
CREATE TABLE calendar_events (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	start_time TIMESTAMP NOT NULL, 
	end_time TIMESTAMP NOT NULL, 
	title VARCHAR, 
	is_meeting BOOLEAN, 
	attendee_count INTEGER, 
	location_context VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for mobility_trips
DROP TABLE IF EXISTS mobility_trips CASCADE;
CREATE TABLE mobility_trips (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	provider VARCHAR NOT NULL, 
	pickup_time TIMESTAMP, 
	dropoff_time TIMESTAMP, 
	cost_amount FLOAT, 
	currency VARCHAR, 
	trip_type VARCHAR, 
	origin_lat FLOAT, 
	origin_lon FLOAT, 
	destination_lat FLOAT, 
	destination_lon FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: mobility_trips (2 rows)
INSERT INTO mobility_trips (id, user_id, provider, pickup_time, dropoff_time, cost_amount, currency, trip_type, origin_lat, origin_lon, destination_lat, destination_lon) VALUES ('011808c6-c022-45be-a0f8-cb32640a1ee6', '79844847-82b2-418d-9a5d-8206ad0b69db', 'uber', NULL, NULL, 0.0, 'USD', 'UberX', NULL, NULL, NULL, NULL);
INSERT INTO mobility_trips (id, user_id, provider, pickup_time, dropoff_time, cost_amount, currency, trip_type, origin_lat, origin_lon, destination_lat, destination_lon) VALUES ('a9ed20ea-d48b-48f8-9c6c-a0b5aed21608', '68b64136-89b4-4035-bf3d-78081cf8754c', 'uber', NULL, NULL, 0.0, 'USD', 'UberX', NULL, NULL, NULL, NULL);
-- Schema for viv_logs
DROP TABLE IF EXISTS viv_logs CASCADE;
CREATE TABLE viv_logs (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	user_intent VARCHAR, 
	context_snapshot_json JSON, 
	decision_logic TEXT, 
	ai_response TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);


-- Table: viv_logs (2 rows)
INSERT INTO viv_logs (id, user_id, timestamp, user_intent, context_snapshot_json, decision_logic, ai_response) VALUES ('c9ab4ad3-f276-45f0-ab13-c10c2e2d2dda', '79844847-82b2-418d-9a5d-8206ad0b69db', '2025-12-23 19:23:14.835762', 'booking', '{"ride_id": "uber_79844847-82b2-418d-9a5d-8206ad0b69db_1766517794", "ride_type": "UberX", "start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "mock": true}', 'uber Interaction', 'Interaction recorded');
INSERT INTO viv_logs (id, user_id, timestamp, user_intent, context_snapshot_json, decision_logic, ai_response) VALUES ('10405345-2a0d-4c7a-b211-6ab04365cad4', '68b64136-89b4-4035-bf3d-78081cf8754c', '2025-12-23 19:23:44.117643', 'booking', '{"ride_id": "uber_68b64136-89b4-4035-bf3d-78081cf8754c_1766517824", "ride_type": "UberX", "start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "mock": true}', 'uber Interaction', 'Interaction recorded');
-- Schema for messages
DROP TABLE IF EXISTS messages CASCADE;
CREATE TABLE messages (
	id VARCHAR NOT NULL, 
	conversation_id VARCHAR NOT NULL, 
	role VARCHAR NOT NULL, 
	content TEXT NOT NULL, 
	date TIMESTAMP, 
	feedback VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id)
);

-- Schema for financial_scores
DROP TABLE IF EXISTS financial_scores CASCADE;
CREATE TABLE financial_scores (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	overall_score FLOAT, 
	cashflow_stability_score FLOAT, 
	bills_coverage_score FLOAT, 
	discretionary_control_score FLOAT, 
	savings_rate_score FLOAT, 
	emergency_buffer_score FLOAT, 
	debt_load_score FLOAT, 
	networth_momentum_score FLOAT, 
	investment_health_score FLOAT, 
	time_window VARCHAR, 
	data_sources_json JSON, 
	total_monthly_income FLOAT, 
	total_monthly_expenses FLOAT, 
	total_monthly_bills FLOAT, 
	total_monthly_savings FLOAT, 
	total_assets_value FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for feature_interests
DROP TABLE IF EXISTS feature_interests CASCADE;
CREATE TABLE feature_interests (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	feature_name VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for health_profiles
DROP TABLE IF EXISTS health_profiles CASCADE;
CREATE TABLE health_profiles (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	diet_style VARCHAR, 
	water_intake_range VARCHAR, 
	smoking_pattern VARCHAR, 
	alcohol_pattern VARCHAR, 
	stress_level VARCHAR, 
	energy_pattern VARCHAR, 
	activity_self_report VARCHAR, 
	lifestyle_habits_json JSON, 
	last_updated TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for time_profiles
DROP TABLE IF EXISTS time_profiles CASCADE;
CREATE TABLE time_profiles (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	work_status VARCHAR, 
	work_hours_per_week VARCHAR, 
	uses_digital_calendar VARCHAR, 
	commute_duration VARCHAR, 
	time_meals_house_daily VARCHAR, 
	time_admin_weekly VARCHAR, 
	main_time_drains JSON, 
	routine_style VARCHAR, 
	task_style VARCHAR, 
	time_overwhelm_level VARCHAR, 
	created_at TIMESTAMP, 
	updated_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for time_events
DROP TABLE IF EXISTS time_events CASCADE;
CREATE TABLE time_events (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	source VARCHAR NOT NULL, 
	start_time TIMESTAMP NOT NULL, 
	end_time TIMESTAMP NOT NULL, 
	duration_minutes INTEGER, 
	title VARCHAR, 
	location VARCHAR, 
	is_all_day BOOLEAN, 
	category VARCHAR, 
	created_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for time_scores
DROP TABLE IF EXISTS time_scores CASCADE;
CREATE TABLE time_scores (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	timestamp TIMESTAMP, 
	overall_score FLOAT, 
	structure_score FLOAT, 
	load_score FLOAT, 
	focus_score FLOAT, 
	friction_score FLOAT, 
	stress_score FLOAT, 
	confidence FLOAT, 
	band VARCHAR, 
	metrics_json JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for transactions
DROP TABLE IF EXISTS transactions CASCADE;
CREATE TABLE transactions (
	id VARCHAR NOT NULL, 
	account_id VARCHAR, 
	statement_id VARCHAR, 
	user_id VARCHAR, 
	amount FLOAT NOT NULL, 
	currency_code VARCHAR, 
	transaction_date TIMESTAMP, 
	description VARCHAR, 
	merchant_name VARCHAR, 
	merchant_category_code VARCHAR, 
	category_primary VARCHAR, 
	category_detailed VARCHAR, 
	is_recurring BOOLEAN, 
	location_lat FLOAT, 
	location_lon FLOAT, 
	deduplication_key VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(account_id) REFERENCES financial_accounts (id), 
	FOREIGN KEY(statement_id) REFERENCES statements (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Schema for orders
DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	transaction_id VARCHAR, 
	provider VARCHAR NOT NULL, 
	service_type VARCHAR NOT NULL, 
	status VARCHAR, 
	amount_estimated FLOAT, 
	amount_final FLOAT, 
	currency VARCHAR, 
	external_order_id VARCHAR, 
	idempotency_key VARCHAR, 
	details_json JSON, 
	error_message TEXT, 
	created_at TIMESTAMP, 
	updated_at TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(transaction_id) REFERENCES transactions (id)
);


-- Table: orders (2 rows)
INSERT INTO orders (id, user_id, transaction_id, provider, service_type, status, amount_estimated, amount_final, currency, external_order_id, idempotency_key, details_json, error_message, created_at, updated_at) VALUES ('96fe9186-0a2b-4497-a093-a8262b51a6dc', '79844847-82b2-418d-9a5d-8206ad0b69db', NULL, 'uber', 'mobility', 'CONFIRMED', 0.0, NULL, 'AED', 'uber_79844847-82b2-418d-9a5d-8206ad0b69db_1766517794', 'test_key_6547a0ba-0a39-4924-8d21-f33a740629a5', '{"start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "ride_type": "UberX"}', NULL, '2025-12-23 19:23:14.803770', '2025-12-23 19:23:14.850933');
INSERT INTO orders (id, user_id, transaction_id, provider, service_type, status, amount_estimated, amount_final, currency, external_order_id, idempotency_key, details_json, error_message, created_at, updated_at) VALUES ('34e6de3a-c1c5-49da-8fb6-c34c25b95bdc', '68b64136-89b4-4035-bf3d-78081cf8754c', NULL, 'uber', 'mobility', 'CONFIRMED', 0.0, NULL, 'AED', 'uber_68b64136-89b4-4035-bf3d-78081cf8754c_1766517824', 'test_key_908395e5-ff12-421d-8d34-bfc2898a2a83', '{"start": {"lat": 25.0, "lng": 55.0, "address": "Test Start"}, "end": {"lat": 25.1, "lng": 55.1, "address": "Test End"}, "ride_type": "UberX"}', NULL, '2025-12-23 19:23:44.083863', '2025-12-23 19:23:44.135144');

-- Export complete
