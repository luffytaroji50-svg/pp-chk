import os
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Telegram Bot Setup ---
BOT_TOKEN = "8369356968:AAHzQJMnOWvor5w8FSOt6Ili5NvexWWg5Wo"

application = Application.builder().token(BOT_TOKEN).build()

# --- Original Handlers (from uploaded file) ---
# We inject the user's original code here so their handlers remain intact.
# NOTE: If their original file defined Updater, Dispatcher, etc., we need to replace with Application.
# For now, we'll just append their code here below, then fix references manually if needed.

# --- BEGIN USER ORIGINAL CODE ---
import aiohttp
import asyncio
import time
import json
import random
from pathlib import Path
import threading
from urllib.parse import urlparse
import io
import tempfile
import os
from datetime import datetime
import logging
import traceback

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# Bot configuration
BOT_TOKEN = "8369356968:AAHzQJMnOWvor5w8FSOt6Ili5NvexWWg5Wo"  # Replace with your bot token
ADMIN_IDS = [6307224822]  # Replace with your admin ID

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedResidentialChecker:
    def __init__(self, bot, session):
        self.bot = bot
        self.session = session
        self.premium_proxies = []
        self.checked_count = 0
        self.total_proxies = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # More reliable test endpoints
        self.test_endpoints = [
            'http://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'http://ip-api.com/json/',
            'https://ipinfo.io/json',
            'http://checkip.amazonaws.com',
        ]
        
        # Real browser user agents (recent versions)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]

    def parse_proxy_from_line(self, line):
        """Parse clean proxy format and convert to HTTP URL for aiohttp"""
        try:
            line = line.strip()
            if not line or line.startswith('#'):
                return None, None
            
            # Store original format and prepare clean format
            original_line = line
            
            # Convert to HTTP URL for aiohttp
            if line.startswith(('http://', 'https://')):
                # Already in URL format, extract clean version
                if line.startswith('http://'):
                    auth_part = line[7:]
                else:
                    auth_part = line[8:]
                proxy_url = line
            else:
                # Clean format: convert to HTTP URL
                auth_part = line
                proxy_url = f"http://{line}"
            
            # Convert authentication format for clean output
            clean_proxy = self.convert_to_clean_format(auth_part)
            
            return proxy_url, clean_proxy
        except Exception as e:
            logger.error(f"Error parsing proxy line '{line}': {e}")
            return None, None
    
    def convert_to_clean_format(self, proxy_string):
        """Convert proxy to IP:PORT:USERNAME:PASSWORD format for authentication proxies"""
        try:
            # Handle username:password@host:port format
            if '@' in proxy_string:
                auth_part, host_port = proxy_string.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                    # Return in IP:PORT:USERNAME:PASSWORD format
                    return f"{host_port}:{username}:{password}"
                else:
                    # No password, just username
                    return f"{host_port}:{auth_part}:"
            else:
                # No authentication, just IP:PORT
                return proxy_string
        except Exception as e:
            logger.error(f"Error converting proxy format '{proxy_string}': {e}")
            return proxy_string

    def get_random_headers(self):
        """Generate realistic browser headers with more fields"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    async def advanced_ip_analysis(self, session, proxy_url, ip_address):
        """More comprehensive IP analysis using multiple services"""
        analysis_results = {}
        total_score = 0
        
        # 1. IP-API.com (comprehensive geolocation + hosting detection)
        try:
            url = f'http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,isp,org,as,proxy,hosting,mobile,query'
            async with session.get(url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'success':
                        analysis_results['ip_api'] = data
                        
                        # Scoring based on IP-API results
                        if not data.get('hosting', True):  # Not hosting
                            total_score += 40
                        else:
                            total_score -= 30
                        
                        if not data.get('proxy', True):  # Not flagged as proxy
                            total_score += 40
                        else:
                            total_score -= 30
                        
                        if data.get('mobile', False):  # Mobile connection
                            total_score += 20
                        
                        # ISP analysis
                        isp = data.get('isp', '').lower()
                        residential_isps = ['comcast', 'verizon', 'at&t', 'charter', 'cox', 'frontier', 'centurylink', 
                                          'optimum', 'spectrum', 'xfinity', 'telus', 'bell', 'rogers', 'shaw',
                                          'bt', 'sky', 'virgin', 'ee', 'vodafone', 'three', 'o2',
                                          'deutsche telekom', 'orange', 'bouygues', 'sfr', 'telefonica',
                                          'telecom', 'broadband', 'cable', 'fiber', 'dsl']
                        
                        datacenter_isps = ['amazon', 'google', 'microsoft', 'digitalocean', 'vultr', 'linode',
                                         'ovh', 'hetzner', 'cloudflare', 'hosting', 'server', 'datacenter',
                                         'cloud', 'vps', 'dedicated']
                        
                        if any(keyword in isp for keyword in residential_isps):
                            total_score += 30
                        elif any(keyword in isp for keyword in datacenter_isps):
                            total_score -= 40
            
            await asyncio.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"IP-API check failed for {ip_address}: {str(e)}")
        
        # 2. IPinfo.io (additional verification)
        try:
            url = f'https://ipinfo.io/{ip_address}/json'
            async with session.get(url, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    analysis_results['ipinfo'] = data
                    
                    # Check organization field
                    org = data.get('org', '').lower()
                    if any(keyword in org for keyword in ['hosting', 'cloud', 'server', 'datacenter', 'vps']):
                        total_score -= 25
                    elif any(keyword in org for keyword in ['telecom', 'communications', 'broadband', 'cable']):
                        total_score += 25
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.debug(f"IPinfo check failed for {ip_address}: {str(e)}")
        
        return total_score, analysis_results

    async def stealth_tests(self, session, proxy_url):
        """Enhanced stealth testing"""
        stealth_score = 0
        
        headers = self.get_random_headers()
        
        # Test 1: Header preservation
        try:
            async with session.get('http://httpbin.org/headers', proxy=proxy_url, 
                                 timeout=aiohttp.ClientTimeout(total=15), headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    received_headers = data.get('headers', {})
                    
                    # Check for proxy-related headers (bad)
                    proxy_headers = ['via', 'x-forwarded-for', 'x-real-ip', 'x-proxy', 'forwarded']
                    for header in proxy_headers:
                        if any(h.lower().startswith(header) for h in received_headers.keys()):
                            stealth_score -= 15
                    
                    # Check if User-Agent preserved (good)
                    if received_headers.get('User-Agent') == headers.get('User-Agent'):
                        stealth_score += 10
                    
        except Exception as e:
            logger.debug(f"Header test failed: {str(e)}")
            stealth_score -= 5  # Failed stealth test
        
        return stealth_score

    async def comprehensive_proxy_test(self, session, proxy_data, semaphore):
        """Ultra-comprehensive proxy testing for premium residential detection"""
        async with semaphore:
            try:
                proxy_url, clean_proxy = proxy_data
                start_time = time.time()
                
                # Step 1: Basic connectivity with random endpoint
                test_url = random.choice(self.test_endpoints)
                headers = self.get_random_headers()
                
                async with session.get(test_url, proxy=proxy_url, 
                                     timeout=aiohttp.ClientTimeout(total=30),
                                     headers=headers, ssl=False) as response:
                    
                    if response.status != 200:
                        return clean_proxy, False, 0, None, "Failed connectivity"
                    
                    response_time = round((time.time() - start_time) * 1000, 2)
                    
                    # Extract IP from response
                    try:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            data = await response.json()
                            ip_address = data.get('ip', data.get('origin', '')).split(',')[0].strip()
                        else:
                            ip_address = (await response.text()).strip()
                    except Exception as e:
                        logger.error(f"Error extracting IP: {e}")
                        return clean_proxy, False, 0, None, "Invalid response format"
                    
                    # Validate IP address
                    if not ip_address:
                        return clean_proxy, False, 0, None, "No IP extracted"
                    
                    # Basic IP validation
                    ip_parts = ip_address.split('.')
                    if len(ip_parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                        return clean_proxy, False, 0, None, "Invalid IP format"
                    
                    # Step 2: Advanced IP analysis
                    reputation_score, ip_details = await self.advanced_ip_analysis(session, proxy_url, ip_address)
                    
                    # Step 3: Stealth testing
                    stealth_score = await self.stealth_tests(session, proxy_url)
                    
                    # Step 4: Speed and consistency test
                    speed_score = 0
                    if response_time < 1000:  # Under 1 second
                        speed_score += 10
                    elif response_time < 3000:  # Under 3 seconds
                        speed_score += 5
                    else:  # Over 3 seconds (typical for residential)
                        speed_score += 2
                    
                    # Step 5: Calculate final score
                    final_score = reputation_score + stealth_score + speed_score
                    
                    # Much stricter threshold for premium residential
                    is_premium_residential = final_score >= 40  # Lowered threshold for testing
                    
                    result_details = {
                        'ip': ip_address,
                        'response_time': response_time,
                        'reputation_score': reputation_score,
                        'stealth_score': stealth_score,
                        'speed_score': speed_score,
                        'final_score': final_score,
                        'country': ip_details.get('ip_api', {}).get('country', 'Unknown'),
                        'isp': ip_details.get('ip_api', {}).get('isp', 'Unknown'),
                        'is_hosting': ip_details.get('ip_api', {}).get('hosting', True),
                        'is_proxy': ip_details.get('ip_api', {}).get('proxy', True),
                        'is_premium': is_premium_residential,
                        'analysis': ip_details
                    }
                    
                    status = "PREMIUM RESIDENTIAL" if is_premium_residential else f"NOT PREMIUM (Score: {final_score})"
                    
                    return clean_proxy, is_premium_residential, response_time, result_details, status
                    
            except asyncio.TimeoutError:
                return clean_proxy, False, 0, None, "Timeout"
            except Exception as e:
                logger.error(f"Comprehensive test error: {e}")
                return clean_proxy, False, 0, None, f"Error: {str(e)[:50]}"

    async def test_proxies_chunk(self, proxies_chunk):
        """Test chunk of proxies with enhanced detection"""
        semaphore = asyncio.Semaphore(15)  # Reduced concurrent connections
        
        connector = aiohttp.TCPConnector(
            limit=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout_config = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config
        ) as session:
            
            tasks = []
            for proxy_data in proxies_chunk:
                task = self.comprehensive_proxy_test(session, proxy_data, semaphore)
                tasks.append(task)
            
            # Process results
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    clean_proxy, is_premium, response_time, details, status = result
                    
                    with self.lock:
                        self.checked_count += 1
                        
                        if is_premium and details:
                            self.premium_proxies.append({
                                'proxy': clean_proxy,
                                'response_time': response_time,
                                'details': details
                            })
                            
                            # Update session
                            self.session['premium_proxies'].append({
                                'proxy': clean_proxy,
                                'response_time': response_time,
                                'details': details
                            })
                        
                        self.session['checked_count'] = self.checked_count
                        
                        # Progress update every 5 checks
                        if self.checked_count % 5 == 0:
                            try:
                                await self.send_progress_update()
                            except Exception as e:
                                logger.error(f"Progress update error: {e}")
                                
                except Exception as e:
                    logger.error(f"Result processing error: {e}")
                    with self.lock:
                        self.checked_count += 1

    async def send_progress_update(self):
        """Send progress update to Telegram"""
        if self.session.get('is_cancelled'):
            return
        
        try:
            user_id = self.session['user_id']
            message_id = self.session['status_message_id']
            
            elapsed = time.time() - self.start_time
            progress = (self.checked_count / self.total_proxies) * 100
            rate = self.checked_count / elapsed if elapsed > 0 else 0
            eta = (self.total_proxies - self.checked_count) / rate if rate > 0 else 0
            
            status_text = f"""ð Checking Proxies...

ð Progress: {self.checked_count:,}/{self.total_proxies:,} ({progress:.1f}%)
â±ï¸ Elapsed: {elapsed:.0f}s | Rate: {rate:.1f}/s
â° ETA: {eta:.0f}s remaining
ð Premium Found: {len(self.premium_proxies)}

ð Status: Analyzing premium residential proxies..."""
            
            keyboard = [[InlineKeyboardButton("ð Cancel", callback_data="cancel_session")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=status_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Progress update error: {e}")

    async def run_premium_tests(self, proxies):
        """Run premium residential proxy tests"""
        self.total_proxies = len(proxies)
        self.session['total_proxies'] = self.total_proxies
        
        logger.info(f"Testing {len(proxies)} proxies with PREMIUM RESIDENTIAL detection...")
        
        # Process in smaller chunks to prevent overwhelming
        chunk_size = 50  # Reduced chunk size
        chunks = [proxies[i:i + chunk_size] for i in range(0, len(proxies), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            if self.session.get('is_cancelled'):
                break
            
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} proxies)...")
            await self.test_proxies_chunk(chunk)
            
            # Delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(5)  # Increased delay


class FastProxyChecker:
    def __init__(self, bot, session):
        self.bot = bot
        self.session = session
        self.working_proxies = []
        self.checked_count = 0
        self.total_proxies = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Settings
        self.timeout = 5
        self.max_concurrent = 200
        self.test_url = "http://httpbin.org/ip"
        self.chunk_size = 1000
        
    def parse_proxy(self, proxy_line):
        """Parse all different proxy formats - optimized version"""
        proxy_line = proxy_line.strip()
        if not proxy_line or proxy_line.startswith('#'):
            return None
        
        # Remove (Http) prefix if present
        if proxy_line.startswith('(Http)'):
            proxy_line = proxy_line[6:]
        
        try:
            # Format: http://host:port
            if proxy_line.startswith(('http://', 'https://')):
                return proxy_line
            
            # Format: socks5://host:port (skip SOCKS for speed, or convert)
            if proxy_line.startswith('socks5://'):
                socks_part = proxy_line[9:]
                return f"http://{socks_part}"
            
            # Format: user:pass@host:port
            if '@' in proxy_line and proxy_line.count(':') >= 3:
                auth_part, host_port = proxy_line.split('@', 1)
                username, password = auth_part.split(':', 1)
                return f"http://{username}:{password}@{host_port}"
            
            # Format: IP:PORT:USERNAME:PASSWORD
            parts = proxy_line.split(':')
            if len(parts) >= 4:
                host, port, username = parts[0], parts[1], parts[2]
                password = ':'.join(parts[3:])
                return f"http://{username}:{password}@{host}:{port}"
            
            # Format: IP:PORT
            elif len(parts) == 2:
                host, port = parts[0], parts[1]
                return f"http://{host}:{port}"
        
        except Exception:
            pass
        
        return None

    def clean_proxy_output(self, proxy):
        """Clean proxy for output - remove http:// prefix and return just IP:PORT or user:pass@IP:PORT"""
        if proxy.startswith('http://'):
            return proxy[7:]  # Remove 'http://'
        elif proxy.startswith('https://'):
            return proxy[8:]  # Remove 'https://'
        return proxy

    async def test_proxy_async(self, session, proxy, semaphore):
        """Asynchronous proxy testing"""
        async with semaphore:
            try:
                start_time = time.time()
                
                timeout_config = aiohttp.ClientTimeout(total=self.timeout, connect=self.timeout/2)
                
                async with session.get(
                    self.test_url,
                    proxy=proxy,
                    timeout=timeout_config,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    ssl=False  # Skip SSL verification for speed
                ) as response:
                    
                    if response.status == 200:
                        end_time = time.time()
                        response_time = round((end_time - start_time) * 1000, 2)
                        
                        try:
                            data = await response.json()
                            ip_info = data.get('origin', 'Unknown')
                        except:
                            ip_info = 'Working'
                        
                        return proxy, True, response_time, ip_info
                        
            except Exception:
                pass
            
            return proxy, False, 0, None

    async def test_proxies_chunk(self, proxies_chunk):
        """Test a chunk of proxies asynchronously"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            skip_auto_headers=['User-Agent']
        ) as session:
            
            tasks = []
            for proxy in proxies_chunk:
                task = self.test_proxy_async(session, proxy, semaphore)
                tasks.append(task)
            
            # Process tasks as they complete
            completed = 0
            
            for coro in asyncio.as_completed(tasks):
                if self.session.get('is_cancelled'):
                    break
                    
                result = await coro
                completed += 1
                
                # Update progress
                with self.lock:
                    self.checked_count += 1
                    proxy, is_working, response_time, ip_info = result
                    
                    if is_working:
                        clean_proxy = self.clean_proxy_output(proxy)
                        proxy_data = {
                            'proxy': clean_proxy,
                            'response_time': response_time,
                            'ip': ip_info
                        }
                        self.working_proxies.append(proxy_data)
                        self.session['working_proxies'].append(proxy_data)
                        
                        logger.info(f"Working proxy found: {clean_proxy} | {response_time}ms")
                    
                    self.session['checked_count'] = self.checked_count
                    
                    # Progress update every 20 checks
                    if self.checked_count % 20 == 0:
                        try:
                            await self.send_progress_update()
                        except Exception as e:
                            logger.error(f"Progress update error: {e}")

    async def send_progress_update(self):
        """Send progress update to Telegram"""
        if self.session.get('is_cancelled'):
            return
        
        try:
            user_id = self.session['user_id']
            message_id = self.session['status_message_id']
            
            elapsed = time.time() - self.start_time
            progress = (self.checked_count / self.total_proxies) * 100
            rate = self.checked_count / elapsed if elapsed > 0 else 0
            eta = (self.total_proxies - self.checked_count) / rate if rate > 0 else 0
            
            status_text = f"""ð Checking Proxies...

ð Progress: {self.checked_count:,}/{self.total_proxies:,} ({progress:.1f}%)
â±ï¸ Elapsed: {elapsed:.0f}s | Rate: {rate:.1f}/s
â° ETA: {eta:.0f}s remaining
â Working Found: {len(self.working_proxies)}

ð Status: Fast proxy checking in progress..."""
            
            keyboard = [[InlineKeyboardButton("ð Cancel", callback_data="cancel_session")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=status_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Progress update error: {e}")

    async def run_tests(self, proxies):
        """Run all proxy tests"""
        self.total_proxies = len(proxies)
        self.session['total_proxies'] = self.total_proxies
        
        logger.info(f"Testing {len(proxies)} proxies with FAST checking...")
        
        # Process proxies in chunks to manage memory
        chunks = [proxies[i:i + self.chunk_size] for i in range(0, len(proxies), self.chunk_size)]
        
        for i, chunk in enumerate(chunks):
            if self.session.get('is_cancelled'):
                break
            
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} proxies)...")
            await self.test_proxies_chunk(chunk)
            
            # Small delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)


class UnifiedProxyBot:
    def __init__(self):
        self.active_sessions = {}
        self.session_lock = threading.Lock()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler with mode selection"""
        try:
            user = update.effective_user
            user_id = user.id
            
            welcome_text = f"""ð¤ **Ultimate Proxy Checker Bot**

Hello {user.first_name}! ð

Choose your checking mode:

ð  **Residential Checker** - Advanced analysis to find premium residential proxies with detailed scoring
â¡ **Fast Checker** - Quick HTTP/HTTPS proxy validation for speed

**ð Commands:**
/start - Show this menu
/show - Download current results (during checking)
/cancel - Cancel active session

Ready to check proxies? ð¯"""
            
            keyboard = [
                [InlineKeyboardButton("ð  Residential Checker", callback_data="mode_residential")],
                [InlineKeyboardButton("â¡ Fast Checker", callback_data="mode_fast")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await update.message.reply_text("An error occurred. Please try again.")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle uploaded proxy file"""
        try:
            user_id = update.effective_user.id
            
            if not context.user_data.get('waiting_for_file'):
                await update.message.reply_text(
                    "â ï¸ Please select a checking mode first using /start!"
                )
                return
            
            document = update.message.document
            
            # Validate file
            if not document.file_name.endswith('.txt'):
                await update.message.reply_text(
                    "â Wrong file type!\n\nPlease send a .txt file."
                )
                return
            
            max_size = 20 * 1024 * 1024 if context.user_data.get('mode') == 'fast' else 10 * 1024 * 1024
            if document.file_size > max_size:
                await update.message.reply_text(
                    f"â File too large! Max: {max_size // (1024*1024)}MB"
                )
                return
            
            # Show processing message
            processing_msg = await update.message.reply_text("ð Processing file...")
            
            try:
                # Download and process file
                file = await context.bot.get_file(document.file_id)
                file_content = await file.download_as_bytearray()
                
                # Parse content with better encoding handling
                try:
                    content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = file_content.decode('latin-1')
                    except UnicodeDecodeError:
                        content = file_content.decode('utf-8', errors='ignore')
                
                lines = content.splitlines()
                
                # Clean and validate proxies
                raw_proxies = []
                for line in lines:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith('#'):
                        raw_proxies.append(clean_line)
                
                if not raw_proxies:
                    await processing_msg.edit_text("â No valid proxies found!")
                    return
                
                max_proxies = 50000 if context.user_data.get('mode') == 'fast' else 10000
                if len(raw_proxies) > max_proxies:
                    await processing_msg.edit_text(
                        f"â Too many proxies! Found: {len(raw_proxies):,}, Max: {max_proxies:,}"
                    )
                    return
                
                await processing_msg.delete()
                context.user_data['waiting_for_file'] = False
                await self.start_checking(update, context, raw_proxies, document.file_name)
                
            except Exception as file_error:
                logger.error(f"File processing error: {file_error}")
                logger.error(f"File processing traceback: {traceback.format_exc()}")
                await processing_msg.edit_text(
                    f"â Error processing file: {str(file_error)[:100]}"
                )
                
        except Exception as e:
            logger.error(f"Document handler error: {e}")
            logger.error(f"Document handler traceback: {traceback.format_exc()}")
            await update.message.reply_text(
                "â An error occurred while processing your file. Please try again."
            )

    async def start_checking(self, update: Update, context: ContextTypes.DEFAULT_TYPE, proxies, filename):
        """Start the checking process"""
        try:
            user_id = update.effective_user.id
            mode = context.user_data.get('mode', 'fast')
            
            if user_id in self.active_sessions:
                await update.message.reply_text("â ï¸ Active session already exists!")
                return
            
            logger.info(f"Starting {mode} proxy check for user {user_id}: {len(proxies)} proxies")
            
            # Create session
            session = {
                'user_id': user_id,
                'proxies': proxies,
                'filename': filename,
                'mode': mode,
                'start_time': time.time(),
                'checked_count': 0,
                'total_proxies': len(proxies),
                'is_cancelled': False,
                'status_message_id': None
            }
            
            # Initialize result storage based on mode
            if mode == 'residential':
                session['premium_proxies'] = []
            else:
                session['working_proxies'] = []
            
            self.active_sessions[user_id] = session
            
            # Initial status message
            keyboard = [[InlineKeyboardButton("ð Cancel", callback_data="cancel_session")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if mode == 'residential':
                status_text = f"""ð Residential Proxy Checking Started

ð File: {filename}
ð Proxies: {len(proxies):,}
ð¯ Mode: Premium Residential Detection
â±ï¸ Status: Initializing...

This may take a while. Updates every 5 checks."""
            else:
                status_text = f"""ð Fast Proxy Checking Started

ð File: {filename}
ð Proxies: {len(proxies):,}
ð¯ Mode: Fast HTTP/HTTPS Checking
â¡ Timeout: 5s | Concurrent: 200
â±ï¸ Status: Initializing...

This will be fast! Updates every 20 checks."""
            
            message = await update.message.reply_text(
                status_text, 
                reply_markup=reply_markup
            )
            session['status_message_id'] = message.message_id
            
            # Start checking in background
            asyncio.create_task(self.run_checking_process(context.bot, session))
            
        except Exception as e:
            logger.error(f"Start checking error: {e}")
            logger.error(f"Start checking traceback: {traceback.format_exc()}")
            await update.message.reply_text("â Error starting check process. Please try again.")

    async def run_checking_process(self, bot, session):
        """Main checking process"""
        try:
            logger.info(f"Starting {session['mode']} check process for user {session['user_id']}")
            
            if session['mode'] == 'residential':
                # Initialize residential checker
                checker = EnhancedResidentialChecker(bot, session)
                
                # Convert proxy format
                proxy_data = []
                for line in session['proxies']:
                    proxy_url, clean_proxy = checker.parse_proxy_from_line(line)
                    if proxy_url and clean_proxy:
                        proxy_data.append((proxy_url, clean_proxy))
                
                session['total_proxies'] = len(proxy_data)
                
                if not proxy_data:
                    await self.send_error_message(bot, session, "No valid proxies could be parsed from the file")
                    return
                
                # Run residential checking
                await checker.run_premium_tests(proxy_data)
                
            else:
                # Initialize fast checker
                checker = FastProxyChecker(bot, session)
                
                # Parse proxies
                parsed_proxies = []
                for line in session['proxies']:
                    parsed = checker.parse_proxy(line)
                    if parsed:
                        parsed_proxies.append(parsed)
                
                session['total_proxies'] = len(parsed_proxies)
                
                if not parsed_proxies:
                    await self.send_error_message(bot, session, "No valid proxies could be parsed from the file")
                    return
                
                # Remove duplicates
                unique_proxies = list(dict.fromkeys(parsed_proxies))
                if len(parsed_proxies) != len(unique_proxies):
                    logger.info(f"Removed {len(parsed_proxies) - len(unique_proxies)} duplicate proxies")
                
                session['total_proxies'] = len(unique_proxies)
                
                # Run fast checking
                await checker.run_tests(unique_proxies)
            
            # Send results
            await self.send_final_results(bot, session)
            
        except Exception as e:
            logger.error(f"Checking process error: {e}")
            logger.error(f"Checking process traceback: {traceback.format_exc()}")
            await self.send_error_message(bot, session, str(e))
        
        finally:
            # Clean up
            user_id = session['user_id']
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            logger.info(f"Finished checking for user {user_id}")

    async def send_final_results(self, bot, session):
        """Send final results to user"""
        try:
            user_id = session['user_id']
            mode = session['mode']
            total_time = time.time() - session['start_time']
            
            if mode == 'residential':
                found_proxies = session['premium_proxies']
                proxy_type = "Premium Residential"
            else:
                found_proxies = session['working_proxies']
                proxy_type = "Working"
            
            logger.info(f"Sending results to user {user_id}: {len(found_proxies)} {proxy_type.lower()} proxies found")
            
            # Results summary
            success_rate = (len(found_proxies) / session['total_proxies']) * 100 if session['total_proxies'] > 0 else 0
            avg_rate = session['total_proxies'] / total_time if total_time > 0 else 0
            
            if mode == 'residential':
                summary = f"""â Residential Proxy Checking Complete!

ð Final Results:
â¢ Total checked: {session['total_proxies']:,}
â¢ Premium found: {len(found_proxies)}
â¢ Success rate: {success_rate:.1f}%
â¢ Total time: {total_time:.0f}s

{f"ð Top premium proxies:" if found_proxies else "â No premium residential proxies found"}"""
                
                if found_proxies:
                    # Show top 5
                    sorted_proxies = sorted(found_proxies, key=lambda x: x['details']['final_score'], reverse=True)
                    for i, proxy_data in enumerate(sorted_proxies[:5], 1):
                        details = proxy_data['details']
                        summary += f"\n{i}. {proxy_data['proxy']}"
                        summary += f"\n   â¡ {proxy_data['response_time']}ms | ð {details['final_score']} pts | ð {details['country']}"
            
            else:
                summary = f"""â Fast Proxy Checking Complete!

ð Final Results:
â¢ Total checked: {session['total_proxies']:,}
â¢ Working found: {len(found_proxies)}
â¢ Success rate: {success_rate:.1f}%
â¢ Total time: {total_time:.1f}s
â¢ Average rate: {avg_rate:.1f} proxies/s

{f"ð Top fastest working proxies:" if found_proxies else "â No working proxies found"}"""
                
                if found_proxies:
                    # Show top 5 fastest
                    sorted_proxies = sorted(found_proxies, key=lambda x: x['response_time'])
                    for i, proxy_data in enumerate(sorted_proxies[:5], 1):
                        summary += f"\n{i}. {proxy_data['proxy']}"
                        summary += f"\n   â¡ {proxy_data['response_time']}ms | ð {proxy_data['ip']}"
            
            await bot.send_message(user_id, summary)
            
            # Send result files
            if found_proxies:
                await self.send_result_files(bot, user_id, session)
                
        except Exception as e:
            logger.error(f"Results sending error: {e}")
            logger.error(f"Results sending traceback: {traceback.format_exc()}")

    async def send_result_files(self, bot, user_id, session):
        """Send result files"""
        try:
            mode = session['mode']
            timestamp = int(time.time())
            
            if mode == 'residential':
                found_proxies = session['premium_proxies']
                file_prefix = "premium_proxies"
                
                # Clean file (just proxy addresses)
                clean_content = ""
                for proxy_data in found_proxies:
                    clean_content += f"{proxy_data['proxy']}\n"
                
                clean_file = io.BytesIO(clean_content.encode('utf-8'))
                clean_file.name = f"{file_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    user_id,
                    clean_file,
                    caption=f"ð Premium Proxies ({len(found_proxies)} found)\nReady to use format"
                )
                
                # Detailed file (with analysis)
                detailed_content = f"# Premium Residential Proxies\n"
                detailed_content += f"# Total checked: {session['total_proxies']}\n"
                detailed_content += f"# Premium found: {len(found_proxies)}\n\n"
                
                for proxy_data in found_proxies:
                    details = proxy_data['details']
                    detailed_content += f"{proxy_data['proxy']} # {proxy_data['response_time']}ms | Score: {details['final_score']} | {details['country']} | {details['isp']} | IP: {details['ip']}\n"
                
                detailed_file = io.BytesIO(detailed_content.encode('utf-8'))
                detailed_file.name = f"{file_prefix}_detailed_{timestamp}.txt"
                
                await bot.send_document(
                    user_id,
                    detailed_file,
                    caption="ð Detailed Analysis\nComplete proxy information with scores"
                )
                
            else:
                found_proxies = session['working_proxies']
                file_prefix = "working_proxies"
                
                # Clean file (just proxy addresses)
                clean_content = ""
                for proxy_data in found_proxies:
                    clean_content += f"{proxy_data['proxy']}\n"
                
                clean_file = io.BytesIO(clean_content.encode('utf-8'))
                clean_file.name = f"{file_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    user_id,
                    clean_file,
                    caption=f"ð Working Proxies ({len(found_proxies)} found)\nReady to use format"
                )
                
                # Detailed file (with response times)
                detailed_content = f"# Fast Proxy Check Results\n"
                detailed_content += f"# Total checked: {session['total_proxies']}\n"
                detailed_content += f"# Working found: {len(found_proxies)}\n\n"
                
                # Sort by response time for detailed file
                sorted_proxies = sorted(found_proxies, key=lambda x: x['response_time'])
                for proxy_data in sorted_proxies:
                    detailed_content += f"{proxy_data['proxy']} # {proxy_data['response_time']}ms | IP: {proxy_data['ip']}\n"
                
                detailed_file = io.BytesIO(detailed_content.encode('utf-8'))
                detailed_file.name = f"{file_prefix}_detailed_{timestamp}.txt"
                
                await bot.send_document(
                    user_id,
                    detailed_file,
                    caption="ð Detailed Results\nWith response times and IP info"
                )
            
            logger.info(f"Sent result files to user {user_id}")
            
        except Exception as e:
            logger.error(f"File sending error: {e}")
            logger.error(f"File sending traceback: {traceback.format_exc()}")

    async def send_error_message(self, bot, session, error):
        """Send error message"""
        try:
            await bot.send_message(
                session['user_id'],
                f"â Error during checking:\n{str(error)[:200]}\n\nPlease try again with /start"
            )
        except Exception as e:
            logger.error(f"Error message sending failed: {e}")

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel session command"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.active_sessions:
                await update.message.reply_text("â¹ï¸ No active session to cancel.")
                return
            
            self.active_sessions[user_id]['is_cancelled'] = True
            await update.message.reply_text("ð Session cancelled.\n\nUse /start to begin again.")
            
            # Clean up after delay
            await asyncio.sleep(3)
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
                
        except Exception as e:
            logger.error(f"Cancel command error: {e}")
            await update.message.reply_text("â Error cancelling session.")

    async def show_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current working/premium proxies command"""
        try:
            user_id = update.effective_user.id
            
            if user_id not in self.active_sessions:
                await update.message.reply_text(
                    "â¹ï¸ No active session found.\n\n"
                    "Start checking proxies with /start first!"
                )
                return
            
            session = self.active_sessions[user_id]
            mode = session.get('mode', 'fast')
            
            # Get current results
            if mode == 'residential':
                current_proxies = session.get('premium_proxies', [])
                proxy_type = "Premium Residential"
                emoji = "ð"
            else:
                current_proxies = session.get('working_proxies', [])
                proxy_type = "Working"
                emoji = "â"
            
            if not current_proxies:
                progress = (session.get('checked_count', 0) / session.get('total_proxies', 1)) * 100
                await update.message.reply_text(
                    f"ð **Current Progress:** {progress:.1f}%\n\n"
                    f"â No {proxy_type.lower()} proxies found yet.\n\n"
                    f"Keep waiting... The checking is still in progress! ð"
                )
                return
            
            # Send current status
            elapsed = time.time() - session.get('start_time', time.time())
            progress = (session.get('checked_count', 0) / session.get('total_proxies', 1)) * 100
            
            status_msg = f"""{emoji} **Current {proxy_type} Proxies Found**

ð **Progress:** {session.get('checked_count', 0):,}/{session.get('total_proxies', 0):,} ({progress:.1f}%)
â±ï¸ **Time Elapsed:** {elapsed:.0f}s
{emoji} **Found So Far:** {len(current_proxies)}

ð¥ Sending current results..."""
            
            await update.message.reply_text(status_msg, parse_mode=ParseMode.MARKDOWN)
            
            # Send current result files
            await self.send_current_results(update.effective_chat.id, session, context.bot)
            
        except Exception as e:
            logger.error(f"Show command error: {e}")
            await update.message.reply_text("â Error retrieving current results.")

    async def send_current_results(self, chat_id, session, bot):
        """Send current working/premium proxies as files"""
        try:
            mode = session.get('mode', 'fast')
            timestamp = int(time.time())
            
            if mode == 'residential':
                current_proxies = session.get('premium_proxies', [])
                file_prefix = "current_premium"
                detailed_prefix = "current_premium_detailed"
                
                if not current_proxies:
                    return
                
                # Clean file (just proxy addresses)
                clean_content = ""
                for proxy_data in current_proxies:
                    clean_content += f"{proxy_data['proxy']}\n"
                
                clean_file = io.BytesIO(clean_content.encode('utf-8'))
                clean_file.name = f"{file_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    chat_id,
                    clean_file,
                    caption=f"ð **Current Premium Proxies** ({len(current_proxies)} found so far)\nð Checking still in progress..."
                )
                
                # Detailed file with analysis
                detailed_content = f"# Current Premium Residential Proxies (Partial Results)\n"
                detailed_content += f"# Found so far: {len(current_proxies)}\n"
                detailed_content += f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                # Sort by score (highest first)
                sorted_proxies = sorted(current_proxies, key=lambda x: x['details']['final_score'], reverse=True)
                for proxy_data in sorted_proxies:
                    details = proxy_data['details']
                    detailed_content += f"{proxy_data['proxy']} # {proxy_data['response_time']}ms | Score: {details['final_score']} | {details['country']} | {details['isp']} | IP: {details['ip']}\n"
                
                detailed_file = io.BytesIO(detailed_content.encode('utf-8'))
                detailed_file.name = f"{detailed_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    chat_id,
                    detailed_file,
                    caption="ð **Current Detailed Analysis**\nWith scores and full proxy information"
                )
                
            else:  # fast mode
                current_proxies = session.get('working_proxies', [])
                file_prefix = "current_working"
                detailed_prefix = "current_working_detailed"
                
                if not current_proxies:
                    return
                
                # Clean file (just proxy addresses)
                clean_content = ""
                for proxy_data in current_proxies:
                    clean_content += f"{proxy_data['proxy']}\n"
                
                clean_file = io.BytesIO(clean_content.encode('utf-8'))
                clean_file.name = f"{file_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    chat_id,
                    clean_file,
                    caption=f"ð **Current Working Proxies** ({len(current_proxies)} found so far)\nð Checking still in progress..."
                )
                
                # Detailed file with response times
                detailed_content = f"# Current Working Proxies (Partial Results)\n"
                detailed_content += f"# Found so far: {len(current_proxies)}\n"
                detailed_content += f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                # Sort by response time (fastest first)
                sorted_proxies = sorted(current_proxies, key=lambda x: x['response_time'])
                for proxy_data in sorted_proxies:
                    detailed_content += f"{proxy_data['proxy']} # {proxy_data['response_time']}ms | IP: {proxy_data['ip']}\n"
                
                detailed_file = io.BytesIO(detailed_content.encode('utf-8'))
                detailed_file.name = f"{detailed_prefix}_{timestamp}.txt"
                
                await bot.send_document(
                    chat_id,
                    detailed_file,
                    caption="ð **Current Detailed Results**\nWith response times and IP information"
                )
            
            logger.info(f"Sent current results to chat {chat_id}: {len(current_proxies)} proxies")
            
        except Exception as e:
            logger.error(f"Current results sending error: {e}")
            logger.error(f"Current results traceback: {traceback.format_exc()}")
            try:
                await bot.send_message(chat_id, "â Error sending current results files.")
            except:
                pass

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user_id = update.effective_user.id
            
            if data == "mode_residential":
                context.user_data['mode'] = 'residential'
                context.user_data['waiting_for_file'] = True
                
                instructions = """ð  **Residential Proxy Checker Mode**

ð Send me your proxy list file

ð **Supported formats:**
```
ip:port
ip:port:username:password  
username:password@ip:port
http://ip:port
http://username:password@ip:port
```

ð **Requirements:**
â¢ File must be .txt format
â¢ One proxy per line
â¢ Maximum 10,000 proxies

ð¬ **What this mode does:**
â¢ Advanced IP reputation analysis
â¢ Residential ISP detection  
â¢ Stealth testing
â¢ Premium scoring system
â¢ Detailed country & ISP info

ð¤ Upload your file now..."""
                
                await query.edit_message_text(instructions, parse_mode=ParseMode.MARKDOWN)
                
            elif data == "mode_fast":
                context.user_data['mode'] = 'fast'
                context.user_data['waiting_for_file'] = True
                
                instructions = """â¡ **Fast Proxy Checker Mode**

ð Send me your proxy list file

ð **Supported formats:**
```
ip:port
ip:port:username:password  
username:password@ip:port
http://ip:port
http://username:password@ip:port
socks5://ip:port
```

ð **Requirements:**
â¢ File must be .txt format
â¢ One proxy per line  
â¢ Maximum 50,000 proxies

ð **What this mode does:**
â¢ Ultra-fast HTTP/HTTPS testing
â¢ 200 concurrent connections
â¢ 5 second timeout per proxy
â¢ Response time measurement
â¢ Basic IP extraction

ð¤ Upload your file now..."""
                
                await query.edit_message_text(instructions, parse_mode=ParseMode.MARKDOWN)
                
            elif data == "cancel_session":
                if user_id not in self.active_sessions:
                    await query.edit_message_text("â No active session found.")
                    return
                
                self.active_sessions[user_id]['is_cancelled'] = True
                
                await query.edit_message_text(
                    "ð Checking cancelled.\n\nUse /start to begin a new session."
                )
                
                # Clean up after delay
                await asyncio.sleep(3)
                if user_id in self.active_sessions:
                    del self.active_sessions[user_id]
                    
        except Exception as e:
            logger.error(f"Button handler error: {e}")
            try:
                await query.edit_message_text("â An error occurred. Please try again with /start.")
            except:
                pass


def main():
    """Main function to run the bot"""
    
    try:
        # Create bot application
        logger.info("Creating Ultimate Proxy Checker Bot application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Create bot instance
        bot_instance = UnifiedProxyBot()
        
        logger.info("Bot instance created successfully")
        
        # Add command handlers
        application.add_handler(CommandHandler("start", bot_instance.start))
        application.add_handler(CommandHandler("show", bot_instance.show_command))
        application.add_handler(CommandHandler("cancel", bot_instance.cancel_command))
        
        # Add message handlers
        application.add_handler(MessageHandler(filters.Document.ALL, bot_instance.handle_document))
        application.add_handler(CallbackQueryHandler(bot_instance.button_handler))
        
        # Enhanced error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Update {update} caused error {context.error}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            
            if update and update.effective_user:
                try:
                    error_msg = "â An unexpected error occurred.\n\n"
                    
                    if "file" in str(context.error).lower():
                        error_msg += "This might be a file processing issue. Please check:\n"
                        error_msg += "â¢ File is in .txt format\n"
                        error_msg += "â¢ File size is within limits\n"
                        error_msg += "â¢ Proxy format is correct\n\n"
                    
                    error_msg += "Please try again with /start"
                    
                    await context.bot.send_message(
                        update.effective_user.id,
                        error_msg
                    )
                except Exception as e:
                    logger.error(f"Error sending error message: {e}")
        
        application.add_error_handler(error_handler)
        
        logger.info("All handlers registered")
        
        # Start bot
        print("\n" + "="*60)
        print("ð ULTIMATE PROXY CHECKER BOT")
        print("="*60)
        print(f"ð¤ Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
        print(f"ð¤ Admin IDs: {ADMIN_IDS}")
        print(f"ð  Residential Mode: Premium detection with scoring")
        print(f"â¡ Fast Mode: Ultra-fast HTTP/HTTPS validation")
        print(f"ð Supports all common proxy formats")
        print(f"ð ï¸ Advanced error handling and logging")
        print("="*60)
        print("â Bot is now running! Send /start to choose mode.")
        print("ð¥ Press Ctrl+C to stop the bot")
        print("="*60)
        
        # Run bot with conflict handling
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting bot (attempt {attempt + 1}/{max_retries})...")
                
                application.run_polling(
                    allowed_updates=Update.ALL_TYPES, 
                    drop_pending_updates=True,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30
                )
                break  # If successful, break the retry loop
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "conflict" in error_msg or "terminated by other" in error_msg:
                    logger.warning(f"Bot conflict detected (attempt {attempt + 1}): {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error("Max retries reached. Please ensure no other bot instances are running.")
                        print("\nâ CONFLICT ERROR: Another bot instance is running!")
                        print("ð§ Solutions:")
                        print("1. Stop all other instances of this bot")
                        print("2. Wait 2-3 minutes for Telegram to clear connections")
                        print("3. Check for background processes: ps aux | grep python")
                        print("4. Restart your terminal/environment")
                        break
                else:
                    # Different error, re-raise
                    raise e
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.error(f"Startup error traceback: {traceback.format_exc()}")
        print(f"\nâ Failed to start bot: {e}")
        print("\nð§ Common fixes:")
        print("1. Check your internet connection")
        print("2. Verify bot token is correct")
        print("3. Install required packages:")
        print("   pip install python-telegram-bot==20.7 aiohttp")
        print("4. Check firewall/proxy settings")


if __name__ == "__main__":
    main()
# --- END USER ORIGINAL CODE ---

# --- Flask Webhook App for Render ---
app = Flask(__name__)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route('/')
def home():
    return "Bot is running!"

# --- Start polling in a background thread so Flask can run ---
def run_bot():
    application.run_polling()

threading.Thread(target=run_bot, daemon=True).start()