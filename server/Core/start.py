# import treepoem
# ghostscript
# pip install python-barcode[pillow]
# data — строка для кодирования
# img = treepoem.generate_barcode(
#     barcode_type='code128',  # тип штрих‑кода
#     data='123456789012'      # данные
# )
# # Сохраняем изображение через PIL
# img.convert('1').save('barcode_treepoem.png')


# import barcode
# from barcode.writer import ImageWriter
#
# # Выбираем стандарт штрих‑кода, например Code128
# CODE = barcode.get_barcode_class('code128')
#
# # Данные, которые нужно закодировать
# data = "1746749582688"
#
# # Создаём штрих‑код и сохраняем в файл PNG
# barcode_obj = CODE(data, writer=ImageWriter())
# filename = barcode_obj.save('my_barcode')  # создаст my_barcode.png
# print(f"Saved barcode to {filename}.png")





