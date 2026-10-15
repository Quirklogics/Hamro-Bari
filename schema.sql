-- ==============================================================================
-- HAMRO BAARI (हाम्रो बारी) - SUPABASE POSTGRESQL SCHEMA & INITIAL DATA
-- Copy and run this script in your Supabase SQL Editor
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PRODUCE INVENTORY TABLE (ताजा तरकारी तथा फलफूल)
CREATE TABLE IF NOT EXISTS public.produce (
    id SERIAL PRIMARY KEY,
    name_ne VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    category VARCHAR(50) NOT NULL DEFAULT 'veggies', -- 'greens', 'veggies', 'roots', 'fruits'
    district VARCHAR(100) NOT NULL, -- 'kavre', 'dhading', 'sindhupalchok', 'bhaktapur', 'syangja', 'kathmandu'
    district_ne VARCHAR(255) NOT NULL,
    district_label VARCHAR(255) NOT NULL,
    farmer_ne VARCHAR(255) NOT NULL,
    farmer_en VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT true,
    price NUMERIC(10, 2) NOT NULL,
    unit_ne VARCHAR(100) DEFAULT 'प्रति १ के.जी.',
    unit_en VARCHAR(100) DEFAULT 'per 1 kg',
    freshness_ne VARCHAR(255) DEFAULT 'टिपेको १८ घण्टा',
    freshness_en VARCHAR(255) DEFAULT '18 hrs since harvest',
    is_organic BOOLEAN DEFAULT true,
    tag_ne VARCHAR(255) DEFAULT 'बारीबाट Direct',
    tag_en VARCHAR(255) DEFAULT 'Direct from farm',
    description_ne TEXT,
    description_en TEXT,
    image_url TEXT NOT NULL,
    stock_kg NUMERIC(10, 2) DEFAULT 100.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CUSTOMER ORDERS TABLE (अग्रिम अर्डरहरू)
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_no VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255) DEFAULT 'Residential Customer',
    customer_phone VARCHAR(50),
    society_cluster VARCHAR(255) NOT NULL, -- 'Hattiban Heights & Residency (Lalitpur-28)', etc.
    delivery_type VARCHAR(50) NOT NULL DEFAULT 'hub', -- 'hub' or 'doorstep'
    delivery_day VARCHAR(50) DEFAULT 'wednesday',
    payment_method VARCHAR(50) NOT NULL DEFAULT 'esewa', -- 'esewa', 'khalti', 'cod'
    payment_status VARCHAR(50) DEFAULT 'pending',
    subtotal_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    delivery_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    jute_deposit NUMERIC(10, 2) NOT NULL DEFAULT 30.0,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    order_status VARCHAR(50) DEFAULT 'confirmed', -- 'confirmed', 'harvesting', 'hub_grading', 'dispatched', 'delivered'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ORDER ITEMS TABLE (अर्डरका सामग्रीहरू)
CREATE TABLE IF NOT EXISTS public.order_items (
    id SERIAL PRIMARY KEY,
    order_id UUID REFERENCES public.orders(id) ON DELETE CASCADE,
    produce_id INT REFERENCES public.produce(id) ON DELETE SET NULL,
    item_name_ne VARCHAR(255) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL
);

-- 4. FARMER VOICE HARVEST BATCHES (किसान आवाज दर्ता बाली)
CREATE TABLE IF NOT EXISTS public.farmer_batches (
    id SERIAL PRIMARY KEY,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    farmer_name VARCHAR(255) NOT NULL,
    district VARCHAR(255) NOT NULL,
    crop_name VARCHAR(255) NOT NULL,
    weight_kg NUMERIC(10, 2) NOT NULL,
    grade VARCHAR(50) DEFAULT 'Grade A (उत्कृष्ट)',
    ready_time VARCHAR(255),
    est_payout NUMERIC(10, 2) NOT NULL,
    status VARCHAR(100) DEFAULT 'संकलन केन्द्र पुग्यो',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. LOGISTICS DISPATCH FLEET (संकलन भ्यान तथा सवारी परिचालन)
CREATE TABLE IF NOT EXISTS public.dispatch_trucks (
    id SERIAL PRIMARY KEY,
    truck_code VARCHAR(50) UNIQUE NOT NULL,
    route_name VARCHAR(255) NOT NULL,
    driver_name VARCHAR(255) NOT NULL,
    vehicle_no VARCHAR(100) NOT NULL,
    capacity_kg NUMERIC(10, 2) NOT NULL,
    loaded_kg NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    departure_time VARCHAR(100) NOT NULL,
    status VARCHAR(100) NOT NULL DEFAULT 'लोडिङ हुँदैछ'
);

-- 6. REAL-TIME SMS BROADCAST LOGS
CREATE TABLE IF NOT EXISTS public.sms_logs (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    recipients_count INT DEFAULT 1,
    category VARCHAR(50) DEFAULT 'farmer_alert',
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES FOR SUPABASE
-- ==============================================================================
ALTER TABLE public.produce ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farmer_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dispatch_trucks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sms_logs ENABLE ROW LEVEL SECURITY;

-- Allow public read access to active produce
CREATE POLICY "Allow public read produce" ON public.produce FOR SELECT USING (is_active = true);

-- Allow public order submission
CREATE POLICY "Allow public insert orders" ON public.orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public read orders" ON public.orders FOR SELECT USING (true);
CREATE POLICY "Allow public insert order_items" ON public.order_items FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public read order_items" ON public.order_items FOR SELECT USING (true);

-- Allow public farmer batch creation and viewing
CREATE POLICY "Allow public farmer_batches" ON public.farmer_batches FOR ALL USING (true) WITH CHECK (true);

-- Allow public dispatch trucks viewing
CREATE POLICY "Allow public dispatch_trucks" ON public.dispatch_trucks FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public sms_logs" ON public.sms_logs FOR ALL USING (true) WITH CHECK (true);

-- ==============================================================================
-- INITIAL SEED DATA (12 AUTHENTIC NEPALI PRODUCE ITEMS & DEMO LOGISTICS)
-- ==============================================================================

INSERT INTO public.produce 
(id, name_ne, name_en, scientific_name, category, district, district_ne, district_label, farmer_ne, farmer_en, verified, price, unit_ne, unit_en, freshness_ne, freshness_en, is_organic, tag_ne, tag_en, description_ne, description_en, image_url)
VALUES
(1, 'गोलभेंडा', 'Local Hybrid Tomato', 'Vine Ripe Organic Tomato', 'veggies', 'kavre', 'काभ्रे बनेपा', 'पाँचखाल, काभ्रे', 'राम बहादुर श्रेष्ठ', 'Ram Bahadur Shrestha', true, 65, 'प्रति १ के.जी.', 'per 1 kg', 'टिपेको १८ घण्टा', '18 hrs since harvest', true, 'काभ्रे बनेपा Direct', 'Kavre Direct', 'पाँचखाल उपत्यकामा प्राङ्गारिक कम्पोस्टबाट उमारिएको ताजा, रसदार र गुलियो गोलभेंडा।', 'Juicy, vine-ripened organic tomatoes grown with natural compost in Panchkhal valley.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCSeJD88_SQV9DL448dL8kh7H1Z468OK6Ns9-dgSuKk6ytg4i3HFd33QtjyFum8g9rIzAps5g1gLJHSOm7v1L6N7SV_vcKTus12H-bVs3aMhvF4Phj1O0nJfHOf4j1UKviF_Qpd1gt1Rglj12A7O2n0OqcE_VCEQxBjp9GLPw6nJ5yM45EwhVSV-M5_RkAfW_cWrQ4lgkx78PutEtCm2SnzcBJ5LmR43TK0Glxni_kOS3vdR5InKSeX4w'),
(2, 'रायोको साग', 'Mustard Greens (Rayo ko Saag)', 'Broadleaf Mustard Greens', 'greens', 'dhading', 'धादिङ बैंसी', 'बेनीघाट रोराङ, धादिङ', 'शान्ती प्रजापति', 'Shanti Prajapati', true, 50, 'प्रति ५०० ग्राम मुठा', 'per 500g bunch', 'बिहानको ताजा टिपाइ', 'Harvested this morning', true, 'धादिङ बैंसी Direct', 'Dhading Direct', 'पहाडी चिसो पानीले सिंचित, कुनै पनि रासायनिक विषादी प्रयोग नगरिएको स्वादिलो रायोको साग।', 'Crisp broadleaf mustard greens naturally irrigated with mountain spring water.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuBC7WQwSMfQBH6OYFo5mUwKwZ4Ic8J9JTUQ1iosOz58ZaBqP59mkmDW6Wp7koEtvjR_icbT25LeUjXX-9civ2OILgEowniNqk8tyab02wwj6GWQMGP78Kq8QkCuvamulfI8FOO3CcnqTyRrpE0Ej07REmOd8OfD8FU52TXNiwaTzBSqNC-KKRMdIpo10ZpvMx0mVcvVupJ0uXwPrjrSAFVK2khF7XS-Hb-f3_vI-8tPeDQRVqw5eRYbrw'),
(3, 'मुडेको रातो आलु', 'High Altitude Red Potato', 'Solanum tuberosum (Mude)', 'roots', 'sindhupalchok', 'मुडे सिन्धुपाल्चोक', 'मुडे बजार, सिन्धुपाल्चोक', 'दावा शेर्पा', 'Dawa Sherpa', true, 110, 'प्रति १ के.जी.', 'per 1 kg', 'रैथाने बीउ', 'Indigenous seed heirloom', true, 'मुडे उच्च पहाड', 'Mude Highland', '२,४०० मिटरको चिसो हावापानीमा फलेको प्रसिद्ध मुडेको रातो आलु। तरकारी र उसिनेर खान उत्कृष्ट।', 'Famous red skin highland potatoes grown at 2,400m altitude in cool Himalayan soil.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDOPc9sZW79K5DlagHsLVoxG_3RoXVtALhI4leZFORrwVMuzs7YYCsnqfXbHX_dQihYNxLbQpIo7HG6lCJg3QcNQMlNjKzTs1M8WYPphn4k57XGT9-J9K2zxJVV3ZR9dUDZydehn6-6ArQBuipnRaa5oXzWb8NouP4KSM3RD8lGhGm0lAG6oVcs3syamBy7pbZAUhTAa-u-0ZRl4IPWQERVwOtHp6VCzgGMfOPzRiMBz6WA6r9UPbYU6A'),
(4, 'धादिङे हरियो सिमि', 'Tender French Green Beans', 'Phaseolus vulgaris', 'veggies', 'dhading', 'धादिङ त्रिशुली', 'गजुरी, धादिङ', 'हरि बहादुर थापा', 'Hari Bahadur Thapa', true, 95, 'प्रति १ के.जी.', 'per 1 kg', 'आजै टिपिएको', 'Picked today', true, 'धादिङ त्रिशुली किनार', 'Dhading Riverbank', 'त्रिशुली नदी किनारको मलिलो पाखामा उमारिएको कोमल र बिना रेसाको हरियो सिमि।', 'Tender stringless french beans grown along the Trishuli river valley.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDKz42oFFq_aCm58kApRTyRduCH8ACH5mEpogXrwUtO-djGAgF0hcQ8_yunBNlAYSv1Er9I3jF3yy0Et9nZzEUxyEQW-ZQ3MdwI25CXYK0eYKdAckLDp__Ylr2AbEhdpkZtmGGfI_leU7_m904sI6VBz9Ru7HcmWIYCtrVMLv6ywLw0NQwaLMKd4nglGJ03NM3XV2TST3DoROZ1Y59qwqcONIebI8BOf0nigVOQSK368ny1E_2bptNW4w'),
(5, 'चाँगुनारायणको काउली', 'Local Organic Cauliflower', 'Brassica oleracea botrytis', 'veggies', 'bhaktapur', 'भक्तपुर चाँगु', 'चाँगुनारायण-४, भक्तपुर', 'कमला प्रजापति', 'Kamala Prajapati', true, 75, 'प्रति १ गोटा (१ केजी औसत)', 'per 1 piece (~1kg)', 'टिपेको २४ घण्टा', '24 hrs freshness', true, 'भक्तपुर प्राङ्गारिक', 'Bhaktapur Organic', 'प्राकृतिक कम्पोस्ट मलबाट उमारिएको बाक्लो र कसिलो सेतो काउली।', 'Crisp, dense, nutrient-dense organic cauliflower from the hills of Bhaktapur.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuC2K7h1lQ9-Bv4D957k967t_ZlS9uP1g_t943M66hYy1W_pZ1Q280QpA-P7X648d8eYvE124567890abcdef1234567890abcdef'),
(6, 'स्याङ्जाली सुन्तला', 'Syangja Sweet Citrus Mandarin', 'Citrus reticulata', 'fruits', 'syangja', 'स्याङ्जा वालिङ', 'वालिङ, स्याङ्जा', 'टेक प्रसाद पौडेल', 'Tek Prasad Poudel', true, 140, 'प्रति १ के.जी.', 'per 1 kg', 'रुखमै पाकेको', 'Tree ripened', true, 'स्याङ्जा सुन्तला पकेट', 'Syangja Mandarin Belt', 'स्याङ्जाका घमाइला पाखाहरूमा प्राकृतिक रुपमा पाकेको गुलियो, रसिलो र पातलो बोक्रा भएको सुन्तला।', 'Tree-ripened, naturally sweet mountain mandarin oranges packed with Vitamin C.', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDYQ12345678901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
ON CONFLICT (id) DO UPDATE SET 
    price = EXCLUDED.price,
    name_ne = EXCLUDED.name_ne,
    image_url = EXCLUDED.image_url;

-- Reset sequence to avoid id collision on future inserts
SELECT setval('public.produce_id_seq', (SELECT MAX(id) FROM public.produce));

-- Seed Demo Trucks
INSERT INTO public.dispatch_trucks (id, truck_code, route_name, driver_name, vehicle_no, capacity_kg, loaded_kg, departure_time, status)
VALUES
(1, 'TRUCK-01', 'काभ्रे - हब - ललितपुर क्लस्टर', 'विक्रम तामाङ', 'बा २ ख ४५८९', 1000, 850, 'बुधबार बिहान ५:३०', 'लोडिङ हुँदैछ'),
(2, 'TRUCK-02', 'धादिङ - मुडे - काठमाडौँ क्लस्टर', 'सुरेश श्रेष्ठ', 'बा ३ ख ७८२१', 1200, 1120, 'बुधबार बिहान ४:४५', 'तयार')
ON CONFLICT (truck_code) DO NOTHING;

-- Seed Demo Farmer Batches
INSERT INTO public.farmer_batches (id, batch_no, farmer_name, district, crop_name, weight_kg, grade, ready_time, est_payout, status)
VALUES
(1, 'BATCH-402', 'राम बहादुर श्रेष्ठ', 'पाँचखाल, काभ्रे', 'गोलभेंडा', 50, 'Grade A (उत्कृष्ट)', 'बिहीबार बिहान ७:०० बजे', 3250, 'संकलन केन्द्र पुग्यो'),
(2, 'BATCH-398', 'शान्ती प्रजापति', 'बेनीघाट, धादिङ', 'रायोको साग', 40, 'Grade A (उत्कृष्ट)', 'हिजो साँझ ५:००', 1600, 'जाँच सम्पन्न'),
(3, 'BATCH-385', 'दावा शेर्पा', 'मुडे, सिन्धुपाल्चोक', 'काउली', 35, 'Grade B', 'मंगलबार', 2450, 'भुक्तानी सम्पन्न')
ON CONFLICT (batch_no) DO NOTHING;
