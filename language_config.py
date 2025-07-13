#!/usr/bin/env python3
"""Comprehensive language configuration for Gemma3's 140+ language support."""

# Hierarchical language structure based on Gemma3's multilingual capabilities
LANGUAGE_HIERARCHY = {
    "Major Languages (High Fluency)": {
        "English": "en",
        "Spanish": "es", 
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Chinese (Simplified)": "zh-cn",
        "Chinese (Traditional)": "zh-tw",
        "Japanese": "ja",
        "Korean": "ko",
        "Arabic": "ar",
        "Hindi": "hi",
        "Dutch": "nl",
        "Polish": "pl",
        "Swedish": "sv",
        "Norwegian": "no",
        "Danish": "da",
        "Finnish": "fi"
    },
    
    "European Languages": {
        "Albanian": "sq",
        "Basque": "eu", 
        "Bulgarian": "bg",
        "Croatian": "hr",
        "Czech": "cs",
        "Estonian": "et",
        "Greek": "el",
        "Hungarian": "hu",
        "Icelandic": "is",
        "Irish": "ga",
        "Latvian": "lv",
        "Lithuanian": "lt",
        "Macedonian": "mk",
        "Maltese": "mt",
        "Romanian": "ro",
        "Serbian": "sr",
        "Slovak": "sk",
        "Slovenian": "sl",
        "Ukrainian": "uk",
        "Welsh": "cy"
    },
    
    "Asian Languages": {
        "Bengali": "bn",
        "Thai": "th",
        "Vietnamese": "vi",
        "Indonesian": "id",
        "Malay": "ms",
        "Filipino": "tl",
        "Tamil": "ta",
        "Telugu": "te",
        "Gujarati": "gu",
        "Marathi": "mr",
        "Urdu": "ur",
        "Persian": "fa",
        "Turkish": "tr",
        "Hebrew": "he",
        "Burmese": "my",
        "Khmer": "km",
        "Lao": "lo",
        "Mongolian": "mn",
        "Nepali": "ne",
        "Sinhala": "si"
    },
    
    "African Languages": {
        "Afrikaans": "af",
        "Amharic": "am",
        "Hausa": "ha",
        "Igbo": "ig",
        "Swahili": "sw",
        "Yoruba": "yo",
        "Zulu": "zu",
        "Xhosa": "xh",
        "Somali": "so",
        "Oromo": "om"
    },
    
    "Latin American Languages": {
        "Catalan": "ca",
        "Galician": "gl",
        "Quechua": "qu",
        "Guarani": "gn",
        "Aymara": "ay"
    },
    
    "Additional Supported Languages": {
        "Azerbaijani": "az",
        "Belarusian": "be",
        "Bosnian": "bs",
        "Georgian": "ka",
        "Kazakh": "kk",
        "Kyrgyz": "ky",
        "Luxembourgish": "lb",
        "Macedonian": "mk",
        "Moldovan": "mo",
        "Montenegrin": "cnr",
        "Tajik": "tg",
        "Turkmen": "tk",
        "Uzbek": "uz",
        "Armenian": "hy",
        "Kurdish": "ku",
        "Pashto": "ps",
        "Sindhi": "sd",
        "Sanskrit": "sa",
        "Tibetan": "bo",
        "Uyghur": "ug"
    }
}

# Flatten for easy access
ALL_LANGUAGES = {}
for category, languages in LANGUAGE_HIERARCHY.items():
    ALL_LANGUAGES.update(languages)

# Popular language pairs for translation
POPULAR_TRANSLATION_PAIRS = [
    ("en", "es"), ("en", "fr"), ("en", "de"), ("en", "it"), ("en", "pt"),
    ("en", "ru"), ("en", "zh-cn"), ("en", "ja"), ("en", "ko"), ("en", "ar"),
    ("en", "hi"), ("es", "pt"), ("fr", "de"), ("zh-cn", "ja"), ("ar", "fa")
]

def get_language_name(code):
    """Get language name from code."""
    for languages in LANGUAGE_HIERARCHY.values():
        for name, lang_code in languages.items():
            if lang_code == code:
                return name
    return code

def get_language_code(name):
    """Get language code from name."""
    return ALL_LANGUAGES.get(name, name.lower())

def generate_language_select_html(selected="en", id_prefix=""):
    """Generate hierarchical language select HTML."""
    html = f'<select id="{id_prefix}language" class="form-control language-select">\n'
    
    for category, languages in LANGUAGE_HIERARCHY.items():
        html += f'  <optgroup label="{category}">\n'
        for name, code in languages.items():
            selected_attr = 'selected' if code == selected else ''
            html += f'    <option value="{code}" {selected_attr}>{name}</option>\n'
        html += '  </optgroup>\n'
    
    html += '</select>'
    return html

def get_gemma3_language_capabilities():
    """Get Gemma3 specific language capabilities."""
    return {
        "total_languages": "140+",
        "high_fluency": len(LANGUAGE_HIERARCHY["Major Languages (High Fluency)"]),
        "tokenizer": "SentencePiece with 262K entries (optimized for CJK)",
        "training_data": "Double multilingual data vs Gemma 2",
        "context_window": "128K tokens",
        "special_strengths": [
            "Chinese, Japanese, Korean (improved tokenizer)",
            "Mathematical reasoning in multiple languages",
            "Cross-lingual understanding",
            "Low-resource language translation"
        ]
    }

def test_language_support(llm_provider, test_language="es"):
    """Test language support with a simple prompt."""
    test_prompt = f"Please respond in {get_language_name(test_language)}: Hello, how are you today?"
    try:
        response = llm_provider.generate_text(test_prompt, max_tokens=100)
        return {"success": True, "response": response, "language": test_language}
    except Exception as e:
        return {"success": False, "error": str(e), "language": test_language}