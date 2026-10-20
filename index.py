import os
import json
import time
import feedparser
import requests

# 1. جلب مفتاح Groq API من متغيرات البيئة بأمان
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# 2. تحديد مصادر الأخبار (RSS Feeds) المعتمدة مع اسم المصدر الصريح لتعزيز الموثوقية
RSS_SOURCES = [
    {"category": "تكنولوجيا", "name": "أنليمتد تيك", "url": "https://unlimit-tech.com/feed/"},
    {"category": "أخبار الالعاب", "name": "IGN الشرق الأوسط", "url": "https://www.ign.com/rss/games/news.xml"},
    {"category": "أخبار عامة", "name": "BBC عربي", "url": "https://www.bbc.com/arabic/index.xml"},
    {"category": "اقتصاد", "name": "CNBC عربية", "url": "https://www.cnbcarabic.com/rss.xml"}
]

def clean_json_text(text):
    """تنظيف النص المرجع من النموذج لضمان قراءة JSON صحيحة"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def rewrite_news_with_ai(original_title, original_summary):
    """إعادة صياغة الخبر باستعمال Groq API ليصبح فريداً وجذاباً"""
    if not GROQ_API_KEY:
        print("تحذير: مفتاح GROQ_API_KEY غير موجود في متغيرات البيئة. سيتم استخدام النص الأصلي.")
        return original_title, original_summary

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    أنت محرر صحفي محترف لموقع إخباري باسم "ترينديكس".
    قم بإعادة صياغة الخبر التالي بأسلوب صحفي مشوق وفريد وجذاب للقرّاء باللغة العربية:
    العنوان الأصلي: {original_title}
    المحتوى الأصلي: {original_summary}

    المطلوب رد بتنسيق JSON فقط بالشكل التالي دون أي نصوص إضافية خارجه:
    {{
      "title": "عنوان جديد مشوق ومختصر",
      "summary": "ملخص الخبر في 5-6 أسطر بأسلوب عصري"
    }}
    """

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data['choices'][0]['message']['content']
            cleaned_text = clean_json_text(content)
            data = json.loads(cleaned_text)
            return data.get("title", original_title), data.get("summary", original_summary)
        else:
            print(f"خطأ من خادم Groq: {response.status_code} - {response.text}")
            return original_title, original_summary
    except Exception as e:
        print(f"خطأ في الاتصال بـ Groq API: {e}")
        return original_title, original_summary

def fetch_all_news():
    processed_news = []
    article_id = 0  # مهم لربط التفاعلات (Like/Dislike) في الموقع
    
    for source in RSS_SOURCES:
        print(f"\n--- جلب الأخبار من قسم: {source['category']} (المصدر: {source['name']}) ---")
        try:
            feed = feedparser.parse(source['url'])
            
            # جلب أحدث 3 مقالات من كل مصدر
            for entry in feed.entries[:3]:
                raw_title = entry.get('title', '')
                raw_summary = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '#')
                published = entry.get('published', time.strftime("%Y-%m-%d %H:%M"))

                # تحديد اسم المصدر بدقة مع أولوية للتكوين الداخلي ثم وسوم الخلاصة
                source_name = source['name']
                if 'source' in entry and hasattr(entry.source, 'title'):
                    source_name = entry.source.title

                print(f"معالجة: {raw_title[:40]}...")
                ai_title, ai_summary = rewrite_news_with_ai(raw_title, raw_summary)

                processed_news.append({
                    "id": article_id,
                    "title": ai_title,
                    "summary": ai_summary,
                    "category": source['category'],
                    "source": source_name,  # الحقل الجديد لإسناد المصدر
                    "link": link,
                    "date": published,
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop",
                    "likes": 0,
                    "dislikes": 0
                })
                article_id += 1
                
        except Exception as e:
            print(f"خطأ في جلب المصدر {source['category']}: {e}")

    # ضمان حفظ البيانات في مسار المجلد الحالي بأسلوب مطلق ديناميكي
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(base_dir, "news_data.json")
    
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(processed_news, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ تمت عملية التحديث بنجاح! تم حفظ {len(processed_news)} خبراً مع المصادر في {file_name}")

if __name__ == "__main__":
    fetch_all_news()