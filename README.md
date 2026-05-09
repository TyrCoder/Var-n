# Varón E-Commerce Platform

A full-featured e-commerce platform built with Flask and PostgreSQL, featuring buyer/seller/rider/admin roles, product management, order tracking, and real-time notifications.

## Features

- **Multi-role system**: Buyers, Sellers, Riders, Admins
- **Product management**: Categories, variants, inventory, images
- **Shopping cart & checkout**
- **Order tracking & status management**
- **Rider delivery system** with ratings
- **Review system** with seller responses
- **OTP verification** via email
- **Seller notifications**
- **Real-time store location mapping** (PSGC integration)
- **Buyer approval system** for controlled access
- **Account restriction/ban controls**
- **Transaction history**

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (Supabase)
- **Frontend**: HTML5, CSS3, JavaScript
- **OTP**: Email-based verification
- **Maps**: PSGC API integration

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL (or Supabase account)
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/varon-ecommerce.git
cd varon-ecommerce
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (see RENDER_DEPLOYMENT.md for example)

5. Run the app:
```bash
python app.py
```

The app will start at `http://localhost:5000`

### Database

This app uses **PostgreSQL** hosted on **Supabase**. Update your `.env` with:
- `DB_HOST`: Your Supabase host
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_NAME`: Database name
- `DB_PORT`: Usually 5432

## Deployment

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for step-by-step Render deployment instructions.

## Project Structure

```
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── Procfile                  # Render deployment config
├── runtime.txt              # Python version
├── .env                     # Environment variables (not committed)
├── .gitignore              # Git ignore rules
├── static/                 # CSS, JS, images
├── templates/              # HTML templates
├── services/               # Business logic
├── utils/                  # Utility functions
├── migrations/             # Database migration scripts
└── scripts/                # Maintenance scripts
```

## Key Routes

- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/seller-dashboard` - Seller dashboard
- `/admin-dashboard` - Admin dashboard
- `/buyer-approval` - Buyer approval system
- `/products` - Product listing
- `/orders` - Order management
- `/riders` - Rider management

## Environment Variables

```env
DB_HOST=              # PostgreSQL host
DB_USER=              # PostgreSQL user
DB_PASSWORD=          # PostgreSQL password
DB_NAME=              # Database name
DB_PORT=              # PostgreSQL port (default: 5432)
SECRET_KEY=           # Flask secret key
MAIL_SERVER=          # SMTP server for OTP
MAIL_USERNAME=        # Email username
MAIL_PASSWORD=        # Email password
```

## Contributing

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open a Pull Request

## License

Proprietary - Varón Apparel

## Support

For issues or questions, open a GitHub issue or contact the team.

---

**Deployed on Render** - Scalable, production-ready hosting
