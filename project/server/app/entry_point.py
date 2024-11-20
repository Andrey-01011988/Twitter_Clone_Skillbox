# import uvicorn
#
# from main import app_proj
#
#
# @app_proj.get('/')
# async def hello():
#     """
#     curl -i GET "http://localhost:8000/"
#     :return: str
#     """
#     return f'Welcome'
# # Запуск периодически барахлит и не обнаруживает модуль module_26_fastapi:
# # (venv) uservm@uservm-VirtualBox:~/PycharmProjects/python_advanced/module_26_fastapi$ uvicorn homework.entry_point_26:app_26 --reload
#
#
# if __name__=='__main__':
#     uvicorn.run(app_proj, host='0.0.0.0', port=8000)
# # Запускается либо из консоли либо, если раскомментировать, из файла