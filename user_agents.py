"""Known search engine and AI bot user agent strings."""

USER_AGENTS = {
    # Google
    "Googlebot (Desktop)": {
        "user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "category": "Google",
    },
    "Googlebot (Desktop - Chrome)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/131.0.0.0 Safari/537.36",
        "category": "Google",
    },
    "Googlebot (Smartphone)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "category": "Google",
    },
    "Google-InspectionTool (Desktop)": {
        "user_agent": "Mozilla/5.0 (compatible; Google-InspectionTool/1.0;)",
        "category": "Google",
    },
    "Google-InspectionTool (Smartphone)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 (compatible; Google-InspectionTool/1.0;)",
        "category": "Google",
    },
    "Googlebot-Image": {
        "user_agent": "Googlebot-Image/1.0",
        "category": "Google",
    },
    "Googlebot-Video": {
        "user_agent": "Googlebot-Video/1.0",
        "category": "Google",
    },
    "Google AdsBot (Desktop)": {
        "user_agent": "AdsBot-Google (+http://www.google.com/adsbot.html)",
        "category": "Google",
    },
    "Google AdsBot (Mobile)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 (compatible; AdsBot-Google-Mobile; +http://www.google.com/mobile/adsbot.html)",
        "category": "Google",
    },
    "Google Storebot (Desktop)": {
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64; Storebot-Google/1.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "category": "Google",
    },

    # Bing
    "Bingbot (Desktop)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/116.0.0.0 Safari/537.36",
        "category": "Bing",
    },
    "Bingbot (Mobile)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "category": "Bing",
    },

    # Yandex
    "YandexBot (Desktop)": {
        "user_agent": "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
        "category": "Yandex",
    },
    "YandexBot (Mobile)": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1 (compatible; YandexMobileBot/3.0; +http://yandex.com/bots)",
        "category": "Yandex",
    },

    # Baidu
    "Baiduspider": {
        "user_agent": "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "category": "Baidu",
    },

    # DuckDuckGo
    "DuckDuckBot": {
        "user_agent": "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)",
        "category": "DuckDuckGo",
    },

    # Apple
    "Applebot (Desktop)": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
        "category": "Apple",
    },
    "Applebot (Mobile)": {
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1 (Applebot/0.1; +http://www.apple.com/go/applebot)",
        "category": "Apple",
    },
    "Applebot-Extended (AI training)": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15 (Applebot-Extended/0.1; +http://www.apple.com/go/applebot)",
        "category": "Apple",
    },

    # Google AI
    "Google-Extended (Gemini training)": {
        "user_agent": "Mozilla/5.0 (compatible; Google-Extended; +https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers)",
        "category": "Google",
    },

    # AI Crawlers - OpenAI
    "GPTBot (OpenAI - training)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
        "category": "AI Crawlers",
    },
    "OAI-SearchBot (ChatGPT Search)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)",
        "category": "AI Crawlers",
    },
    "ChatGPT-User (browsing)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)",
        "category": "AI Crawlers",
    },

    # AI Crawlers - Anthropic
    "ClaudeBot (Anthropic - training)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com/crawling-agent)",
        "category": "AI Crawlers",
    },

    # AI Crawlers - Perplexity
    "PerplexityBot (indexing)": {
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://docs.perplexity.ai/docs/perplexity-bot)",
        "category": "AI Crawlers",
    },

    # AI Crawlers - Meta
    "Meta-ExternalAgent": {
        "user_agent": "Mozilla/5.0 (compatible; Meta-ExternalAgent/1.0; +https://developers.facebook.com/docs/sharing/webmasters/crawler)",
        "category": "AI Crawlers",
    },

    # AI Crawlers - Other
    "Amazonbot": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/600.2.5 (KHTML, like Gecko) Version/8.0.2 Safari/600.2.5 (Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot)",
        "category": "AI Crawlers",
    },
    "Bytespider (ByteDance/TikTok)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)",
        "category": "AI Crawlers",
    },

    # Regular browsers (for comparison)
    "Chrome (Desktop - Latest)": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "category": "Browsers",
    },
    "Chrome (Mobile)": {
        "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "category": "Browsers",
    },
}
