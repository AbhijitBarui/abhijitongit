# abhijitongit

## Environment setup for deployment

1. Create a `.env` file in the project root and add your secret key:

   ```env
   SECRET_KEY=<your value>
   ```
 
2. Set `DEBUG=False` and configure `ALLOWED_HOSTS` with your domain or server IP.

3. After defining `STATIC_ROOT` in `settings.py`, run the following inside the `backend` directory to collect static files:

   ```bash
   python manage.py collectstatic
   ```
