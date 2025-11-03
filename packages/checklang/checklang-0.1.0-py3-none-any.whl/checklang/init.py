import os
from ahserver.serverenv import ServerEnv
import fasttext
# 需先下载模型：https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

class LanguageChecker:
	def __init__(self):
		p = os.path.join(os.path.dirname(__file__), 'lid.176.ftz')
		print(f'model path={p}')
		self.model = fasttext.load_model(p)

	def checklang(self, text):
		pred = self.model.predict(text) 
		d = pred[0][0][9:]
		return {
			'lang':d
		}   

def get_languages():
	"""
	获取地球上主要人类语言列表
	返回值: [{'value': 'en', 'text': 'English'}, ...]
	"""
	languages = [
		{"value": "af", "text": "Afrikaans"},
		{"value": "am", "text": "Amharic"},
		{"value": "ar", "text": "Arabic"},
		{"value": "az", "text": "Azerbaijani"},
		{"value": "be", "text": "Belarusian"},
		{"value": "bg", "text": "Bulgarian"},
		{"value": "bn", "text": "Bengali"},
		{"value": "bo", "text": "Tibetan"},
		{"value": "bs", "text": "Bosnian"},
		{"value": "ca", "text": "Catalan"},
		{"value": "ceb", "text": "Cebuano"},
		{"value": "cs", "text": "Czech"},
		{"value": "cy", "text": "Welsh"},
		{"value": "da", "text": "Danish"},
		{"value": "de", "text": "German"},
		{"value": "dv", "text": "Dhivehi"},
		{"value": "el", "text": "Greek"},
		{"value": "en", "text": "English"},
		{"value": "eo", "text": "Esperanto"},
		{"value": "es", "text": "Spanish"},
		{"value": "et", "text": "Estonian"},
		{"value": "eu", "text": "Basque"},
		{"value": "fa", "text": "Persian"},
		{"value": "fi", "text": "Finnish"},
		{"value": "fil", "text": "Filipino"},
		{"value": "fr", "text": "French"},
		{"value": "fy", "text": "Frisian"},
		{"value": "ga", "text": "Irish"},
		{"value": "gd", "text": "Scottish Gaelic"},
		{"value": "gl", "text": "Galician"},
		{"value": "gu", "text": "Gujarati"},
		{"value": "ha", "text": "Hausa"},
		{"value": "haw", "text": "Hawaiian"},
		{"value": "he", "text": "Hebrew"},
		{"value": "hi", "text": "Hindi"},
		{"value": "hmn", "text": "Hmong"},
		{"value": "hr", "text": "Croatian"},
		{"value": "ht", "text": "Haitian Creole"},
		{"value": "hu", "text": "Hungarian"},
		{"value": "hy", "text": "Armenian"},
		{"value": "id", "text": "Indonesian"},
		{"value": "ig", "text": "Igbo"},
		{"value": "is", "text": "Icelandic"},
		{"value": "it", "text": "Italian"},
		{"value": "ja", "text": "Japanese"},
		{"value": "jv", "text": "Javanese"},
		{"value": "ka", "text": "Georgian"},
		{"value": "kk", "text": "Kazakh"},
		{"value": "km", "text": "Khmer"},
		{"value": "kn", "text": "Kannada"},
		{"value": "ko", "text": "Korean"},
		{"value": "ku", "text": "Kurdish"},
		{"value": "ky", "text": "Kyrgyz"},
		{"value": "la", "text": "Latin"},
		{"value": "lb", "text": "Luxembourgish"},
		{"value": "lo", "text": "Lao"},
		{"value": "lt", "text": "Lithuanian"},
		{"value": "lv", "text": "Latvian"},
		{"value": "mg", "text": "Malagasy"},
		{"value": "mi", "text": "Maori"},
		{"value": "mk", "text": "Macedonian"},
		{"value": "ml", "text": "Malayalam"},
		{"value": "mn", "text": "Mongolian"},
		{"value": "mr", "text": "Marathi"},
		{"value": "ms", "text": "Malay"},
		{"value": "mt", "text": "Maltese"},
		{"value": "my", "text": "Burmese"},
		{"value": "ne", "text": "Nepali"},
		{"value": "nl", "text": "Dutch"},
		{"value": "no", "text": "Norwegian"},
		{"value": "ny", "text": "Nyanja"},
		{"value": "or", "text": "Odia"},
		{"value": "pa", "text": "Punjabi"},
		{"value": "pl", "text": "Polish"},
		{"value": "ps", "text": "Pashto"},
		{"value": "pt", "text": "Portuguese"},
		{"value": "ro", "text": "Romanian"},
		{"value": "ru", "text": "Russian"},
		{"value": "rw", "text": "Kinyarwanda"},
		{"value": "sd", "text": "Sindhi"},
		{"value": "si", "text": "Sinhala"},
		{"value": "sk", "text": "Slovak"},
		{"value": "sl", "text": "Slovenian"},
		{"value": "sm", "text": "Samoan"},
		{"value": "sn", "text": "Shona"},
		{"value": "so", "text": "Somali"},
		{"value": "sq", "text": "Albanian"},
		{"value": "sr", "text": "Serbian"},
		{"value": "st", "text": "Sesotho"},
		{"value": "su", "text": "Sundanese"},
		{"value": "sv", "text": "Swedish"},
		{"value": "sw", "text": "Swahili"},
		{"value": "ta", "text": "Tamil"},
		{"value": "te", "text": "Telugu"},
		{"value": "tg", "text": "Tajik"},
		{"value": "th", "text": "Thai"},
		{"value": "ti", "text": "Tigrinya"},
		{"value": "tk", "text": "Turkmen"},
		{"value": "tl", "text": "Tagalog"},
		{"value": "tr", "text": "Turkish"},
		{"value": "tt", "text": "Tatar"},
		{"value": "ug", "text": "Uyghur"},
		{"value": "uk", "text": "Ukrainian"},
		{"value": "ur", "text": "Urdu"},
		{"value": "uz", "text": "Uzbek"},
		{"value": "vi", "text": "Vietnamese"},
		{"value": "xh", "text": "Xhosa"},
		{"value": "yi", "text": "Yiddish"},
		{"value": "yo", "text": "Yoruba"},
		{"value": "zh", "text": "Chinese"},
		{"value": "zu", "text": "Zulu"}
	]
	return languages

def load_checklang():
	env = ServerEnv()
	env.get_languages = get_languages
	env.language_checker = LanguageChecker()
