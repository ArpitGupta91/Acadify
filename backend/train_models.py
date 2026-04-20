import os

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Create models directory
os.makedirs("models", exist_ok=True)

# ===========================================================
# TRAINING DATA — INTENT CLASSIFIER
# Detects WHAT the user wants to do
# ===========================================================

INTENT_TRAINING_DATA = [
    # ── SYLLABUS intent ──────────────────────────────────────
    ("what is the syllabus", "syllabus"),
    ("show me syllabus", "syllabus"),
    ("syllabus of daa", "syllabus"),
    ("what topics are covered", "syllabus"),
    ("course content", "syllabus"),
    ("what is taught in", "syllabus"),
    ("units of database", "syllabus"),
    ("unit 1 of os", "syllabus"),
    ("topics in computer networks", "syllabus"),
    ("what are the units", "syllabus"),
    ("syllabus of 4th sem", "syllabus"),
    ("course structure", "syllabus"),
    ("tell me about the course", "syllabus"),
    ("what do we study in java", "syllabus"),
    ("sylabus of daa", "syllabus"),
    ("sillabus of os", "syllabus"),
    ("syllbus", "syllabus"),
    ("silabus of cn", "syllabus"),
    ("what is coverd in ai", "syllabus"),
    ("cours content of dbms", "syllabus"),
    ("unit wise topics", "syllabus"),
    ("chapter list", "syllabus"),
    ("what chapters are there", "syllabus"),
    ("tell me the chapters", "syllabus"),
    ("algorithim syllabus", "syllabus"),
    ("databse syllabus", "syllabus"),
    ("operatig system syllabus", "syllabus"),
    ("machin learning syllabus", "syllabus"),
    ("show units of web tech", "syllabus"),

    # ── MARKS intent ─────────────────────────────────────────
    ("marking scheme of daa", "marks"),
    ("how many marks", "marks"),
    ("total marks", "marks"),
    ("marks of computer networks", "marks"),
    ("mse marks", "marks"),
    ("ese marks", "marks"),
    ("ca marks", "marks"),
    ("internal marks", "marks"),
    ("external marks", "marks"),
    ("marking scheme", "marks"),
    ("marks distribution", "marks"),
    ("marks breakdown", "marks"),
    ("how is it evaluated", "marks"),
    ("evaluation scheme", "marks"),
    ("markin scheme", "marks"),
    ("makring scheme", "marks"),
    ("how much marks", "marks"),
    ("total marks of os", "marks"),
    ("marks for java", "marks"),
    ("mse1 marks", "marks"),
    ("mse2 marks", "marks"),
    ("ese marks of daa", "marks"),
    ("internal external marks", "marks"),
    ("marking sceme of dbms", "marks"),
    ("marks of databse", "marks"),
    ("how marks are given", "marks"),
    ("exam marks", "marks"),

    # ── CREDITS intent ───────────────────────────────────────
    ("how many credits", "credits"),
    ("credits of daa", "credits"),
    ("credit hours", "credits"),
    ("credit structure", "credits"),
    ("total credits", "credits"),
    ("credits in 4th sem", "credits"),
    ("how many credits does it carry", "credits"),
    ("what is the credit", "credits"),
    ("creidts of cn", "credits"),
    ("credts of os", "credits"),
    ("credit of java", "credits"),
    ("subject credits", "credits"),
    ("ltpc", "credits"),
    ("l t p c", "credits"),

    # ── TEXTBOOK intent ──────────────────────────────────────
    ("textbooks of daa", "textbook"),
    ("reference books", "textbook"),
    ("books for computer networks", "textbook"),
    ("recommended books", "textbook"),
    ("which book to follow", "textbook"),
    ("study material", "textbook"),
    ("textbok", "textbook"),
    ("refrence books", "textbook"),
    ("books to read", "textbook"),
    ("which textbook", "textbook"),
    ("book list", "textbook"),
    ("reading material", "textbook"),
    ("author of textbook", "textbook"),
    ("which author", "textbook"),

    # ── EXAM_SCHEDULE intent ─────────────────────────────────
    ("when is mse1", "exam_schedule"),
    ("when is mse2", "exam_schedule"),
    ("when is end semester", "exam_schedule"),
    ("exam dates", "exam_schedule"),
    ("exam schedule", "exam_schedule"),
    ("when are exams", "exam_schedule"),
    ("mse1 date", "exam_schedule"),
    ("ese date", "exam_schedule"),
    ("exam timetable", "exam_schedule"),
    ("when is the exam", "exam_schedule"),
    ("date of mse", "exam_schedule"),
    ("mid semester exam date", "exam_schedule"),
    ("end sem date", "exam_schedule"),
    ("wen is mse1", "exam_schedule"),
    ("when is ese", "exam_schedule"),
    ("practical exam date", "exam_schedule"),
    ("makeup exam", "exam_schedule"),
    ("when is makeup", "exam_schedule"),
    ("result date", "exam_schedule"),
    ("when is result", "exam_schedule"),
    ("result publication", "exam_schedule"),
    ("detention list", "exam_schedule"),
    ("grievance date", "exam_schedule"),

    # ── HOLIDAY intent ───────────────────────────────────────
    ("when is holi", "holiday"),
    ("holiday list", "holiday"),
    ("list of holidays", "holiday"),
    ("when is eid", "holiday"),
    ("when is republic day", "holiday"),
    ("holidays in march", "holiday"),
    ("how many holidays", "holiday"),
    ("college holiday", "holiday"),
    ("when is shivratri", "holiday"),
    ("ram navami holiday", "holiday"),
    ("when is bakrid", "holiday"),
    ("saturday holiday", "holiday"),
    ("is saturday off", "holiday"),
    ("holday list", "holiday"),
    ("holidys", "holiday"),
    ("hoilday", "holiday"),
    ("leave", "holiday"),
    ("days off", "holiday"),
    ("when is ambedkar jayanti", "holiday"),
    ("baisakhi holiday", "holiday"),

    # ── ATTENDANCE intent ────────────────────────────────────
    ("i attended 35 out of 50", "attendance"),
    ("how many classes to attend", "attendance"),
    ("attendance percentage", "attendance"),
    ("am i detained", "attendance"),
    ("will i be detained", "attendance"),
    ("75 percent attendance", "attendance"),
    ("how many classes can i miss", "attendance"),
    ("classes needed for 75", "attendance"),
    ("attendance calculator", "attendance"),
    ("attndance", "attendance"),
    ("atendance", "attendance"),
    ("how many bunk", "attendance"),
    ("can i bunk", "attendance"),
    ("i missed classes", "attendance"),
    ("present in 40 out of 60", "attendance"),
    ("shortage of attendance", "attendance"),
    ("attendance short", "attendance"),
    ("how many classes required", "attendance"),
    ("minimum attendance", "attendance"),
    ("detained due to attendance", "attendance"),

    # ── CGPA intent ──────────────────────────────────────────
    ("calculate cgpa", "cgpa"),
    ("what is my cgpa", "cgpa"),
    ("cgpa calculator", "cgpa"),
    ("how to calculate cgpa", "cgpa"),
    ("grade points", "cgpa"),
    ("grading system", "cgpa"),
    ("sgpa", "cgpa"),
    ("gpa calculation", "cgpa"),
    ("cgpa formula", "cgpa"),
    ("what grade do i need", "cgpa"),
    ("cgpa to percentage", "cgpa"),
    ("cumulative grade", "cgpa"),
    ("o grade points", "cgpa"),
    ("a plus grade", "cgpa"),

    # ── SUBJECTS_LIST intent ─────────────────────────────────
    ("subjects in 3rd sem", "subjects_list"),
    ("subjects in 4th semester", "subjects_list"),
    ("all subjects", "subjects_list"),
    ("list of subjects", "subjects_list"),
    ("what subjects do we have", "subjects_list"),
    ("course list", "subjects_list"),
    ("4th sem subjects", "subjects_list"),
    ("3rd semester courses", "subjects_list"),
    ("how many subjects", "subjects_list"),
    ("subject list", "subjects_list"),
    ("subjcts in 4th sem", "subjects_list"),
    ("which subjects in sem 3", "subjects_list"),
    ("semester subjects", "subjects_list"),

    # ── IMPORTANT_DATES intent ───────────────────────────────
    ("when does semester start", "important_dates"),
    ("last instructional day", "important_dates"),
    ("ca1 deadline", "important_dates"),
    ("ca2 upload deadline", "important_dates"),
    ("erp deadline", "important_dates"),
    ("semester start date", "important_dates"),
    ("when do classes start", "important_dates"),
    ("when does new semester begin", "important_dates"),
    ("academic calendar", "important_dates"),
    ("important dates", "important_dates"),
    ("semester end date", "important_dates"),
    ("last date", "important_dates"),
    ("submission deadline", "important_dates"),
    ("when is orientation", "important_dates"),

    # ── PREREQUISITES intent ─────────────────────────────────
    ("prerequisite for daa", "prerequisite"),
    ("what should i know before", "prerequisite"),
    ("pre requisite", "prerequisite"),
    ("required knowledge", "prerequisite"),
    ("what is needed for java", "prerequisite"),
    ("background required", "prerequisite"),

    # ── PROFESSIONAL_ELECTIVE intent ─────────────────────────
    ("which elective should i choose", "elective"),
    ("professional elective options", "elective"),
    ("pe1 options", "elective"),
    ("elective subjects", "elective"),
    ("which pe to choose", "elective"),
    ("react elective", "elective"),
    ("devops elective", "elective"),
    ("aws elective", "elective"),
    ("ios elective", "elective"),
    ("azure elective", "elective"),
    ("elective list", "elective"),
]

# ===========================================================
# TRAINING DATA — SUBJECT CLASSIFIER
# Detects WHICH subject user is asking about
# ===========================================================

SUBJECT_TRAINING_DATA = [
    # ── DATABASE SYSTEMS (IT301L) ────────────────────────────
    ("database systems", "IT301L"),
    ("dbms", "IT301L"),
    ("sql queries", "IT301L"),
    ("database management", "IT301L"),
    ("it301l", "IT301L"),
    ("rdbms", "IT301L"),
    ("relational database", "IT301L"),
    ("er diagram", "IT301L"),
    ("normalization", "IT301L"),
    ("acid properties", "IT301L"),
    ("pl sql", "IT301L"),
    ("stored procedure", "IT301L"),
    ("triggers database", "IT301L"),
    ("bcnf normalization", "IT301L"),
    ("3nf", "IT301L"),
    ("concurrency control", "IT301L"),
    ("transaction management", "IT301L"),

    # ── OPERATING SYSTEM (CS206L) ────────────────────────────
    ("operating system", "CS206L"),
    ("os", "CS206L"),
    ("cs206l", "CS206L"),
    ("process scheduling", "CS206L"),
    ("cpu scheduling", "CS206L"),
    ("deadlock", "CS206L"),
    ("memory management", "CS206L"),
    ("paging", "CS206L"),
    ("semaphore", "CS206L"),
    ("linux", "CS206L"),
    ("shell scripting", "CS206L"),
    ("operting system", "CS206L"),
    ("oprating systm", "CS206L"),
    ("operatig sys", "CS206L"),
    ("os concepts", "CS206L"),
    ("virtual memory", "CS206L"),
    ("page replacement", "CS206L"),
    ("process synchronization", "CS206L"),
    ("fcfs", "CS206L"),
    ("round robin", "CS206L"),
    ("bankers algorithm", "CS206L"),
    ("disk scheduling", "CS206L"),

    # ── OOP JAVA (CS301L) ────────────────────────────────────
    ("java", "CS301L"),
    ("object oriented programming", "CS301L"),
    ("oop", "CS301L"),
    ("cs301l", "CS301L"),
    ("spring boot", "CS301L"),
    ("servlet", "CS301L"),
    ("jdbc", "CS301L"),
    ("jvm", "CS301L"),
    ("inheritance", "CS301L"),
    ("polymorphism", "CS301L"),
    ("java collections", "CS301L"),
    ("oops", "CS301L"),
    ("jva", "CS301L"),
    ("jaava", "CS301L"),
    ("objct oriented", "CS301L"),
    ("lambda expression", "CS301L"),
    ("multithreading", "CS301L"),
    ("exception handling", "CS301L"),

    # ── PROBABILITY STATISTICS (MA105L) ─────────────────────
    ("probability and statistics", "MA105L"),
    ("probability", "MA105L"),
    ("statistics", "MA105L"),
    ("ma105l", "MA105L"),
    ("bayes theorem", "MA105L"),
    ("normal distribution", "MA105L"),
    ("regression analysis", "MA105L"),
    ("anova", "MA105L"),
    ("chi square", "MA105L"),
    ("probabilty", "MA105L"),
    ("statistcs", "MA105L"),
    ("probablity", "MA105L"),
    ("maths", "MA105L"),
    ("binomial distribution", "MA105L"),
    ("poisson distribution", "MA105L"),
    ("hypothesis testing", "MA105L"),

    # ── ADVANCE DATA STRUCTURE (CS302B) ─────────────────────
    ("advance data structure", "CS302B"),
    ("data structure", "CS302B"),
    ("ads", "CS302B"),
    ("cs302b", "CS302B"),
    ("binary tree", "CS302B"),
    ("avl tree", "CS302B"),
    ("graph traversal", "CS302B"),
    ("bfs dfs", "CS302B"),
    ("hashing", "CS302B"),
    ("trie", "CS302B"),
    ("heap", "CS302B"),
    ("data structur", "CS302B"),
    ("advanc data structure", "CS302B"),
    ("advnce data str", "CS302B"),
    ("linked list", "CS302B"),
    ("huffman coding", "CS302B"),
    ("topological sort", "CS302B"),

    # ── ARTIFICIAL INTELLIGENCE (CS205B) ────────────────────
    ("artificial intelligence", "CS205B"),
    ("ai and its applications", "CS205B"),
    ("cs205b", "CS205B"),
    ("search algorithms", "CS205B"),
    ("genetic algorithm", "CS205B"),
    ("reinforcement learning", "CS205B"),
    ("intelligent agents", "CS205B"),
    ("a star algorithm", "CS205B"),
    ("artifcial intellignce", "CS205B"),
    ("artficial intelligence", "CS205B"),
    ("aritficial intelligence", "CS205B"),
    ("bfs dfs ai", "CS205B"),
    ("minimax", "CS205B"),
    ("knowledge representation", "CS205B"),

    # ── DESIGN ANALYSIS ALGORITHMS (CS401L) ─────────────────
    ("design and analysis of algorithms", "CS401L"),
    ("daa", "CS401L"),
    ("algorithm", "CS401L"),
    ("cs401l", "CS401L"),
    ("greedy algorithm", "CS401L"),
    ("dynamic programming", "CS401L"),
    ("backtracking", "CS401L"),
    ("np completeness", "CS401L"),
    ("kmp algorithm", "CS401L"),
    ("dijkstra", "CS401L"),
    ("algoritm", "CS401L"),
    ("algorythm", "CS401L"),
    ("algorithim", "CS401L"),
    ("daa subject", "CS401L"),
    ("design n analysis", "CS401L"),
    ("knapsack", "CS401L"),
    ("prims algorithm", "CS401L"),
    ("kruskals algorithm", "CS401L"),
    ("string matching", "CS401L"),

    # ── COMPUTER NETWORKS (IT302L) ───────────────────────────
    ("computer networks", "IT302L"),
    ("networks", "IT302L"),
    ("cn", "IT302L"),
    ("it302l", "IT302L"),
    ("tcp ip", "IT302L"),
    ("osi model", "IT302L"),
    ("routing", "IT302L"),
    ("data link layer", "IT302L"),
    ("network layer", "IT302L"),
    ("ip addressing", "IT302L"),
    ("comp networks", "IT302L"),
    ("computer netwrk", "IT302L"),
    ("neworks", "IT302L"),
    ("netwrks", "IT302L"),
    ("subnetting", "IT302L"),
    ("ethernet", "IT302L"),
    ("http dns", "IT302L"),
    ("tcp udp", "IT302L"),

    # ── DATA ANALYTICS (IT202B) ──────────────────────────────
    ("da", "IT202B"),
    ("da syllabus", "IT202B"),
    ("da marks", "IT202B"),
    ("da subject", "IT202B"),
    ("data analytics", "IT202B"),
    ("data analytic", "IT202B"),
    ("analytics subject", "IT202B"),
    ("it202b", "IT202B"),
    ("hadoop spark", "IT202B"),
    ("power bi tableau", "IT202B"),
    ("big data analytics", "IT202B"),
    ("hadoop", "IT202B"),
    ("power bi", "IT202B"),
    ("tableau", "IT202B"),
    ("pandas numpy", "IT202B"),
    ("data cleaning", "IT202B"),
    ("big data", "IT202B"),
    ("mapreduce", "IT202B"),
    ("spark", "IT202B"),

    # ── ANN MACHINE LEARNING (CS303B) ───────────────────────
    ("ann and machine learning", "CS303B"),
    ("machine learning", "CS303B"),
    ("ann", "CS303B"),
    ("cs303b", "CS303B"),
    ("neural network", "CS303B"),
    ("mlp", "CS303B"),
    ("random forest", "CS303B"),
    ("svm", "CS303B"),
    ("knn", "CS303B"),
    ("deep learning", "CS303B"),
    ("machin learning", "CS303B"),
    ("machne lerning", "CS303B"),
    ("ml subject", "CS303B"),
    ("automl", "CS303B"),
    ("sklearn", "CS303B"),
    ("perceptron", "CS303B"),

    # ── WEB TECHNOLOGY (CS208B) ──────────────────────────────
    ("web technology", "CS208B"),
    ("web tech", "CS208B"),
    ("cs208b", "CS208B"),
    ("react", "CS208B"),
    ("flutter", "CS208B"),
    ("django", "CS208B"),
    ("flask", "CS208B"),
    ("javascript", "CS208B"),
    ("dart", "CS208B"),
    ("es6", "CS208B"),
    ("web technolgy", "CS208B"),
    ("webtechnology", "CS208B"),
    ("nodejs", "CS208B"),

    # ── UNIVERSAL HUMAN VALUES (HS112L) ─────────────────────
    ("universal human values", "HS112L"),
    ("human values", "HS112L"),
    ("hs112l", "HS112L"),
    ("value education", "HS112L"),
    ("ethics", "HS112L"),
    ("humaan values", "HS112L"),

    # ── CONSTITUTION OF INDIA (HS109L) ───────────────────────
    ("constitution of india", "HS109L"),
    ("constitution", "HS109L"),
    ("hs109l", "HS109L"),
    ("indian constitution", "HS109L"),
    ("fundamental rights", "HS109L"),
    ("constitushn", "HS109L"),

    # ── APTITUDE (HS113L) ────────────────────────────────────
    ("aptitude", "HS113L"),
    ("aptitude 2", "HS113L"),
    ("hs113l", "HS113L"),
    ("logical reasoning", "HS113L"),
    ("quantitative aptitude", "HS113L"),

    # ── SOFT SKILLS (HS114L) ────────────────────────────────
    ("soft skills", "HS114L"),
    ("hs114l", "HS114L"),
    ("communication skills", "HS114L"),
    ("soft skill", "HS114L"),

    # ── PROFESSIONAL ELECTIVES ───────────────────────────────
    ("react nextjs", "CS318E"),
    ("frontend engineering", "CS318E"),
    ("cs318e", "CS318E"),
    ("devops", "CS304E"),
    ("cs304e", "CS304E"),
    ("intelligent systems text vision", "CS307E"),
    ("cs307e", "CS307E"),
    ("aws foundations", "CS335E"),
    ("cs335e", "CS335E"),
    ("ios app development", "CS321E"),
    ("swift programming", "CS321E"),
    ("cs321e", "CS321E"),
    ("microsoft azure", "IT306E"),
    ("azure fundamentals", "IT306E"),
    ("it306e", "IT306E"),
]

# ===========================================================
# TRAIN INTENT CLASSIFIER
# ===========================================================

print("=" * 50)
print("Training Intent Classifier...")
print("=" * 50)

intent_texts = [item[0] for item in INTENT_TRAINING_DATA]
intent_labels = [item[1] for item in INTENT_TRAINING_DATA]

intent_pipeline = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            analyzer="char_wb",
            min_df=1,
        ),
    ),
    (
        "clf",
        LogisticRegression(
            max_iter=1000,
            C=5.0,
            random_state=42,
        ),
    ),
])

# Train on ALL data (small dataset, no need for split)
intent_pipeline.fit(intent_texts, intent_labels)

# Quick accuracy check
predictions = intent_pipeline.predict(intent_texts)
correct = sum(p == l for p, l in zip(predictions, intent_labels))
print(f"Intent Classifier Training Accuracy: {correct}/{len(intent_labels)} ({100 * correct // len(intent_labels)}%)")

# Save
joblib.dump(intent_pipeline, "models/intent_classifier.pkl")
print("Saved: models/intent_classifier.pkl")

# ===========================================================
# TRAIN SUBJECT CLASSIFIER
# ===========================================================

print()
print("=" * 50)
print("Training Subject Classifier...")
print("=" * 50)

subject_texts = [item[0] for item in SUBJECT_TRAINING_DATA]
subject_labels = [item[1] for item in SUBJECT_TRAINING_DATA]

subject_pipeline = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            analyzer="char_wb",
            min_df=1,
        ),
    ),
    (
        "clf",
        LogisticRegression(
            max_iter=1000,
            C=5.0,
            random_state=42,
        ),
    ),
])

subject_pipeline.fit(subject_texts, subject_labels)

predictions = subject_pipeline.predict(subject_texts)
correct = sum(p == l for p, l in zip(predictions, subject_labels))
print(f"Subject Classifier Training Accuracy: {correct}/{len(subject_labels)} ({100 * correct // len(subject_labels)}%)")

joblib.dump(subject_pipeline, "models/subject_classifier.pkl")
print("Saved: models/subject_classifier.pkl")

# ===========================================================
# TEST THE MODELS WITH SAMPLE QUERIES
# ===========================================================

print()
print("=" * 50)
print("Testing with misspelled queries...")
print("=" * 50)

test_queries = [
    ("algoritm syllabus", "syllabus", "CS401L"),
    ("databse marking scheme", "marks", "IT301L"),
    ("operting system credits", "credits", "CS206L"),
    ("comp netwrks textbook", "textbook", "IT302L"),
    ("machin lerning units", "syllabus", "CS303B"),
    ("when is mse1", "exam_schedule", None),
    ("i attended 35 out of 50 classes", "attendance", None),
    ("holiday list", "holiday", None),
    ("how many credits does daa carry", "credits", "CS401L"),
    ("probabilty textbooks", "textbook", "MA105L"),
]

print(f"{'Query':<40} {'Intent':^15} {'Subject':^10}")
print("-" * 70)

for query, expected_intent, expected_subject in test_queries:
    pred_intent = intent_pipeline.predict([query])[0]
    pred_subject = subject_pipeline.predict([query])[0]

    intent_ok = "✅" if pred_intent == expected_intent else "❌"
    subject_ok = "✅" if (expected_subject is None or pred_subject == expected_subject) else "❌"

    print(f"{query:<40} {pred_intent:^15}{intent_ok} {pred_subject:^10}{subject_ok}")

print()
print("Model training complete! Files saved in models/ folder.")
print("Run backend with: uvicorn backend.main:app --reload")
