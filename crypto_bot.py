import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import numpy as np
import praw
import os
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import warnings
warnings.filterwarnings('ignore')

# Sound notification imports
try:
    import pygame
    SOUND_AVAILABLE = True
except ImportError:
    try:
        import winsound
        SOUND_AVAILABLE = True
    except ImportError:
        try:
            import playsound
            SOUND_AVAILABLE = True
        except ImportError:
            SOUND_AVAILABLE = False
            print("⚠️ No sound library available. Install pygame, playsound, or run on Windows for sound notifications.")

# Load environment variables
load_dotenv()
analyzer = SentimentIntensityAnalyzer()

class DayTradingBot:
    def __init__(self):
        self.symbol = "bitcoin"  # Changed to CoinGecko format
        self.balance = 1000  # Starting balance in USDT
        self.risk_per_trade = 2.0  # Risk 2% per trade (higher for day trading)
        self.stop_loss_pct = 0.5  # 0.5% stop loss
        self.take_profit_pct = 1.0  # 1.0% take profit
        self.position = None  # Current position
        self.entry_price = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0
        
        # Initialize sound system
        self.init_sound_system() 
        self.winning_trades = 0
        self.total_pnl = 0
        
        # Initialize sound system
        self.init_sound_system()
        
    def init_sound_system(self):
        """Initialize sound notification system"""
        self.sound_enabled = SOUND_AVAILABLE
        
        if not self.sound_enabled:
            return
            
        try:
            # Try pygame first (most reliable)
            if 'pygame' in globals():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.sound_method = 'pygame'
                print("🔊 Sound notifications enabled (pygame)")
            elif 'winsound' in globals():
                self.sound_method = 'winsound'
                print("🔊 Sound notifications enabled (winsound)")
            elif 'playsound' in globals():
                self.sound_method = 'playsound'
                print("🔊 Sound notifications enabled (playsound)")
            else:
                self.sound_enabled = False
                print("⚠️ Sound notifications disabled")
        except Exception as e:
            self.sound_enabled = False
            print(f"⚠️ Sound initialization failed: {e}")
    
    def create_sound_files(self):
        """Create simple sound files if they don't exist"""
        import struct
        import math
        
        def create_beep(filename, frequency, duration, sample_rate=22050):
            """Create a simple beep sound file"""
            frames = int(duration * sample_rate)
            data = []
            for i in range(frames):
                value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                data.append(struct.pack('<h', value))
            
            # Create WAV file
            with open(filename, 'wb') as f:
                # WAV header
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))  # PCM
                f.write(struct.pack('<H', 1))  # Mono
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(data) * 2))
                for sample in data:
                    f.write(sample)
        
        # Create sound files if they don't exist
        if not os.path.exists('buy_signal.wav'):
            create_beep('buy_signal.wav', 800, 0.5)  # Higher pitch for buy
        
        if not os.path.exists('sell_signal.wav'):
            create_beep('sell_signal.wav', 400, 0.5)  # Lower pitch for sell
    
    def play_notification_sound(self, signal_type):
        """Play notification sound based on signal type"""
        if not self.sound_enabled:
            return
            
        try:
            if signal_type.upper() == "BUY":
                self.play_buy_sound()
            elif signal_type.upper() == "SELL":
                self.play_sell_sound()
        except Exception as e:
            print(f"⚠️ Sound playback failed: {e}")
    
    def play_buy_sound(self):
        """Play buy signal sound"""
        if self.sound_method == 'pygame':
            try:
                # Create sound file if it doesn't exist
                if not os.path.exists('buy_signal.wav'):
                    self.create_sound_files()
                
                buy_sound = pygame.mixer.Sound('buy_signal.wav')
                buy_sound.play()
            except:
                # Fallback to system beep
                self.system_beep(800, 500)  # High pitch
        
        elif self.sound_method == 'winsound':
            # Windows system beep - high pitch for buy
            winsound.Beep(800, 500)
        
        elif self.sound_method == 'playsound':
            try:
                if not os.path.exists('buy_signal.wav'):
                    self.create_sound_files()
                playsound.playsound('buy_signal.wav', block=False)
            except:
                pass
    
    def play_sell_sound(self):
        """Play sell signal sound"""
        if self.sound_method == 'pygame':
            try:
                # Create sound file if it doesn't exist
                if not os.path.exists('sell_signal.wav'):
                    self.create_sound_files()
                
                sell_sound = pygame.mixer.Sound('sell_signal.wav')
                sell_sound.play()
            except:
                # Fallback to system beep
                self.system_beep(400, 500)  # Low pitch
        
        elif self.sound_method == 'winsound':
            # Windows system beep - low pitch for sell
            winsound.Beep(400, 500)
        
        elif self.sound_method == 'playsound':
            try:
                if not os.path.exists('sell_signal.wav'):
                    self.create_sound_files()
                playsound.playsound('sell_signal.wav', block=False)
            except:
                pass
    
    def system_beep(self, frequency, duration):
        """Fallback system beep"""
        if os.name == 'nt':  # Windows
            try:
                import winsound
                winsound.Beep(frequency, duration)
            except:
                print('\a')  # Terminal bell
        else:  # Unix/Linux/Mac
            print('\a')  # Terminal bell

    def setup_reddit_api(self):
        """Setup Reddit API client"""
        try:
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent='day_trading_bot_1.0'
            )
            reddit.user.me()
            return reddit
        except Exception as e:
            print(f"Reddit API setup failed: {e}")
            return None

    def get_crypto_data(self, symbol="BTC", to_symbol="USD"):
        """Fetch cryptocurrency data from CryptoCompare API (free, reliable)"""
        try:
            # CryptoCompare API for historical hourly data (free tier)
            url = 'https://min-api.cryptocompare.com/data/v2/histohour'
            params = {
                'fsym': symbol,      # From symbol (BTC)
                'tsym': to_symbol,   # To symbol (USD)
                'limit': 100,        # Get 100 hours of data
                'aggregate': 1       # 1 hour intervals
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ CryptoCompare API error: {response.status_code}")
                return self.get_alternative_data()
                
            data = response.json()
            
            if 'Data' not in data or 'Data' not in data['Data'] or len(data['Data']['Data']) < 50:
                print(f"❌ Insufficient data from CryptoCompare")
                return self.get_alternative_data()
            
            # Convert CryptoCompare data to DataFrame
            candles = data['Data']['Data']
            
            df_data = []
            for candle in candles:
                df_data.append({
                    'timestamp': candle['time'],
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close']),
                    'volume': float(candle['volumeto']) if candle['volumeto'] > 0 else 1000000
                })
            
            # Create DataFrame
            df = pd.DataFrame(df_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            
            # Sort by timestamp (most recent last)
            df = df.sort_index()
            
            if len(df) < 50:
                print(f"❌ Not enough data: {len(df)}")
                return self.get_alternative_data()
            
            print(f"✅ Successfully fetched {len(df)} hourly candles from CryptoCompare")
            return df
            
        except Exception as e:
            print(f"❌ Error with CryptoCompare: {e}")
            return self.get_alternative_data()
    
    def get_alternative_data(self):
        """Alternative method using Yahoo Finance crypto data"""
        try:
            # Try alternative free API - Yahoo Finance style
            url = 'https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD'
            params = {
                'interval': '1h',
                'range': '5d'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and data['chart']['result']:
                    result = data['chart']['result'][0]
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    
                    df_data = []
                    for i, ts in enumerate(timestamps):
                        if i < len(quotes['open']) and quotes['open'][i] is not None:
                            df_data.append({
                                'timestamp': ts,
                                'open': float(quotes['open'][i]),
                                'high': float(quotes['high'][i]),
                                'low': float(quotes['low'][i]),
                                'close': float(quotes['close'][i]),
                                'volume': float(quotes['volume'][i]) if quotes['volume'][i] else 1000000
                            })
                    
                    if len(df_data) >= 50:
                        df = pd.DataFrame(df_data)
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                        df.set_index('timestamp', inplace=True)
                        df = df.sort_index()
                        print(f"✅ Successfully fetched {len(df)} hourly candles from Yahoo Finance")
                        return df
            
            # If all APIs fail, create synthetic data
            return self.create_synthetic_data()
            
        except Exception as e:
            print(f"❌ Error with alternative API: {e}")
            return self.create_synthetic_data()
    
    def create_synthetic_data(self):
        """Create synthetic OHLCV data for testing (when all APIs fail)"""
        try:
            print("🔄 Creating synthetic data for testing...")
            
            # Base price around current BTC levels
            base_price = 95000  # Approximate BTC price
            
            synthetic_data = []
            current_time = datetime.now()
            
            for i in range(100):  # Create 100 hourly candles
                # Create realistic price movement (random walk)
                time_offset = current_time - pd.Timedelta(hours=100-i)
                
                # Add some trend and noise
                trend = i * 50  # Slight upward trend
                noise = np.random.normal(0, 500)  # Random noise
                base = base_price + trend + noise
                
                # Create OHLCV for this hour
                open_price = base * (1 + np.random.uniform(-0.01, 0.01))
                close_price = base * (1 + np.random.uniform(-0.01, 0.01))
                high_price = max(open_price, close_price) * (1 + np.random.uniform(0, 0.005))
                low_price = min(open_price, close_price) * (1 - np.random.uniform(0, 0.005))
                volume = np.random.uniform(500000, 2000000)
                
                synthetic_data.append({
                    'timestamp': time_offset,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            
            # Create DataFrame
            df = pd.DataFrame(synthetic_data)
            df.set_index('timestamp', inplace=True)
            df = df.sort_index()
            
            print(f"✅ Created {len(df)} synthetic candles for testing")
            print(f"📊 Current synthetic BTC price: ${df['close'].iloc[-1]:.2f}")
            return df
            
        except Exception as e:
            print(f"❌ Error creating synthetic data: {e}")
            return None

    def compute_rsi(self, series, period=14):
        """Calculate RSI for day trading"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def compute_macd(self, close, fast=12, slow=26, signal=9):
        """Calculate MACD for trend analysis"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    def compute_bollinger_bands(self, close, period=20, std=2):
        """Calculate Bollinger Bands for volatility"""
        sma = close.rolling(window=period).mean()
        std_dev = close.rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        return upper_band, sma, lower_band

    def get_news_sentiment(self, keyword="Bitcoin", limit=5):
        """Get sentiment from news articles"""
        try:
            api_key = os.getenv('NEWS_API_KEY')
            if not api_key:
                return 0
                
            url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&pageSize={limit}&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if response.status_code != 200:
                return 0
            
            sentiments = []
            for article in data.get('articles', []):
                title = article.get('title', '')
                description = article.get('description', '')
                text = f"{title} {description}"
                
                if text.strip() and text != "None None":
                    score = analyzer.polarity_scores(text)['compound']
                    sentiments.append(score)
            
            return np.mean(sentiments) if sentiments else 0
        except Exception as e:
            return 0

    def get_fear_greed_index(self):
        """Get Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            fng_value = int(data['data'][0]['value'])
            sentiment = (fng_value - 50) / 50
            sentiment = max(-1, min(1, sentiment))
            return sentiment, fng_value, data['data'][0]['value_classification']
        except Exception as e:
            return 0, 50, "Neutral"

    def get_combined_sentiment(self):
        """Get combined sentiment score"""
        sentiments = []
        
        # News sentiment
        news_sentiment = self.get_news_sentiment()
        if news_sentiment != 0:
            sentiments.append(news_sentiment)
        
        # Fear & Greed Index
        fng_sentiment, fng_value, fng_text = self.get_fear_greed_index()
        if fng_sentiment != 0:
            sentiments.append(fng_sentiment)
        
        combined = np.mean(sentiments) if sentiments else 0
        return combined, fng_value, fng_text

    def generate_day_trading_signal(self, df, sentiment_score):
        """Generate day trading signals with technical + sentiment analysis"""
        # Enhanced data validation
        if df is None:
            print("⚠️ DataFrame is None")
            return "INSUFFICIENT DATA", 0, {}
        
        if len(df) < 50:
            print(f"⚠️ Insufficient data: {len(df)} rows (need at least 50)")
            return "INSUFFICIENT DATA", 0, {}
        
        try:
            # Calculate technical indicators with error handling
            df_copy = df.copy()
            df_copy['rsi'] = self.compute_rsi(df_copy['close'])
            macd, signal_line, hist = self.compute_macd(df_copy['close'])
            df_copy['macd'] = macd
            df_copy['macd_signal'] = signal_line
            df_copy['macd_hist'] = hist
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.compute_bollinger_bands(df_copy['close'])
            df_copy['bb_upper'] = bb_upper
            df_copy['bb_middle'] = bb_middle
            df_copy['bb_lower'] = bb_lower
            
            # EMAs for trend
            df_copy['ema_21'] = df_copy['close'].ewm(span=21).mean()
            df_copy['ema_50'] = df_copy['close'].ewm(span=50).mean()
            
            # Volume analysis
            df_copy['vol_sma'] = df_copy['volume'].rolling(window=20).mean()
            df_copy['vol_ratio'] = df_copy['volume'] / df_copy['vol_sma']
            
            # Validate data before accessing
            if len(df_copy) < 2:
                print("⚠️ Not enough data after calculations")
                return "INSUFFICIENT DATA", 0, {}
            
            # Get latest values with bounds checking
            latest = df_copy.iloc[-1]
            prev = df_copy.iloc[-2]
            
            # Check for NaN values in critical indicators
            if pd.isna(latest['rsi']) or pd.isna(latest['macd_hist']) or pd.isna(latest['ema_21']):
                print("⚠️ NaN values in technical indicators")
                return "WAIT", 0, {
                    'rsi': 50,
                    'macd_cross': 'NONE',
                    'bb_position': 'MIDDLE',
                    'trend': 'NEUTRAL',
                    'volume': 'NORMAL',
                    'price_momentum': '0.00%',
                    'market_structure': 'NEUTRAL',
                    'bullish_score': 0,
                    'bearish_score': 0
                }
            
            # Technical conditions with safe value extraction
            rsi = float(latest['rsi']) if not pd.isna(latest['rsi']) else 50
            macd_cross_up = (not pd.isna(prev['macd_hist']) and not pd.isna(latest['macd_hist']) and 
                           prev['macd_hist'] < 0 and latest['macd_hist'] > 0)
            macd_cross_down = (not pd.isna(prev['macd_hist']) and not pd.isna(latest['macd_hist']) and 
                             prev['macd_hist'] > 0 and latest['macd_hist'] < 0)
            
            price = float(latest['close'])
            bb_upper = float(latest['bb_upper']) if not pd.isna(latest['bb_upper']) else price + 100
            bb_lower = float(latest['bb_lower']) if not pd.isna(latest['bb_lower']) else price - 100
            bb_middle = float(latest['bb_middle']) if not pd.isna(latest['bb_middle']) else price
            
            ema_21 = float(latest['ema_21']) if not pd.isna(latest['ema_21']) else price
            ema_50 = float(latest['ema_50']) if not pd.isna(latest['ema_50']) else price
            vol_ratio = float(latest['vol_ratio']) if not pd.isna(latest['vol_ratio']) else 1.0
            
            # Price momentum with bounds checking
            if len(df_copy) >= 6:
                price_momentum = ((latest['close'] - df_copy.iloc[-6]['close']) / df_copy.iloc[-6]['close']) * 100
            else:
                price_momentum = 0.0
            
            # Market structure with bounds checking
            if len(df_copy) >= 10:
                recent_high = df_copy['high'].rolling(10).max().iloc[-1]
                prev_high = df_copy['high'].rolling(10).max().iloc[-6] if len(df_copy) >= 11 else recent_high
                recent_low = df_copy['low'].rolling(10).min().iloc[-1]
                prev_low = df_copy['low'].rolling(10).min().iloc[-6] if len(df_copy) >= 11 else recent_low
            else:
                recent_high = prev_high = df_copy['high'].max()
                recent_low = prev_low = df_copy['low'].min()

            # BALANCED signal scoring
            bullish_score = 0
            bearish_score = 0
            
            # RSI conditions (BALANCED)
            if rsi < 25:  # Very oversold - strong buy
                bullish_score += 4
            elif rsi < 35:  # Oversold - moderate buy
                bullish_score += 2
            elif rsi > 75:  # Very overbought - strong sell
                bearish_score += 4
            elif rsi > 65:  # Overbought - moderate sell
                bearish_score += 2
            
            # MACD conditions (BALANCED)
            if macd_cross_up:
                bullish_score += 3
            elif macd_cross_down:
                bearish_score += 3
            elif not pd.isna(latest['macd_hist']) and not pd.isna(prev['macd_hist']):
                if latest['macd_hist'] > prev['macd_hist']:  # MACD strengthening
                    bullish_score += 1
                elif latest['macd_hist'] < prev['macd_hist']:  # MACD weakening
                    bearish_score += 1
            
            # Bollinger Bands (BALANCED)
            if price <= bb_lower:  # Near lower band - buy signal
                bullish_score += 3
            elif price >= bb_upper:  # Near upper band - sell signal
                bearish_score += 3
            elif price > bb_middle:  # Upper half
                if latest['close'] > prev['close']:  # Price rising in upper area
                    bullish_score += 1
            else:  # Lower half
                if latest['close'] < prev['close']:  # Price falling in lower area
                    bearish_score += 1
            
            # Trend conditions (BALANCED)
            if ema_21 > ema_50:  # Uptrend
                if price > ema_21:  # Price above trend
                    bullish_score += 2
                elif price < ema_21:  # Price below trend in uptrend
                    bearish_score += 1
            else:  # Downtrend
                if price < ema_21:  # Price below trend
                    bearish_score += 2
                elif price > ema_21:  # Price above trend in downtrend
                    bullish_score += 1
            
            # Price momentum (BALANCED)
            if price_momentum > 0.5:  # Strong upward momentum
                bullish_score += 2
            elif price_momentum > 0.1:  # Mild upward momentum
                bullish_score += 1
            elif price_momentum < -0.5:  # Strong downward momentum
                bearish_score += 2
            elif price_momentum < -0.1:  # Mild downward momentum
                bearish_score += 1
            
            # Volume analysis (BALANCED)
            if vol_ratio > 1.5:  # High volume
                if price_momentum > 0:  # High volume with price rise = accumulation
                    bullish_score += 2
                elif price_momentum < 0:  # High volume with price decline = distribution
                    bearish_score += 2
            
            # Sentiment influence (BALANCED)
            if sentiment_score > 0.3:  # Positive sentiment
                bullish_score += 1
            elif sentiment_score < -0.3:  # Negative sentiment
                bearish_score += 1
            
            # Market structure analysis
            if recent_high > prev_high:  # Higher highs pattern
                bullish_score += 1
            elif recent_high < prev_high:  # Lower highs pattern
                bearish_score += 1
                
            if recent_low > prev_low:  # Higher lows pattern
                bullish_score += 1
            elif recent_low < prev_low:  # Lower lows pattern
                bearish_score += 1
            
            # Generate final signal (BALANCED thresholds)
            signal = "WAIT"
            confidence = 0
            
            if bullish_score >= 5:  # Strong buy signal
                signal = "BUY"
                confidence = min(bullish_score * 10, 100)
            elif bearish_score >= 5:  # Strong sell signal
                signal = "SELL"
                confidence = min(bearish_score * 10, 100)
            elif bullish_score >= 3 and bearish_score <= 1:  # Moderate buy with low bear pressure
                signal = "BUY (weak)"
                confidence = min(bullish_score * 15, 80)
            elif bearish_score >= 3 and bullish_score <= 1:  # Moderate sell with low bull pressure
                signal = "SELL (weak)"
                confidence = min(bearish_score * 15, 80)
            elif sentiment_score > 0.5 and bullish_score >= 2:  # Sentiment-driven buy
                signal = "BUY (sentiment)"
                confidence = 50
            elif sentiment_score < -0.5 and bearish_score >= 2:  # Sentiment-driven sell
                signal = "SELL (sentiment)"
                confidence = 50
            
            # Analysis details
            analysis = {
                'rsi': rsi,
                'macd_cross': 'UP' if macd_cross_up else 'DOWN' if macd_cross_down else 'NONE',
                'bb_position': 'UPPER' if price >= bb_upper else 'LOWER' if price <= bb_lower else 'MIDDLE',
                'trend': 'UP' if ema_21 > ema_50 else 'DOWN',
                'volume': 'HIGH' if vol_ratio > 1.5 else 'NORMAL',
                'price_momentum': f"{price_momentum:.2f}%",
                'market_structure': 'HIGHER_HIGHS' if recent_high > prev_high else 'LOWER_HIGHS' if recent_high < prev_high else 'NEUTRAL',
                'bullish_score': bullish_score,
                'bearish_score': bearish_score
            }
            
            return signal, confidence, analysis
            
        except Exception as e:
            print(f"⚠️ Error in signal generation: {e}")
            return "ERROR", 0, {
                'rsi': 50,
                'macd_cross': 'ERROR',
                'bb_position': 'ERROR',
                'trend': 'ERROR',
                'volume': 'ERROR',
                'price_momentum': 'ERROR',
                'market_structure': 'ERROR',
                'bullish_score': 0,
                'bearish_score': 0
            }

    def calculate_position_size(self, current_price):
        """Calculate position size based on risk management"""
        risk_amount = self.balance * (self.risk_per_trade / 100)
        stop_loss_amount = current_price * (self.stop_loss_pct / 100)
        position_size = risk_amount / stop_loss_amount
        return round(position_size, 6)

    def execute_trade(self, signal, current_price, confidence):
        """Simulate trade execution with sound notification"""
        if self.position is not None:
            return
        
        if signal == "WAIT" or confidence < 60:
            return
        
        position_size = self.calculate_position_size(current_price)
        
        if "BUY" in signal:
            self.position = "LONG"
            self.entry_price = current_price
            print(f"\n🟢 LONG ENTRY: ${self.entry_price:.2f}")
            print(f"📊 Position Size: {position_size:.6f} BTC | Confidence: {confidence}%")
            
            # Play buy sound notification
            self.play_notification_sound("BUY")
            
        elif "SELL" in signal:
            self.position = "SHORT"
            self.entry_price = current_price
            print(f"\n🔴 SHORT ENTRY: ${self.entry_price:.2f}")
            print(f"📊 Position Size: {position_size:.6f} BTC | Confidence: {confidence}%")
            
            # Play sell sound notification
            self.play_notification_sound("SELL")

    def check_exit_conditions(self, current_price):
        """Check stop loss and take profit"""
        if self.position is None:
            return
        
        pnl_pct = 0
        
        if self.position == "LONG":
            pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        elif self.position == "SHORT":
            pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        
        # Check exit conditions
        if pnl_pct <= -self.stop_loss_pct:
            self.close_position("STOP LOSS", current_price, pnl_pct)
        elif pnl_pct >= self.take_profit_pct:
            self.close_position("TAKE PROFIT", current_price, pnl_pct)

    def close_position(self, reason, exit_price, pnl_pct):
        """Close current position"""
        self.total_trades += 1
        
        # Calculate dollar P&L
        position_size = self.calculate_position_size(self.entry_price)
        dollar_pnl = (pnl_pct / 100) * position_size * self.entry_price
        self.total_pnl += dollar_pnl
        
        if pnl_pct > 0:
            self.winning_trades += 1
            result = "✅ WIN"
        else:
            result = "❌ LOSS"
        
        win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
        
        print(f"\n{result} {self.position} {reason}")
        print(f"📈 Entry: ${self.entry_price:.2f} → Exit: ${exit_price:.2f}")
        print(f"💰 P&L: {pnl_pct:.2f}% (${dollar_pnl:.2f})")
        print(f"📊 Total Trades: {self.total_trades} | Win Rate: {win_rate:.1f}% | Total P&L: ${self.total_pnl:.2f}")
        
        self.position = None
        self.entry_price = 0

    def is_signal_time(self):
        """Generate signals every 15 minutes"""
        current_time = datetime.now()
        return current_time.minute % 15 == 0

    def display_market_status(self, df, signal, confidence, analysis, sentiment_score, fng_value, fng_text):
        """Display comprehensive market analysis"""
        current_price = df['close'].iloc[-1]
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{'='*80}")
        print(f"⏰ {timestamp} | 📊 BTC/USD: ${current_price:.2f}")
        print(f"🎯 Signal: {signal} | Confidence: {confidence}%")
        print(f"{'='*80}")
        
        # Technical Analysis (enhanced display)
        print(f"📈 RSI: {analysis['rsi']:.1f} | MACD: {analysis['macd_cross']} | Trend: {analysis['trend']}")
        print(f"📊 Bollinger: {analysis['bb_position']} | Volume: {analysis['volume']}")
        print(f"⚡ Momentum: {analysis['price_momentum']} | Structure: {analysis['market_structure']}")
        print(f"🔥 Bull Score: {analysis['bullish_score']} | Bear Score: {analysis['bearish_score']}")
        
        # Sentiment Analysis
        print(f"💭 Sentiment: {sentiment_score:.3f} | Fear/Greed: {fng_value} ({fng_text})")
        
        # Position Status
        if self.position:
            if self.position == "LONG":
                unrealized_pnl = ((current_price - self.entry_price) / self.entry_price) * 100
            else:
                unrealized_pnl = ((self.entry_price - current_price) / self.entry_price) * 100
            
            print(f"📍 Position: {self.position} @ ${self.entry_price:.2f} | Unrealized: {unrealized_pnl:.2f}%")
        else:
            print(f"📍 Position: None | Looking for setup...")

    def run(self):
        """Main day trading bot loop"""
        print("🚀 DAY TRADING BOT STARTING...")
        print("=" * 80)
        print(f"💰 Balance: ${self.balance}")
        print(f"⚡ Risk per trade: {self.risk_per_trade}%")
        print(f"🛡️ Stop Loss: {self.stop_loss_pct}% | Take Profit: {self.take_profit_pct}%")
        print(f"📊 Signal Frequency: Every 15 minutes")
        print(f"📈 Data Source: CryptoCompare + Yahoo Finance (Free)")
        print(f"🔊 Sound notifications: {'Enabled' if self.sound_enabled else 'Disabled'}")
        print("=" * 80)
        
        while True:
            try:
                # Get market data from multiple sources
                df = self.get_crypto_data()
                if df is None:
                    print("❌ Failed to get market data, retrying in 30 seconds...")
                    time.sleep(30)
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # Check exit conditions
                if self.position:
                    self.check_exit_conditions(current_price)
                
                # Generate signals every 15 minutes
                if self.is_signal_time():
                    # Get sentiment
                    sentiment_score, fng_value, fng_text = self.get_combined_sentiment()
                    
                    # Generate signal
                    signal, confidence, analysis = self.generate_day_trading_signal(df, sentiment_score)
                    
                    # Display status
                    self.display_market_status(df, signal, confidence, analysis, sentiment_score, fng_value, fng_text)
                    
                    # Execute trade
                    if not self.position:
                        self.execute_trade(signal, current_price, confidence)
                
                # Sleep for 30 seconds (reasonable for day trading)
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n👋 Day trading bot stopped by user")
                if self.position:
                    print(f"⚠️ You have an open {self.position} position at ${self.entry_price:.2f}")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)

def main():
    """Initialize and run day trading bot"""
    bot = DayTradingBot()
    bot.run()

if __name__ == "__main__":
    main()