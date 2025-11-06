import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        prog='pyarabify',
        description='مكتبة Python للبرمجة بالعربية',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
المطور: MERO
Telegram: @QP4RM
GitHub: https://github.com/6x-u

الاستخدام:
  pyarabify program.py              تنفيذ ملف عربي
  pyarabify --dialect short prog.py تنفيذ بلهجة مختصرة
  pyarabify --help                  عرض هذه المساعدة

الأوامر:
  تحميل(اسم_المكتبة)              تثبيت مكتبة Python
  
أمثلة:
  from pyarabify import execute
  execute('اطبع("اهلين دوددد")')
  
  from pyarabify import تحميل
  تحميل('numpy')
  
المميزات:
  - 12,238+ كلمة عربية
  - 4 لهجات عربية مختلفة
  - 57 دالة Git بالعربية
  - 25 دالة ويب (افتح_رابط، الحصول، تحميل)
  - معالجة أخطاء فورية بالعربية مع شرح مبسط
  - دالة تحميل() لتثبيت المكتبات
  - متوافق مع Python 2.7+

للمزيد: https://github.com/6x-u/pyarabify
'''
    )
    
    parser.add_argument('file', nargs='?', help='ملف Python للتنفيذ')
    parser.add_argument('--dialect', default='formal', 
                       choices=['formal', 'short', 'egyptian', 'gulf'],
                       help='اللهجة المستخدمة')
    parser.add_argument('--show-english', action='store_true',
                       help='عرض الكود المترجم للإنجليزية')
    parser.add_argument('--version', action='version',
                       version='pyarabify 2.0.0')
    
    args = parser.parse_args()
    
    if args.file:
        from pyarabify import execute_file
        execute_file(args.file, dialect=args.dialect, show_english=args.show_english)
    else:
        from pyarabify.src.exe import run_repl
        run_repl(dialect=args.dialect)

if __name__ == '__main__':
    main()
