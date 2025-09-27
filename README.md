# 🎨 Marina Portfolio - Backend API

> Professional Flask API with modular architecture | Capstone project for [Bottega Code School](https://bottega.tech/)

## 🏗️ **Architecture Overview**

Modern Flask application with **clean architecture** and **separation of concerns**:

- **🌐 REST API** for React frontend (`/api/*`)
- **👨‍💼 Admin Panel** for user management (`/manager`)
- **🔐 JWT Authentication** with role-based access control
- **☁️ Cloudinary Integration** for optimized image management
- **📦 Modular Structure** with blueprints and services

## 🛠️ **Tech Stack**

### **Backend Framework**
- **Python 3.9** - Core language
- **Flask** - Web framework with Factory Pattern
- **Flask-JWT-Extended** - JWT authentication
- **Flask-WTF** - Forms and validation
- **Flask-CORS** - Cross-origin requests

### **Database & Storage**
- **MongoDB Atlas** - Cloud database
- **PyMongo** - MongoDB driver
- **Cloudinary** - Image storage and optimization

### **Development & Deployment**
- **Pipenv** - Dependency management
- **Render** - Cloud deployment
- **GitHub** - Version control
- **Postman** - API testing

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
cd marina-back-end
pipenv install
```

### **2. Environment Setup**
Create `.env` file with:
```env
SECRET_KEY=your-secret-key
ATLAS_URI=your-mongodb-connection
JWT_SECRET=your-jwt-secret
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
ADMIN_CREATION_KEY=your-bootstrap-key
```

### **3. Run Application**

**Recommended (New Architecture):**
```bash
pipenv run python run.py
```

**Alternative (Legacy Compatible):**
```bash
pipenv run python app.py
```

**Or with Flask CLI:**
```bash
export FLASK_APP="app:create_app('development')"
pipenv run flask run
```

## 📁 **Project Structure**

```
marina-back-end/
├── app/                        # 🏭 Main application
│   ├── __init__.py            # Factory pattern
│   ├── config.py              # Configuration management
│   │
│   ├── api/                   # 🌐 REST API (React frontend)
│   │   ├── auth.py           # JWT authentication
│   │   ├── portfolio.py      # Portfolio CRUD
│   │   └── store.py          # Store management
│   │
│   ├── admin/                 # 👨‍💼 Admin interface (Flask templates)
│   │   ├── routes.py         # User management
│   │   └── forms.py          # WTForms
│   │
│   ├── models/                # 📊 Data models
│   │   └── user.py           # User model + CRUD
│   │
│   ├── services/              # 🔧 Business logic
│   │   ├── auth_service.py   # Authentication logic
│   │   └── cloudinary_service.py # Image management
│   │
│   ├── utils/                 # 🛠️ Utilities
│   │   ├── decorators.py     # Auth decorators
│   │   └── validators.py     # Input validation
│   │
│   └── templates/             # 📄 Flask templates
│
├── run.py                     # 🎯 Application entry point
├── app.py                     # 🔄 Legacy compatibility
└── ARCHITECTURE.md            # 📚 Detailed architecture docs
```

## 🔗 **API Endpoints**

### **🔐 Authentication**
- `POST /api/token` - Login & get JWT token
- `POST /api/create-admin` - Create admin user (protected)

### **🎨 Portfolio Management**
- `GET /api/portfolio` - List all portfolios (public)
- `GET /api/portfolio/<id>` - Get single portfolio (public)
- `POST /api/portfolio` - Create portfolio (admin only)
- `DELETE /api/portfolio/<id>` - Delete portfolio (admin only)

### **🛍️ Store Management**
- `GET /api/store` - List all products (public)
- `GET /api/store/<id>` - Get single product (public)
- `POST /api/store` - Create product (admin only)
- `DELETE /api/store/<id>` - Delete product (admin only)

### **👨‍💼 Admin Panel (Flask Templates)**
- `GET /` - Login page
- `GET /manager` - User management dashboard (super admin)
- `POST /manager` - Create new users (super admin)
- `GET /update/<id>` - Edit user form (super admin)

## 🔒 **Role-Based Access Control**

1. **`super_admin`** (You):
   - ✅ Full Flask admin panel access
   - ✅ Create/manage React app users
   - ✅ Create other super admins
   - ✅ Access all API endpoints

2. **`admin`** (React App Users):
   - ✅ Manage portfolio content via API
   - ✅ Manage store products via API
   - ❌ No Flask admin panel access
   - ❌ Cannot create users

3. **`user`** (Public):
   - ✅ Read-only access to public content

## 🌐 **Live Deployment**

- **Production API:** [Render Flask App](https://marina-backend.onrender.com/)
- **Health Check:** `GET /api/portfolio`

## 🧪 **Testing**

```bash
# Test API endpoints
curl http://localhost:8080/api/portfolio

# Test authentication
curl -X POST http://localhost:8080/api/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

## 📈 **Architecture Benefits**

- **✅ Scalable:** Modular design supports growth
- **✅ Maintainable:** Clear separation of concerns
- **✅ Testable:** Independent components
- **✅ Professional:** Industry-standard patterns
- **✅ Secure:** Role-based authentication
- **✅ Flexible:** Multiple deployment configurations

---

## 🗝️ Bootstrap primer super_admin

1) .env:
- SECRET_KEY=...
- ATLAS_URI=...
- JWT_SECRET=...
- ADMIN_CREATION_KEY=<tu_clave_segura>

2) Arrancar:
pipenv run python run.py

3) Crear super_admin:
curl -s -X POST http://127.0.0.1:8080/api/create-admin \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Creation-Key: TU_CLAVE' \
  -d '{"email":"admin@tuapp.com","password":"Marina123","username":"SuperAdmin"}'

4) Política de contraseñas:
- Mínimo 8 caracteres
- Debe contener al menos 1 letra y 1 número

5) A partir del segundo admin (cuando ya existe un `super_admin`):
- Debes autenticarte como `super_admin` y usar su JWT en el header `Authorization`
- Obtén token:
```bash
curl -s -X POST http://127.0.0.1:8080/api/token \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@tuapp.com","password":"Marina123"}'
```
- Usa el `access_token` resultante para crear otro admin:
```bash
TOKEN=PEGA_AQUI_EL_ACCESS_TOKEN
curl -s -X POST http://127.0.0.1:8080/api/create-admin \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":"nuevo@tuapp.com","password":"Marina123","username":"Editor"}'
```

## Stripe 

Para probar webhooks de Stripe en local necesitas el Stripe CLI.
El flujo es:

Inicias sesión con tu cuenta:

```bash
stripe login
```


Te suscribes a los eventos que quieres escuchar y los reenvías a tu backend local (ejemplo Flask en localhost:5000/webhook):

```bash
stripe listen --forward-to localhost:5000/webhook
```

---

*Built with ❤️ using modern Flask best practices*