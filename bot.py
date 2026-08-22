import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bypass import bypass_link

# ------------------ TOKEN ------------------
# Token bạn cung cấp (đã hardcode)
BOT_TOKEN = "8921957218:AAFCEqYBED26CTyp3vFxKpfU3m4dsFduBiI"
# Khuyến cáo: nên đọc từ biến môi trường để bảo mật tốt hơn
# BOT_TOKEN = os.getenv("BOT_TOKEN", BOT_TOKEN)
# -------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bypass Pro Bot*\n\n"
        "Gửi link rút gọn bất kỳ (adf.ly, link4m, ouo.io, v.v.)\n"
        "Bot sẽ tự động lấy link gốc KHÔNG cần captcha.\n"
        "Hỗ trợ: API bypass + Playwright headless.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Cách dùng:\n"
        "- Gửi link rút gọn trực tiếp.\n"
        "- Bot sẽ trả về link gốc sau vài giây.\n"
        "- Hỗ trợ: link4m, adf.ly, ouo.io, shorte.st, sh.st, v.v."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Vui lòng gửi link hợp lệ (bắt đầu bằng http:// hoặc https://)")
        return

    msg = await update.message.reply_text("⏳ Đang xử lý... (có thể mất 10-30 giây)")
    try:
        result = await bypass_link(url)
        if result:
            await msg.edit_text(f"✅ Link gốc:\n`{result}`", parse_mode='Markdown')
        else:
            await msg.edit_text("❌ Không thể bypass link này. Có thể link yêu cầu tương tác phức tạp.")
    except Exception as e:
        logger.error(f"Lỗi xử lý: {e}")
        await msg.edit_text(f"❌ Đã xảy ra lỗi: {str(e)[:100]}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()