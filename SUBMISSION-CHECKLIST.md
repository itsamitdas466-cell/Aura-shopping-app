# AURA — submission-day checklist

## Run locally
1. Install Python 3.11+.
2. Double-click `run_windows.bat` (first run needs internet to install dependencies), or follow README instructions.
3. Open `http://127.0.0.1:5000`.
4. Development admin: `admin@aura.local` / `ChangeMe123!` (local demo only; change before public hosting).
5. Register a customer account, add a product to the bag, checkout with Cash on Delivery, then sign into admin and update the order status.

## Mobile demonstration
- For a same-Wi-Fi demonstration, find the laptop's local IPv4 address (`ipconfig`) and open `http://LAPTOP-IP:5000` on the phone while both devices share Wi-Fi and the firewall allows Python. This is a local demo, not HTTPS.
- For a shareable internet link, deploy the Flask app to a Python web host and enable persistent storage for SQLite. A static hosting upload will not run this backend app.
- PWA/Android installation packaging is not included in this Flask MVP; a live HTTPS host and separate PWA/Android packaging step are needed for installable delivery.

## Honest demo limitations
- Checkout is Cash on Delivery simulation only; no real payment is collected.
- No courier integration, SMS/email notifications, or actual shipment tracking is connected.
- Product imagery is sample remote imagery; use licensed/owned images for a public release.
- Verify the app on the submission laptop before presenting. This bundle has Python syntax validation, but the authoring environment did not have Flask installed for a full runtime test.
