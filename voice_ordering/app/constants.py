"""Shared vocabulary: enums, unit normalisation tables and workflow rules.

Everything the AI output is validated against lives here so the Gemini prompt
and the server-side validation can never drift apart silently.
"""

# --- Requesters ---------------------------------------------------------------
USER_TYPES = ("farmer", "customer")
USER_TYPE_LABELS = {
    "farmer": {"ne": "किसान", "en": "Farmer"},
    "customer": {"ne": "ग्राहक", "en": "Customer"},
}

# --- Request type -------------------------------------------------------------
REQUEST_TYPES = ("selling", "buying")
REQUEST_TYPE_LABELS = {
    "selling": {"ne": "बेच्ने", "en": "Selling (produce offer)"},
    "buying": {"ne": "किन्ने", "en": "Buying (order)"},
}

# --- Status -------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_CLARIFICATION = "clarification_required"

STATUSES = (STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_CLARIFICATION)
STATUS_LABELS = {
    STATUS_PENDING: {"ne": "प्रतीक्षामा", "en": "Pending", "tone": "warn"},
    STATUS_APPROVED: {"ne": "स्वीकृत", "en": "Approved", "tone": "ok"},
    STATUS_REJECTED: {"ne": "अस्वीकृत", "en": "Rejected", "tone": "bad"},
    STATUS_CLARIFICATION: {
        "ne": "स्पष्टीकरण चाहिन्छ",
        "en": "Clarification required",
        "tone": "info",
    },
}

# Allowed status transitions. Approved / rejected are terminal so the audit
# trail stays trustworthy; an admin must submit a new request instead.
ALLOWED_TRANSITIONS = {
    STATUS_PENDING: (STATUS_APPROVED, STATUS_REJECTED, STATUS_CLARIFICATION),
    STATUS_CLARIFICATION: (STATUS_APPROVED, STATUS_REJECTED, STATUS_CLARIFICATION),
    STATUS_APPROVED: (),
    STATUS_REJECTED: (),
}

# Statuses in which request details may still be corrected by an administrator.
EDITABLE_STATUSES = (STATUS_PENDING, STATUS_CLARIFICATION)

# --- Actions recorded in the audit / history trail ---------------------------
ACTION_CREATED = "created"
ACTION_APPROVED = "approved"
ACTION_REJECTED = "rejected"
ACTION_CLARIFICATION = "clarification_requested"
ACTION_EDITED = "details_edited"
ACTION_SUBMITTED_AGAIN = "resubmitted"

# --- Units --------------------------------------------------------------------
SUPPORTED_UNITS = (
    "kg",
    "gram",
    "tonne",
    "piece",
    "crate",
    "dozen",
    "bunch",
    "sack",
    "litre",
)

UNIT_LABELS = {
    "kg": {"ne": "के.जी.", "en": "kg"},
    "gram": {"ne": "ग्राम", "en": "gram"},
    "tonne": {"ne": "टन", "en": "tonne"},
    "piece": {"ne": "गोटा", "en": "piece"},
    "crate": {"ne": "क्रेट", "en": "crate"},
    "dozen": {"ne": "दर्जन", "en": "dozen"},
    "bunch": {"ne": "मुठा", "en": "bunch"},
    "sack": {"ne": "बोरा", "en": "sack"},
    "litre": {"ne": "लिटर", "en": "litre"},
}

# Accepted spellings / transliterations -> canonical unit.
UNIT_ALIASES = {
    # kilograms
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg",
    "kilograms": "kg", "केजी": "kg", "के.जी.": "kg", "के.जी": "kg",
    "किलो": "kg", "किलोग्राम": "kg",
    # grams
    "g": "gram", "gm": "gram", "gms": "gram", "gram": "gram", "grams": "gram",
    "gramme": "gram", "ग्राम": "gram",
    # tonnes
    "ton": "tonne", "tons": "tonne", "tonne": "tonne", "tonnes": "tonne",
    "mt": "tonne", "टन": "tonne",
    # pieces
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece",
    "nos": "piece", "no": "piece", "गोटा": "piece", "गोट": "piece",
    "दाना": "piece", "थान": "piece", "एक": "piece",
    # crates
    "crate": "crate", "crates": "crate", "box": "crate", "boxes": "crate",
    "peti": "crate", "पेटी": "crate", "क्रेट": "crate",
    # dozens
    "dozen": "dozen", "dozens": "dozen", "dajan": "dozen", "दर्जन": "dozen",
    # bunches
    "bunch": "bunch", "bunches": "bunch", "mutha": "bunch", "mutho": "bunch",
    "मुठा": "bunch", "गड्डी": "bunch",
    # sacks
    "sack": "sack", "sacks": "sack", "bag": "sack", "bags": "sack",
    "bora": "sack", "बोरा": "sack", "बोर": "sack",
    # litres
    "l": "litre", "lt": "litre", "ltr": "litre", "litre": "litre",
    "liter": "litre", "litres": "litre", "liters": "litre", "लिटर": "litre",
}

# (inclusive) plausible quantity ranges per unit, used to catch hallucinated
# or mis-heard quantities before they reach the database.
UNIT_QUANTITY_RANGE = {
    "kg": (0.1, 50_000.0),
    "gram": (1.0, 500_000.0),
    "tonne": (0.01, 500.0),
    "piece": (1.0, 100_000.0),
    "crate": (1.0, 5_000.0),
    "dozen": (1.0, 10_000.0),
    "bunch": (1.0, 20_000.0),
    "sack": (1.0, 5_000.0),
    "litre": (0.1, 10_000.0),
}

MIN_PRICE_PER_UNIT = 0.01
MAX_PRICE_PER_UNIT = 1_000_000.0
MAX_EXPECTED_TOTAL = 100_000_000.0

# --- Fulfilment ---------------------------------------------------------------
FULFILLMENT_TYPES = ("delivery", "pickup")
FULFILLMENT_LABELS = {
    "delivery": {"ne": "घरमै डेलिभरी", "en": "Delivery"},
    "pickup": {"ne": "आफैं लिन", "en": "Pickup"},
}

# Fields a request must carry before it may be submitted for review.
REQUIRED_FIELDS = (
    "requester_name",
    "user_type",
    "request_type",
    "product_name",
    "quantity",
    "unit",
    "location",
)

# Optional fields that make an ambiguous request suspicious when guessed by the AI.
SENSITIVE_FIELDS = ("phone", "price_per_unit", "expected_total", "requested_date")

FIELD_LABELS = {
    "requester_name": {"ne": "नाम", "en": "Name"},
    "phone": {"ne": "फोन", "en": "Phone"},
    "user_type": {"ne": "तपाईं को हुनुहुन्छ", "en": "You are a"},
    "request_type": {"ne": "किन्ने/बेच्ने", "en": "Buying or selling"},
    "product_name": {"ne": "उत्पादन", "en": "Product"},
    "quantity": {"ne": "परिमाण", "en": "Quantity"},
    "unit": {"ne": "एकाइ", "en": "Unit"},
    "price_per_unit": {"ne": "प्रति एकाइ मूल्य", "en": "Price per unit"},
    "expected_total": {"ne": "अनुमानित जम्मा", "en": "Expected total"},
    "location": {"ne": "स्थान", "en": "Location"},
    "fulfillment_type": {"ne": "डेलिभरी/पिकअप", "en": "Delivery or pickup"},
    "requested_date": {"ne": "मिति", "en": "Requested date"},
}

# --- Enum aliases -------------------------------------------------------------
# Accepted spellings for the closed enums, so a mixed Nepali/romanised sentence
# still lands on a canonical value. Anything not listed here is rejected and
# becomes a clarification question, never a guess.
USER_TYPE_ALIASES = {
    "farmer": "farmer", "farmers": "farmer", "kisan": "farmer", "kishan": "farmer",
    "producer": "farmer", "किसान": "farmer", "कृषक": "farmer",
    "customer": "customer", "customers": "customer", "grahak": "customer",
    "buyer": "customer", "consumer": "customer", "ग्राहक": "customer", "उपभोक्ता": "customer",
}

REQUEST_TYPE_ALIASES = {
    "buying": "buying", "buy": "buying", "purchase": "buying", "order": "buying",
    "kinne": "buying", "kinnu": "buying", "kharid": "buying", "kharidne": "buying",
    "chahiyo": "buying", "chahincha": "buying", "किन्ने": "buying", "किन्छु": "buying",
    "selling": "selling", "sell": "selling", "supply": "selling", "offer": "selling",
    "bechne": "selling", "bechnu": "selling", "bikri": "selling", "bechna": "selling",
    "cha": "selling", "chha": "selling", "बेच्ने": "selling", "बिक्री": "selling",
}

FULFILLMENT_ALIASES = {
    "delivery": "delivery", "deliver": "delivery", "doorstep": "delivery",
    "ghar": "delivery", "gharma": "delivery", "pathaune": "delivery",
    "डेलिभरी": "delivery", "घरमा": "delivery",
    "pickup": "pickup", "pick_up": "pickup", "pick up": "pickup", "collect": "pickup",
    "aafai": "pickup", "afai": "pickup", "lina": "pickup", "linu": "pickup",
    "पिकअप": "pickup", "आफैं": "pickup", "लिन": "pickup",
}

# --- Produce vocabulary -------------------------------------------------------
# Common Nepali / Romanized Nepali produce names -> canonical bilingual name.
# Used to normalise AI output and to give the model a reference list. Unknown
# products are kept exactly as spoken (never replaced with a guess).
PRODUCT_ALIASES = {
    "alu": {"ne": "आलु", "en": "Potato"},
    "aalu": {"ne": "आलु", "en": "Potato"},
    "आलु": {"ne": "आलु", "en": "Potato"},
    "potato": {"ne": "आलु", "en": "Potato"},
    "potatoes": {"ne": "आलु", "en": "Potato"},
    "pyaj": {"ne": "प्याज", "en": "Onion"},
    "piyaj": {"ne": "प्याज", "en": "Onion"},
    "प्याज": {"ne": "प्याज", "en": "Onion"},
    "onion": {"ne": "प्याज", "en": "Onion"},
    "onions": {"ne": "प्याज", "en": "Onion"},
    "golbheda": {"ne": "गोलभेंडा", "en": "Tomato"},
    "golbhenda": {"ne": "गोलभेंडा", "en": "Tomato"},
    "गोलभेंडा": {"ne": "गोलभेंडा", "en": "Tomato"},
    "tomato": {"ne": "गोलभेंडा", "en": "Tomato"},
    "tomatoes": {"ne": "गोलभेंडा", "en": "Tomato"},
    "kauli": {"ne": "काउली", "en": "Cauliflower"},
    "काउली": {"ne": "काउली", "en": "Cauliflower"},
    "cauliflower": {"ne": "काउली", "en": "Cauliflower"},
    "banda": {"ne": "बन्दा", "en": "Cabbage"},
    "बन्दा": {"ne": "बन्दा", "en": "Cabbage"},
    "cabbage": {"ne": "बन्दा", "en": "Cabbage"},
    "saag": {"ne": "साग", "en": "Leafy greens"},
    "sag": {"ne": "साग", "en": "Leafy greens"},
    "rayo": {"ne": "रायोको साग", "en": "Mustard greens"},
    "साग": {"ne": "साग", "en": "Leafy greens"},
    "spinach": {"ne": "पालुङ्गो", "en": "Spinach"},
    "palungo": {"ne": "पालुङ्गो", "en": "Spinach"},
    "simi": {"ne": "सिमि", "en": "Green beans"},
    "semi": {"ne": "सिमि", "en": "Green beans"},
    "सिमि": {"ne": "सिमि", "en": "Green beans"},
    "beans": {"ne": "सिमि", "en": "Green beans"},
    "suntala": {"ne": "सुन्तला", "en": "Mandarin orange"},
    "sunthala": {"ne": "सुन्तला", "en": "Mandarin orange"},
    "सुन्तला": {"ne": "सुन्तला", "en": "Mandarin orange"},
    "mandarin": {"ne": "सुन्तला", "en": "Mandarin orange"},
    "orange": {"ne": "सुन्तला", "en": "Mandarin orange"},
    "kera": {"ne": "केरा", "en": "Banana"},
    "केरा": {"ne": "केरा", "en": "Banana"},
    "banana": {"ne": "केरा", "en": "Banana"},
    "gahu": {"ne": "गहुँ", "en": "Wheat"},
    "गहुँ": {"ne": "गहुँ", "en": "Wheat"},
    "wheat": {"ne": "गहुँ", "en": "Wheat"},
    "dhan": {"ne": "धान", "en": "Paddy rice"},
    "चामल": {"ne": "चामल", "en": "Rice"},
    "rice": {"ne": "चामल", "en": "Rice"},
    "makai": {"ne": "मकै", "en": "Maize"},
    "मकै": {"ne": "मकै", "en": "Maize"},
    "maize": {"ne": "मकै", "en": "Maize"},
    "corn": {"ne": "मकै", "en": "Maize"},
    "khursani": {"ne": "खुर्सानी", "en": "Chilli"},
    "खुर्सानी": {"ne": "खुर्सानी", "en": "Chilli"},
    "chilli": {"ne": "खुर्सानी", "en": "Chilli"},
    "lasun": {"ne": "लसुन", "en": "Garlic"},
    "लसुन": {"ne": "लसुन", "en": "Garlic"},
    "garlic": {"ne": "लसुन", "en": "Garlic"},
    "gajar": {"ne": "गाजर", "en": "Carrot"},
    "गाजर": {"ne": "गाजर", "en": "Carrot"},
    "carrot": {"ne": "गाजर", "en": "Carrot"},
    "khira": {"ne": "खीरा", "en": "Cucumber"},
    "खीरा": {"ne": "खीरा", "en": "Cucumber"},
    "cucumber": {"ne": "खीरा", "en": "Cucumber"},
    "dudh": {"ne": "दूध", "en": "Milk"},
    "दूध": {"ne": "दूध", "en": "Milk"},
    "milk": {"ne": "दूध", "en": "Milk"},
    "ghee": {"ne": "घ्यू", "en": "Ghee"},
    "घ्यू": {"ne": "घ्यू", "en": "Ghee"},
    "mah": {"ne": "मह", "en": "Honey"},
    "मह": {"ne": "मह", "en": "Honey"},
    "honey": {"ne": "मह", "en": "Honey"},
}

# --- Languages ----------------------------------------------------------------
SUPPORTED_LANGUAGES = ("ne", "en", "ne-roman", "mixed", "unknown")
LANGUAGE_LABELS = {
    "ne": "नेपाली",
    "en": "English",
    "ne-roman": "Romanized Nepali",
    "mixed": "Mixed",
    "unknown": "Auto detect",
}

# --- Notifications ------------------------------------------------------------
AUDIENCE_ADMIN = "admin"
AUDIENCE_REQUESTER = "requester"
NOTIFICATION_CHANNEL_IN_APP = "in_app"

EVENT_NEW_REQUEST = "new_request"
EVENT_APPROVED = "request_approved"
EVENT_REJECTED = "request_rejected"
EVENT_CLARIFICATION = "clarification_requested"
EVENT_UPDATED = "request_updated"
