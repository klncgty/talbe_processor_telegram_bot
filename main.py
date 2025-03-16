from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import json
import shutil
from processor import PDFTableProcessor
import zipfile
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = "oregon_processor_bot"

# Varsayılan formatı JSON olarak ayarla
DEFAULT_FORMAT = "json"

# Komut: /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['output_format'] = DEFAULT_FORMAT  # Kullanıcıya özel formatı sakla
    await update.message.reply_text("Merhaba! PDF veya görsel dosyalarınızdaki tabloları JSON veya CSV formatına dönüştürmek için buradayım. /help ile komutları görün.")

# Komut: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Komutlar:\n"
        "/start - Botu başlatır\n"
        "/help - Bu mesajı gösterir\n"
        "/process - Dosya işlemek için talimat verir\n"
        "/formats - Desteklenen formatları listeler\n"
        "/setformat - Çıktı formatını belirler (json veya csv)\n"
        "/status - İşlem durumunu gösterir\n"
        "/cancel - Devam eden işlemi iptal eder\n"
        "/info - Bot hakkında bilgi verir"
    )

# Komut: /process
async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Lütfen bir PDF dosyası gönder, seçtiğiniz formatta (" + context.user_data.get('output_format', DEFAULT_FORMAT) + ") işleyip geri döneyim.")

# Komut: /formats
async def formats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Desteklenen formatlar: JSON, CSV. Şu anki format: " + context.user_data.get('output_format', DEFAULT_FORMAT))

# Komut: /setformat
async def setformat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir format belirtin: /setformat json veya /setformat csv")
        return
    format_choice = context.args[0].lower()
    if format_choice in ["json", "csv"]:
        context.user_data['output_format'] = format_choice
        await update.message.reply_text(f"Çıktı formatı {format_choice} olarak ayarlandı.")
    else:
        await update.message.reply_text("Geçersiz format. Sadece 'json' veya 'csv' seçebilirsiniz.")

# Komut: /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'processing' in context.user_data:
        await update.message.reply_text("Şu anda bir dosya işleniyor, lütfen bekleyin.")
    else:
        await update.message.reply_text("Hiçbir işlem şu anda aktif değil.")

# Komut: /cancel
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'processing' in context.user_data:
        context.user_data.pop('processing')
        await update.message.reply_text("İşlem iptal edildi.")
    else:
        await update.message.reply_text("İptal edilecek bir işlem yok.")

# Komut: /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Oregon Processor Bot, v1.0. Şirketler için tablo işleme çözümü. Destek: [senin e-postan].")

# PDF işleme fonksiyonu
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['processing'] = True
    message = await update.message.reply_text("PDF'i işliyorum, lütfen bekle...")
    file = await update.message.document.get_file()
    file_path = f"temp_{update.message.message_id}.pdf"
    await file.download_to_drive(file_path)

    try:
        processor = PDFTableProcessor(file_path)
        total_tables = processor.total_tables
        if total_tables == 0:
            await message.edit_text("PDF'te tablo bulunamadı.")
            return

        output_dir = f"outputs_{update.message.message_id}"
        os.makedirs(output_dir, exist_ok=True)
        output_files = []
        
        # Kullanıcının seçtiği formatı al (varsayılan: JSON)
        output_format = context.user_data.get('output_format', DEFAULT_FORMAT)
        
        # Tabloları seçilen formatta işle
        for idx, result in enumerate(processor.process_tables(output_format=output_format)):
            if output_format == "json":
                json_file, image_path = result
                output_files.append(json_file)
            elif output_format == "csv":
                csv_file, image_path = result
                output_files.append(csv_file)

        # ZIP dosyası oluştur
        zip_path = f"outputs_{update.message.message_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in output_files:
                zipf.write(file, os.path.basename(file))

        # ZIP dosyasını gönder
        with open(zip_path, 'rb') as zip_file:
            await update.message.reply_document(document=zip_file, filename=f"tables_{update.message.message_id}.zip")
        await message.edit_text(f"PDF işlendi! {total_tables} tablo bulundu ve {output_format} formatında gönderildi.")

    except Exception as e:
        await message.edit_text(f"Bir hata oluştu: {str(e)}")
    finally:
        context.user_data.pop('processing', None)
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

# Ana fonksiyon
def main():
    print("Bot çalışıyor...")
    app = Application.builder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("process", process_command))
    app.add_handler(CommandHandler("formats", formats_command))
    app.add_handler(CommandHandler("setformat", setformat_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("info", info_command))

    # PDF dosyalarını yakala
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))

    # Botu başlat
    app.run_polling()

if __name__ == "__main__":
    main()