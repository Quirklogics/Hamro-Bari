# हाम्रो बारी (Hamro Baari) - Farm to Community Produce Web Platform

A web application built from the **Hamro Baari Organic Earth** design system and UI resources located in `C:\Users\LENOVO\Downloads\stitch_nepal_farm_to_community_produce_app`.

---

## 🌟 Overview & Key Modules

This frontend connects smallholder farmers in Nepal (Kavre, Dhading, Mude, Bhaktapur, Syangja) with residential apartment communities across Kathmandu & Lalitpur. It unites all 5 core UI workflows into an interactive single-page application:

1. **🏡 Customer Storefront (`home`)**:
   - Hero banner with weekly cycle announcement (हप्ता #४२ अर्डर खुला छ).
   - Real-time countdown timer to the Sunday 8:00 PM pre-order cutoff.
   - Community residential society selector (Hattiban, Sanepa, Jhamsikhel, Baluwatar, Mandikhatar).
   - 4-column community impact statistics (450+ families, 28 farmers, 0% waste, Rs. 3.4L+ payouts).
   - Featured seasonal produce picks with +/- stepper controls.
   - Farm-to-Community 4-step dispatch visualization.

2. **🥬 Browse Produce Catalog (`browse`)**:
   - 2-Column responsive catalog layout.
   - Sourcing district filters (काभ्रेपलाञ्चोक, धादिङ, सिन्धुपाल्चोक, भक्तपुर, स्याङ्जा, काठमाडौँ).
   - Category navigation (सबै, हरियो सागपात, ताजा तरकारी, जरा र आलु, फलफूल).
   - Real-time price slider and search bar with voice recognition simulation.
   - Freshness & organic badges ("टिपेको १८ घण्टा", "जैविक प्रमाणित", "रैथाने बीउ").

3. **🛒 Cart & Pre-Order Checkout (`cart`)**:
   - Dynamic quantity adjustments with weight-based calculation in Nepalese Rupees (`रु. / NPR`).
   - Free Community Society Hub pickup vs. Doorstep flat delivery (+रु. ५०).
   - Zero-waste refundable jute bag deposit tracking (रु. ३०).
   - Coupon code system (e.g. `HAMROEARTH` for 10% discount).
   - Payment method selector: **eSewa**, **Khalti**, **Cash on Delivery**.
   - Confetti celebration animation and 4-step status order tracker modal on booking.

4. **👨‍🌾 Farmer Voice Portal & Harvest Management (`farmer`)**:
   - Specially designed for rural farmers with large high-contrast tactile buttons and speech synthesis.
   - Nepali voice assistant:
     - **१. तयार (Idle)**: Giant 124px pulsating green microphone button with ripple rings.
     - **२. सुन्दैछ (Listening)**: Live HTML5 canvas animated audio waveform.
     - **३. नतिजा (Parsed Card)**: Parsed crop batch (e.g., "गोलभेंडा ५० केजी") with estimated payout calculation.
     - **४. नयाँ मागहरू (Hub Demands)**: Live demand board from Kathmandu and Lalitpur communities.
   - Web Audio synthesizer & Web Speech API speech synthesis ("नमस्ते राम बहादुर ज्यू!").
   - Registered batch history ledger and 1-tap coordinator phone call button.

5. **🚚 Logistics & Admin Dispatch Console (`admin`)**:
   - Active supply cycle alert (हप्ता #४२ कात्तिक चक्र).
   - 92% collection progress indicator.
   - Executive KPIs: Total orders (284), Total weight (1,420 kg), Active farmers (19), Societies (10).
   - Real-time truck dispatch loading progress (TRUCK-01 & TRUCK-02).
   - Bulk SMS broadcast simulation to all farmers and drivers with delivery log.
   - Printable delivery manifest (`window.print()`).

---

## 🎨 Design System & Aesthetics (Organic Earth)

- **Colors**:
  - Primary: Deep Emerald Forest (`#00652c`, `#15803d`)
  - Secondary: Sunlit Amber (`#904d00`, `#fe932c`)
  - Tertiary: Terracotta Soil (`#9a3500`, `#c34500`)
  - Surfaces: Cream & Slate-tinted layers (`#f9f9ff`, `#f0f3ff`, `#ffffff`)
- **Typography**: Google Fonts **Noto Sans** (Devanagari conjunct support) and **Inter** (labels & metrics).
- **Icons**: Material Symbols Outlined.
- **Audio Feedback**: Web Audio API soft harmonic chimes and Web Speech synthesizer.
- **Device Frame Preview**: Toggle between full **Desktop View** and **Mobile Phone Frame Simulator** (complete with top notch, speaker island, and mobile chassis).

---

## 🚀 How to Run

Because this application uses standard HTML5, Vanilla CSS, and modern modular JavaScript without requiring a heavy Node runtime:

1. **Directly in Browser**:
   - Double click [index.html](file:///c:/Users/LENOVO/Downloads/Deliver/index.html) to open in Chrome, Edge, Firefox, or Safari.
2. **Via Local Static Server** (optional):
   ```powershell
   # If you have Python:
   python -m http.server 8000
   # Then open: http://localhost:8000
   ```

---

## 📁 Project Structure

```
Deliver/
├── index.html              # Main application shell with all 5 view modules
├── styles.css              # Design tokens, mobile frame chassis, and animations
├── app.js                  # Reactive state, cart logic, audio chime, and voice engine
├── DESIGN.md               # Original design tokens and guidelines from stitch resource
├── README.md               # Documentation & user manual
└── reference_screens/      # Screenshots of the original 10 UI designs for reference
    ├── hamro_baari_customer_home_desktop.png
    ├── hamro_baari_browse_produce_desktop.png
    ├── hamro_baari_cart_pre_order_desktop.png
    ├── hamro_baari_farmer_portal_desktop.png
    ├── hamro_baari_farmer_voice_portal.png
    ├── hamro_baari_admin_dashboard_desktop.png
    └── ...
```
