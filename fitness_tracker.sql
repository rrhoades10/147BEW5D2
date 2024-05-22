CREATE DATABASE fitness_tracker;

USE fitness_tracker;

-- members table  - Customers table from ecommerce
CREATE TABLE Members (
	member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    phone_number VARCHAR(150), 
    credit_card VARCHAR(30)
);

--  workout session table - orders
CREATE TABLE Workouts (
	workout_id INT AUTO_INCREMENT PRIMARY KEY,
    activity VARCHAR(150) NOT NULL,
    date DATE, 
    time TIME,
    member_id INT,
    FOREIGN KEY(member_id) REFERENCES Members(member_id)

);

DROP TABLE Workouts;
-- date format "yyyy-mm-dd"
-- time format "hh:mm:ss"

