# 🚀 AURA / Aethel E-Commerce — Production Deployment Guide

This guide provides step-by-step instructions for deploying your E-Commerce web application live to the internet so that customers anywhere in the world can access it.

---

## ⚡ Option 1: Deploy to Render.com (Recommended — Fast & Free/Low Cost)

Render is the easiest platform to deploy Python/Flask applications directly from a GitHub repository.

### Step 1: Push your code to GitHub
1. Initialize a git repository if you haven't already:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for production"
   ```
2. Create a new repository on [GitHub.com](https://github.com/new) (public or private).
3. Link and push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Create a Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `aura-healthcare-store` (or your chosen store name)
   - **Region**: Choose the closest region (e.g., Frankfurt, Singapore, or Oregon)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --workers 4 --threads 2 --bind 0.0.0.0:$PORT`
4. Under **Environment Variables**, add:
   - `SECRET_KEY`: *(Click "Generate" on Render or paste a 32+ character random string)*
   - `FLASK_ENV`: `production`
   - `FORCE_SEED`: `false`
5. *(Optional for Permanent Data)*: If you want SQLite data saved across redeploys, add a **Render Disk** mounted at `/var/data` and add the environment variable:
   - `DATABASE_PATH`: `/var/data/ecommerce.db`
6. Click **Create Web Service**. Your store will be live in 1–2 minutes with free HTTPS/SSL!

---

## 🚂 Option 2: Deploy to Railway.app

Railway offers instant deployment and automatically detects the `Procfile` and `requirements.txt`.

1. Go to [Railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your repository.
4. Go to **Variables** tab and set:
   - `SECRET_KEY`: `<your-random-secret-key>`
   - `FLASK_ENV`: `production`
5. Railway will automatically build and assign a live public URL (e.g. `https://aura-store-production.up.railway.app`).
6. Under **Settings** → **Domains**, you can connect your own custom domain (e.g., `www.yourbrand.com`).

---

## 🐍 Option 3: Deploy to PythonAnywhere

1. Create an account at [PythonAnywhere.com](https://www.pythonanywhere.com/).
2. Open a **Bash Console** and clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git ecommerce
   cd ecommerce
   mkvirtualenv --python=/usr/bin/python3.10 myenv
   pip install -r requirements.txt
   ```
3. Go to the **Web** tab in PythonAnywhere dashboard:
   - Click **Add a new web app** → **Manual configuration** → **Python 3.10**.
   - Set **Source code path**: `/home/yourusername/ecommerce`
   - Set **Working directory**: `/home/yourusername/ecommerce`
   - Set **Virtualenv path**: `/home/yourusername/.virtualenvs/myenv`
4. Edit the **WSGI configuration file** (link provided in Web tab):
   ```python
   import sys
   import os

   path = '/home/yourusername/ecommerce'
   if path not in sys.path:
       sys.path.append(path)

   from app import app as application
   ```
5. Click **Reload yourusername.pythonanywhere.com** to launch.

---

## 🐳 Option 4: Deploy with Docker on any VPS (DigitalOcean, Linode, AWS, Hetzner)

If you have a Linux VPS (Ubuntu/Debian):

### 1. Build and Run the Docker Container
```bash
# Build the Docker image
docker build -t ecommerce-store .

# Run container with persistent database volume on port 80
docker run -d \
  --name store_app \
  -p 80:5000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY="your_secure_secret_key_here" \
  -e DATABASE_PATH="/app/data/ecommerce.db" \
  -e FLASK_ENV="production" \
  --restart always \
  ecommerce-store
```

### 2. Setup Free SSL with Certbot & Nginx (Optional Reverse Proxy)
```nginx
server {
    server_name yourstore.com www.yourstore.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔐 Production Checklist & Best Practices

1. **Secret Key**: Generate a secure 64-character secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Never commit `.env` containing your real secret key to public git repositories.
2. **Admin Credentials**: Immediately change the default admin credentials:
   - Default Admin: `admin@store.com` or `admin@aethel.com`
   - Default Password: `admin123`
   - You can update your password in the admin panel or user profile.
3. **Payments**:
   - For live operations, you can connect your merchant payment gateways (Stripe / 3D-Secure Card / Bank Transfer / Cash on Delivery).
4. **Backups**: Periodically download or back up `ecommerce.db`.
