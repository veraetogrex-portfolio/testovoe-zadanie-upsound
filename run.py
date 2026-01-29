"""
Скрипт запуска бота.
Использование: python run.py
"""

if __name__ == "__main__":
    from src.bot import main
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
