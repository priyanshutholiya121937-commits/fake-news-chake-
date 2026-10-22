import os
import json
import re
import string
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Setup NLTK stopwords if available, else standard fallback set
try:
    import nltk
    from nltk.corpus import stopwords
    nltk.download('stopwords', quiet=True)
    STOPWORDS = set(stopwords.words('english'))
except Exception:
    STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
        "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
        'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
        'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
        'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
        'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
        'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd',
        'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
        "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
        'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't",
        'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't",
        'won', "won't", 'wouldn', "wouldn't"
    }

def clean_text(text: str) -> str:
    """Preprocess and clean input text for NLP."""
    if not isinstance(text, str):
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove stopwords
    tokens = [w for w in text.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(tokens)

def generate_sample_dataset() -> pd.DataFrame:
    """Create a curated, comprehensive fake vs real news training dataset."""
    data = [
        # --- REAL NEWS SAMPLES (label = 0 for Real) ---
        ("NASA James Webb Telescope Discovers Distant Galaxy", 
         "NASA's James Webb Space Telescope has captured deep-field observations of a galaxy formed just 300 million years after the Big Bang, astronomers confirmed in a peer-reviewed paper published in Nature Astronomy. Spectroscopic analysis confirmed high redshift and primitive star clusters.", 0),
        ("Federal Reserve Holds Interest Rates Steady Amid Inflation Data", 
         "The Federal Reserve announced on Wednesday that benchmark interest rates will remain unchanged at 5.25% to 5.50%. Federal Reserve Chairman Jerome Powell noted that while inflation has shown moderation toward the 2% target, central bank policymakers require sustained evidence before enacting monetary policy easing.", 0),
        ("European Union Approves Comprehensive AI Regulation Framework", 
         "European lawmakers voted overwhelmingly to adopt the Artificial Intelligence Act, setting global guardrails for high-risk AI deployments, facial recognition biometric categorization, and mandatory transparency for foundation models. Member states will enforce compliance over a 24-month phased period.", 0),
        ("World Health Organization Releases New Guidelines on Urban Air Quality", 
         "The World Health Organization (WHO) updated its ambient air quality benchmarks, urging member nations to reduce particulate matter PM2.5 exposure to protect public respiratory health. The report cited epidemiological data collected across 115 countries over seven years.", 0),
        ("Renewable Energy Surpasses 30% of Global Electricity Generation", 
         "The International Energy Agency (IEA) reported that global renewable electricity capacity reached historic milestones in 2024, driven by accelerated solar PV installations in Asia and offshore wind projects in the North Sea. Fossil fuel consumption for power generation declined by 1.4%.", 0),
        ("Global Semiconductor Supply Chain Stabilizes as New Fabs Open", 
         "Industry analysts report that global chip shortages have eased substantially following the commissioning of new semiconductor fabrication plants in Taiwan, Japan, and the United States. Automotive and consumer electronics lead times returned to pre-2020 averages.", 0),
        ("Astronomers Detect Repeating Fast Radio Bursts from Nearby Magnetar", 
         "A team of astrophysicists using the CHIME radio telescope recorded periodic milliseconds-long radio pulses originating from a galactic magnetar located approximately 30,000 light-years from Earth, shedding light on the physics of ultra-dense neutron stars.", 0),
        ("FDA Approves First Non-Invasive Continuous Blood Glucose Monitor", 
         "The US Food and Drug Administration granted approval for a next-generation optical continuous glucose monitoring system for adult diabetes management. Clinical trial results involving 2,400 patients demonstrated mean absolute relative difference of under 8%.", 0),
        ("United Nations Climate Summit Concludes with Carbon Market Accord", 
         "Delegates from 195 countries reached a consensus on Article 6 rules governing international carbon credit trading mechanisms at the COP summit. The agreement establishes centralized UN oversight for offset validation and double-counting prevention.", 0),
        ("Tokyo Stock Exchange Implements New Corporate Governance Disclosures", 
         "The Tokyo Stock Exchange introduced enhanced ESG and capital efficiency reporting requirements for Prime market listed firms. Japanese equities responded with positive trading volumes as international institutional investors welcomed the transparency reforms.", 0),
        ("Global Shipping Routes Rebound as Port Congestion Eases", 
         "Container freight rates have normalized across major trans-Pacific and Asia-Europe shipping corridors as container terminal dwell times dropped to three-year lows, according to the Baltic and International Maritime Council (BIMCO).", 0),
        ("Scientists Engineer Drought-Resilient Wheat Strains Using Gene Editing", 
         "Agricultural researchers at Rothamsted Research successfully concluded field trials for a CRISPR-modified wheat variant exhibiting 25% higher grain yield during prolonged dry spells without compromising protein content or baking quality.", 0),
        ("Quantum Computing Lab Achieves Fault-Tolerant Logical Qubit Benchmark", 
         "Researchers demonstrated quantum error correction with a 99.8% two-qubit gate fidelity, suppressing physical noise across 48 superconducting logical qubits, as reported in Physical Review Letters.", 0),
        ("Electric Vehicle Adoption Reaches Record Share in Northern Europe", 
         "Official transport ministry statistics show pure battery electric vehicles accounted for 88% of all new passenger car registrations last month, supported by comprehensive national charging infrastructure investments.", 0),
        ("Archaeologists Unearth Roman-Era Civic Forum in Spain", 
         "Excavations in southern Spain revealed well-preserved limestone colonnades, commemorative inscriptions, and municipal basilica foundations dating to the first century CE, offering fresh insights into provincial Roman administrative architecture.", 0),
        ("Bilingual Education Shows Measurable Cognitive Benefits in Long-Term Study", 
         "A 15-year longitudinal study conducted by Oxford University researchers found that early dual-language immersion enhances executive function and working memory capacity across diverse socioeconomic backgrounds.", 0),
        ("Global Cyber Defense Coalition Neutralizes Ransomware Syndicate Infrastructure", 
         "Law enforcement agencies including Europol and the FBI coordinated the seizure of command-and-control servers used by an international cybercrime cartel responsible for targeting critical healthcare infrastructure.", 0),
        ("Deep Sea Expedition Maps Unexplored Submarine Mountain Range", 
         "Oceanographers aboard the R/V Falkor discovered four massive seamounts rising over 3,000 meters from the ocean floor in the southeast Pacific, hosting dozens of previously undocumented deep-sea coral and sponge ecosystems.", 0),
        ("Major Airline Completes First Transatlantic Flight on 100% Sustainable Aviation Fuel", 
         "A commercial Boeing 787 powered entirely by hydroprocessed esters and fatty acids (HEFA) synthetic fuel landed safely at Heathrow, reducing lifecycle carbon emissions by an estimated 70% compared to conventional jet A-1 fuel.", 0),
        ("Central Banks Accelerate Cross-Border Wholesale Digital Currency Trials", 
         "Project Nexus, a multilateral payment network connecting central bank digital currency infrastructure across five Asian economies, completed real-time settlement tests with zero settlement risk.", 0),

        # --- FAKE NEWS SAMPLES (label = 1 for Fake) ---
        ("SHOCKING Secret Miracle Lemon Water Cures All Cancer Overnight Doctors BANNED It", 
         "Doctors are terrified! Big pharma is hiding this one weird trick: drinking boiled lemon juice with baking soda completely vaporizes all stage 4 tumors in under 24 hours! Government scientists tried to assassinate the herbal doctor who revealed the truth! Share this before Facebook deletes it!", 1),
        ("BREAKING Aliens Landed at Secret Military Base in Nevada Proof Confirmed by Leaked Tape", 
         "Deep state whistleblowers just leaked classified 8K footage showing living extraterrestrial beings shaking hands with top military generals in underground bunker Area 52. The mainstream media refuses to cover this world-changing event! Watch before it gets taken down forever!", 1),
        ("Secret 5G Towers Are Broadcasting Mind Control Frequencies to Turn Citizens into Slaves", 
         "Shocking secret documents reveal that all new telecom towers are actually electromagnetic mind control transmitters installed by globalist billionaires to manipulate brainwaves and force everyone to buy synthetic meat! Wear tin foil hats immediately!", 1),
        ("Pope Francis Arrested in Midnight Raid by Italian SWAT Team for Financial Conspiracy", 
         "Vatican in total blackout! Italian military commandos stormed the papal palace at 3 AM and arrested Pope Francis on 80 felony counts of global election interference and gold smuggling! Mass media is covering it up with fake live broadcasts!", 1),
        ("NASA Confirms Moon Is Actually Hollow Artificial Space Station Built by Ancient Giants", 
         "Secret Apollo transcripts declassified yesterday prove that when lunar modules crashed, the moon rang like a giant metal bell for three hours! Ancient astronauts built the moon as an observation satellite 50,000 years ago!", 1),
        ("Miracle Cryptocurrency Guaranteed to Make You a Multimillionaire in 48 Hours with Secret AI Algorithm", 
         "Elon Musk has launched a brand new automated quantum investment platform that guarantees 50,000% daily returns! Banks are trying to shut it down! Deposit $250 today and wake up tomorrow as a millionaire! Guaranteed zero risk!", 1),
        ("Government Secretly Adding Microchips into Tap Water to Track Everyone GPS Location", 
         "Anonymous whistleblower leaks video evidence showing government water treatment plants dumping millions of microscopic tracking nanobots into public municipal water supplies to monitor your thoughts and location 24/7!", 1),
        ("Famous Celebrity Faked Death and Is Currently Living in Secret Underground Bunker in Antarctica", 
         "Exclusive photos prove Michael Jackson and Elvis Presley are alive and well, running a luxury tropical resort inside a geothermal hollow beneath the Antarctic ice sheet funded by world elites!", 1),
        ("Ancient Egyptian Battery Discovered That Generates Unlimited Free Energy Perpetually", 
         "Scientists discovered a 4,000-year-old quartz battery that produces unlimited electricity forever with zero fuel! Power companies are spending billions to suppress this invention and burn the research labs!", 1),
        ("Eating Raw Garlic and Salt Cures All Heart Attacks in Under 3 Minutes Say Secret Whistleblowers", 
         "Cardiologists do not want you to know this simple ancient remedy! If someone is having a massive cardiac arrest, just shove 5 cloves of raw garlic into their mouth and they will immediately recover with 100% clean arteries!", 1),
        ("Massive Asteroid Guaranteed to Collide with Earth Next Tuesday Government Evacuating Billionaires", 
         "Astronomer leaks classified military memo: a 10-mile wide asteroid named Doomsday-X is on direct collision course with Earth! World leaders are quietly boarding subterranean bunkers while keeping citizens in the dark!", 1),
        ("Drinking Bleach Solution Daily Cleanses Toxins and Extends Human Lifespan to 150 Years", 
         "Renowned self-proclaimed guru reveals that diluted industrial bleach kills every pathogen and reverses human biological aging! Mainstream medical cartel is trying to silence this incredible discovery!", 1),
        ("Secret Quantum Satellite Will Erase All Student Debt and Bank Accounts at Midnight Tonight", 
         "Global financial reset NESARA/GESARA has been triggered! All credit cards, mortgages, and bank balances will be wiped clean tonight by a benevolent military space satellite! Claim your free gold bars now!", 1),
        ("Scientists Discover Real Living Dragons in Remote Amazon Rainforest Cave System", 
         "Expedition team films fire-breathing reptilian creatures with 40-foot wingspans living in volcanic cavern! National Geographic is covering up the expedition photos to protect evolutionary theory!", 1),
        ("Putting Onions in Your Socks Overnight Sucks Out All Deadly Toxins and Cures Diabetes", 
         "No more insulin needed! Big pharma has been lying to you for decades! Just slice a red onion and place it under your feet while sleeping to magnetically pull out all glucose and toxins through your soles!", 1),
        ("Billionaires Are Secretly Constructing Floating Cloud Cities to Escape Common People", 
         "Leaked blueprints show anti-gravity flying metropolis being built in the stratosphere where trillionaires will live above the clouds while leaving regular citizens on a polluted Earth! Shocking whistle-blower report!", 1),
        ("New Wi-Fi Signal Format Emits Sound Waves That Subliminally Compel People to Vote", 
         "Top secret intelligence leak shows routers are emitting ultrasonic brainwave manipulation signals that force unsuspecting internet users to change their political opinions while browsing social media!", 1),
        ("Eating Dirt from Your Backyard Gives Complete Immunity to All Known Viruses", 
         "Forget modern medicine! Soil contains primordial cosmic microbes that grant superhuman immune resistance against all diseases! Doctors are furious this natural secret got leaked to the public!", 1),
        ("Ancient Pyramids Were Actually Giant Wireless Power Transmitters Built by Reptilians", 
         "Declassified satellite imagery proves the Great Pyramids channeled atmospheric ionosphere energy to beam wireless electricity across the planet before evil cabals destroyed the receiving obelisks!", 1),
        ("If You Share This Post on Social Media You Will Receive $50,000 from Bill Gates Tomorrow", 
         "Bill Gates is giving away his entire fortune to random people who repost this picture within 10 minutes! Over 100,000 people have already received their wire transfers! Do not miss out on your share!", 1),
    ]

    # Augment with variations to create a robust dataset
    expanded_data = []
    # Add base data
    for title, text, label in data:
        expanded_data.append({"title": title, "text": text, "label": label})

    # Additional Real News Variations across categories
    real_topics = [
        ("World Meteorological Organization Confirms Record Ocean Heat Absorption", 
         "Marine temperature records exceeded historic averages for the 14th consecutive month, impacting coral reef ecosystems across equatorial latitudes. Climate researchers stress that ocean heat content serves as a fundamental indicator of planetary energy imbalance.", 0),
        ("Central Bank Interest Rate Cut Follows Cooled Consumer Price Index", 
         "The European Central Bank reduced its key deposit rate by 25 basis points following Eurostat data showing headline inflation fell to 2.2%. ECB President Christine Lagarde highlighted progress in domestic wage moderation during the monetary policy press conference.", 0),
        ("Clinical Trial Validates mRNA Vaccine Candidate for Pancreatic Cancer", 
         "Memorial Sloan Kettering Cancer Center published Phase 2 trial results demonstrating tailored neoantigen mRNA vaccines stimulated long-lasting T-cell immune responses, significantly delaying tumor recurrence in post-surgical patients.", 0),
        ("Autonomous Electric Ferries Begin Commercial Service in Stockholm", 
         "Sweden launched the world's first commercial zero-emission autonomous passenger ferry network across Stockholm's urban waterways, utilizing radar, lidar, and computerized vision systems for automated docking and collision avoidance.", 0),
        ("Global Biodiversity Treaty Establishes Protected Marine Sanctuaries", 
         "High Seas Treaty ratification crossed the necessary 60-nation threshold at the UN headquarters, establishing international legal mechanisms to conserve biodiversity in areas beyond national jurisdiction.", 0),
        ("Archaeologists Identify Pre-Inca Irrigation Terraces in Peruvian Andes", 
         "LiDAR aerial surveys in the Ayacucho valley revealed an intricate network of stone canal aqueducts and agricultural terraces constructed by the Wari civilization around 750 CE.", 0),
        ("New Battery Chemistry Achieves 1000 Cycles with Zero Cobalt", 
         "Materials scientists developed a high-energy density sodium-ion cathode utilizing abundant manganese and iron, cutting manufacturing costs by 40% while matching lithium iron phosphate cycle life.", 0),
        ("Global Food Security Index Shows Mixed Progress in Grain Distribution", 
         "The Food and Agriculture Organization (FAO) published its quarterly global food outlook, noting robust wheat harvest yields in Australia and North America offset by localized supply chain disruptions in sub-Saharan regions.", 0),
        ("NASA Mars Rover Collects Rock Core Containing Ancient Hydrothermal Mineral Deposits", 
         "The Perseverance rover successfully drilled and sealed its 24th geological core sample from Jezero Crater, containing silica-rich clays that formed in warm alkaline water billions of years ago.", 0),
        ("Supreme Court Delivers Unanimous Ruling on Digital Privacy and Device Searches", 
         "The high court held that law enforcement officers must obtain a judicial search warrant prior to accessing biometric data stored on encrypted consumer electronic devices during routine traffic stops.", 0)
    ]

    fake_topics = [
        ("EXPOSED Secret Cure for Blindness Made from Honey and Vinegar Doctors Don't Want You to Know", 
         "Put two drops of raw honey and apple cider vinegar directly into your eyes every morning to regrow your optic nerve and restore 20/20 vision in 3 days! Optometrists are threatening to sue the whistleblower!", 1),
        ("SHOCKING Leaked Video Proves the Earth Is Completely Flat and Surrounded by Giant Ice Walls", 
         "Antarctic military guards caught on hidden bodycam turning away private ships at gunpoint from the edge of the world! The global elite have been faking satellite photos with Photoshop since 1958!", 1),
        ("Billionaire Secret Society Drinking Youth Elixir Extracted from Volcanoes to Live Forever", 
         "An undercover butler reveals world leaders gather every full moon in underground caverns to drink glowing volcanic magma juice that prevents biological death! Share before this gets scrubbed!", 1),
        ("EMERGENCY Alert All Cell Phones Will Explode at Midnight Tonight Unless You Unplug Them", 
         "Dangerous electromagnetic cosmic pulse hitting Earth tonight will cause all lithium smartphone batteries to detonate instantly! Wrap your phone in aluminum foil and bury it in your garden immediately!", 1),
        ("Secret Government Weather Machine Unleashed Artificial Hurricanes to Target Opponents", 
         "HAARP scientists admit on deathbed that all major storms and blizzards are artificially created using ionized microwave beams to manipulate the jet stream and destroy private farms!", 1),
        ("Drinking Turmeric and Coconut Oil Instantly Regrows Missing Teeth and Cartilage in 48 Hours", 
         "Dentists are panicking! You will never need dental implants or fillings again! Just swish this miracle yellow potion in your mouth and watch brand new adult teeth sprout within 2 days!", 1),
        ("Proof Discovered That Dinosaurs Never Existed and Fossils Are Plaster Casts Made by Museums", 
         "Leaked museum receipts show millions spent annually fabricating fake T-Rex bones in secret warehouse facilities to promote evolutionary dogma and deceive the public! Wake up sheeple!", 1),
        ("Mysterious Pyramid Floating in Clouds Over New York City Caught on 4K Drone Camera", 
         "Shocked tourists recorded an enormous metallic flying mothership hovering silently above Manhattan before cloaking itself with artificial cloud vapor! Pentagons refusal to comment confirms cover-up!", 1),
        ("Secret Bank Glitch Gives Free $10,000 to Anyone Who Enters This ATM Code Combination", 
         "Former bank software engineer leaks secret master developer backdoor code! Press 9-9-9-Enter at any ATM and collect $10,000 cash instantly with no account deduction! Try before banks patch it!", 1),
        ("Microscopic Robot Parasites Discovered in Commercial Breakfast Cereal Brands", 
         "Microbiology student places cornflakes under microscope and films self-replicating nanomachines crawling inside food! Food agencies are bribed to keep silent while population is infected!", 1)
    ]

    for item in real_topics:
        expanded_data.append({"title": item[0], "text": item[1], "label": item[2]})
    for item in fake_topics:
        expanded_data.append({"title": item[0], "text": item[1], "label": item[2]})

    # Generate additional combinatorial samples for statistical diversity
    real_entities = ["NASA", "WHO", "European Union", "Federal Reserve", "MIT Researchers", "Stanford University", "Oxford University", "UN Climate Council", "Global Health Authority", "International Astronomical Union"]
    real_actions = ["publishes peer-reviewed findings on", "announces breakthrough data in", "completes multi-center clinical trial for", "establishes regulatory guidelines for", "reports significant decline in emissions from", "confirms successful validation of"]
    real_subjects = ["clean hydrogen energy storage systems", "mRNA therapeutic applications in oncology", "deep space spectroscopic measurements", "neurodegenerative disease early biomarkers", "sustainable agricultural crop resilience", "secure quantum communication protocols"]
    real_contexts = [
        "The findings, published in leading scientific journals, underwent rigorous double-blind peer review and independent replication across multiple research facilities.",
        "Officials emphasized that the policy recommendations are based on longitudinal data collected over a decade of empirical monitoring and statistical analysis.",
        "The research team observed statistically significant improvements with a p-value of less than 0.001 across all tested control cohorts.",
        "The international coalition plans to implement phased deployment over the next fiscal quarter in coordination with local regulatory bodies.",
        "Economic indicators and quarterly supply chain metrics confirmed a steady return to baseline operating efficiencies."
    ]

    for i in range(120):
        ent = real_entities[i % len(real_entities)]
        act = real_actions[i % len(real_actions)]
        subj = real_subjects[i % len(real_subjects)]
        ctx = real_contexts[i % len(real_contexts)]
        title = f"{ent} {act.capitalize()} {subj.title()}"
        text = f"{ent} announced that recent investigation into {subj} has demonstrated measurable progress. {ctx} Industry analysts and independent observers welcomed the development as a reliable benchmark for future standards."
        expanded_data.append({"title": title, "text": text, "label": 0})

    fake_triggers = ["SHOCKING LEAK:", "BREAKING SECRET:", "DOCTORS BANNED THIS:", "THEY ARE HIDING THIS:", "UNBELIEVABLE MIRACLE:", "PROOF CONFIRMED:"]
    fake_subjects = ["Miracle Lemon Tonic", "Ancient Energy Stone", "Secret 5G Frequency", "Hidden Alien Artifact", "Banned Herb Extract", "Invisible Space Mothership", "Government Mind Wave Device", "Magnetic Water Remedy"]
    fake_claims = ["Cures All Diseases Overnight With Zero Medicine", "Powers Entire Homes Forever For Free Without Electricity", "Controls Thoughts and Forces Citizens to Obey", "Proves Deep State Is Hiding Extraterrestrials", "Reverses Aging and Extends Lifespan to 200 Years", "Guarantees Millions in 24 Hours With Secret Loophole"]
    fake_contexts = [
        "Big pharma and corrupt politicians are trying to censor this video immediately! Share with everyone before it gets deleted from the internet!",
        "Doctors are in utter shock and pharmaceutical billionaires are threatening to sue the discoverer to protect their trillion-dollar profits!",
        "Mainstream media will never show you this classified footage! Open your eyes and wake up to the truth before it is too late!",
        "This secret ancient remedy has been suppressed for 2,000 years by the global elite to keep the population sick and obedient!",
        "Whistleblower risked their life to smuggle this secret memory card out of the military base! Guaranteed 100% real and verified!"
    ]

    for i in range(120):
        trig = fake_triggers[i % len(fake_triggers)]
        subj = fake_subjects[i % len(fake_subjects)]
        claim = fake_claims[i % len(fake_claims)]
        ctx = fake_contexts[i % len(fake_contexts)]
        title = f"{trig} {subj} {claim}"
        text = f"You won't believe what they just exposed! {subj} has been proven to {claim.lower()}. {ctx} Drink this, follow these secret instructions, and bypass all medical doctors completely!"
        expanded_data.append({"title": title, "text": text, "label": 1})

    df = pd.DataFrame(expanded_data)
    return df

def train_and_evaluate_models():
    """Train multiple models, compare metrics, and serialize the best model."""
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "fake_news.csv")
    model_dir = os.path.dirname(__file__)

    # Ensure dataset exists
    if not os.path.exists(dataset_path):
        print("Generating comprehensive fake news dataset...")
        df = generate_sample_dataset()
        df.to_csv(dataset_path, index=False)
        print(f"Dataset saved to {dataset_path} with {len(df)} records.")
    else:
        print(f"Loading existing dataset from {dataset_path}...")
        df = pd.read_csv(dataset_path)

    # Preprocess
    df.dropna(subset=['title', 'text', 'label'], inplace=True)
    df.drop_duplicates(inplace=True)
    df['combined_text'] = df['title'].astype(str) + " " + df['text'].astype(str)
    df['cleaned_text'] = df['combined_text'].apply(clean_text)

    # Split dataset
    X = df['cleaned_text']
    y = df['label'].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # TF-IDF Vectorization
    print("Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Define candidate models
    models = {
        "Logistic Regression": LogisticRegression(C=2.0, max_iter=1000, random_state=42),
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.5),
        "Linear SVM (Calibrated)": CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, dual=False))
    }

    results = {}
    best_model_name = None
    best_f1 = -1.0
    best_model_obj = None

    print("\n--- Model Training & Comparison ---")
    for name, model in models.items():
        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        results[name] = {
            "accuracy": round(float(acc) * 100, 2),
            "precision": round(float(prec) * 100, 2),
            "recall": round(float(rec) * 100, 2),
            "f1_score": round(float(f1) * 100, 2)
        }

        print(f"\nModel: {name}")
        print(f"  Accuracy:  {results[name]['accuracy']}%")
        print(f"  Precision: {results[name]['precision']}%")
        print(f"  Recall:    {results[name]['recall']}%")
        print(f"  F1 Score:  {results[name]['f1_score']}%")

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model

    print(f"\n>>> Selected Best Model: {best_model_name} (F1: {round(best_f1 * 100, 2)}%)")

    # Serialize files
    model_file = os.path.join(model_dir, "fake_news_model.pkl")
    vectorizer_file = os.path.join(model_dir, "tfidf_vectorizer.pkl")
    metadata_file = os.path.join(model_dir, "model_metadata.json")

    joblib.dump(best_model_obj, model_file)
    joblib.dump(vectorizer, vectorizer_file)

    metadata = {
        "best_model": best_model_name,
        "metrics": results[best_model_name],
        "all_model_comparison": results,
        "total_samples": len(df),
        "vocab_size": len(vectorizer.vocabulary_),
        "classes": ["LIKELY REAL", "LIKELY FAKE"],
        "timestamp": pd.Timestamp.now().isoformat()
    }

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"Model saved to {model_file}")
    print(f"Vectorizer saved to {vectorizer_file}")
    print(f"Metadata saved to {metadata_file}")
    return metadata

if __name__ == "__main__":
    train_and_evaluate_models()
