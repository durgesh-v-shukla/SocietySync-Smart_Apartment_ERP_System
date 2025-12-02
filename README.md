# SocietySyncERP 🏢

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40.2-red.svg)
![DBMS](https://img.shields.io/badge/DBMS-Project-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎓 Academic DBMS Project

A comprehensive Database Management System (DBMS) project demonstrating real-world application of database concepts, SQL operations, normalization, transactions, and security principles. This Smart Apartment Management System is built using Python, Streamlit, and PostgreSQL to manage residential society operations with role-based access control, advanced visitor management, and real-time notifications.

**An exemplary DBMS project showcasing:**
- ✅ Database Design & Normalization (3NF)
- ✅ 11 Normalized Database Tables
- ✅ 60+ SQL Queries (Complex JOINs, Aggregations, Transactions)
- ✅ 50+ Advanced DBMS Concepts
- ✅ Transaction Management (ACID Properties)
- ✅ Security (SQL Injection Prevention, Password Hashing)
- ✅ Real-world Application Development

**GitHub Repository:** [https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System](https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System)

---

## 📋 Table of Contents

1. [Why This is the Best DBMS Project](#-why-this-is-the-best-dbms-project)
2. [Overview](#-overview)
3. [Key Features](#-key-features)
4. [DBMS Concepts Demonstrated](#-dbms-concepts-demonstrated)
5. [Prerequisites](#-prerequisites)
6. [Setup & Running Instructions](#-setup--running-instructions)
7. [Project Structure](#️-project-structure)
8. [Technology Stack](#-technology-stack)
9. [Project Team](#-project-team)
10. [License](#-license)

---

## 🏆 Why This is the Best DBMS Project

### **Comprehensive DBMS Implementation**
This project is a perfect example of real-world database management system implementation because:

1. **Complete Database Lifecycle**: From design to deployment, covering all phases of database development
2. **Industry-Standard Practices**: Uses professional tools (PostgreSQL, Python, Streamlit) and follows best practices
3. **All DBMS Concepts in One Place**: Demonstrates 50+ database concepts in a single cohesive application
4. **Real-World Application**: Solves actual problems faced by residential societies, not just theoretical exercises
5. **Scalable Architecture**: Designed to handle growing data and user base efficiently

### **Why Students Choose This Project**
- ✅ **Easy to Understand**: Clear code structure with proper documentation
- ✅ **Easy to Demonstrate**: Visual interface makes concepts tangible during presentations
- ✅ **Easy to Extend**: Modular design allows adding new features easily
- ✅ **Academic Excellence**: Covers all topics in DBMS syllabus with practical examples
- ✅ **Portfolio Ready**: Professional-grade project for resumes and GitHub profiles

### **What Makes It Stand Out**
- 🎯 **11 Normalized Tables**: Perfect demonstration of database normalization (3NF)
- 🎯 **60+ SQL Queries**: Covers SELECT, INSERT, UPDATE, DELETE, JOINs, Aggregations, Transactions
- 🎯 **Role-Based Access**: Shows real-world authentication and authorization
- 🎯 **Transaction Management**: ACID properties implementation with proper error handling
- 🎯 **Security Best Practices**: SQL injection prevention, password hashing, session management

---

## 🎯 Overview

SocietySyncERP is a comprehensive apartment management solution designed specifically for Vishwakarma Apartment in Pune. Built with modern web technologies, it provides a centralized platform for administrators, flat owners, and tenants to manage all society operations efficiently.

**The system streamlines daily operations including:**
- 👥 User & Resident Management
- 💰 Billing & Payment Tracking
- 🎫 Complaint Resolution System
- 👤 Advanced Visitor Management with Photos & Camera Capture
- 🔔 Real-time Notification System
- 🗳️ Democratic Polling & Voting
- 📊 Analytics & Reporting

---

## ✨ Key Features

### 🔐 Security & Authentication
- **Role-Based Access Control (RBAC)**: Three distinct roles - Admin, Owner, Tenant
- **Secure Password Hashing**: bcrypt encryption for all passwords
- **Session Management**: Streamlit session state for secure user sessions
- **Profile Management**: Users can update their information and change passwords

### 👥 Advanced User Management
- **Automated User Creation**: Auto-generate usernames and secure passwords
- **Owner Management**: Complete CRUD operations with flat assignments
- **Tenant Management**: Link tenants to flat owners with rental period tracking
- **Bulk Operations**: Manage multiple users efficiently
- **Only Allotted Flats**: System shows only flats that have assigned residents

### 💰 Smart Billing System
- **Bill Generation**: Create bills for specific flats with multiple categories
- **Payment Tracking**: Real-time status updates (Pending/Paid/Overdue)
- **Advanced Filtering**: Filter by flat, status, date range, and amount
- **Bill Analytics**: Visual charts showing payment distribution
- **Due Date Management**: Automatic overdue detection
- **Bill History**: Complete payment history for all residents

### 📝 Complaint Management System
- **Multi-Priority Support**: Low, Normal, High, Critical priority levels
- **Status Tracking**: Pending → In Progress → Resolved workflow
- **Resident Complaints**: Owners and tenants can submit complaints
- **Admin Dashboard**: Centralized complaint resolution interface
- **Complete Audit Trail**: Track complaint lifecycle with timestamps
- **Categorization**: Organize complaints by type and severity

### 👤 Advanced Visitor Management 🆕
- **📷 Dual Photo Capture**: Upload photos from files OR capture directly using laptop camera
- **📁 File Upload**: Support for PNG, JPG, JPEG image formats
- **📸 Live Camera**: Real-time photo capture using device camera (webcam/built-in camera)
- **Real-time Logging**: Track entry and exit times
- **Visitor History**: Complete historical records with search and filters
- **Multi-field Search**: Filter by flat, date, status, and visitor details
- **Vehicle Tracking**: Record vehicle numbers for parking management
- **Purpose Documentation**: Track purpose of visits
- **Automatic Notifications**: 🔔 Residents get notified when visitors arrive
- **Owner Information**: Display flat owner names in visitor records

### 🔔 Real-time Notification System
- **Broadcast Announcements**: Admin can send society-wide notifications
- **Priority Levels**: Low, Normal, High priority messages
- **Read Receipt Tracking**: Track who has read each notification
- **Unread Indicators**: Visual badges for unread notifications
- **Notification History**: Access all past notifications
- **Visitor Alerts**: Automatic notifications when visitors arrive at your flat
- **Targeted Messaging**: Notifications sent to specific flat residents

### 🗳️ Democratic Polling System
- **Multi-Option Polls**: Create polls with unlimited options
- **Real-time Voting**: Instant vote counting and results
- **Visual Analytics**: Pie charts showing vote distribution
- **Active/Closed Status**: Control poll availability
- **Vote Tracking**: Prevent duplicate voting
- **Participation Analytics**: See total participation rates

### 🎨 Modern User Interface
- **Responsive Design**: Clean, professional interface with styled containers
- **White Background Containers**: Consistent styling across all pages
- **Visual Icons**: Emoji-based navigation and status indicators
- **Color-coded Status**: Green (success), Yellow (pending), Red (critical)
- **Interactive Charts**: Plotly-powered data visualizations
- **Smooth Navigation**: Sidebar-based menu system with icons



## 🛠️ Prerequisites

- **Python 3.9+** or **Python 3.13** (Recommended)
- **PostgreSQL 12+** (Version 14+ recommended)
- **pip** (Python package installer)
- **Modern Web Browser** (Chrome, Firefox, Edge)

---

## 🚀 Setup & Running Instructions

### 1️⃣ Install Dependencies and Setup Virtual Environment

In VS Code terminal:

```bash
# Install required Python packages
pip install streamlit psycopg2-binary pandas plotly bcrypt python-dotenv

# Create a virtual environment
python -m venv societysync_env

# Activate the virtual environment
# Windows
societysync_env\Scripts\activate
# macOS/Linux
source societysync_env/bin/activate
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/societysync
```

Replace `YOUR_POSTGRES_PASSWORD` with your actual PostgreSQL password.

---

### 2️⃣ Initialize PostgreSQL Database

In Command Prompt or terminal:

```bash
# Enter PostgreSQL shell
psql -U postgres

# You will be prompted to enter your PostgreSQL password

# Create the database
CREATE DATABASE societysync;

# Exit psql
\q

# Apply schema and seed data
psql -U postgres -d societysync -f societysync_schema.sql
psql -U postgres -d societysync -f societysync_data.sql
```

---

### 3️⃣ Synchronize Table Sequences

In pgAdmin4 query tool, run the following queries to reset sequences:

```sql
-- Users
SELECT MAX(user_id) FROM users;
SELECT setval('users_user_id_seq', <max_user_id>);

-- Owners
SELECT MAX(owner_id) FROM owners;
SELECT setval('owners_owner_id_seq', <max_owner_id>);

-- Bills
SELECT MAX(bill_id) FROM bills;
SELECT setval('bills_bill_id_seq', <max_bill_id>);

-- Visitors
SELECT MAX(visitor_id) FROM visitors;
SELECT setval('visitors_visitor_id_seq', <max_visitor_id>);

-- Notifications
SELECT MAX(notification_id) FROM notifications;
SELECT setval('notifications_notification_id_seq', <max_notification_id>);

-- Polls
SELECT MAX(poll_id) FROM polls;
SELECT setval('polls_poll_id_seq', <max_poll_id>);

-- Votes
SELECT MAX(vote_id) FROM votes;
SELECT setval('votes_vote_id_seq', <max_vote_id>);

-- Complaints
SELECT MAX(complaint_id) FROM complaints;
SELECT setval('complaints_complaint_id_seq', <max_complaint_id>);

-- Poll Options
SELECT MAX(option_id) FROM poll_options;
SELECT setval('poll_options_option_id_seq', <max_option_id>);
```

---

### 4️⃣ Run SocietySyncERP App

Make sure the virtual environment is activated.

#### **Option 1: Using Run Script (Recommended)** ⭐

**PowerShell:**
```powershell
.\run_app.ps1
```

**Command Prompt/Batch:**
```cmd
run_app.bat
```

#### **Option 2: Manual Command**

```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/societysync"

# Run Streamlit app (port 8501 is default, use 8502 if needed)
streamlit run app.py --server.port 8501
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

#### **Option 3: Set Environment Variable Permanently**

1. Open **System Properties** → **Advanced** → **Environment Variables**
2. Add new System Variable:
   - **Name:** `DATABASE_URL`
   - **Value:** `postgresql://postgres:YOUR_PASSWORD@localhost:5432/societysync`
3. Replace `YOUR_PASSWORD` with your actual PostgreSQL password
4. Restart terminal, then just run:
   ```bash
   streamlit run app.py --server.port 8501
   ```

**Access the application:**
- 🌐 **URL:** http://localhost:8501/
- 📱 Open in your browser after the app starts

---

## 🗂️ Project Structure

```
SocietySyncERP/
├── 📄 Core Application Files
│   ├── app.py                          # Main Streamlit application entry point
│   ├── database.py                     # Database operations & SQL queries (60+ queries)
│   ├── auth.py                         # Authentication & session management
│   ├── utils.py                        # Utility functions & reusable UI components
│
├── 📊 Dashboard Modules (Role-Based)
│   ├── admin_dashboard.py              # Admin interface (full system control)
│   ├── owner_dashboard.py              # Flat owner dashboard (bills, visitors, complaints)
│   ├── tenant_dashboard.py             # Tenant dashboard (limited access)
│
├── 🗄️ Database Files
│   ├── societysync_schema.sql          # Complete database schema (11 tables)
│   ├── societysync_data.sql            # Sample data for testing
│
├── 🚀 Run Scripts
│   ├── run_app.ps1                     # PowerShell run script (Windows)
│   ├── run_app.bat                     # Batch run script (Windows)
│
├── 📦 Configuration
│   ├── requirements.txt                # Python dependencies
│   ├── README.md                       # This file
│   ├── LICENSE                         # MIT License
│   └── .gitignore                      # Git ignore rules
```

---

## 🎓 DBMS Concepts Demonstrated

### **Database Design**
- ✅ **Normalization**: Tables designed in 3NF (Third Normal Form)
- ✅ **Entity-Relationship Model**: Clear relationships between entities
- ✅ **Referential Integrity**: Foreign key constraints with cascading
- ✅ **Data Types**: Appropriate use of VARCHAR, INTEGER, TIMESTAMP, TEXT, BOOLEAN

### **Constraints & Validation**
- ✅ **PRIMARY KEY**: Unique identifiers for all tables
- ✅ **FOREIGN KEY**: Maintains relationships (users→flats, bills→users, etc.)
- ✅ **UNIQUE Constraints**: Prevent duplicate usernames, emails
- ✅ **NOT NULL**: Mandatory fields enforcement
- ✅ **CHECK Constraints**: Validate data (status IN ('pending', 'paid'), priority levels)
- ✅ **DEFAULT Values**: Automatic timestamps, status defaults

### **Advanced SQL Operations**
- ✅ **Complex JOINs**: LEFT JOIN, INNER JOIN for multi-table queries
- ✅ **Aggregate Functions**: COUNT(), SUM(), AVG(), MAX(), MIN()
- ✅ **GROUP BY & HAVING**: Statistical analysis and filtering
- ✅ **Subqueries**: Nested SELECT statements for complex data retrieval
- ✅ **DISTINCT ON**: PostgreSQL-specific deduplication
- ✅ **Window Functions**: Advanced analytics (potential for future expansion)

### **Sequences & Auto-increment**
- ✅ **SERIAL Columns**: Auto-incrementing primary keys
- ✅ **Sequence Synchronization**: Manual sync after data import
- ✅ **RETURNING Clause**: Get auto-generated IDs after INSERT

### **Transactions & ACID Properties**
- ✅ **Atomicity**: All-or-nothing operations
- ✅ **Consistency**: Data integrity maintained
- ✅ **Isolation**: Concurrent transaction handling
- ✅ **Durability**: Permanent data storage
- ✅ **Autocommit Mode**: Automatic transaction commits
- ✅ **Error Handling**: Rollback on exceptions

### **Indexing & Performance**
- ✅ **Primary Key Indexes**: Automatic indexing on PKs
- ✅ **Foreign Key Indexes**: Faster JOIN operations
- ✅ **Query Optimization**: Efficient WHERE clauses and JOINs

### **Security Features**
- ✅ **Password Hashing**: bcrypt for secure password storage
- ✅ **SQL Injection Prevention**: Parameterized queries using psycopg2
- ✅ **Role-Based Access**: Database-level and application-level security
- ✅ **Prepared Statements**: All queries use parameter binding

### **Advanced Features**
- ✅ **Triggers**: Potential for audit logging (future enhancement)
- ✅ **Views**: Can be added for complex reporting
- ✅ **Stored Procedures**: Candidates for complex business logic
- ✅ **BLOB Storage**: Base64 encoding for visitor photos

---

## 💻 Technology Stack

### **Backend**
- **Python 3.13** - Core programming language
- **PostgreSQL 14+** - Relational database
- **psycopg2-binary** - PostgreSQL adapter for Python
- **bcrypt** - Password hashing and security

### **Frontend**
- **Streamlit** - Web application framework
- **HTML/CSS** - Custom styling with markdown
- **JavaScript (via Streamlit)** - Interactive components

### **Data Visualization**
- **Plotly** - Interactive charts and graphs
- **Pandas** - Data manipulation and analysis
- **PIL (Pillow)** - Image processing for visitor photos

### **Development Tools**
- **VS Code** - IDE with Pylance extension
- **pgAdmin 4** - PostgreSQL administration
- **Git** - Version control
- **PowerShell** - Automation scripts

### **Libraries & Dependencies**
```
streamlit>=1.28.0
psycopg2-binary>=2.9.9
pandas>=2.0.0
plotly>=5.17.0
bcrypt>=4.0.1
python-dotenv>=1.0.0
Pillow>=10.0.0
```

---

## 👥 Project Team

### **Group Members**
- **Durgesh Shukla** - [@durgesh-v-shukla](https://github.com/durgesh-v-shukla)
- **Siddhant Gade**
- **Rushi Solanakar**
- **Rohit Shitole**

### **Academic Information**
- 🏛️ **Institution**: Vishwakarma Institute of Technology, Pune
- 🎓 **Department**: Computer Engineering
- 📚 **Course**: Database Management Systems (DBMS)
- 👩‍🏫 **Project Guide**: Prof. Dr. Disha Wankhede
- 📅 **Academic Year**: 2025-2026 (Semester III)

### **Project Scope**
This project is developed as part of the DBMS curriculum to demonstrate practical application of database concepts including:
- Database design and normalization
- SQL query optimization
- Transaction management and ACID properties
- Security and authentication mechanisms
- Real-world application development

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 📧 Contact

For queries related to this project, please contact:

- 📩 **Durgesh Shukla** - [GitHub](https://github.com/durgesh-v-shukla)
- 🏫 **Institution**: Vishwakarma Institute of Technology, Pune
- 🔗 **Repository**: [https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System](https://github.com/durgesh-v-shukla/SocietySync-Smart_Apartment_ERP_System)

---

**⭐ If you find this project helpful, please consider giving it a star! ⭐**

---

**Made with ❤️ by Team K10 - VIT Pune**
