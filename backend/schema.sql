-- ============================================================
-- The Hunger Project - Ghana | Fleet Management System
-- Complete Schema v2.0
-- ============================================================

-- Lookup tables
CREATE TABLE fuel_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vehicle_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Projects (THP-Ghana specific - which project a trip/cost belongs to)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vendors (mechanic shops, fuel stations, car dealers, insurers)
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    category VARCHAR(50), -- 'fuel_station', 'workshop', 'dealer', 'insurer', 'other'
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vehicle groups
CREATE TABLE vehicle_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vehicles
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    unit_number VARCHAR(50) UNIQUE NOT NULL,
    registration VARCHAR(50) UNIQUE NOT NULL,
    vin VARCHAR(50),
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    color VARCHAR(50),
    engine_number VARCHAR(100),
    vehicle_type_id INTEGER REFERENCES vehicle_types(id),
    fuel_type_id INTEGER REFERENCES fuel_types(id),
    department_id INTEGER REFERENCES departments(id),
    group_id INTEGER REFERENCES vehicle_groups(id),
    tank_capacity NUMERIC(8,2),
    current_odometer INTEGER DEFAULT 0,
    purchase_date DATE,
    purchase_cost NUMERIC(12,2),
    purchase_vendor_id INTEGER REFERENCES vendors(id),
    -- Insurance
    insurance_policy VARCHAR(100),
    insurance_vendor_id INTEGER REFERENCES vendors(id),
    insurance_expiry DATE,
    insurance_cost NUMERIC(12,2),
    -- Roadworthy
    roadworthy_number VARCHAR(100),
    roadworthy_expiry DATE,
    roadworthy_cost NUMERIC(12,2),
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Drivers / Personnel
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    employee_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    department_id INTEGER REFERENCES departments(id),
    licence_number VARCHAR(50),
    licence_expiry DATE,
    licence_state VARCHAR(50),
    health_ref VARCHAR(100),
    health_expiry DATE,
    hire_date DATE,
    hourly_wage NUMERIC(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Fuel Cards (GoCard)
CREATE TABLE fuel_cards (
    id SERIAL PRIMARY KEY,
    card_number VARCHAR(100) UNIQUE NOT NULL,
    card_type VARCHAR(50) DEFAULT 'GO CARD',
    vehicle_id INTEGER REFERENCES vehicles(id),
    driver_id INTEGER REFERENCES drivers(id),
    current_balance NUMERIC(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Fuel Card Transactions (top-ups, transfers, fuel purchases)
CREATE TABLE fuel_transactions (
    id SERIAL PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    transaction_type VARCHAR(20) DEFAULT 'purchase', -- 'purchase', 'topup', 'transfer'
    vehicle_id INTEGER REFERENCES vehicles(id),
    driver_id INTEGER REFERENCES drivers(id),
    fuel_card_id INTEGER REFERENCES fuel_cards(id),
    transfer_to_card_id INTEGER REFERENCES fuel_cards(id), -- for card transfers
    fuel_type_id INTEGER REFERENCES fuel_types(id),
    vendor_id INTEGER REFERENCES vendors(id), -- filling station
    project_id INTEGER REFERENCES projects(id),
    location VARCHAR(200), -- State/Province where fuel was bought
    trip_purpose TEXT, -- purpose of the trip
    odometer_start INTEGER,
    odometer_end INTEGER,
    litres NUMERIC(10,3),
    cost_per_litre NUMERIC(10,4),
    total_cost NUMERIC(12,2),
    invoice_number VARCHAR(100),
    reference TEXT, -- notes/reference like in the report
    is_full_tank BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Trip log (who moved the vehicle, for what purpose, which project)
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) NOT NULL,
    driver_id INTEGER REFERENCES drivers(id),
    project_id INTEGER REFERENCES projects(id),
    trip_date DATE NOT NULL,
    departure_time TIME,
    return_time TIME,
    origin VARCHAR(200),
    destination VARCHAR(200),
    purpose TEXT NOT NULL,
    odometer_start INTEGER,
    odometer_end INTEGER,
    distance INTEGER GENERATED ALWAYS AS (
        CASE WHEN odometer_end IS NOT NULL AND odometer_start IS NOT NULL
        THEN odometer_end - odometer_start ELSE NULL END
    ) STORED,
    passengers INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Maintenance records
CREATE TABLE maintenance_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    interval_km INTEGER,
    interval_days INTEGER,
    reminder_days INTEGER DEFAULT 14,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE maintenance_records (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) NOT NULL,
    maintenance_type_id INTEGER REFERENCES maintenance_types(id),
    vendor_id INTEGER REFERENCES vendors(id), -- mechanic shop
    project_id INTEGER REFERENCES projects(id),
    service_date DATE NOT NULL,
    odometer INTEGER,
    description TEXT NOT NULL,
    technician VARCHAR(100),
    labour_cost NUMERIC(12,2) DEFAULT 0,
    parts_cost NUMERIC(12,2) DEFAULT 0,
    total_cost NUMERIC(12,2) DEFAULT 0,
    invoice_number VARCHAR(100),
    next_due_date DATE,
    next_due_odometer INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insurance records (history of renewals)
CREATE TABLE insurance_records (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    project_id INTEGER REFERENCES projects(id),
    policy_number VARCHAR(100),
    start_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    cost NUMERIC(12,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Roadworthy records
CREATE TABLE roadworthy_records (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    project_id INTEGER REFERENCES projects(id),
    certificate_number VARCHAR(100),
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    cost NUMERIC(12,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reminders (auto-generated + manual)
CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    driver_id INTEGER REFERENCES drivers(id),
    reminder_type VARCHAR(50) NOT NULL, -- 'insurance', 'roadworthy', 'service', 'licence', 'health', 'custom'
    title VARCHAR(200) NOT NULL,
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved'
    reference TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'viewer', -- 'admin', 'manager', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_fuel_tx_vehicle ON fuel_transactions(vehicle_id);
CREATE INDEX idx_fuel_tx_date ON fuel_transactions(transaction_date);
CREATE INDEX idx_fuel_tx_card ON fuel_transactions(fuel_card_id);
CREATE INDEX idx_fuel_tx_project ON fuel_transactions(project_id);
CREATE INDEX idx_maint_vehicle ON maintenance_records(vehicle_id);
CREATE INDEX idx_maint_date ON maintenance_records(service_date);
CREATE INDEX idx_trips_vehicle ON trips(vehicle_id);
CREATE INDEX idx_trips_project ON trips(project_id);
CREATE INDEX idx_reminders_status ON reminders(status);
CREATE INDEX idx_reminders_due ON reminders(due_date);

-- Seed Data
INSERT INTO fuel_types (name) VALUES ('Diesel'), ('Petrol'), ('LPG');
INSERT INTO vehicle_types (name) VALUES ('Pickup'),('Land Cruiser'),('Hilux'),('Saloon'),('Van'),('Motorcycle');
INSERT INTO departments (name, code) VALUES 
    ('Office Pool', 'POOL'),
    ('HOPE-V 1', 'HV1'),
    ('HOPE-V 2', 'HV2'),
    ('HOPE-V 3', 'HV3'),
    ('HOPE-V 4', 'HV4'),
    ('Administration', 'ADM');
INSERT INTO vehicle_groups (name) VALUES ('HOPE-V'), ('Office Pool'), ('Field Operations');
INSERT INTO maintenance_types (name, interval_km, interval_days, reminder_days) VALUES
    ('Oil Change', 10000, 90, 14),
    ('Tyre Rotation', 15000, 180, 14),
    ('Full Service', 20000, 365, 30),
    ('Brake Inspection', 20000, 180, 14),
    ('Air Filter', 20000, 365, 14),
    ('Transmission Service', 40000, 730, 30);

-- Add balance threshold to fuel cards (run after initial schema)
ALTER TABLE fuel_cards ADD COLUMN IF NOT EXISTS balance_threshold NUMERIC(12,2) DEFAULT 500;

-- Reminder settings table
CREATE TABLE IF NOT EXISTS reminder_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value VARCHAR(200) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO reminder_settings (setting_key, setting_value, description) VALUES
    ('insurance_reminder_days', '30', 'Days before insurance expiry to remind'),
    ('roadworthy_reminder_days', '30', 'Days before roadworthy expiry to remind'),
    ('licence_reminder_days', '30', 'Days before driver licence expiry to remind'),
    ('health_reminder_days', '30', 'Days before health certificate expiry to remind'),
    ('fuel_card_threshold', '500', 'Default low balance threshold in GH₵')
ON CONFLICT (setting_key) DO NOTHING;

-- Run this if upgrading existing DB
-- ALTER TABLE fuel_cards ADD COLUMN IF NOT EXISTS balance_threshold NUMERIC(12,2) DEFAULT 500;
