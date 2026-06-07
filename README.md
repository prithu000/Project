# CamCap - Wearable Camera Cap E-Commerce Platform

Modern e-commerce platform for selling CamCap - a wearable camera cap with built-in video recording capabilities.

## Features

- 🎨 Modern UI with light blue cyber theme
- 🔐 Google OAuth authentication
- 💳 Razorpay payment gateway (Cards, UPI, NetBanking, Wallets)
- 💰 Cash on Delivery (COD) option
- 📦 Advanced order tracking with 6-step timeline
- 📧 Email notifications for orders
- 🎥 Video converter (.build to MP4)
- 👨‍💼 Admin panel for managing products and orders
- 📱 Fully responsive design

## Tech Stack

- **Backend**: Django 5.2
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Payment**: Razorpay
- **Authentication**: django-allauth (Google OAuth)
- **Email**: Gmail SMTP

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/prithu000/Project.git
cd Project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_SECRET=your-google-secret

# Razorpay
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

### 5. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

## Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth credentials
5. Add authorized redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
6. Add credentials to `.env` file

### Razorpay Setup

1. Sign up at [Razorpay](https://razorpay.com/)
2. Get API keys from Dashboard
3. For testing, use test mode keys
4. Add credentials to `.env` file

### Gmail SMTP Setup

1. Enable 2-Factor Authentication on Gmail
2. Generate App Password: [Google Account Security](https://myaccount.google.com/security)
3. Use app password in `.env` file

## Admin Panel

Access admin panel at: http://127.0.0.1:8000/admin/

**Features:**
- Update product price
- Manage orders
- Update order status
- Add tracking information (tracking number, courier, delivery date)
- View payment details

## Order Tracking Statuses

1. **Order Placed** - Initial status when order is created
2. **Confirmed** - Order confirmed by admin
3. **Packed** - Order packed and ready to ship
4. **Shipped** - Order dispatched
5. **Out for Delivery** - Order is on the way
6. **Delivered** - Order delivered to customer

## Deployment

### Environment Variables (Production)

```env
DEBUG=False
DJANGO_SECRET_KEY=[generate-new-secret]
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=your-database-url
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Update Google OAuth Redirect URI

Add production callback URL: `https://yourdomain.com/accounts/google/login/callback/`

## Project Structure

```
project11/
├── camcap/           # Main Django project
├── shop/             # E-commerce app
├── converter/        # Video converter app
├── templates/        # Custom templates
├── static/           # Static files
├── media/            # Uploaded files
├── .env             # Environment variables (not in git)
└── requirements.txt  # Python dependencies
```

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit `.env` file to Git
- Always use environment variables for secrets
- Generate new `SECRET_KEY` for production
- Use Razorpay live keys for production
- Keep Gmail app passwords secure

## Support

For issues or questions, please open an issue on GitHub.

## License

This project is private and proprietary.

---

**Developed for CamCap** - Capture Every Moment Hands-Free
