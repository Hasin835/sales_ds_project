# Sales Data Science Project — Phase 1: Data Foundation

## Folder Structure
```
sales_ds_project/
├── data/
│   └── Sales_Data.xlsx          <- তোমার original file এখানে রাখো
├── scripts/
│   └── 01_reshape_and_clean.py  <- Phase 1 pipeline
├── outputs/                     <- script চালালে এখানে auto তৈরি হবে
└── requirements.txt
```

## VS Code-এ সেটআপ করার ধাপ

### ১. Python extension ইনস্টল
VS Code-এ **Extensions (Ctrl+Shift+X)** থেকে **"Python" (Microsoft)** extension ইনস্টল করো, যদি আগে থেকে না থাকে।

### ২. এই folder-টা VS Code-এ খোলো
`File > Open Folder` → `sales_ds_project` সিলেক্ট করো।

### ৩. Virtual environment বানাও (Terminal খুলে — Ctrl+` )
```bash
python -m venv venv
```
Activate করো:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

VS Code নিচের ডানে ভেনভ ডিটেক্ট করলে "Select Interpreter" popup আসবে — সেটাকে সিলেক্ট করো (অথবা `Ctrl+Shift+P` → "Python: Select Interpreter" → venv সিলেক্ট করো)।

### ৪. Dependencies ইনস্টল করো
```bash
pip install -r requirements.txt
```

### ৫. তোমার ডেটা ফাইল রাখো
`Sales_Data.xlsx` ফাইলটা `data/` ফোল্ডারে কপি করো (নাম ঠিক রাখতে হবে, নাহলে script-এর `INPUT_FILE` path বদলাও)।

### ৬. Script চালাও
Terminal-এ:
```bash
python scripts/01_reshape_and_clean.py
```
অথবা VS Code-এ script খুলে উপরে ডানে ▶ (Run) বাটনে ক্লিক করো।

### ৭. Output দেখো
`outputs/` ফোল্ডারে তৈরি হবে:
- `Sales_Data_Cleaned_Phase1.xlsx` — 5 sheet (Data_Quality_Report, Target_Gap_List, Zero_Achievers, Customer_Master, Clean_Activity_Level)
- `sales_long_format.csv`, `clean_activity_level.csv`, `customer_master.csv`

## পরের ধাপ (Phase 2 প্রস্তুতির জন্য)
`outputs/customer_master.csv` আর `outputs/clean_activity_level.csv` — এই দুইটাই পরের সব কাজের (segmentation, prediction) ভিত্তি হবে। Phase 2-তে যখন এগোবে, নতুন script (`02_segmentation.py`) `outputs/` থেকে এই CSV পড়েই কাজ শুরু করবে।
