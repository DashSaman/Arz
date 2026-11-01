# V5 — کلکتور مستقل Base، فقط‌خواندنی و بدون معاملات

**وضعیت: کد و پیکربندی استقرار؛ هنوز روی سرور مستقل مجاز اجرا نشده. تصمیم مالی NO-GO و سرمایه مجاز صفر دلار.**

## هدف

ممیزی PR80 نشان داد در سه روز کامل ۲۸ تا ۳۰ اکتبر، فقط ۹ اجرا از ۱۸ نوبت اسمی GitHub ثبت شده و برای یک کندل، هر دو بازار WETH/cbBTC تا یک ساعت بعد از بسته‌شدن در آرشیو دیده شده‌اند.

این سرویس با ساعت مستقل خود، رأس ۰۰:۱۲، ۰۴:۱۲، ۰۸:۱۲، ۱۲:۱۲، ۱۶:۱۲ و ۲۰:۱۲ UTC فعال می‌شود. timestamp واقعی منبع و SHA نگهداری می‌شوند، فایل‌های ثبت‌شده بازنویسی نمی‌شوند و داده متناقض باعث توقف محافظه‌کارانه می‌شود. جمع‌آوری عقب‌گردی یا ساختن سابقه مصنوعی مجاز نیست.

آرشیو محلی به‌طور خودکار در GitHub قرار نمی‌گیرد. همچنین صرفاً وجود این کلکتور، استقلال واقعی داده، پیوستگی ۱۹۴ کندلی، سودآوری، یا هزینه واقعی اجرای DEX را تأیید نمی‌کند.

## نصب روی میزبان اختصاصی و مجاز پروژه Arz

پیش‌نیازها: Docker Compose، همگام‌سازی UTC، فضای ذخیره دائمی، سیاست دسترسی قانونی به سرویس‌دهندگان و بررسی image رسمی Python. تصویر فعلی هنوز به digest قفل نشده؛ قبل از استقرار تولیدی Digest معتبر را تثبیت کنید. خطای HTTP 429 به معنی مجوز دورزدن محدودیت نرخ نیست.

از ریشه ریپو:

~~~sh
mkdir -p runtime/arz-collector/forward runtime/arz-collector/events
sudo chown -R 65534:65534 runtime/arz-collector
sudo chmod 700 runtime/arz-collector runtime/arz-collector/forward runtime/arz-collector/events
docker compose -f deploy/collector/docker-compose.yml up -d
docker compose -f deploy/collector/docker-compose.yml ps
docker compose -f deploy/collector/docker-compose.yml logs --tail=50
~~~

پیش‌فرض **هیچ درخواست شبکه‌ای ندارد**. تست بدون شبکه:

~~~sh
docker compose -f deploy/collector/docker-compose.yml run --rm \
  arz-readonly-collector python -m scripts.strat01_independent_collector dry-run --data-root /data
~~~

فقط پس از اجازه برای میزبان و منبع داده، دریافت اطلاعات فقط‌خواندنی را فعال کنید:

~~~sh
ARZ_COLLECTOR_NETWORK=explicit-readonly docker compose -f deploy/collector/docker-compose.yml up -d --force-recreate
~~~

فعال‌شدن این گزینه دسترسی کیف پول، امضا، approve، ارسال تراکنش یا اجازه سرمایه واقعی نمی‌دهد.

توقف بدون حذف داده‌ها:

~~~sh
docker compose -f deploy/collector/docker-compose.yml stop
~~~

فایل‌های بازار در runtime/arz-collector/forward و اتفاقات در runtime/arz-collector/events می‌مانند. اگر .collector.lock پس از توقف باقی ماند، قبل از هر تغییر آن را دستی بررسی کنید. Heartbeat فقط زنده‌بودن سرویس را نشان می‌دهد، نه کامل‌بودن داده بازار.

## شروط پیشرفت

باید تست‌های مصنوعی و CI پاس شوند و سپس اجرای شش نوبت در روز روی سرور مجاز و مستقل واقعاً اندازه‌گیری شود. پیش از سرمایه‌گذاری هنوز اثبات ۱۹۴ کندل معتبر متوالی، هزینه واقعی سفارش ۲۰ دلاری با تأخیر ۶۰ ثانیه، دست‌کم ۹۰ روز واقعی Paper Trading و حسابرسی امنیتی لازم است. سود و اجازه سرمایه واقعی همچنان تأیید نشده‌اند.
