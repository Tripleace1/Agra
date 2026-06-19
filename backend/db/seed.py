"""Seed Agra SQLite DB with crop tolerances and agricultural advisories."""
from __future__ import annotations

import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "schema.sql"
DB = HERE / "agra.sqlite"


CROPS = [
    # name, name_yo, ph_min, ph_max, n_min, n_max, p_min, p_max, k_min, k_max, soil_types, season_notes, season_notes_yo
    ("Maize", "Agbado", 5.5, 7.5, 20, 60, 15, 40, 80, 200, "loamy,sandy,silt", "Plant at start of rainy season; 90-120 day cycle.", "Gbin ni ibere ti akoko ojo; oja ojo 90-120."),
    ("Cassava", "Ege", 4.5, 7.0, 10, 40, 10, 30, 40, 150, "sandy,loamy", "Tolerates poor soils; harvest 9-12 months.", "Faramo ile alaini; ikore osu 9-12."),
    ("Yam", "Isu", 5.5, 6.5, 25, 50, 20, 35, 100, 180, "loamy,silt", "Needs deep tilled mounds; rainy season planting.", "Nilo ebe jinle; gbin lakoko ojo."),
    ("Rice (upland)", "Iresi", 5.5, 6.5, 30, 80, 20, 50, 80, 160, "loamy,clay", "Steady moisture required; 100-130 day cycle.", "Nilo omi ti o duro; oja 100-130 ojo."),
    ("Sorghum", "Oka baba", 5.5, 7.5, 20, 50, 15, 35, 70, 150, "sandy,loamy", "Drought tolerant; ideal for drier regions.", "Faramo gbigbona; dara fun agbegbe gbigbe."),
    ("Cowpea", "Ewa", 5.5, 7.0, 10, 25, 15, 35, 60, 140, "sandy,loamy", "Nitrogen-fixing legume; 60-90 day cycle.", "Ewa ti n da nitrogen sile; ojo 60-90."),
    ("Groundnut", "Epa", 5.5, 7.0, 10, 30, 20, 40, 80, 160, "sandy,loamy", "Sandy loam preferred; legume rotation crop.", "Iyanrin loamy dara; gbin pelu yiyi-irugbin."),
    ("Tomato", "Tomati", 6.0, 6.8, 30, 70, 25, 50, 100, 220, "loamy,silt", "Stake; needs steady water; 60-80 day cycle.", "Lo igi atileyin; nilo omi to peye; ojo 60-80."),
    ("Pepper", "Ata", 5.5, 7.0, 25, 60, 20, 45, 90, 200, "loamy,sandy", "Warm season crop; mulch to conserve moisture.", "Irugbin akoko gbona; bo ile lati pa omi mo."),
    ("Okra", "Ila", 6.0, 7.0, 25, 55, 20, 40, 90, 180, "loamy,sandy", "Fast 50-65 day cycle; harvest pods young.", "Yara po, ojo 50-65; ka eso re tete."),
    ("Sweet potato", "Anamo", 5.5, 6.5, 15, 35, 20, 40, 100, 200, "sandy,loamy", "Ridge planting; 90-120 day cycle.", "Gbin lori ebe; ojo 90-120."),
    ("Plantain", "Ogede agbagba", 5.5, 7.0, 30, 70, 20, 45, 150, 300, "loamy,silt", "Perennial; mulch heavily; needs steady rain.", "Ti odoodun; bo ile pupo; nilo ojo to duro."),
]


ADVISORIES = [
    # (title, category, lang, body)
    ("Nitrogen deficiency symptoms", "soil",  "en", "Low nitrogen causes yellowing of older leaves, stunted growth, and reduced yield. Apply well-rotted compost, plant nitrogen-fixing cover crops such as cowpea or mucuna, or use urea sparingly at 50-100 kg/ha split-applied."),
    ("Phosphorus deficiency symptoms", "soil","en", "Phosphorus shortage shows as purplish leaf tints and poor root development. Apply rock phosphate or bone meal before planting and incorporate into top 15 cm of soil."),
    ("Potassium deficiency symptoms", "soil", "en", "Potassium-deficient plants show leaf-edge scorching and weak stems. Apply wood ash sparingly (pH risk) or muriate of potash at 50-80 kg/ha."),
    ("Soil pH correction", "soil", "en", "Acidic soils (pH < 5.5) benefit from agricultural lime at 1-3 t/ha. Alkaline soils (pH > 7.5) benefit from elemental sulfur or composted organic matter to lower pH gradually."),
    ("Maize pest: fall armyworm", "pest", "en", "Scout fields weekly. Hand-pick larvae early morning. Apply neem extract (50 g/L water) at first sign. Avoid mono-cropping; rotate with legumes."),
    ("Cassava mosaic disease", "pest", "en", "Use certified clean cuttings. Remove and burn infected plants. Control whitefly vectors with neem or sticky yellow traps."),
    ("Tomato blight management", "pest", "en", "Late blight thrives in humid conditions. Stake plants for airflow, prune lower leaves, water at base only. Apply copper-based fungicide weekly if outbreak begins."),
    ("Crop rotation basics", "rotation", "en", "Rotate heavy feeders (maize, tomato) with legumes (cowpea, groundnut) to restore nitrogen. Avoid planting the same family in succession to break pest cycles."),
    ("Drip irrigation best practices", "irrigation", "en", "Drip systems save 30-60% water versus flood irrigation. Run early morning to reduce evaporation. Flush lines weekly to prevent clogging."),
    ("Mulching for moisture retention", "irrigation", "en", "Apply 5-10 cm of dry grass, straw, or leaves around plants to reduce evaporation and suppress weeds. Keep mulch 5 cm away from stems to prevent rot."),
    ("Composting fundamentals", "soil", "en", "Layer green (kitchen scraps, fresh leaves) and brown (dry leaves, straw) material at 1:3 ratio. Turn pile every 2 weeks. Ready in 6-10 weeks when dark and crumbly."),
    ("Planting calendar Nigeria", "season", "en", "Southern Nigeria: early rains April-July for maize/cassava; late rains September-October for cowpea/vegetables. Northern Nigeria: single rainy season May-September."),
    ("Yam mound preparation", "soil", "en", "Build mounds 60-90 cm tall with topsoil. Add compost to core. Plant one seed yam per mound after first reliable rain."),

    # Yoruba
    ("Aami ti aini Nitrogen", "soil", "yo", "Aini nitrogen n fa ki ewe atijo di pupa, idagba kuru, ati ikore ti ko peye. Lo compost ti o ti pon dada, gbin irugbin bii ewa tabi mucuna, tabi lo urea diedie ni 50-100 kg/ha."),
    ("Aami ti aini Phosphorus", "soil", "yo", "Aini phosphorus n fa awo eleyii lori ewe ati ki gbongbo ma se da ru. Lo rock phosphate tabi iyo egungun ki o to gbin, fi sinu ile centimita 15 oke."),
    ("Aami ti aini Potassium", "soil", "yo", "Eweko ti ko ni potassium ni eti ewe ti o ti gbe ati igi alailagbara. Lo eeru igi diedie tabi muriate of potash ni 50-80 kg/ha."),
    ("Atunse pH ile", "soil", "yo", "Ile alajaja (pH labe 5.5) nilo ikan ile ni 1-3 t/ha. Ile mimo (pH ju 7.5) nilo sulfur tabi compost lati doje pH die."),
    ("Itoju kokoro Agbado: armyworm", "pest", "yo", "Wo oko re ni gbogbo ose. Mu kokoro pelu owo ni owuro. Lo neem (50 g ni omi lita kan) ni ami akoko. Ma gbin nikan, yi pelu ewa."),
    ("Arun Ege: cassava mosaic", "pest", "yo", "Lo eso ege mimo lati gbin. Yo ki o si jo ohun ti aisan ti ba je. Wa whitefly pelu neem tabi awo ofeefee."),
    ("Itoju arun Tomati", "pest", "yo", "Late blight n yara po ninu omi. Lo igi atileyin, ge ewe isale, fi omi le isale nikan. Lo fungicide bi o tile bere ni gbogbo ose."),
    ("Ipilese yiyi irugbin", "rotation", "yo", "Yi irugbin ti o n je pupo (agbado, tomati) pelu ewa (cowpea, epa) lati pada nitrogen sile. Ma gbin idile irugbin kanna leralera."),
    ("Iwosan drip irigeesonu", "irrigation", "yo", "Eto drip n fipa omi 30-60% jo ikun-omi. Lo ni owuro lati din omi ti n yo. Wo opo ni gbogbo ose ki o ma di."),
    ("Mulching fun titoju omi", "irrigation", "yo", "Lo koriko gbigbe tabi ewe centimita 5-10 yi eweko ka lati din omi ti n yo ati lati pa egbo. Fi mulch silẹ centimita 5 si igi."),
    ("Ipilese compost", "soil", "yo", "Ko awo elewe (eso idana, ewe tutu) ati awo gbigbe (ewe gbigbe, koriko) ni 1:3. Yi ni gbogbo ose meji. Yoo ti ye ni ose 6-10."),
    ("Akoko gbingbin Naijiria", "season", "yo", "Guusu Naijiria: ojo tete April-July fun agbado/ege; ojo pe September-October fun ewa/eweko. Ariwa Naijiria: akoko ojo kan May-September."),
    ("Ipilese ebe Isu", "soil", "yo", "Gbe ebe ti o ga centimita 60-90 pelu ile oke. Fi compost si arin. Gbin eso isu kan fun ebe kan leyin ojo akoko."),
]


def init_db():
    if DB.exists():
        DB.unlink()
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    with open(SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.executemany(
        """INSERT INTO crops (name, name_yo, ph_min, ph_max, n_min, n_max,
                              p_min, p_max, k_min, k_max, soil_types,
                              season_notes, season_notes_yo)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        CROPS,
    )
    conn.executemany(
        "INSERT INTO advisories (title, category, lang, body) VALUES (?,?,?,?)",
        ADVISORIES,
    )
    conn.commit()
    conn.close()
    print(f"Seeded {DB} : {len(CROPS)} crops, {len(ADVISORIES)} advisories")


if __name__ == "__main__":
    init_db()
