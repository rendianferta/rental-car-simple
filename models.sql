Drop DATABASE car_rental;
CREATE DATABASE IF NOT EXISTS car_rental;
USE car_rental;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255),
    role ENUM('admin', 'member')
);

CREATE TABLE cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(255),
    status ENUM('available', 'rented')
);

CREATE TABLE rentals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    car_id INT,
    due_date date,
    status ENUM('pending', 'approved', 'rejected','complete'),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (car_id) REFERENCES cars(id)
);

INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');
INSERT INTO cars (name, category, status) VALUES ('Toyota Avanza', 'SUV', 'available'), ('Honda Jazz', 'Hatchback', 'available');
