-- Fatloss Planner 数据库Schema
-- 生成时间: 2026-03-09
-- 数据库: sqlite:///./data/fatloss.db


CREATE TABLE app_configs (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	unit_system VARCHAR(8) NOT NULL, 
	theme VARCHAR(5) NOT NULL, 
	language VARCHAR(10) NOT NULL, 
	weekly_check_day INTEGER NOT NULL, 
	carb_adjustment_unit_g INTEGER NOT NULL, 
	monthly_loss_percentage FLOAT NOT NULL, 
	exercise_calories_per_minute FLOAT NOT NULL, 
	enable_notifications BOOLEAN NOT NULL, 
	data_retention_days INTEGER NOT NULL, 
	created_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	updated_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE daily_nutrition_plans (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	plan_date DATE NOT NULL, 
	target_tdee FLOAT NOT NULL, 
	carbohydrates_g FLOAT NOT NULL, 
	protein_g FLOAT NOT NULL, 
	fat_g FLOAT NOT NULL, 
	is_adjusted BOOLEAN, 
	adjustment_units INTEGER, 
	notes TEXT, 
	created_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE user_profiles (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	gender VARCHAR(6) NOT NULL, 
	birth_date DATE NOT NULL, 
	height_cm FLOAT NOT NULL, 
	initial_weight_kg FLOAT NOT NULL, 
	activity_level VARCHAR(11) NOT NULL, 
	created_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	updated_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE weekly_nutrition_plans (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	week_start_date DATE NOT NULL, 
	week_end_date DATE NOT NULL, 
	total_carbohydrates_g FLOAT NOT NULL, 
	total_protein_g FLOAT NOT NULL, 
	total_fat_g FLOAT NOT NULL, 
	notes TEXT, 
	created_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE weight_records (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	weight_kg FLOAT NOT NULL, 
	record_date DATE NOT NULL, 
	notes TEXT, 
	created_at DATE DEFAULT CURRENT_DATE NOT NULL, 
	PRIMARY KEY (id)
)

