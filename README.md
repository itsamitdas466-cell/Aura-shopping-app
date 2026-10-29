

## Latest UI improvements
- Persistent light/dark theme toggle (browser preference)
- Mobile side navigation drawer
- Order success celebration screen
- Demo coupon codes: `AURA10` (10% off) and `STYLE15` (15% off), minimum ₹999 subtotal
- PWA manifest, icon, and service worker shell cache for HTTPS hosting

## Honest limitations
This is a college/demo MVP. COD orders are stored locally in SQLite. There is no live payment gateway, courier/shipping integration, SMS/email notification service, or production monitoring. External product images/fonts require internet. Installable PWA support requires deployment over HTTPS (or localhost). Change default admin credentials and set a stable `SECRET_KEY` before any public deployment. Test all workflows before demonstrating.
