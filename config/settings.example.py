# =============================================
# Developer : ✘ 𝙍𝘼𝙑𝙀𝙉
# Telegram  : @P_X_24
# =============================================
# انسخ هذا الملف وسميه settings.py وضع قيمك الحقيقية
# Copy this file, rename it to settings.py and fill in your values

# توكن البوت - احصل عليه من @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# معرف المالك - ضع هنا الـ Telegram ID بتاعك
OWNER_ID = 0

# ─── Custom Emoji IDs ─────────────────────────────────────
EMOJI = {
    "wave":    "5402498632739996967",
    "shield":  "5805250158606162294",
    "warn":    "5363870079131872533",
    "check":   "5332533929020761310",
    "star":    "5053473385355412667",
    "pen":     "5197269100878907942",
    "money":   "5312441698347934993",
    "btn_list":     "5805250158606162294",
    "btn_super":    "5053473385355412667",
    "btn_ton":      "5312441698347934993",
    "btn_rules":    "5197269100878907942",
    "btn_scam":     "5375320925799475175",
    "btn_contact":  "4985902563262990693",
    "btn_panel":    "5258096772776991776",
    "btn_add":      "5461123669315048125",
    "btn_remove":   "5460847760615956009",
    "btn_crown":    "5965154754563677033",
    "btn_enable":   "5323787447165787608",
    "btn_disable":  "5981335554225081686",
    "btn_edit":     "5395444784611480792",
    "btn_stats":    "6084693581426069171",
    "btn_groups":   "5258513401784573443",
    "btn_back":     "5352759161945867747",
    "btn_refresh":  "5017470156276761427",
    "verified":     "5872921774991089124",
    "convert":      "5978846612087114958",
    "notify":       "5247215795255126185",
    "trusted":      "5967407877227288473",
    "untrusted":    "5454350746407419714",
    "banned":       "5462882007451185227",
    "rating":       "5951892127481860949",
    "search":       "5188217332748527444",
    "add_ban":      "5469798743043764619",
    "log":          "5843596438373667352",
    "del_ban":      "5384174292210566675",
    "alert":        "5384278638441023723",
    "btn_convert":  "5258500400918587241",
    "calendar":     "5028418466000930064",
    "num_1":   "5906854782588428238",
    "num_2":   "5906941528042904486",
    "num_3":   "5906642198887143657",
    "num_4":   "5906490608016431238",
    "ton_gem":  "5381975814415866082",
    "flag_us":  "5224321781321442532",
    "flag_eg":  "5228743673490977536",
    "clock":    "5384305778339366177",
    "arrow":    "5456327792868220208",
    "antenna":  "5877641725006057409",
}

TRIGGER_KEYWORDS = ["وسيط", "عايز وسيط", "في وسيط", "trustedmiddleman", "trusted middleman", "middleman"]
TON_KEYWORDS = ["1t", "1 t", "ton", "تون", "طون", "سعر تون", "سعر التون", "ton price", "toncoin"]
VERIFY_KEYWORDS = ["تحقق", "verify", "موثوق", "trusted"]
CONVERT_KEYWORDS = ["دولار", "جنيه", "usd", "egp", "dollar", "pound"]

COOLDOWN_SECONDS = 60
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd,egp"
BINANCE_API   = "https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT"
EXCHANGERATE_API = "https://open.er-api.com/v6/latest/USD"
DATABASE_FILE = "bot_data.json"
