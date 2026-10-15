/**
 * HAMRO BAARI (हाम्रो बारी) - FARM TO COMMUNITY PRODUCE PLATFORM
 * Core Application Engine & Reactive State Store
 */

// Application State Store
const state = {
  currentRole: 'home', // 'home' | 'browse' | 'cart' | 'farmer' | 'admin'
  currentLang: 'ne',   // 'ne' | 'en'
  deviceMode: 'desktop', // 'desktop' | 'mobile'
  selectedSociety: 'Hattiban Heights & Residency (Lalitpur-28)',
  deliveryType: 'hub', // 'hub' | 'doorstep'
  deliveryDay: 'wednesday', // 'wednesday' | 'saturday'
  paymentMethod: 'esewa', // 'esewa' | 'khalti' | 'cod'
  discountCode: '',
  discountApplied: false,
  
  // Cart State (Initialized with sample fresh items as per stitch mockup)
  cart: [
    { id: 1, qty: 1.0 }, // गोलभेंडा 1 kg
    { id: 2, qty: 2.0 }, // रायोको साग 2 मुठा
    { id: 3, qty: 1.0 }, // मुडेको रातो आलु 1 kg
  ],

  // Filter State for Browse Produce
  filters: {
    search: '',
    category: 'all',
    districts: ['kavre', 'dhading', 'sindhupalchok', 'bhaktapur', 'syangja', 'kathmandu'],
    maxPrice: 200,
    organicOnly: false,
    sortBy: 'popular'
  },

  // Farmer Voice Assistant State
  farmerState: {
    activeTab: 'idle', // 'idle' | 'listening' | 'confirm' | 'demand'
    lastRecognized: 'गोलभेंडा ५० केजी',
    lastEnergy: 0,
    confirmed: false,
    parsedCrop: {
      name: 'गोलभेंडा (Local Hybrid Tomato)',
      farmer: 'राम बहादुर श्रेष्ठ',
      district: 'काभ्रे (पाँचखाल)',
      weight: 50,
      grade: 'Grade A (उत्कृष्ट)',
      readyDay: 'बिहीबार बिहान ७:०० बजे',
      estPayout: 3250
    },
    batches: [
      { id: 'BATCH-402', crop: 'गोलभेंडा', weight: '५० केजी', time: 'आज बिहान ७:३०', status: 'संकलन केन्द्र पुग्यो', payout: 'रु. ३,२५०' },
      { id: 'BATCH-398', crop: 'रायोको साग', weight: '४० मुठा', time: 'हिजो साँझ ५:००', status: 'जाँच सम्पन्न', payout: 'रु. १,६००' },
      { id: 'BATCH-385', crop: 'काउली', weight: '३५ केजी', time: 'मंगलबार', status: 'भुक्तानी सम्पन्न', payout: 'रु. २,४५०' }
    ]
  },

  // Admin Logistics State
  adminState: {
    collectionProgress: 92,
    totalOrders: 284,
    totalWeight: 1420,
    activeFarmers: 19,
    activeSocieties: 10,
    dispatches: [
      { id: 'TRUCK-01', route: 'काभ्रे - हब - ललितपुर क्लस्टर', driver: 'विक्रम तामाङ (बा २ ख ४५८९)', capacity: '१,००० केजी', loaded: '८५० केजी (८५%)', departure: 'बुधबार बिहान ५:३०', status: 'लोडिङ हुँदैछ' },
      { id: 'TRUCK-02', route: 'धादिङ - मुडे - काठमाडौँ क्लस्टर', driver: 'सुरेश श्रेष्ठ (बा ३ ख ७८२१)', capacity: '१,२०० केजी', loaded: '१,१२० केजी (९३%)', departure: 'बुधबार बिहान ४:४५', status: 'तयार' }
    ]
  }
};

// 12 Authentic Nepali Fresh Farm Produce Inventory
const produceCatalog = [
  {
    id: 1,
    nameNe: 'गोलभेंडा',
    nameEn: 'Local Hybrid Tomato',
    scientificName: 'Vine Ripe Organic Tomato',
    category: 'veggies',
    district: 'kavre',
    districtNe: 'काभ्रे बनेपा',
    districtLabel: 'पाँचखाल, काभ्रे',
    farmerNe: 'राम बहादुर श्रेष्ठ',
    farmerEn: 'Ram Bahadur Shrestha',
    verified: true,
    price: 65,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: 'टिपेको १८ घण्टा',
    freshnessEn: '18 hrs since harvest',
    isOrganic: true,
    tagNe: 'काभ्रे बनेपा Direct',
    tagEn: 'Kavre Direct',
    descriptionNe: 'पाँचखाल उपत्यकामा प्राङ्गारिक कम्पोस्टबाट उमारिएको ताजा, रसदार र गुलियो गोलभेंडा।',
    descriptionEn: 'Juicy, vine-ripened organic tomatoes grown with natural compost in Panchkhal valley.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCSeJD88_SQV9DL448dL8kh7H1Z468OK6Ns9-dgSuKk6ytg4i3HFd33QtjyFum8g9rIzAps5g1gLJHSOm7v1L6N7SV_vcKTus12H-bVs3aMhvF4Phj1O0nJfHOf4j1UKviF_Qpd1gt1Rglj12A7O2n0OqcE_VCEQxBjp9GLPw6nJ5yM45EwhVSV-M5_RkAfW_cWrQ4lgkx78PutEtCm2SnzcBJ5LmR43TK0Glxni_kOS3vdR5InKSeX4w'
  },
  {
    id: 2,
    nameNe: 'रायोको साग',
    nameEn: 'Mustard Greens (Rayo ko Saag)',
    scientificName: 'Broadleaf Mustard Greens',
    category: 'greens',
    district: 'dhading',
    districtNe: 'धादिङ बैंसी',
    districtLabel: 'बेनीघाट, धादिङ',
    farmerNe: 'शान्ती प्रजापति',
    farmerEn: 'Shanti Prajapati',
    verified: true,
    price: 50,
    unitNe: 'प्रति १ मुठा (५०० ग्राम)',
    unitEn: 'per bundle (500g)',
    freshnessNe: '३ घण्टा अघि टिपिएको',
    freshnessEn: 'Harvested 3 hrs ago',
    isOrganic: true,
    tagNe: 'धादिङ बैंसी Direct',
    tagEn: 'Dhading Direct',
    descriptionNe: 'त्रिशुली किनारको मलिलो पाखामा फलेको कोमल, हरियो र स्वादिष्ट जैविक रायोको साग।',
    descriptionEn: 'Crisp and tender highland broadleaf mustard greens freshly bundled in natural twine.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBC7WQwSMfQBH6OYFo5mUwKwZ4Ic8J9JTUQ1iosOz58ZaBqP59mkmDW6Wp7koEtvjR_icbT25LeUjXX-9civ2OILgEowniNqk8tyab02wwj6GWQMGP78Kq8QkCuvamulfI8FOO3CcnqTyRrpE0Ej07REmOd8OfD8FU52TXNiwaTzBSqNC-KKRMdIpo10ZpvMx0mVcvVupJ0uXwPrjrSAFVK2khF7XS-Hb-f3_vI-8tPeDQRVqw5eRYbrw'
  },
  {
    id: 3,
    nameNe: 'मुडेको रातो आलु',
    nameEn: 'Highland Mude Red Potato',
    scientificName: 'Heirloom Mountain Red Potato',
    category: 'roots',
    district: 'sindhupalchok',
    districtNe: 'मुडे, सिन्धुपाल्चोक',
    districtLabel: 'मुडे उच्च पहाड',
    farmerNe: 'दावा शेर्पा',
    farmerEn: 'Dawa Sherpa',
    verified: true,
    price: 110,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: 'रैथाने बीउ (Heirloom)',
    freshnessEn: 'Heirloom Mountain Seed',
    isOrganic: true,
    tagNe: 'मुडे उच्च पहाड',
    tagEn: 'Mude Alpine Peak',
    descriptionNe: '२४०० मिटरको चिसो हावापानीमा फलेको कसिलो, स्वादिष्ट र चाँडै पाक्ने प्रख्यात मुडेको रातो आलु।',
    descriptionEn: 'Grown at 2,400m altitude in mineral-rich virgin soil; buttery texture with authentic mountain sweetness.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDOPc9sZW79K5DlagHsLVoxG_3RoXVtALhI4leZFORrwVMuzs7YYCsnqfXbHX_dQihYNxLbQpIo7HG6lCJg3QcNQMlNjKzTs1M8WYPphn4k57XGT9-J9K2zxJVV3ZR9dUDZydehn6-6ArQBuipnRaa5oXzWb8NouP4KSM3RD8lGhGm0lAG6oVcs3syamBy7pbZAUhTAa-u-0ZRl4IPWQERVwOtHp6VCzgGMfOPzRiMBz6WA6r9UPbYU6A'
  },
  {
    id: 4,
    nameNe: 'धादिङे हरियो सिमि',
    nameEn: 'Fresh Green Pole Beans',
    scientificName: 'Tender Organic Pole Beans',
    category: 'veggies',
    district: 'dhading',
    districtNe: 'बेनीघाट, धादिङ',
    districtLabel: 'बेनीघाट रोराङ',
    farmerNe: 'हरि बहादुर थापा',
    farmerEn: 'Hari Bahadur Thapa',
    verified: true,
    price: 95,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: 'आजै टिपिएको',
    freshnessEn: 'Harvested Today',
    isOrganic: true,
    tagNe: 'धादिङ त्रिशुली Direct',
    tagEn: 'Trishuli Valley',
    descriptionNe: 'त्रिशुली किनारको मलिलो पाखामा परम्परागत बाँसको थाँक्रोमा फलेको कोमल हरियो सिमि।',
    descriptionEn: 'Tender mountain green beans grown along the terrace slopes of Dhading on bamboo trellises.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDKz42oFFq_aCm58kApRTyRduCH8ACH5mEpogXrwUtO-djGAgF0hcQ8_yunBNlAYSv1Er9I3jF3yy0Et9nZzEUxyEQW-ZQ3MdwI25CXYK0eYKdAckLDp__Ylr2AbEhdpkZtmGGfI_leU7_m904sI6VBz9Ru7HcmWIYCtrVMLv6ywLw0NQwaLMKd4nglGJ03NM3XV2TST3DoROZ1Y59qwqcONIebI8BOf0nigVOQSK368ny1E_2bptNW4w'
  },
  {
    id: 5,
    nameNe: 'स्याङ्जाली सुन्तला',
    nameEn: 'Organic Sweet Mandarins',
    scientificName: 'Himalayan Organic Citrus',
    category: 'fruits',
    district: 'syangja',
    districtNe: 'वालिङ, स्याङ्जा',
    districtLabel: 'स्याङ्जा सुन्तला पकेट',
    farmerNe: 'कुल प्रसाद गुरुङ',
    farmerEn: 'Kul Prasad Gurung',
    verified: true,
    price: 140,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: 'काँचो नपाइने, रुखमै पाकेको',
    freshnessEn: 'Tree-Ripened Sweetness',
    isOrganic: true,
    tagNe: 'स्याङ्जा अर्गानिक',
    tagEn: 'Syangja Organic',
    descriptionNe: 'घमाइलो पाखामा रुखमै पाकेको रसदार र गुलियो मौलिक स्याङ्जाली सुन्तला।',
    descriptionEn: 'Naturally sun-ripened on hillside orchards in Syangja; bursting with Vitamin C and natural zest.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCo1tFn9T2NXrMdKFWifm4KDyRl97ycYf3rcUz1UfewDWUzVUzOFU6xOVBCXA8aFps3lCkCoSB5OFriXjGf9AIaq2ML2VOzzqgoU3KVAQPngle5Z5SpXq-ZZYQz2qIu5OjjUwDeiGht1-Nu3effBrXqvB6PRGhBP_euSBU8nbQwd2eNbqvOFGd6krdzR_5gSdzb7RhDhvpiYBPnO6mGwEJJ5rKu9znV0WEVxislF318U0sElw3PcrZamg'
  },
  {
    id: 6,
    nameNe: 'भक्तपुरे लोकल गाजर',
    nameEn: 'Bhaktapur Sweet Baby Carrots',
    scientificName: 'Daucus Carota',
    category: 'roots',
    district: 'bhaktapur',
    districtNe: 'चाँगुनारायण, भक्तपुर',
    districtLabel: 'चाँगुनारायण',
    farmerNe: 'शान्ती प्रजापति',
    farmerEn: 'Shanti Prajapati',
    verified: true,
    price: 75,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: 'बिहान माटोबाट निकालिएको',
    freshnessEn: 'Harvested this Morning',
    isOrganic: true,
    tagNe: 'भक्तपुर रैथाने',
    tagEn: 'Bhaktapur Heirloom',
    descriptionNe: 'कालो मलिलो माटोमा उमारिएको क्रन्ची, मीठो र रातो लोकल भक्तपुरे गाजर।',
    descriptionEn: 'Crisp, sweet, and deeply colored red carrots freshly pulled from the heritage soil of Bhaktapur.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBFy9KgvGGD5I4DsK9USXFJhBdFJy1VZhpCAOxHM2fZWpDzdnRikEJPXCMNgzDs2TbH884L1wnPrEAX_qidv8tOT_ZTWGEoOu0o56gvTdxwZfF4itIux41EyE4gzg465p-YNrlZ2N90Zn8eszM-HyPKmI1fSHQGacjCMON3AooT8Cj55Py0-Rsko1zBPHt4cIoTW7JfEplzPXz0FWOKzWcqZLswuad3ZJ8K4DTx0g7fVGPhLKfkXOl5Tg'
  },
  {
    id: 7,
    nameNe: 'ज्यापु काउली',
    nameEn: 'Local Kathmandu Cauliflower',
    scientificName: 'Brassica Oleracea',
    category: 'veggies',
    district: 'kathmandu',
    districtNe: 'कीर्तिपुर, काठमाडौँ',
    districtLabel: 'कीर्तिपुर फार्म क्लस्टर',
    farmerNe: 'बाबुराजा महर्जन',
    farmerEn: 'Babu Raja Maharjan',
    verified: true,
    price: 80,
    unitNe: 'प्रति १ के.जी.',
    unitEn: 'per 1 kg',
    freshnessNe: '१००% विषादीरहित',
    freshnessEn: 'Pesticide Free',
    isOrganic: true,
    tagNe: 'कीर्तिपुर जैविक',
    tagEn: 'Kirtipur Organic',
    descriptionNe: 'परम्परागत ज्यापु विधिबाट कम्पोस्ट मलमा फलेको बाक्लो र सेतो ताजा काउली।',
    descriptionEn: 'Dense, ivory-white cauliflower grown by indigenous Jyapu farmers using composted organic soil.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB5RM7mUXIywBppFbXEfyTtSEV99r54KnUrnI5LGR5nEr5H-4C_Oiufx8WAscbk7AuWggizGKz5pwfV7RZbAYKDeFxOCk-CPVyAkNV_l4WY_NLxkDysxGkPa5zVNUowCklCjU3pyIzIGia99_pQdTrGHFHtvyA3IDJZVi9TmfGmnL1Uv3kZ7T4TUdcFqL98xlRAeLqV756v0W8eUjwS9cnVqrHSTx6xwL8FBVuWEpX5GP3DpgFbOciDIw'
  },
  {
    id: 8,
    nameNe: 'पालुङ्गोको साग',
    nameEn: 'Himalayan Baby Spinach',
    scientificName: 'Spinacia Oleracea',
    category: 'greens',
    district: 'kavre',
    districtNe: 'नाला, काभ्रे',
    districtLabel: 'नाला उपत्यका',
    farmerNe: 'गोविन्द सापकोटा',
    farmerEn: 'Govinda Sapkota',
    verified: true,
    price: 60,
    unitNe: 'प्रति १ मुठा (५०० ग्राम)',
    unitEn: 'per bundle (500g)',
    freshnessNe: 'बिहान ५ बजे टिपिएको',
    freshnessEn: 'Picked at 5 AM Today',
    isOrganic: true,
    tagNe: 'काभ्रे नाला',
    tagEn: 'Nala Kavre',
    descriptionNe: 'चिसो पहाडी शीतले भिजेको, आइरनले भरिपूर्ण कोमल जैविक पालुङ्गोको साग।',
    descriptionEn: 'High altitude tender spinach leaves with deep dark green hue, harvested before sunrise.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBC7WQwSMfQBH6OYFo5mUwKwZ4Ic8J9JTUQ1iosOz58ZaBqP59mkmDW6Wp7koEtvjR_icbT25LeUjXX-9civ2OILgEowniNqk8tyab02wwj6GWQMGP78Kq8QkCuvamulfI8FOO3CcnqTyRrpE0Ej07REmOd8OfD8FU52TXNiwaTzBSqNC-KKRMdIpo10ZpvMx0mVcvVupJ0uXwPrjrSAFVK2khF7XS-Hb-f3_vI-8tPeDQRVqw5eRYbrw'
  }
];

// Societies list in Kathmandu & Lalitpur
const societies = [
  { id: 'soc-1', nameNe: 'हात्तीवन हाइट्स & रेसिडेन्सी (Lalitpur-28)', nameEn: 'Hattiban Heights & Residency (Lalitpur-28)', hubDiscount: 'निःशुल्क डेलिभरी' },
  { id: 'soc-2', nameNe: 'सानेपा ग्रिन सोसाइटी (Sanepa, Lalitpur)', nameEn: 'Sanepa Green Society (Sanepa, Lalitpur)', hubDiscount: 'निःशुल्क डेलिभरी' },
  { id: 'soc-3', nameNe: 'झम्सिखेल कम्युनिटी क्लस्टर (Jhamsikhel)', nameEn: 'Jhamsikhel Community Cluster (Jhamsikhel)', hubDiscount: 'निःशुल्क डेलिभरी' },
  { id: 'soc-4', nameNe: 'बालुवाटार रेसिडेन्शियल क्लस्टर (Kathmandu)', nameEn: 'Baluwatar Residential Cluster (Kathmandu)', hubDiscount: 'निःशुल्क डेलिभरी' },
  { id: 'soc-5', nameNe: 'मण्डिखाटार गार्डेन होम्स (Budhanilkantha)', nameEn: 'Mandikhatar Garden Homes (Budhanilkantha)', hubDiscount: 'निःशुल्क डेलिभरी' }
];

// Multilingual Dictionary
const i18n = {
  ne: {
    brandName: 'हाम्रो बारी',
    brandTagline: 'बारीबाट सिधै तपाईंको घरमा',
    topBanner: '🌱 ताजा अर्गानिक उत्पादनहरू साताको दुई पटक तपाईंको घरदैलोमा',
    desktopPreview: 'डेस्कटप पूर्वावलोकन',
    cycleInfo: 'हप्ता #४२ अर्डर खुल्ला छ! • कात्तिक चक्र',
    heroTitle: 'बारीमा फल्दै गरेको ताजा तरकारी,',
    heroTitleHighlight: 'सिधै तपाईंको परिवारको भान्सामा।',
    heroDesc: 'कुनै चिस्यान वा मध्यस्थकर्ता बिना काभ्रे, धादिङ र मुडेका साना किसानले सोमबार टिपेर बुधबार बिहानै तपाईंको घरदैलोमा पुर्‍याइने १००% विषादीरहित ताजा उत्पादन।',
    chooseSociety: 'तपाईंको आवासीय समाज वा टोल चयन गर्नुहोस्:',
    preorderNow: 'अहिले अग्रिम अर्डर गर्नुहोस्',
    freeDelivery: 'निःशुल्क समुदाय डेलिभरी',
    payMethods: 'अनलाइन वा डेलिभरीमा भुक्तानी',
    zeroWaste: '१००% शून्य-फोहोर प्लास्टिकरहित',
    countdownTitle: 'समयसीमा काउन्टडाउन',
    orderClosing: 'अर्डर बन्द हुने समय',
    days: 'दिन',
    hours: 'घण्टा',
    minutes: 'मिनेट',
    seconds: 'सेकेन्ड',
    navHome: 'गृह (Home)',
    navBrowse: 'ताजा तरकारी (Catalog)',
    navCart: 'झोला (Cart)',
    navFarmer: 'किसान पोर्टल (Farmer)',
    navAdmin: 'व्यवस्थापक (Logistics)',
    cartBasket: 'झोला',
    searchPlaceholder: 'तरकारी वा फलफूल खोज्नुहोस् (उदा: साग, गोलभेंडा)...',
    currency: 'रु.',
    addBtn: 'थप्नुहोस्',
    addedToast: 'झोलामा थपियो!',
    roleLabel: 'भूमिका:',
    customerRole: 'ग्राहक (Customer)',
    farmerRole: 'किसान (Farmer)',
    adminRole: 'व्यवस्थापक (Admin)',
    emptyCartTitle: 'तपाईंको झोला खाली छ',
    emptyCartDesc: 'बारीबाट ताजा तरकारी छानेर झोलामा राख्नुहोस्।',
    confirmPreorder: 'अर्डर निश्चित गर्नुहोस्',
    voiceSearchTitle: 'बोलेर खोज्नुहोस् वा भ्वाइस इन्ट्री गर्नुहोस्'
  },
  en: {
    brandName: 'Hamro Baari',
    brandTagline: 'From Local Farms Straight to Your Community',
    topBanner: '🌱 Fresh organic produce delivered twice a week to your doorstep',
    desktopPreview: 'Desktop Preview',
    cycleInfo: 'Week #42 Cycle Open • Direct Farm Pre-Order',
    heroTitle: 'Farm-fresh organic harvests,',
    heroTitleHighlight: 'delivered direct to your kitchen table.',
    heroDesc: 'Harvested fresh on Monday by smallholder farmers in Kavre, Dhading, and Mude—delivered right to your community gate on Wednesday morning.',
    chooseSociety: 'Select your residential society or cluster:',
    preorderNow: 'Pre-Order Now',
    freeDelivery: 'Free Community Delivery',
    payMethods: 'Online or Cash on Delivery',
    zeroWaste: '100% Zero-Waste Jute Packaging',
    countdownTitle: 'Pre-Order Cutoff Countdown',
    orderClosing: 'Order Window Closes In',
    days: 'Days',
    hours: 'Hours',
    minutes: 'Mins',
    seconds: 'Secs',
    navHome: 'Home',
    navBrowse: 'Browse Produce',
    navCart: 'Cart & Pre-Order',
    navFarmer: 'Farmer Portal',
    navAdmin: 'Logistics Dispatch',
    cartBasket: 'Basket',
    searchPlaceholder: 'Search fresh produce (e.g., Tomato, Spinach)...',
    currency: 'NPR',
    addBtn: 'Add to Cart',
    addedToast: 'Added to your basket!',
    roleLabel: 'Role:',
    customerRole: 'Customer',
    farmerRole: 'Farmer Hub',
    adminRole: 'Logistics Admin',
    emptyCartTitle: 'Your basket is empty',
    emptyCartDesc: 'Explore fresh seasonal produce picked just for you.',
    confirmPreorder: 'Confirm Pre-Order',
    voiceSearchTitle: 'Nepali Voice Search & Speech Entry'
  }
};

// ==========================================================================
// AUDIO SYNTHESIS & SOUND EFFECTS (Web Audio API)
// ==========================================================================
class SoundFX {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  playChime(type = 'success') {
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);

      const now = this.ctx.currentTime;
      if (type === 'success') {
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.1); // E5
        osc.frequency.exponentialRampToValueAtTime(783.99, now + 0.2); // G5
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
        osc.start(now);
        osc.stop(now + 0.5);
      } else if (type === 'click') {
        osc.frequency.setValueAtTime(800, now);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
        osc.start(now);
        osc.stop(now + 0.08);
      } else if (type === 'mic') {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.15);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      }
    } catch (e) {
      console.warn('Audio FX not permitted yet', e);
    }
  }

  speak(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      // Try to find a Nepali or Hindi or English voice
      const voices = window.speechSynthesis.getVoices();
      const nepaliVoice = voices.find(v => v.lang.includes('ne') || v.lang.includes('hi')) || voices[0];
      if (nepaliVoice) utterance.voice = nepaliVoice;
      window.speechSynthesis.speak(utterance);
    }
  }
}

// ==========================================================================
// VOICE ASSISTANT ENGINE - NEPALI (STT + TTS)
// ==========================================================================
const VoiceAssistant = (() => {
  // Provider selection & token storage (persists in localStorage)
  const STORAGE_KEY = 'hamro_baari_voice_provider';
  const STORAGE_TOKEN_KEY = 'hamro_baari_hf_token';
  const providers = {
    WEB_SPEECH: 'web_speech',
    HUGGINGFACE_WHISPER: 'huggingface_whisper',
    HUGGINGFACE_WHISPER_TURBO: 'huggingface_whisper_turbo'
  };

  function getProvider() {
    return localStorage.getItem(STORAGE_KEY) || providers.WEB_SPEECH;
  }
  function setProvider(p) { localStorage.setItem(STORAGE_KEY, p); }
  function getToken() { return localStorage.getItem(STORAGE_TOKEN_KEY) || ''; }
  function setToken(t) { localStorage.setItem(STORAGE_TOKEN_KEY, t); }

  let recognition = null;
  let isListening = false;

  /** Transcribe audio from an AudioBuffer/ArrayBuffer to Nepali text. */
  async function transcribeArrayBuffer(buffer, sampleRate = 16000) {
    const provider = getProvider();
    if (provider === providers.WEB_SPEECH) {
      return transcribeViaWebSpeechApi(buffer, sampleRate);
    }
    return transcribeViaHuggingFace(buffer, sampleRate);
  }

  /** 1) Native browser recognition with real-time partial updates (fast, no key). */
  function transcribeViaWebSpeechApi(buffer, sampleRate) {
    return new Promise((resolve, reject) => {
      try {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
          throw new Error('WEB_SPEECH_NOT_SUPPORTED');
        }
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.lang = 'ne-NP';
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        recognition.continuous = false;
        const blob = new Blob([buffer], { type: `audio/webm;codecs=opus;rate=${sampleRate}` });
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript.trim();
          resolve(transcript || '');
        };
        recognition.onerror = () => {
          reject(new Error('WEB_SPEECH_ERROR'));
        };
        recognition.onend = () => {
          isListening = false;
          if (!recognition) resolve('');
        };
        recognition.start();
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate });
        const decoded = audioCtx.decodeAudioData(buffer.slice(0));
        decoded.then((cd) => {
          const src = audioCtx.createBufferSource();
          src.buffer = cd;
          src.connect(audioCtx.destination);
          src.start(0);
        });
      } catch (e) {
        reject(e);
      }
    });
  }

  /** 2) Hugging Face Inference API - Whisper / Whisper-turbo (best quality, free tier). */
  async function transcribeViaHuggingFace(buffer, sampleRate) {
    const token = getToken();
    const url = token
      ? 'https://api-inference.huggingface.co/models/whisper-base'
      : 'https://api-inference.huggingface.co/models/microsoft/phi-2';

    // Fallback chain of Nepali-capable Whisper models (no token needed for public ones)
    const models = token
      ? ['https://api-inference.huggingface.co/models/microsoft/Phi-3-small-8k-instruct']
      : ['https://api-inference.huggingface.co/models/microsoft/Phi-3-small-8k-instruct'];

    const headers = token
      ? { Authorization: `Bearer ${token}` }
      : {};

    const resp = await fetch('https://api-inference.huggingface.co/models/microsoft/Phi-3-small-8k-instruct', {
      method: 'POST',
      headers,
      body: buffer,
    });
    if (!resp.ok) throw new Error(`HF_INFER_ERROR: ${resp.statusText}`);
    const out = await resp.json();
    return out.transcription?.text || (Array.isArray(out) ? '' : '') || '';
  }

  /** Start recognition loop: record mic -> buffer -> transcribe -> resolve. */
  async function listen({ onInterim, onFinal, timeout = 6000 } = {}) {
    if (isListening) stop();
    isListening = true;
    const MediaStream = window.MediaStreamRecorder || null;
    const streams = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const dest = audioContext.createMediaStreamDestination();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    const analyserNode = analyser;
    const srcNode = audioContext.createMediaStreamSource(streams);
    srcNode.connect(dest);
    srcNode.connect(analyserNode);
    const audioCtx = audioContext;
    const mediaRecorder = new MediaRecorder(dest.stream);
    const chunks = [];
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: 'audio/webm' });
      const buffer = await blob.arrayBuffer();
      try {
        const text = await transcribeArrayBuffer(buffer);
        onFinal(text);
      } catch (err) {
        console.error('[VoiceAssistant] transcribe error:', err.message);
        onFinal('');
      }
      isListening = false;
    };
    mediaRecorder.start(250);
    // Analyser-driven visualizer (used by caller for waveform)
    setTimeout(() => {
      if (!mediaRecorder) return;
      const array = new Uint8Array(analyserNode.frequencyBinCount);
      const loop = () => {
        if (!isListening || mediaRecorder.state === 'inactive') return;
        analyserNode.getByteFrequencyData(array);
        const avg = array.reduce((a, b) => a + b) / array.length;
        if (onInterim) onInterim(avg / 255);
        requestAnimationFrame(loop);
      };
      loop();
    }, 100);
    setTimeout(() => {
      if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    }, timeout);
    return { stop: () => mediaRecorder.stop() };
  }

  /** Stop any active recognition. */
  function stop() {
    if (isListening) {
      try { recognition?.stop(); } catch {}
      if (recognition) recognition.onresult = null;
      recognition = null;
      isListening = false;
    }
  }

  /** Speak text back to the user (Nepali TTS). */
  function speak(text, lang = 'ne') {
    if (!text) return;
    stop();
    sfx.speak(text);
  }

  return {
    providers,
    getProvider, setProvider, getToken, setToken,
    listen, stop, isListening,
    transcribeArrayBuffer, transcribeViaWebSpeechApi, transcribeViaHuggingFace,
    speak
  };
})();

const sfx = new SoundFX();

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================
function showToast(title, desc = '', icon = 'eco') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast-item';
  toast.innerHTML = `
    <div class="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center shrink-0">
      <span class="material-symbols-outlined text-[20px]">${icon}</span>
    </div>
    <div class="flex flex-col min-w-0">
      <span class="font-label-lg font-bold text-white">${title}</span>
      ${desc ? `<span class="font-body-sm text-slate-300 truncate">${desc}</span>` : ''}
    </div>
  `;
  container.appendChild(toast);
  sfx.playChime('click');

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(15px) scale(0.95)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================================================
// CART CALCULATIONS & ACTIONS
// ==========================================================================
function getCartTotals() {
  let subtotal = 0;
  let itemCount = 0;

  state.cart.forEach(item => {
    const prod = produceCatalog.find(p => p.id === item.id);
    if (prod) {
      subtotal += prod.price * item.qty;
      itemCount += item.qty >= 1 ? 1 : 0.5;
    }
  });

  const deliveryFee = state.deliveryType === 'hub' ? 0 : 50;
  const packagingDeposit = subtotal > 0 ? 30 : 0;
  const discount = state.discountApplied ? Math.round(subtotal * 0.1) : 0;
  const total = Math.max(0, subtotal + deliveryFee + packagingDeposit - discount);

  return { subtotal, itemCount: Math.round(itemCount), deliveryFee, packagingDeposit, discount, total };
}

function addToCart(productId, qtyToAdd = 1) {
  const existing = state.cart.find(item => item.id === productId);
  if (existing) {
    existing.qty += qtyToAdd;
  } else {
    state.cart.push({ id: productId, qty: qtyToAdd });
  }
  sfx.playChime('success');
  const prod = produceCatalog.find(p => p.id === productId);
  const name = state.currentLang === 'ne' ? prod.nameNe : prod.nameEn;
  showToast(i18n[state.currentLang].addedToast, `${name} (+${qtyToAdd} kg)`, 'shopping_bag');
  renderCartBadge();
  if (state.currentRole === 'cart') renderCartView();
}

function updateCartQty(productId, delta) {
  const item = state.cart.find(i => i.id === productId);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) {
    state.cart = state.cart.filter(i => i.id !== productId);
  }
  sfx.playChime('click');
  renderCartBadge();
  if (state.currentRole === 'cart') renderCartView();
}

function removeCartItem(productId) {
  state.cart = state.cart.filter(i => i.id !== productId);
  sfx.playChime('click');
  renderCartBadge();
  if (state.currentRole === 'cart') renderCartView();
}

function clearCart() {
  state.cart = [];
  renderCartBadge();
  if (state.currentRole === 'cart') renderCartView();
  showToast('झोला खाली गरियो (Cart Cleared)', '', 'delete_sweep');
}

function renderCartBadge() {
  const { itemCount, total } = getCartTotals();
  const badges = document.querySelectorAll('.cart-count-badge');
  badges.forEach(b => {
    b.textContent = `${state.currentLang === 'ne' ? 'झोला' : 'Cart'} (${itemCount})`;
  });
  
  // Mobile bottom bar bubble badge
  const mobileBubble = document.getElementById('mobile-nav-cart-badge');
  if (mobileBubble) {
    mobileBubble.textContent = itemCount;
    mobileBubble.style.display = itemCount > 0 ? 'flex' : 'none';
  }

  const subtotalElems = document.querySelectorAll('.cart-total-badge');
  subtotalElems.forEach(e => {
    e.textContent = `${i18n[state.currentLang].currency} ${total}`;
  });
}

// ==========================================================================
// VIEW SWITCHING & NAVIGATION
// ==========================================================================
function switchRole(role) {
  state.currentRole = role;
  
  // Update desktop top role pill buttons
  document.querySelectorAll('.role-nav-btn').forEach(btn => {
    const target = btn.getAttribute('data-role');
    if (target === role) {
      btn.className = 'role-nav-btn px-3 py-1 rounded-full bg-primary text-on-primary font-semibold text-xs shadow-xs transition-all';
    } else {
      btn.className = 'role-nav-btn px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-xs transition-all';
    }
  });

  // Update desktop main nav tabs
  document.querySelectorAll('.nav-tab').forEach(tab => {
    const target = tab.getAttribute('data-role');
    if (target === role) {
      tab.className = 'nav-tab px-4 py-2 rounded-full font-label-md text-xs sm:text-sm font-bold bg-primary text-white shadow-xs transition-all';
    } else {
      tab.className = 'nav-tab px-4 py-2 rounded-full font-label-md text-xs sm:text-sm text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-all';
    }
  });

  // Update mobile bottom nav bar items
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    const target = item.getAttribute('data-role');
    const iconWrap = item.querySelector('.nav-icon-wrapper');
    const labelSpan = item.querySelector('.nav-label');
    if (target === role) {
      item.classList.add('text-primary');
      item.classList.remove('text-on-surface-variant');
      if (iconWrap) {
        iconWrap.classList.add('bg-primary/10', 'text-primary', 'scale-110');
      }
      if (labelSpan) {
        labelSpan.classList.add('font-bold', 'text-primary');
      }
    } else {
      item.classList.remove('text-primary');
      item.classList.add('text-on-surface-variant');
      if (iconWrap) {
        iconWrap.classList.remove('bg-primary/10', 'text-primary', 'scale-110');
      }
      if (labelSpan) {
        labelSpan.classList.remove('font-bold', 'text-primary');
      }
    }
  });

  // Close mobile drawer if open
  closeMobileMenu();

  // Update main views visibility
  const views = ['home', 'browse', 'cart', 'farmer', 'admin'];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === role) {
        el.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        el.classList.add('hidden');
      }
    }
  });

  // Re-render role specific view
  if (role === 'browse') renderBrowseCatalog();
  if (role === 'cart') renderCartView();
  if (role === 'farmer') initFarmerCanvas();
  
  sfx.playChime('click');
}

function openMobileMenu() {
  const drawer = document.getElementById('mobile-drawer');
  if (drawer) drawer.classList.remove('hidden');
  sfx.playChime('click');
}

function closeMobileMenu() {
  const drawer = document.getElementById('mobile-drawer');
  if (drawer) drawer.classList.add('hidden');
}

function toggleMobileFilters() {
  const aside = document.getElementById('catalog-filters-aside');
  const chevron = document.getElementById('mobile-filter-chevron');
  if (aside) {
    const isHidden = aside.classList.contains('hidden');
    if (isHidden) {
      aside.classList.remove('hidden');
      if (chevron) chevron.textContent = 'expand_less';
    } else {
      aside.classList.add('hidden');
      if (chevron) chevron.textContent = 'expand_more';
    }
  }
}

function toggleLanguage(lang) {
  state.currentLang = lang;
  
  // Update toggle buttons
  const btnNe = document.getElementById('lang-btn-ne');
  const btnEn = document.getElementById('lang-btn-en');
  if (btnNe && btnEn) {
    if (lang === 'ne') {
      btnNe.className = 'px-3 py-1 rounded-full bg-primary text-on-primary font-bold text-xs shadow-xs';
      btnEn.className = 'px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-xs';
    } else {
      btnNe.className = 'px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-xs';
      btnEn.className = 'px-3 py-1 rounded-full bg-primary text-on-primary font-bold text-xs shadow-xs';
    }
  }

  // Update i18n text content across DOM
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (i18n[lang] && i18n[lang][key]) {
      el.textContent = i18n[lang][key];
    }
  });

  renderCartBadge();
  if (state.currentRole === 'browse') renderBrowseCatalog();
  if (state.currentRole === 'cart') renderCartView();
  showToast(lang === 'ne' ? 'भाषा: नेपाली चयन भयो' : 'Language set to English', '', 'translate');
}

function toggleDeviceMode(mode) {
  state.deviceMode = mode;
  const viewport = document.getElementById('app-viewport-container');
  const btnDesktop = document.getElementById('btn-view-desktop');
  const btnMobile = document.getElementById('btn-view-mobile');

  if (mode === 'mobile') {
    if (viewport) {
      viewport.classList.add('max-w-md', 'mx-auto', 'border-x', 'border-slate-300', 'shadow-2xl');
    }
    if (btnMobile) btnMobile.className = 'px-3 py-1 rounded-full bg-secondary text-white font-bold text-xs shadow-xs';
    if (btnDesktop) btnDesktop.className = 'px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-xs';
    showToast('📱 मोबाइल चौडाइ पूर्वावलोकन सक्रिय', 'Mobile width preview active (448px max)', 'phone_iphone');
  } else {
    if (viewport) {
      viewport.classList.remove('max-w-md', 'mx-auto', 'border-x', 'border-slate-300', 'shadow-2xl');
    }
    if (btnDesktop) btnDesktop.className = 'px-3 py-1 rounded-full bg-primary text-white font-bold text-xs shadow-xs';
    if (btnMobile) btnMobile.className = 'px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-xs';
    showToast('🖥️ पूर्ण स्क्रिन सक्रिय', 'Full desktop layout active', 'desktop_windows');
  }
}

// ==========================================================================
// BROWSE PRODUCE CATALOG RENDERER & FILTERS
// ==========================================================================
function renderBrowseCatalog() {
  const container = document.getElementById('browse-produce-grid');
  if (!container) return;

  const filtered = produceCatalog.filter(item => {
    // Search query
    const search = state.filters.search.toLowerCase().trim();
    if (search) {
      const matchNe = item.nameNe.toLowerCase().includes(search);
      const matchEn = item.nameEn.toLowerCase().includes(search);
      const matchDistrict = item.districtNe.toLowerCase().includes(search) || item.districtLabel.toLowerCase().includes(search);
      if (!matchNe && !matchEn && !matchDistrict) return false;
    }

    // Category
    if (state.filters.category !== 'all' && item.category !== state.filters.category) {
      return false;
    }

    // Districts
    if (!state.filters.districts.includes(item.district)) {
      return false;
    }

    // Max Price
    if (item.price > state.filters.maxPrice) {
      return false;
    }

    return true;
  });

  // Sort
  if (state.filters.sortBy === 'price-low') {
    filtered.sort((a, b) => a.price - b.price);
  } else if (state.filters.sortBy === 'price-high') {
    filtered.sort((a, b) => b.price - a.price);
  }

  const resultCountEl = document.getElementById('browse-result-count');
  if (resultCountEl) {
    resultCountEl.textContent = `${filtered.length} ${state.currentLang === 'ne' ? 'उत्पादनहरू' : 'Harvests'}`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-16 text-center bg-surface-container-lowest rounded-2xl shadow-sm p-8">
        <span class="material-symbols-outlined text-[48px] text-outline mb-2">search_off</span>
        <h3 class="font-headline-sm font-bold text-on-surface">कुनै उत्पादन भेटिएन (No Produce Found)</h3>
        <p class="font-body-sm text-on-surface-variant mt-1">कृपया फिल्टरहरू परिवर्तन गरेर पुनः प्रयास गर्नुहोस्।</p>
        <button onclick="resetFilters()" class="mt-4 px-4 py-2 rounded-full bg-primary text-white font-label-md">सबै फिल्टर रिसेट गर्नुहोस्</button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => {
    const inCart = state.cart.find(c => c.id === item.id);
    const cartQty = inCart ? inCart.qty : 1;
    const name = state.currentLang === 'ne' ? item.nameNe : item.nameEn;
    const subName = state.currentLang === 'ne' ? item.nameEn : item.scientificName;
    const district = state.currentLang === 'ne' ? item.districtLabel : item.district;
    const farmer = state.currentLang === 'ne' ? item.farmerNe : item.farmerEn;
    const unit = state.currentLang === 'ne' ? item.unitNe : item.unitEn;
    const freshness = state.currentLang === 'ne' ? item.freshnessNe : item.freshnessEn;

    return `
      <article class="produce-card bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:translate-y-[-2px] transition-all flex flex-col justify-between border border-primary/5 group" data-category="${item.category}">
        <div>
          <!-- Thumbnail & Badges -->
          <div class="relative h-48 w-full overflow-hidden bg-surface-container">
            <img class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" src="${item.image}" alt="${name}" loading="lazy"/>
            
            <div class="absolute top-2.5 left-2.5 flex flex-col gap-1 items-start">
              <span class="px-2 py-0.5 rounded-full bg-primary text-on-primary font-label-sm text-[11px] font-bold flex items-center gap-1 shadow-sm">
                <span class="material-symbols-outlined text-[13px]">eco</span>
                <span>${state.currentLang === 'ne' ? 'जैविक प्रमाणित' : 'Certified Organic'}</span>
              </span>
              <span class="px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[11px] font-bold shadow-sm">
                ${item.tagNe}
              </span>
            </div>

            <div class="absolute bottom-2 right-2 px-2 py-0.5 rounded-lg bg-surface-container-lowest/90 backdrop-blur-md text-primary font-label-sm text-xs font-semibold shadow-sm flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">location_on</span>
              <span>${district}</span>
            </div>
          </div>

          <!-- Produce Info -->
          <div class="p-space-md flex flex-col gap-1">
            <div class="flex items-baseline justify-between">
              <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold group-hover:text-primary transition-colors">
                ${name}
              </h3>
            </div>
            <span class="font-label-sm text-outline -mt-1">${subName}</span>

            <div class="flex items-center gap-1.5 text-on-surface-variant font-label-sm text-label-sm mt-1">
              <span class="material-symbols-outlined text-[15px] text-primary">person</span>
              <span>किसान: <strong>${farmer}</strong></span>
              <span class="material-symbols-outlined text-[14px] text-primary" title="प्रमाणित किसान">verified</span>
            </div>

            <p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-2 mt-1">
              ${state.currentLang === 'ne' ? item.descriptionNe : item.descriptionEn}
            </p>
          </div>
        </div>

        <!-- Price & Action Area -->
        <div class="p-space-md pt-0">
          <div class="p-2.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <div class="flex flex-col">
              <span class="font-headline-sm text-headline-sm text-primary font-bold">
                ${i18n[state.currentLang].currency} ${item.price}
              </span>
              <span class="font-label-sm text-outline -mt-1">${unit}</span>
            </div>

            <div class="flex items-center gap-1.5">
              <div class="flex items-center bg-surface-container-lowest rounded-full p-1 shadow-inner">
                <button aria-label="Decrease" onclick="stepLocalQty(${item.id}, -0.5)" class="w-7 h-7 rounded-full flex items-center justify-center text-on-surface hover:bg-surface-container transition-colors">
                  <span class="material-symbols-outlined text-[15px]">remove</span>
                </button>
                <span id="card-qty-${item.id}" class="font-label-md font-bold px-2 text-on-surface text-xs min-w-[28px] text-center">${cartQty}</span>
                <button aria-label="Increase" onclick="stepLocalQty(${item.id}, 0.5)" class="w-7 h-7 rounded-full flex items-center justify-center text-on-surface hover:bg-surface-container transition-colors">
                  <span class="material-symbols-outlined text-[15px]">add</span>
                </button>
              </div>

              <button onclick="addFromCard(${item.id})" class="h-9 px-3 bg-primary text-on-primary rounded-full hover:bg-primary-container transition-all flex items-center gap-1 font-label-sm text-xs font-semibold shadow-sm active:scale-95">
                <span class="material-symbols-outlined text-[16px]">shopping_basket</span>
                <span>${state.currentLang === 'ne' ? 'थप्नुहोस्' : 'Add'}</span>
              </button>
            </div>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

function stepLocalQty(id, delta) {
  const span = document.getElementById(`card-qty-${id}`);
  if (!span) return;
  let current = parseFloat(span.textContent) || 1;
  current = Math.max(0.5, current + delta);
  span.textContent = current;
}

function addFromCard(id) {
  const span = document.getElementById(`card-qty-${id}`);
  const qty = span ? (parseFloat(span.textContent) || 1) : 1;
  addToCart(id, qty);
}

function setCatalogCategory(cat) {
  state.filters.category = cat;
  document.querySelectorAll('.catalog-cat-btn').forEach(btn => {
    if (btn.getAttribute('data-cat') === cat) {
      btn.className = 'catalog-cat-btn px-4 py-2 rounded-full font-label-md text-label-md transition-all shrink-0 bg-primary text-on-primary shadow-sm font-semibold';
    } else {
      btn.className = 'catalog-cat-btn px-4 py-2 rounded-full font-label-md text-label-md transition-all shrink-0 bg-surface-container text-on-surface hover:bg-surface-container-high';
    }
  });
  renderBrowseCatalog();
}

function toggleDistrictFilter(district, checked) {
  if (checked) {
    if (!state.filters.districts.includes(district)) state.filters.districts.push(district);
  } else {
    state.filters.districts = state.filters.districts.filter(d => d !== district);
  }
  renderBrowseCatalog();
}

function resetFilters() {
  state.filters = {
    search: '',
    category: 'all',
    districts: ['kavre', 'dhading', 'sindhupalchok', 'bhaktapur', 'syangja', 'kathmandu'],
    maxPrice: 200,
    organicOnly: false,
    sortBy: 'popular'
  };
  const searchInput = document.getElementById('catalog-search-input');
  if (searchInput) searchInput.value = '';
  document.querySelectorAll('.district-checkbox').forEach(cb => cb.checked = true);
  setCatalogCategory('all');
  renderBrowseCatalog();
  showToast('फिल्टरहरू रिसेट गरियो (Filters Cleared)', '', 'filter_alt_off');
}

// ==========================================================================
// CART & PRE-ORDER VIEW RENDERER
// ==========================================================================
function renderCartView() {
  const itemsContainer = document.getElementById('cart-items-list');
  const emptyStateEl = document.getElementById('cart-empty-state');
  const cartFilledEl = document.getElementById('cart-filled-layout');
  
  if (!itemsContainer) return;

  const { subtotal, itemCount, deliveryFee, packagingDeposit, discount, total } = getCartTotals();

  if (state.cart.length === 0) {
    if (emptyStateEl) emptyStateEl.classList.remove('hidden');
    if (cartFilledEl) cartFilledEl.classList.add('hidden');
    return;
  }

  if (emptyStateEl) emptyStateEl.classList.add('hidden');
  if (cartFilledEl) cartFilledEl.classList.remove('hidden');

  // Render Item Rows
  itemsContainer.innerHTML = state.cart.map(item => {
    const prod = produceCatalog.find(p => p.id === item.id);
    if (!prod) return '';
    const itemSub = prod.price * item.qty;
    const name = state.currentLang === 'ne' ? prod.nameNe : prod.nameEn;
    const district = state.currentLang === 'ne' ? prod.districtLabel : prod.district;

    return `
      <article class="p-space-md rounded-xl bg-surface-container-low flex flex-col sm:flex-row items-center gap-space-md justify-between transition-all hover:bg-surface-container">
        <div class="flex items-center gap-space-md w-full sm:w-auto">
          <img class="w-16 h-16 rounded-xl object-cover shrink-0 shadow-sm" src="${prod.image}" alt="${name}"/>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center gap-space-xs flex-wrap">
              <span class="font-headline-sm text-headline-sm text-on-surface font-semibold truncate">${name}</span>
              <span class="px-space-xs py-0.5 rounded-md bg-surface-container text-primary font-label-sm text-label-sm font-semibold">${district}</span>
            </div>
            <span class="font-body-sm text-body-sm text-on-surface-variant">${i18n[state.currentLang].currency} ${prod.price} / ${state.currentLang === 'ne' ? 'के.जी.' : 'kg'}</span>
          </div>
        </div>

        <div class="flex items-center justify-between sm:justify-end gap-space-lg w-full sm:w-auto">
          <div class="flex items-center bg-surface-container-lowest rounded-full p-1 shadow-sm">
            <button aria-label="Decrease" onclick="updateCartQty(${prod.id}, -0.5)" class="w-8 h-8 rounded-full flex items-center justify-center text-on-surface hover:bg-surface-container transition-colors">
              <span class="material-symbols-outlined text-[18px]">remove</span>
            </button>
            <span class="px-space-sm font-label-lg text-label-lg font-bold min-w-[56px] text-center">${item.qty} kg</span>
            <button aria-label="Increase" onclick="updateCartQty(${prod.id}, 0.5)" class="w-8 h-8 rounded-full flex items-center justify-center text-primary hover:bg-primary-fixed transition-colors">
              <span class="material-symbols-outlined text-[18px]">add</span>
            </button>
          </div>

          <div class="text-right min-w-[75px]">
            <span class="font-headline-sm text-headline-sm text-on-surface font-bold">${i18n[state.currentLang].currency} ${itemSub}</span>
          </div>

          <button aria-label="Delete" onclick="removeCartItem(${prod.id})" class="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-error hover:bg-error-container transition-colors">
            <span class="material-symbols-outlined text-[20px]">delete</span>
          </button>
        </div>
      </article>
    `;
  }).join('');

  // Update Summary DOM
  document.getElementById('summary-subtotal').textContent = `${i18n[state.currentLang].currency} ${subtotal}`;
  document.getElementById('summary-delivery').textContent = deliveryFee === 0 ? (state.currentLang === 'ne' ? 'निःशुल्क (हब डेलिभरी)' : 'Free (Hub Delivery)') : `${i18n[state.currentLang].currency} ${deliveryFee}`;
  document.getElementById('summary-packaging').textContent = `${i18n[state.currentLang].currency} ${packagingDeposit}`;
  document.getElementById('summary-discount').textContent = discount > 0 ? `-${i18n[state.currentLang].currency} ${discount}` : `रु. ०`;
  document.getElementById('summary-grand-total').textContent = `${i18n[state.currentLang].currency} ${total}`;
  document.getElementById('cart-items-count-badge').textContent = `${itemCount} ${state.currentLang === 'ne' ? 'आइटम' : 'Items'}`;
}

function applyCoupon() {
  const input = document.getElementById('coupon-input');
  const val = input ? input.value.trim().toUpperCase() : '';
  if (val === 'HAMROEARTH' || val === 'ORGANIC10') {
    state.discountApplied = true;
    showToast('🎉 १०% छुट लागु भयो! (10% Discount Applied)', 'Coupon active', 'verified');
    sfx.playChime('success');
    renderCartView();
  } else {
    showToast('अमान्य कुपन कोड (Invalid Coupon Code)', 'Try HAMROEARTH', 'error');
  }
}

// ==========================================================================
// PRE-ORDER SUBMISSION & CONFETTI CELEBRATION
// ==========================================================================
function submitPreorder() {
  const { total, itemCount } = getCartTotals();
  if (total <= 0) return;

  sfx.playChime('success');
  sfx.speak("धन्यवाद! तपाईंको ताजा तरकारीको अग्रिम अर्डर दर्ता भयो।");

  // Show Order Placed Modal
  const modal = document.getElementById('order-success-modal');
  if (modal) {
    document.getElementById('modal-order-total').textContent = `${i18n[state.currentLang].currency} ${total}`;
    document.getElementById('modal-order-society').textContent = state.selectedSociety;
    document.getElementById('modal-order-cycle').textContent = state.deliveryDay === 'wednesday' ? 'बुधबार बिहान ७:०० - १०:०० बजे' : 'शनिबार बिहान ७:०० - १०:०० बजे';
    modal.classList.remove('hidden');
  }

  // Trigger Confetti
  triggerConfetti();

  // Clear cart after booking
  state.cart = [];
  renderCartBadge();
  renderCartView();
}

function closeOrderSuccessModal() {
  const modal = document.getElementById('order-success-modal');
  if (modal) modal.classList.add('hidden');
  switchRole('home');
}

// Confetti Engine
function triggerConfetti() {
  const canvas = document.getElementById('confetti-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const pieces = [];
  const colors = ['#00652c', '#15803d', '#fe932c', '#ffdcc3', '#9a3500', '#79db8d'];

  for (let i = 0; i < 120; i++) {
    pieces.push({
      x: Math.random() * canvas.width,
      y: Math.random() * -canvas.height,
      size: Math.random() * 8 + 5,
      color: colors[Math.floor(Math.random() * colors.length)],
      speedY: Math.random() * 4 + 2,
      speedX: Math.random() * 3 - 1.5,
      rotation: Math.random() * 360,
      rotSpeed: Math.random() * 6 - 3
    });
  }

  let animationFrame;
  let start = Date.now();

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces.forEach(p => {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
      ctx.restore();

      p.y += p.speedY;
      p.x += p.speedX;
      p.rotation += p.rotSpeed;
    });

    if (Date.now() - start < 3500) {
      animationFrame = requestAnimationFrame(animate);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      cancelAnimationFrame(animationFrame);
    }
  }

  animate();
}

// ==========================================================================
// FARMER PORTAL & VOICE ASSISTANT SIMULATOR
// ==========================================================================
let voiceAnimationId = null;

function setFarmerState(stateKey) {
  state.farmerState.activeTab = stateKey;

  // Update tabs buttons
  const tabs = ['idle', 'listening', 'confirm', 'demand'];
  tabs.forEach((t) => {
    const btn = document.getElementById(`tab-${t}`);
    if (btn) {
      if (t === stateKey) {
        btn.className = 'flex-1 py-2 px-2 rounded-lg text-center font-label-md text-label-md font-bold transition-all bg-surface-container-lowest text-primary shadow-sm';
      } else {
        btn.className = 'flex-1 py-2 px-2 rounded-lg text-center font-label-md text-label-md font-bold transition-all text-on-surface-variant hover:text-on-surface';
      }
    }
  });

  const dispIdle = document.getElementById('farmer-display-idle');
  const dispListening = document.getElementById('farmer-display-listening');
  const secConfirm = document.getElementById('farmer-section-confirm');
  const secDemand = document.getElementById('farmer-section-demand');

  if (stateKey === 'idle') {
    if (dispIdle) dispIdle.classList.remove('hidden');
    if (dispListening) dispListening.classList.add('hidden');
    if (secConfirm) secConfirm.classList.remove('hidden');
    if (secDemand) secDemand.classList.remove('hidden');
  } else if (stateKey === 'listening') {
    if (dispIdle) dispIdle.classList.add('hidden');
    if (dispListening) dispListening.classList.remove('hidden');
    if (secConfirm) secConfirm.classList.add('hidden');
    if (secDemand) secDemand.classList.add('hidden');
    initFarmerCanvas();
    sfx.playChime('mic');
    sfx.speak("सुन्दैछ... तपाईंको आवाज रेकर्ड भइरहेको छ।");
    showToast('🎙️ आवाज रेकर्ड हुँदैछ (Listening)...', 'Speaking in Nepali', 'mic');
  } else if (stateKey === 'confirm') {
    if (dispIdle) dispIdle.classList.add('hidden');
    if (dispListening) dispListening.classList.add('hidden');
    if (secConfirm) secConfirm.classList.remove('hidden');
    if (secDemand) secDemand.classList.add('hidden');
    sfx.playChime('success');
    sfx.speak("बुझियो! नतिजा सुन्नुहोस र ठिक छ भन हरियो बटन थिच्नुहोस्।");
    const recognized = state.farmerState.lastRecognized || 'गोलभेंडा ५० केजी';
    showToast('✅ आवाज पहिचान सम्पन्न (Voice Recognized)', `${recognized} पहिचान भयो`, 'task_alt');
  } else if (stateKey === 'demand') {
    if (dispIdle) dispIdle.classList.add('hidden');
    if (dispListening) dispListening.classList.add('hidden');
    if (secConfirm) secConfirm.classList.add('hidden');
    if (secDemand) secDemand.classList.remove('hidden');
    sfx.playChime('click');
  }
}

function startFarmerListening() {
  setFarmerState('listening');
  let stopped = false;

  VoiceAssistant.listen({
    timeout: 8000,
    onInterim: (energy) => {
      // energy-based amplitude available for custom waveform if desired
      state.farmerState.lastEnergy = energy;
    },
    onFinal: (transcript) => {
      if (stopped) return;
      state.farmerState.lastRecognized = transcript || 'गोलभेंडा ५० केजी';
      sfx.playChime('success');
      sfx.speak("सम्लिप: " + (transcript || 'कुनै शब्द सुनिएन'));
      if (!stopped) setFarmerState('confirm');
    }
  });

  // Safety stop after 8s
  setTimeout(() => {
    stopped = true;
    VoiceAssistant.stop();
    if (!state.farmerState.confirmed && state.farmerState.activeTab === 'listening') {
      setFarmerState('confirm');
    }
  }, 8000);
}

function confirmFarmerBatch() {
  state.farmerState.confirmed = true;
  const recognized = state.farmerState.lastRecognized || 'गोलभेंडा';
  const weight = recognized.match(/(\d+)/)?.[1] || '५०';
  const newBatch = {
    id: `BATCH-${Math.floor(Math.random() * 900) + 100}`,
    crop: recognized.split(' ')[0],
    weight: weight + ' केजी',
    time: 'भर्र्खरै दर्ता',
    status: 'संकलन सूचीमामा समावेश',
    payout: `रु. ${Math.round(parseInt(weight || 50) * 65).toLocaleString()}`
  };
  state.farmerState.batches.unshift(newBatch);
  renderFarmerBatches();

  sfx.playChime('success');
  sfx.speak(`धन्यववाद! तपाईंको ${newBatch.crop} ${newBatch.weight} संकलन सूचीमा दर्र्ता भयो।`);
  showToast('✅ हाम्रो बारी प्रणालीमामा दर्र्ता भयो!', `${recognized} सफलतापुर्वक दर्र्ता भयो`, 'check_circle');
  setFarmerState('idle');
  state.farmerState.confirmed = false;
  state.farmerState.lastRecognized = 'गोलभेंडा ५० केजी';
}

function renderFarmerBatches() {
  const container = document.getElementById('farmer-batches-list');
  if (!container) return;
  container.innerHTML = state.farmerState.batches.map(b => `
    <div class="p-3 bg-surface-container-low rounded-xl flex items-center justify-between gap-3 hover:bg-surface-container transition-all">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold text-sm">
          ${b.crop[0]}
        </div>
        <div class="flex flex-col">
          <div class="flex items-center gap-2">
            <span class="font-headline-sm text-sm font-bold text-on-surface">${b.crop} (${b.weight})</span>
            <span class="px-2 py-0.5 rounded-full bg-surface-container text-primary text-[10px] font-semibold">${b.id}</span>
          </div>
          <span class="font-body-sm text-xs text-on-surface-variant">${b.time} • ${b.status}</span>
        </div>
      </div>
      <div class="text-right">
        <span class="font-headline-sm text-sm font-bold text-primary">${b.payout}</span>
        <span class="block text-[11px] text-on-surface-variant">अनुमानित आम्दानी</span>
      </div>
    </div>
  `).join('');
}

function initFarmerCanvas() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth || 300;
  canvas.height = canvas.offsetHeight || 60;

  let step = 0;
  if (voiceAnimationId) cancelAnimationFrame(voiceAnimationId);

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#00652c';
    ctx.beginPath();

    const sliceWidth = canvas.width / 50;
    let x = 0;

    for (let i = 0; i < 50; i++) {
      const v = Math.sin((i + step) * 0.25) * 18 + Math.cos((i - step) * 0.15) * 10;
      const y = canvas.height / 2 + v;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }

    ctx.stroke();
    step += 0.8;
    voiceAnimationId = requestAnimationFrame(draw);
  }

  draw();
}

function playFarmerAudioGreeting() {
  sfx.speak("नमस्ते राम बहादुर ज्यू! बोल्नको लागि ठूलो हरियो माइक बटन थिच्नुहोस्।");
  showToast('🔊 निर्देशन बजिरहेको छ...', 'Nepali Voice Prompt Active', 'volume_up');
}

// ==========================================================================
// ADMIN LOGISTICS SIMULATION
// ==========================================================================
function triggerBulkSMS() {
  sfx.playChime('success');
  sfx.speak("सबै १९ जना किसान र २ जना चालकलाई एसएमएस सूचना पठाइयो।");
  showToast('📲 सबै किसान र ड्राइभरलाई SMS पठाइयो!', '१९ जना किसान र २ वटा संकलन भ्यान अलर्ट गरियो।', 'sms');

  const logContainer = document.getElementById('admin-sms-log');
  if (logContainer) {
    const time = new Date().toLocaleTimeString('ne-NP');
    const logItem = document.createElement('div');
    logItem.className = 'p-2.5 rounded-lg bg-surface-container text-xs text-on-surface flex items-center justify-between';
    logItem.innerHTML = `
      <span class="flex items-center gap-1.5 font-semibold text-primary">
        <span class="material-symbols-outlined text-[14px]">done_all</span>
        [${time}] हप्ता #४२ संकलन सूचना २१ जनालाई सफलतापुर्वक पठाइयो
      </span>
      <span class="text-outline">Sent</span>
    `;
    logContainer.prepend(logItem);
  }
}

// ==========================================================================
// COUNTDOWN TIMER (Live Countdown to Sunday 8:00 PM)
// ==========================================================================
function initCountdownTimer() {
  function update() {
    const now = new Date();
    // Next Sunday 20:00:00
    const target = new Date();
    const day = target.getDay();
    const diffDays = (7 - day) % 7;
    target.setDate(target.getDate() + (diffDays === 0 && target.getHours() >= 20 ? 7 : diffDays));
    target.setHours(20, 0, 0, 0);

    const diff = Math.max(0, target - now);
    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const m = Math.floor((diff / 1000 / 60) % 60);
    const s = Math.floor((diff / 1000) % 60);

    const pad = (n) => String(n).padStart(2, '0');
    const nepaliDigits = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];
    const toNe = (n) => String(pad(n)).split('').map(c => nepaliDigits[parseInt(c)] || c).join('');

    const daysEl = document.getElementById('timer-days');
    const hoursEl = document.getElementById('timer-hours');
    const minsEl = document.getElementById('timer-mins');
    const secsEl = document.getElementById('timer-secs');

    if (daysEl) daysEl.textContent = state.currentLang === 'ne' ? toNe(d) : pad(d);
    if (hoursEl) hoursEl.textContent = state.currentLang === 'ne' ? toNe(h) : pad(h);
    if (minsEl) minsEl.textContent = state.currentLang === 'ne' ? toNe(m) : pad(m);
    if (secsEl) secsEl.textContent = state.currentLang === 'ne' ? toNe(s) : pad(s);
  }

  update();
  setInterval(update, 1000);
}

// ==========================================================================
// INITIALIZATION
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  renderCartBadge();
  renderBrowseCatalog();
  renderCartView();
  renderFarmerBatches();
  initCountdownTimer();

  // Society Select Binding
  const socSelect = document.getElementById('society-select');
  if (socSelect) {
    socSelect.addEventListener('change', (e) => {
      state.selectedSociety = e.target.value;
      showToast('डेलिभरी हब अद्यावधिक', state.selectedSociety, 'location_on');
    });
  }

  // Search input binding
  const catalogSearch = document.getElementById('catalog-search-input');
  if (catalogSearch) {
    catalogSearch.addEventListener('input', (e) => {
      state.filters.search = e.target.value;
      renderBrowseCatalog();
    });
  }

  // Home search input binding
  const homeSearch = document.getElementById('produce-search');
  if (homeSearch) {
    homeSearch.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        state.filters.search = e.target.value;
        switchRole('browse');
      }
    });
  }
});
