# Oregon Processor Bot

Telegram üzerinden PDF ve tablo fotoğraflarını JSON/CSV formatına çeviren bir bot.

## Özellikler
- PDF'den tablo çıkarır.
- Fotoğraflardan tablo işler (GOT-OCR2.0).
- JSON/CSV çıktı seçeneği.

## Kurulum
1. `git clone https://github.com/klncgty/oregon-processor-bot.git`
2. `cd oregon-processor-bot`
3. `poetry install`
4. `bot.py`'de `TOKEN`ı güncelle.
5. `poetry run python bot.py`

## Kullanım
- `/start` - Botu başlatır 🚀
- `/help` - Komutları gösterir ❓
- `/setformat [json|csv]` - Format seçer 🔧
- PDF veya fotoğraf gönder → ZIP dosyası al.

## Bağımlılıklar
- python-telegram-bot
- gmft
- matplotlib
- pillow
- pandas
- transformers

## İletişim
- çağatay - cgtyklnc@gmail.com
