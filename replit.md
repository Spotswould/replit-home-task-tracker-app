# Home Task Tracker - Repository Overview

## User Preferences

Preferred communication style: Simple, everyday language.

## Project Status

**Current State**: Production-ready application optimized for deployment
**User Feedback**: Application ready for Git deployment with all debugging code removed
**Date**: August 12, 2025

## Recent Changes

✓ **Production Deployment Preparation** - Removed all debugging code, console logs, and optimized for deployment with .gitignore and README.md
✓ **Task Description Character Limits** - Added 200 character limit with live feedback and color-coded character counter for admin task creation
✓ **Expandable Text Fix** - Resolved JavaScript event handling issues for task description expansion on worker dashboard
✓ **Complete Password Reset System** - Implemented secure password reset functionality with email integration, token-based security, and Gmail SMTP support
✓ **Paid Status System** - Replaced weekly reset with "Paid" status tracking system for better payment management
✓ **Task Resubmission Feature** - Workers can now resubmit rejected tasks for the same date after addressing admin feedback
✓ **Visual Improvements** - Updated admin dashboard with vacuum cleaner icon and reports page with colorful chart icon
✓ **Worker Dashboard Enhancement** - Added admin comment visibility in Recent Activity with clear earnings display and paid status tracking
✓ **Payment Status Clarity** - Updated worker dashboard to clearly distinguish "You were paid £X" vs "You are awaiting payment for this task of £X" messages
✓ **Admin Payment Interface** - Implemented expandable worker cards showing payment summaries and interactive payment tables with one-click "Mark Paid" functionality
✓ **History Page Updates** - Updated completion history with payment status cards and filters: "Awaiting Payment", "Paid", "Total Paid" replacing previous "Approved" and "Total Earned"
✓ **Worker Dashboard Refinement** - Replaced "This Week's Earnings" and "Approval Rate" cards with "Awaiting Payment" and "Rejected" for clearer payment status visibility
✓ **About Page** - Created comprehensive workflow guide for administrators and workers with navigation access
✓ **Approval Queue Fix** - Resolved 500 error by removing undefined csrf_token() function reference
✓ **UK Date Format** - Updated all date displays across the system to use DD/MM/YYYY format instead of US format
✓ **Profile Enhancement** - Added password change functionality for both admin and worker users
✓ **Account Security** - Implemented secure account deletion with multiple verification steps
✓ **Registration UX** - Added clear password requirements display on Create Account page
✓ **Error Messages** - Improved worker registration validation with specific error feedback
✓ **Database Fixes** - Resolved profile view server errors and Flask-Login configuration issues

## System Architecture

This is a Flask-based web application for managing household tasks with a two-tier user system (administrators and workers). The application follows a traditional MVC architecture pattern with server-side rendering using Jinja2 templates.

### Core Technologies
- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **Authentication**: Flask-Login for session management
- **Frontend**: Bootstrap 5 with custom CSS and JavaScript
- **Forms**: WTForms for form handling and validation

## Key Components

### Database Models (`models.py`)
- **User Model**: Handles both admin and worker roles with hierarchical relationships
- **Task Model**: Stores task information including title, description, monetary value, and metadata
- **TaskCompletion Model**: Tracks task completions and approval workflow

### Authentication & Authorization (`auth.py`)
- Role-based access control with decorators
- Three permission levels: login_required, admin_required, worker_required
- Ownership validation for data access control

### Forms (`forms.py`)
- Login/Registration forms with email validation
- Task creation and completion forms
- Approval workflow forms with status management
- Report generation forms with date range selection

### Routes (`routes.py`)
- Separate dashboard views for admin and worker roles
- CRUD operations for tasks and completions
- Approval queue management
- Report generation and CSV export functionality

### Utilities (`utils.py`)
- Payment calculation functions
- Date/week management utilities
- Statistics and reporting helpers

## Data Flow

1. **Task Creation**: Admins create tasks with monetary values and descriptions
2. **Task Assignment**: Tasks are available to all workers under an admin
3. **Task Completion**: Workers mark tasks as completed with completion dates
4. **Approval Process**: Admins review and approve/reject completed tasks
5. **Payment Tracking**: Approved tasks contribute to worker earnings calculations

## External Dependencies

### Python Packages
- Flask and Flask extensions (SQLAlchemy, Login, WTF)
- Werkzeug for security utilities
- SQLAlchemy for database operations

### Frontend Dependencies
- Bootstrap 5.3.0 (CSS framework)
- Font Awesome 6.4.0 (icons)
- Custom CSS and JavaScript for enhanced user experience

### Environment Variables
- `SESSION_SECRET`: Flask session encryption key
- `DATABASE_URL`: Database connection string

## Deployment Strategy

The application is configured for deployment with:
- ProxyFix middleware for reverse proxy support
- Database connection pooling with health checks
- Environment-based configuration management
- Logging configuration for debugging and monitoring

### Database Initialization
- Automatic table creation on startup
- SQLAlchemy migrations support (implicit)
- Support for both development (SQLite) and production (PostgreSQL) databases

### Security Features
- Password hashing with Werkzeug
- CSRF protection via Flask-WTF
- Role-based access control
- Session management with Flask-Login

The application is designed to be simple yet comprehensive, focusing on task management workflow with proper user roles, approval processes, and payment tracking capabilities.