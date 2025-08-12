# Home Task Tracker

A comprehensive Flask-based web application for managing household tasks with role-based user management and payment tracking. Built specifically for administrators to assign tasks and track worker completion with an integrated approval and payment system.

## Features

### 🏠 Task Management
- **Admin Features**: Create, edit, and manage household tasks with monetary values
- **Worker Features**: View available tasks, mark completions, and track payment status
- **Real-time Status**: Track task completion status with approval workflow

### 👥 User Roles
- **Administrators**: Full control over task creation, worker management, and payment approval
- **Workers**: Task completion, progress tracking, and payment history viewing
- **Role-based Access**: Secure access control with hierarchical permissions

### 💰 Payment System
- **UK Currency**: All transactions in British Pounds (£)
- **Payment Tracking**: Comprehensive "Paid" status system replacing weekly resets
- **Financial Reports**: Detailed payment history and pending payment summaries
- **Task Resubmission**: Workers can resubmit rejected tasks after addressing feedback

### 🔐 Security & Authentication
- **Secure Login**: Password-protected user accounts with session management
- **Password Reset**: Email-based password recovery with Gmail SMTP integration
- **Account Management**: Profile editing and secure account deletion options
- **Admin Verification**: Worker registration requires valid administrator email

### 📊 Reporting & Analytics
- **Payment Dashboard**: Visual cards showing payment status and financial summaries
- **Task History**: Complete completion history with filtering by payment status
- **Performance Metrics**: Worker performance tracking and approval rates
- **CSV Export**: Export reports for external analysis

### 🌐 User Experience
- **Responsive Design**: Bootstrap 5-based interface optimized for all devices
- **UK Date Format**: DD/MM/YYYY date display throughout the application
- **Character Limits**: Smart task description limits with real-time feedback
- **Expandable Content**: Click-to-expand descriptions for better readability

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Authentication**: Flask-Login with secure session management
- **Email**: Flask-Mail with Gmail SMTP support
- **Forms**: WTForms with comprehensive validation

## Quick Start

1. **Environment Setup**
   ```bash
   # Required environment variables
   SESSION_SECRET=your-secret-key
   DATABASE_URL=your-postgresql-url
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-gmail@gmail.com
   ```

2. **Database Configuration**
   - PostgreSQL database with automatic table creation
   - Environment-based configuration for development and production

3. **Email Configuration**
   - Gmail SMTP for password reset functionality
   - App passwords recommended for enhanced security

## User Workflows

### Administrator Workflow
1. **Account Setup**: Register as administrator
2. **Task Creation**: Create tasks with descriptions, values, and priorities
3. **Worker Management**: Review worker registrations and manage accounts
4. **Approval Process**: Review completed tasks and approve/reject with comments
5. **Payment Management**: Track payments and mark tasks as paid
6. **Reporting**: Generate reports and export data for analysis

### Worker Workflow
1. **Registration**: Sign up with administrator's email for verification
2. **Task Viewing**: Browse available tasks with expandable descriptions
3. **Task Completion**: Mark tasks as completed with specific dates
4. **Status Tracking**: Monitor approval status and payment information
5. **Resubmission**: Address rejected tasks and resubmit for approval
6. **Payment History**: View comprehensive payment history and status

## Key Improvements

### Payment System Enhancement
- Replaced weekly reset system with persistent "Paid" status tracking
- Added comprehensive payment dashboards for both admins and workers
- Implemented task resubmission functionality for rejected tasks
- Created detailed payment history with status filtering

### User Experience Improvements
- UK date format (DD/MM/YYYY) implemented throughout
- Character-limited task descriptions with live feedback
- Expandable text functionality for better content management
- Enhanced visual feedback with color-coded status indicators

### Security & Reliability
- Complete password reset system with email integration
- Secure account deletion with verification steps
- Improved form validation with clear error messaging
- Production-ready logging and error handling

## Production Deployment

The application is optimized for production deployment with:
- Environment-based configuration management
- Database connection pooling with health checks
- Secure session management
- SMTP email integration
- Responsive design for mobile and desktop access

Perfect for household management, small business task tracking, or any scenario requiring role-based task assignment with payment tracking capabilities.