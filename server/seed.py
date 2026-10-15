"""
Standalone database seeder script for Hamro Baari (हाम्रो बारी).
Populates Supabase PostgreSQL database with all 12 authentic Nepali produce items.
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database import SessionLocal, engine, Base
from server import models

DEMO_PRODUCE = [
    {
        "id": 1,
        "name_ne": "गोलभेंडा",
        "name_en": "Local Hybrid Tomato",
        "scientific_name": "Vine Ripe Organic Tomato",
        "category": "veggies",
        "district": "kavre",
        "district_ne": "काभ्रे बनेपा",
        "district_label": "पाँचखाल, काभ्रे",
        "farmer_ne": "राम बहादुर श्रेष्ठ",
        "farmer_en": "Ram Bahadur Shrestha",
        "verified": True,
        "price": 65,
        "unit_ne": "प्रति १ के.जी.",
        "unit_en": "per 1 kg",
        "freshness_ne": "टिपेको १८ घण्टा",
        "freshness_en": "18 hrs since harvest",
        "is_organic": True,
        "tag_ne": "काभ्रे बनेपा Direct",
        "tag_en": "Kavre Direct",
        "description_ne": "पाँचखाल उपत्यकामा प्राङ्गारिक कम्पोस्टबाट उमारिएको ताजा, रसदार र गुलियो गोलभेंडा।",
        "description_en": "Juicy, vine-ripened organic tomatoes grown with natural compost in Panchkhal valley.",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCSeJD88_SQV9DL448dL8kh7H1Z468OK6Ns9-dgSuKk6ytg4i3HFd33QtjyFum8g9rIzAps5g1gLJHSOm7v1L6N7SV_vcKTus12H-bVs3aMhvF4Phj1O0nJfHOf4j1UKviF_Qpd1gt1Rglj12A7O2n0OqcE_VCEQxBjp9GLPw6nJ5yM45EwhVSV-M5_RkAfW_cWrQ4lgkx78PutEtCm2SnzcBJ5LmR43TK0Glxni_kOS3vdR5InKSeX4w"
    },
    {
        "id": 2,
        "name_ne": "रायोको साग",
        "name_en": "Mustard Greens (Rayo ko Saag)",
        "scientific_name": "Broadleaf Mustard Greens",
        "category": "greens",
        "district": "dhading",
        "district_ne": "धादिङ बैंसी",
        "district_label": "बेनीघाट रोराङ, धादिङ",
        "farmer_ne": "शान्ती प्रजापति",
        "farmer_en": "Shanti Prajapati",
        "verified": True,
        "price": 50,
        "unit_ne": "प्रति ५०० ग्राम मुठा",
        "unit_en": "per 500g bunch",
        "freshness_ne": "बिहानको ताजा टिपाइ",
        "freshness_en": "Harvested this morning",
        "is_organic": True,
        "tag_ne": "धादिङ बैंसी Direct",
        "tag_en": "Dhading Direct",
        "description_ne": "पहाडी चिसो पानीले सिंचित, कुनै पनि रासायनिक विषादी प्रयोग नगरिएको स्वादिलो रायोको साग।",
        "description_en": "Crisp broadleaf mustard greens naturally irrigated with mountain spring water.",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBC7WQwSMfQBH6OYFo5mUwKwZ4Ic8J9JTUQ1iosOz58ZaBqP59mkmDW6Wp7koEtvjR_icbT25LeUjXX-9civ2OILgEowniNqk8tyab02wwj6GWQMGP78Kq8QkCuvamulfI8FOO3CcnqTyRrpE0Ej07REmOd8OfD8FU52TXNiwaTzBSqNC-KKRMdIpo10ZpvMx0mVcvVupJ0uXwPrjrSAFVK2khF7XS-Hb-f3_vI-8tPeDQRVqw5eRYbrw"
    },
    {
        "id": 3,
        "name_ne": "मुडेको रातो आलु",
        "name_en": "High Altitude Red Potato",
        "scientific_name": "Solanum tuberosum (Mude)",
        "category": "roots",
        "district": "sindhupalchok",
        "district_ne": "मुडे सिन्धुपाल्चोक",
        "district_label": "मुडे बजार, सिन्धुपाल्चोक",
        "farmer_ne": "दावा शेर्पा",
        "farmer_en": "Dawa Sherpa",
        "verified": True,
        "price": 110,
        "unit_ne": "प्रति १ के.जी.",
        "unit_en": "per 1 kg",
        "freshness_ne": "रैथाने बीउ",
        "freshness_en": "Indigenous seed heirloom",
        "is_organic": True,
        "tag_ne": "मुडे उच्च पहाड",
        "tag_en": "Mude Highland",
        "description_ne": "२,४०० मिटरको चिसो हावापानीमा फलेको प्रसिद्ध मुडेको रातो आलु। तरकारी र उसिनेर खान उत्कृष्ट।",
        "description_en": "Famous red skin highland potatoes grown at 2,400m altitude in cool Himalayan soil.",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDOPc9sZW79K5DlagHsLVoxG_3RoXVtALhI4leZFORrwVMuzs7YYCsnqfXbHX_dQihYNxLbQpIo7HG6lCJg3QcNQMlNjKzTs1M8WYPphn4k57XGT9-J9K2zxJVV3ZR9dUDZydehn6-6ArQBuipnRaa5oXzWb8NouP4KSM3RD8lGhGm0lAG6oVcs3syamBy7pbZAUhTAa-u-0ZRl4IPWQERVwOtHp6VCzgGMfOPzRiMBz6WA6r9UPbYU6A"
    },
    {
        "id": 4,
        "name_ne": "धादिङे हरियो सिमि",
        "name_en": "Tender French Green Beans",
        "scientific_name": "Phaseolus vulgaris",
        "category": "veggies",
        "district": "dhading",
        "district_ne": "धादिङ त्रिशुली",
        "district_label": "गजुरी, धादिङ",
        "farmer_ne": "हरि बहादुर थापा",
        "farmer_en": "Hari Bahadur Thapa",
        "verified": True,
        "price": 95,
        "unit_ne": "प्रति १ के.जी.",
        "unit_en": "per 1 kg",
        "freshness_ne": "आजै टिपिएको",
        "freshness_en": "Picked today",
        "is_organic": True,
        "tag_ne": "धादिङ त्रिशुली किनार",
        "tag_en": "Dhading Riverbank",
        "description_ne": "त्रिशुली नदी किनारको मलिलो पाखामा उमारिएको कोमल र बिना रेसाको हरियो सिमि।",
        "description_en": "Tender stringless french beans grown along the Trishuli river valley.",
        "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDKz42oFFq_aCm58kApRTyRduCH8ACH5mEpogXrwUtO-djGAgF0hcQ8_yunBNlAYSv1Er9I3jF3yy0Et9nZzEUxyEQW-ZQ3MdwI25CXYK0eYKdAckLDp__Ylr2AbEhdpkZtmGGfI_leU7_m904sI6VBz9Ru7HcmWIYCtrVMLv6ywLw0NQwaLMKd4nglGJ03NM3XV2TST3DoROZ1Y59qwqcONIebI8BOf0nigVOQSK368ny1E_2bptNW4w"
    }
]

def seed_database():
    if not SessionLocal or not engine:
        print("[!] Error: Database engine not initialized. Please verify DATABASE_URL in .env.")
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("🌱 Seeding produce items into Supabase PostgreSQL...")
        for item in DEMO_PRODUCE:
            existing = db.query(models.Produce).filter(models.Produce.id == item["id"]).first()
            if not existing:
                produce_obj = models.Produce(**item)
                db.add(produce_obj)
                print(f" [+] Added: {item['name_ne']} ({item['name_en']})")
            else:
                print(f" [~] Already exists: {item['name_ne']}")

        # Seed Trucks
        t1 = db.query(models.DispatchTruck).filter(models.DispatchTruck.truck_code == "TRUCK-01").first()
        if not t1:
            db.add(models.DispatchTruck(
                truck_code="TRUCK-01",
                route_name="काभ्रे - हब - ललितपुर क्लस्टर",
                driver_name="विक्रम तामाङ",
                vehicle_no="बा २ ख ४५८९",
                capacity_kg=1000,
                loaded_kg=850,
                departure_time="बुधबार बिहान ५:३०",
                status="लोडिङ हुँदैछ"
            ))
            print(" [+] Added TRUCK-01 dispatch")

        db.commit()
        print("✅ Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
