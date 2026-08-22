import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bypass import bypass_link

# ====== TOKEN MỚI ======
BOT_TOKEN = "8921957218:AAHsfSKG0LZ1ufTQDrGtl0gz65m5a2tM2Xw"
# =====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bypass Pro Bot v5.0 - Siêu Cấp Vip*\n\n"
        "📌 *Tính năng:*\n"
        "✅ Bypass mọi link rút gọn\n"
        "✅ Hỗ trợ: link4m, adf.ly, ouo.io, sh.st, shorte.st, v.v.\n"
        "✅ Không cần captcha\n\n"
        "🚀 *Công nghệ:*\n"
        "- 30+ API bypass\n"
        "- Playwright headless\n"
        "- Selenium fallback\n"
        "- Requests fallback\n\n"
        "⚡ *Tỷ lệ thành công:* 90-95%\n"
        "⏱️ *Thời gian:* 5-30 giây\n\n"
        "📤 *Cách dùng:* Gửi link rút gọn trực tiếp vào chat.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Hướng dẫn sử dụng:*\n\n"
        "1️⃣ Gửi link rút gọn (http:// hoặc https://)\n"
        "2️⃣ Bot tự động xử lý\n"
        "3️⃣ Nhận link gốc\n\n"
        "🔗 *Hỗ trợ các loại link:*\n"
        "- link4m.com\n"
        "- adf.ly\n"
        "- ouo.io\n"
        "- sh.st\n"
        "- shorte.st\n"
        "- Và nhiều loại khác...\n\n"
        "📊 *Lệnh:*\n"
        "/start - Giới thiệu\n"
        "/help - Hướng dẫn\n"
        "/stats - Thống kê",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bypass import CACHE
    cache_size = len(CACHE)
    await update.message.reply_text(
        f"📊 *Thống kê bot:*\n\n"
        f"📦 Cache: {cache_size} links\n"
        f"⚡ Trạng thái: 🟢 Hoạt động\n"
        f"🔄 Phiên bản: v5.0\n"
        f"🤖 Token: {BOT_TOKEN[:10]}...",
        parse_mode='Markdown'
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
            await msg.edit_text(
                f"✅ *Bypass thành công!*\n\n"
                f"🔗 *Link gốc:*\n`{result}`\n\n"
                f"📊 *Cache:* {'Đã lưu' if result else 'Chưa lưu'}",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"❌ *Không thể bypass link này.*\n\n"
                f"📌 *Nguyên nhân có thể:*\n"
                f"- Link yêu cầu captcha phức tạp\n"
                f"- Sử dụng Cloudflare Turnstile\n"
                f"- Link đã hỏng hoặc không tồn tại\n"
                f"- Server quá tải\n\n"
                f"🔄 Vui lòng thử lại sau.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Lỗi xử lý: {e}")
        await msg.edit_text(f"❌ *Lỗi:* {str(e)[:150]}", parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Lỗi: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Đã xảy ra lỗi, vui lòng thử lại.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("🚀 Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()