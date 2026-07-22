# DeliverySlip Flask App

A simple Flask application for registering delivery slips and updating their status.

## Features

- Login required for registering and updating delivery slips
- Root user can register new users
- Delivery slip statuses progress through:
  - `terdaftar`
  - `mencetak`
  - `menyiapkan barang`
  - `mengirim`
  - `mengupload`
- Users can register delivery slips and update the status of their own slips
- Root user can view all slips and register users

## Setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Run the app:

   ```powershell
   python app.py
   ```

3. Open http://127.0.0.1:5000 in your browser.

   To make the app accessible from other devices on the same network, run:

   ```powershell
   $env:HOST = "0.0.0.0"
   $env:PORT = "5000"
   python app.py
   ```

   Then open http://<your-computer-ip>:5000 on the other device.

## Default root user

The app initializes a default root user when the database is created:

- Username: `root`
- Password: `root`

You can change the default password by setting the `ROOT_PASSWORD` environment variable before starting the app.

## Notes

- Only the root user can access `/users/register` to create new users.
- Regular users can access `/delivery/register` and update the status of their own delivery slips.
