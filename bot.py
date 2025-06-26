from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
import json
import os

# Token bot Telegram kamu
BOT_TOKEN = "7979155836:AAHKdWhjZLKRx84lPwGMAeKPF3Ni2UOmDCU"
PASSWORD = os.getenv("PASSWORD", "1722")
KEYPAIR_FILE = "dev_wallet.json"
authorized_users = set()

# Load Keypair dari file
with open(KEYPAIR_FILE, "r") as f:
    secret = json.load(f)
    keypair = Keypair.from_secret_key(bytes(secret))

# Command /start untuk autentikasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if user_id in authorized_users or (args and args[0] == PASSWORD):
        authorized_users.add(user_id)
        await update.message.reply_text("✅ Akses diberikan.")
        await show_main_menu(update)
    else:
        await update.message.reply_text("❌ Akses ditolak. Gunakan /start 1722")

# Tampilkan menu utama
async def show_main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("CreateCoin 🪙", callback_data="createcoin"),
         InlineKeyboardButton("Generate Wallet 🔐", callback_data="genwallet")],
        [InlineKeyboardButton("Dump All 💸", callback_data="dump")],
        [InlineKeyboardButton("My Profits 📈", callback_data="profits")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🧠 Memecoin Dev Menu:", reply_markup=markup)

# Handler tombol menu
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in authorized_users:
        await query.edit_message_text("❌ Kamu belum login. Gunakan /start 1722")
        return

    if query.data == "genwallet":
        wallet = Keypair()
        await query.edit_message_text(f"🔐 Wallet baru:\n{wallet.public_key}")
    elif query.data == "dump":
        await query.edit_message_text("💸 Simulasi Dump semua token...")
    elif query.data == "profits":
        await query.edit_message_text("📈 Profit estimasi: 3.2 SOL (simulasi)")
    elif query.data == "createcoin":
        await query.edit_message_text("🪙 Gunakan perintah:\n/createcoin NamaCoin SYMBOL 1000000000")

# Perintah buat token
async def createcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("❌ Akses ditolak.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("Format: /createcoin NamaCoin SYMBOL supply")
        return

    name = context.args[0]
    symbol = context.args[1]
    supply = int(context.args[2])

    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        token = await AsyncToken.create_mint(
            client,
            keypair,
            keypair.public_key,
            9,
            TOKEN_PROGRAM_ID
        )
        ata = await token.get_or_create_associated_account_info(keypair.public_key)
        await token.mint_to(ata, keypair, supply)
        await update.message.reply_text(f"✅ Token {name} ({symbol}) berhasil dibuat!\nAddress: {token.pubkey}")

# Jalankan bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createcoin", createcoin))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    print("🤖 Bot berjalan...")
    app.run_polling()
